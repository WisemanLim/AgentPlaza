"""서비스 계정·API 키 (D9-03, UI K04). 원문 키는 생성 응답에서 1회만 노출하고 해시만 저장한다."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin
from app.core.security import new_api_key
from app.db import get_db, utcnow
from app.models import ROLE_RANK, ROLES, ApiKey
from app.services import audit

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"], dependencies=[Depends(require_admin)])


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: str = "user"
    agents: list[str] = Field(default_factory=lambda: ["*"])


def key_out(k: ApiKey) -> dict:
    return {"id": k.id, "name": k.name, "prefix": k.key_prefix, "role": k.role, "scopes": k.scopes,
            "created_at": k.created_at, "last_used_at": k.last_used_at, "revoked": k.revoked_at is not None}


@router.get("")
def list_keys(db: Session = Depends(get_db)):
    return [key_out(k) for k in db.execute(select(ApiKey).order_by(ApiKey.id)).scalars()]


@router.post("", status_code=201)
def create_key(body: ApiKeyCreate, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    if body.role not in ROLES or ROLE_RANK[body.role] > ROLE_RANK[p.role]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "자기 역할 초과 키 불가 / cannot exceed own role")
    raw, prefix, h = new_api_key()
    k = ApiKey(name=body.name, key_prefix=prefix, key_hash=h, role=body.role,
               scopes={"agents": body.agents or ["*"]}, owner_id=int(p.id) if p.type == "user" else 0)
    db.add(k)
    db.flush()
    audit.record(db, actor=p.actor, actor_type=p.type, action="api_key.created", resource=f"api_key:{k.id}",
                 detail={"role": k.role, "scopes": k.scopes})
    return {**key_out(k), "key": raw}


@router.delete("/{key_id}")
def revoke_key(key_id: int, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    k = db.get(ApiKey, key_id)
    if k is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "키 없음 / not found")
    if k.revoked_at is None:
        k.revoked_at = utcnow()
        audit.record(db, actor=p.actor, actor_type=p.type, action="api_key.revoked", resource=f"api_key:{k.id}")
    return key_out(k)
