"""Orchestrator·작업·승인 API (D2-01~06, UI C01 의도·계획 카드, I04 승인함)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_user
from app.db import get_db
from app.llm.router import parse_data_class
from app.models import ROLE_RANK, Approval, Task
from app.orchestrator import service
from app.services import approvals

router = APIRouter(tags=["orchestrator"], dependencies=[Depends(require_user)])


class OrchestrateIn(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    session_id: str | None = None
    agent_scope: str | None = None
    data_class: str | None = None  # L0~L3 — 정책 판정 기준(D9-05). 없으면 L2


class Decision(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


def _is_admin(p: Principal) -> bool:
    return ROLE_RANK.get(p.role, 0) >= ROLE_RANK["admin"]


def _task_for(db: Session, task_id: str, p: Principal) -> Task:
    t = db.get(Task, task_id)
    if t is None or (t.principal != p.actor and not _is_admin(p)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "작업 없음 / not found")
    return t


@router.post("/api/orchestrate")
async def orchestrate(body: OrchestrateIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    events: list[dict] = []

    async def collect(ev: dict) -> None:
        events.append(ev)

    try:
        level = parse_data_class(body.data_class)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    result = await service.start(db, principal=p.actor, role=p.role, message=body.message,
                                 session_id=body.session_id, agent_scope=body.agent_scope, emit=collect,
                                 data_class=level)
    return {**result, "events": events}


@router.get("/api/tasks/{task_id}")
def get_task(task_id: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    approvals.expire_due(db)
    return service.out(_task_for(db, task_id, p))


@router.get("/api/approvals")
def list_approvals(state: str = "pending", p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    approvals.expire_due(db)
    q = select(Approval).order_by(Approval.created_at.desc())
    if state != "all":
        q = q.where(Approval.status == state)
    if not _is_admin(p):  # 일반 사용자는 자기 요청만
        q = q.where(Approval.requester == p.actor)
    return [{"id": a.id, "task_id": a.task_id, "agent_id": a.agent_id, "capability": a.capability, "args": a.args,
             "requester": a.requester, "approver": a.approver, "status": a.status, "reason": a.reason,
             "expires_at": a.expires_at, "created_at": a.created_at} for a in db.execute(q).scalars()]


async def _decide(approval_id: str, approve: bool, body: Decision, p: Principal, db: Session) -> dict:
    ap = approvals.decide(db, approval_id, p, approve, body.reason)
    task = db.get(Task, ap.task_id)
    events: list[dict] = []

    async def collect(ev: dict) -> None:
        events.append(ev)

    result = await service.resume(db, task, collect)
    return {"approval": {"id": ap.id, "status": ap.status}, **result, "events": events}


@router.post("/api/approvals/{approval_id}/approve")
async def approve(approval_id: str, body: Decision | None = None, p: Principal = Depends(require_user),
                  db: Session = Depends(get_db)):
    return await _decide(approval_id, True, body or Decision(), p, db)


@router.post("/api/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: Decision | None = None, p: Principal = Depends(require_user),
                 db: Session = Depends(get_db)):
    return await _decide(approval_id, False, body or Decision(), p, db)
