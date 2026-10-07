"""공급망 신뢰 (D5-03·D5-04): 신뢰 키 등록·철회, 공급망 정책. admin 이상."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin
from app.db import get_db
from app.models import TrustedKey
from app.services import audit
from app.supplychain import trust

router = APIRouter(prefix="/api/trust", tags=["trust"], dependencies=[Depends(require_admin)])


class KeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    public_key: str = Field(min_length=40, max_length=4000)
    publisher_id: str | None = Field(default=None, max_length=64)


@router.get("/keys")
def list_keys(db: Session = Depends(get_db)):
    return [trust.key_out(k) for k in db.execute(select(TrustedKey).order_by(TrustedKey.created_at)).scalars()]


@router.post("/keys", status_code=201)
def add_key(body: KeyIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        k = trust.add_key(db, name=body.name, public_pem=body.public_key, created_by=p.actor, publisher_id=body.publisher_id)
    except trust.TrustError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="trust.key_added", resource=f"key:{k.kid}",
                 detail={"name": k.name, "publisher_id": k.publisher_id})
    return trust.key_out(k)


@router.delete("/keys/{kid}")
def revoke_key(kid: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        k = trust.revoke_key(db, kid)
    except trust.TrustError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="trust.key_revoked", resource=f"key:{kid}")
    return trust.key_out(k)


@router.get("/policy")
def get_policy(db: Session = Depends(get_db)):
    return trust.policy(db)


@router.put("/policy")
def put_policy(body: dict, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        pol = trust.set_policy(db, body)
    except trust.TrustError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="trust.policy_updated", detail=body)
    return pol
