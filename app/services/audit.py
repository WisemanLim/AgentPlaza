"""감사 원장(D9-07): append-only + 해시 체인. hash = sha256(prev_hash + 정규화 JSON(이벤트))."""
import hashlib
import json
from datetime import UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import as_utc, utcnow
from app.models import AuditEvent, Setting

GENESIS = "0" * 64
HEAD_KEY = "audit_head"


def digest(value: Any) -> str | None:
    """인자·결과는 원문 대신 해시로만 남긴다(PRD 13.4)."""
    if value is None:
        return None
    raw = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _payload(ev: AuditEvent) -> str:
    body = {
        "ts": as_utc(ev.ts).astimezone(UTC).isoformat(), "actor": ev.actor, "actor_type": ev.actor_type,
        "agent_id": ev.agent_id, "action": ev.action, "resource": ev.resource, "outcome": ev.outcome,
        "args_hash": ev.args_hash, "result_hash": ev.result_hash, "detail": ev.detail or {},
    }
    return json.dumps(body, sort_keys=True, ensure_ascii=False, default=str)


def _chain_hash(prev_hash: str, ev: AuditEvent) -> str:
    return hashlib.sha256((prev_hash + _payload(ev)).encode()).hexdigest()


def record(db: Session, *, actor: str, actor_type: str, action: str, resource: str | None = None,
           agent_id: str | None = None, outcome: str = "ok", args: Any = None, result: Any = None,
           detail: dict | None = None, commit: bool = True) -> AuditEvent:
    # head 행을 잠가 동시 기록 시 체인이 갈라지지 않게 한다(PostgreSQL FOR UPDATE, SQLite 는 쓰기 직렬화).
    head = db.execute(select(Setting).where(Setting.key == HEAD_KEY).with_for_update()).scalar_one_or_none()
    if head is None:
        head = Setting(key=HEAD_KEY, value={"hash": GENESIS})
        db.add(head)
        db.flush()
    ev = AuditEvent(ts=utcnow().replace(microsecond=0), actor=actor, actor_type=actor_type, agent_id=agent_id,
                    action=action, resource=resource, outcome=outcome, args_hash=digest(args),
                    result_hash=digest(result), detail=detail or {}, prev_hash=head.value["hash"])
    ev.hash = _chain_hash(ev.prev_hash, ev)
    db.add(ev)
    head.value = {"hash": ev.hash}
    if commit:
        db.commit()
    else:
        db.flush()
    return ev


def verify(db: Session) -> dict:
    """처음부터 체인을 재계산해 첫 불일치 지점을 돌려준다."""
    prev = GENESIS
    count = 0
    for ev in db.execute(select(AuditEvent).order_by(AuditEvent.id)).scalars():
        if ev.prev_hash != prev or _chain_hash(prev, ev) != ev.hash:
            return {"ok": False, "checked": count, "broken_at": ev.id}
        prev = ev.hash
        count += 1
    return {"ok": True, "checked": count, "head": prev}
