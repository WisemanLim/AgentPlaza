"""인증·인가 의존성 (D9-02·D9-03). Bearer JWT(사용자/서비스) 또는 x-api-key 를 받는다."""
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import API_KEY_PREFIX, decode_token, hash_api_key
from app.db import get_db, utcnow
from app.models import ROLE_RANK, ApiKey, User


@dataclass
class Principal:
    id: str
    role: str
    type: str  # user | service
    email: str | None = None
    scopes: dict = field(default_factory=lambda: {"agents": ["*"]})

    def can_access_agent(self, agent_id: str) -> bool:
        agents = self.scopes.get("agents", ["*"])
        return "*" in agents or agent_id in agents

    @property
    def actor(self) -> str:
        return self.email or f"{self.type}:{self.id}"


def _unauthorized(detail: str = "인증 필요 / authentication required") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def principal_from_api_key(db: Session, raw: str) -> Principal:
    key = db.execute(select(ApiKey).where(ApiKey.key_hash == hash_api_key(raw))).scalar_one_or_none()
    if key is None or key.revoked_at is not None:
        raise _unauthorized("유효하지 않은 API 키 / invalid api key")
    key.last_used_at = utcnow()
    db.commit()
    return Principal(id=str(key.id), role=key.role, type="service", scopes=key.scopes or {"agents": ["*"]})


def current_principal(authorization: str | None = Header(default=None),
                      x_api_key: str | None = Header(default=None),
                      db: Session = Depends(get_db)) -> Principal:
    if x_api_key:
        return principal_from_api_key(db, x_api_key)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized()
    bearer = authorization.split(" ", 1)[1].strip()
    if bearer.startswith(API_KEY_PREFIX):  # OpenAI 호환 클라이언트는 키를 Bearer 로 보낸다
        return principal_from_api_key(db, bearer)
    try:
        claims = decode_token(bearer)
    except jwt.PyJWTError:
        raise _unauthorized("토큰 만료 또는 무효 / invalid token") from None
    if claims.get("typ") == "service":
        return Principal(id=claims["sub"], role=claims["role"], type="service",
                         scopes=claims.get("scopes") or {"agents": ["*"]})
    if claims.get("typ", "user") != "user":  # 위젯 방문자 토큰 등은 플랫폼 주체가 아니다(D3-07)
        raise _unauthorized("이 토큰으로는 쓸 수 없음 / token not valid here")
    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        raise _unauthorized("비활성 계정 / inactive account")
    return Principal(id=str(user.id), role=user.role, type="user", email=user.email)


def require_role(min_role: str):
    def dep(p: Principal = Depends(current_principal)) -> Principal:
        if ROLE_RANK.get(p.role, 0) < ROLE_RANK[min_role]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"{min_role} 이상 필요 / requires {min_role}")
        return p
    return dep


require_user = require_role("user")
require_admin = require_role("admin")
require_supervisor = require_role("supervisor")
