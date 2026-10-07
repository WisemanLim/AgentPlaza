"""거버넌스 API (D9-04·D9-05·D9-06·D7-07): 정책 문서, 시크릿(값 비노출), 가드레일 점검, 에이전트 시크릿 pull."""
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin
from app.db import get_db
from app.governance import guardrails
from app.governance import policy as gov
from app.models import Agent, Secret
from app.services import audit, registry
from app.services import secrets as store

router = APIRouter(tags=["governance"])
admin = [Depends(require_admin)]


@router.get("/api/policy", dependencies=admin)
def get_policy(db: Session = Depends(get_db)):
    return gov.get(db)


@router.put("/api/policy")
def put_policy(body: dict, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        out = gov.put(db, body)
    except gov.PolicyError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="policy.updated", detail={"sections": sorted(body)})
    return out


class SecretIn(BaseModel):
    value: str = Field(min_length=1, max_length=8000)


@router.get("/api/secrets", dependencies=admin)
def list_secrets(scope: str | None = None, db: Session = Depends(get_db)):
    q = select(Secret).order_by(Secret.scope, Secret.name)
    if scope:
        q = q.where(Secret.scope == scope)
    return [store.meta(r) for r in db.execute(q).scalars()]


@router.put("/api/secrets/{scope}/{name}")
def put_secret(scope: str, name: str, body: SecretIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """생성·회전. 원문은 응답에 다시 나오지 않는다. 에이전트는 다음 조회(캐시 30초)부터 새 값을 쓴다."""
    try:
        row = store.put(db, scope, name, body.value, p.actor)
    except store.SecretError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="secret.put", resource=f"{scope}/{name}",
                 detail={"version": row.version})
    return store.meta(row)


@router.delete("/api/secrets/{scope}/{name}")
def delete_secret(scope: str, name: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    n = store.delete(db, scope, name)
    if not n:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "시크릿 없음 / not found")
    audit.record(db, actor=p.actor, actor_type=p.type, action="secret.deleted", resource=f"{scope}/{name}")
    return {"deleted": f"{scope}/{name}"}


@router.get("/api/agent/secrets")
def agent_secrets(x_plaza_agent: str = Header(), x_api_key: str = Header(), db: Session = Depends(get_db)):
    """에이전트 시크릿 pull: 자기 내부 키(HMAC 파생)로 인증하고, agent.yaml env.secretRefs 에 선언한 것만 받는다."""
    a = db.get(Agent, x_plaza_agent)
    if a is None or not hmac.compare_digest(x_api_key, registry.agent_key(x_plaza_agent)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid agent credentials")
    refs = a.manifest.get("spec", {}).get("env", {}).get("secretRefs", [])
    values = store.values(db, f"agent:{a.id}", refs)
    audit.record(db, actor=f"agent:{a.id}", actor_type="service", agent_id=a.id, action="secret.read",
                 detail={"names": sorted(values)})
    return values


class CheckIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


@router.post("/api/guardrails/check", dependencies=admin)
def check(body: CheckIn):
    """가드레일 점검(콘솔 시험용): 인젝션 판정 + PII 마스킹 결과."""
    masked, found = guardrails.mask_pii(body.text)
    return {"injection": guardrails.injection(body.text), "pii": {"masked": masked, "found": found}}
