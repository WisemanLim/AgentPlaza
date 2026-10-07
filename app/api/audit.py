"""감사 원장 질의·체인 검증 (D9-07, UI M03). 쓰기 API 는 없다(append-only)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db import get_db
from app.models import AuditEvent
from app.services import audit

router = APIRouter(prefix="/api/audit", tags=["audit"], dependencies=[Depends(require_admin)])


@router.get("")
def list_events(action: str | None = None, agent_id: str | None = None, actor: str | None = None,
                limit: int = Query(100, ge=1, le=1000), before_id: int | None = None,
                db: Session = Depends(get_db)):
    q = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
    if action:
        q = q.where(AuditEvent.action == action)
    if agent_id:
        q = q.where(AuditEvent.agent_id == agent_id)
    if actor:
        q = q.where(AuditEvent.actor == actor)
    if before_id:
        q = q.where(AuditEvent.id < before_id)
    return [{"id": e.id, "ts": e.ts, "actor": e.actor, "actor_type": e.actor_type, "agent_id": e.agent_id,
             "action": e.action, "resource": e.resource, "outcome": e.outcome, "args_hash": e.args_hash,
             "result_hash": e.result_hash, "detail": e.detail, "hash": e.hash}
            for e in db.execute(q).scalars()]


@router.get("/verify")
def verify_chain(db: Session = Depends(get_db)):
    return audit.verify(db)
