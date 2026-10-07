"""운영 API (D8-06): 플랫폼 DB + 설치 에이전트 전체 백업. supervisor 전용."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import ops
from app.core.deps import Principal, require_supervisor
from app.db import get_db
from app.runtime.driver import RuntimeFailure
from app.services import audit

router = APIRouter(tags=["ops"])


@router.post("/api/admin/backup")
async def backup_all(p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        out = await ops.backup_all()
    except (RuntimeFailure, AttributeError) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, f"백업 실패 / backup failed: {exc}") from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="platform.backup",
                 detail={"platform": out["platform"].get("backup"), "agents": out["agents"]})
    return out
