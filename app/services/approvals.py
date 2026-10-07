"""휴먼 승인 게이트 (D2-06, DP8): 메타에 선언 → 게이트가 집행 → 원장에 기록. 만료 시 작업 취소(US8)."""
import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Principal
from app.db import as_utc, utcnow
from app.models import ROLE_RANK, Approval, Task
from app.services import audit, sysconfig


def create(db: Session, task: Task, step: dict, requester: str) -> Approval:
    ap = Approval(id=str(uuid.uuid4()), task_id=task.id, step_id=step["id"], agent_id=step["agent"],
                  capability=step["capability"], args=step.get("args", {}), requester=requester,
                  expires_at=utcnow() + timedelta(minutes=sysconfig.get(db, "hitl_ttl_minutes")))
    db.add(ap)
    audit.record(db, actor=requester, actor_type="user", agent_id=step["agent"], action="approval.requested",
                 resource=f"approval:{ap.id}", args=ap.args, detail={"capability": ap.capability, "task": task.id})
    return ap


def expire_due(db: Session) -> list[Approval]:
    now = utcnow()
    expired = []
    for ap in db.execute(select(Approval).where(Approval.status == "pending")).scalars():
        if as_utc(ap.expires_at) <= now:
            ap.status, ap.decided_at = "expired", now
            task = db.get(Task, ap.task_id)
            if task and task.state == "waiting_approval":
                task.state, task.ended_at, task.answer = "canceled", now, "승인 만료로 취소됨 / canceled: approval expired"
            audit.record(db, actor="system", actor_type="system", agent_id=ap.agent_id, action="approval.expired",
                         resource=f"approval:{ap.id}", commit=False)
            expired.append(ap)
    db.commit()
    return expired


def decide(db: Session, approval_id: str, approver: Principal, approve: bool, reason: str | None) -> Approval:
    expire_due(db)
    ap = db.get(Approval, approval_id)
    if ap is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "승인 요청 없음 / not found")
    if ap.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"이미 처리됨 / already {ap.status}")
    if ROLE_RANK.get(approver.role, 0) < ROLE_RANK["admin"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "승인 권한 없음 / approver must be admin+")
    if approver.actor == ap.requester and not settings.hitl_allow_self_approval:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "본인 요청은 승인 불가 / four-eyes rule")
    ap.status = "approved" if approve else "rejected"
    ap.approver, ap.reason, ap.decided_at = approver.actor, reason, utcnow()
    audit.record(db, actor=approver.actor, actor_type=approver.type, agent_id=ap.agent_id,
                 action=f"approval.{ap.status}", resource=f"approval:{ap.id}", detail={"reason": reason or ""})
    return ap
