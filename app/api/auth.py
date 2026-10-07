"""셋업(최초 관리자)·로그인·토큰 교환·비밀번호 변경 (D9-01, D9-03, UI A01·A02·A04)."""
from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Principal, current_principal, principal_from_api_key, require_user
from app.core.security import create_token, hash_password, verify_password
from app.db import as_utc, get_db, utcnow
from app.models import Agent, User
from app.services.registry import agent_key
from app.services import audit, orgs

router = APIRouter(tags=["auth"])


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=8, max_length=256)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=256)


def user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active, "locale": u.locale,
            "must_change_password": u.must_change_password}


SESSION_COOKIE = "plaza_session"


def _token_response(u: User, response: Response | None = None) -> dict:
    token = create_token(str(u.id), u.role)
    if response is not None:  # 콘솔 iframe(Addon 화면) 용 HttpOnly 쿠키 — forwardAuth 에서만 읽는다(PRD 12.4)
        response.set_cookie(SESSION_COOKIE, token, max_age=settings.jwt_ttl_minutes * 60, httponly=True,
                            samesite="lax", secure=settings.app_env == "prod", path="/")
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.jwt_ttl_minutes * 60,
            "user": user_out(u)}


def is_initialized(db: Session) -> bool:
    return db.scalar(select(func.count()).select_from(User).where(User.role == "supervisor")) > 0


@router.get("/api/setup/status")
def setup_status(db: Session = Depends(get_db)):
    return {"initialized": is_initialized(db)}


@router.post("/api/setup/admin", status_code=201)
def setup_admin(body: Credentials, response: Response, db: Session = Depends(get_db)):
    """supervisor 가 하나도 없을 때만 허용. 이후에는 409 (셋업 위저드 1단계)."""
    if is_initialized(db):
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 초기화됨 / already initialized")
    u = User(email=body.email.lower(), password_hash=hash_password(body.password), role="supervisor")
    db.add(u)
    db.flush()
    orgs.join_default(db, u)  # 기본 조직 구성원(PRD Q7)
    audit.record(db, actor=u.email, actor_type="user", action="setup.admin_created", resource=f"user:{u.id}")
    return _token_response(u, response)


@router.post("/api/auth/login")
def login(body: Credentials, response: Response, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    now = utcnow()
    if u and u.locked_until and as_utc(u.locked_until) > now:
        audit.record(db, actor=body.email.lower(), actor_type="user", action="auth.login", outcome="locked")
        raise HTTPException(status.HTTP_423_LOCKED, "계정 잠김 — 잠시 후 다시 시도 / account locked")
    if u is None or not u.is_active or not verify_password(body.password, u.password_hash):
        if u is not None:
            u.failed_logins += 1
            if u.failed_logins >= settings.login_max_failures:
                u.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
                u.failed_logins = 0
        audit.record(db, actor=body.email.lower(), actor_type="user", action="auth.login", outcome="denied")
        # 아이디·비밀번호 중 무엇이 틀렸는지 구분하지 않는다(UI A01).
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않음 / invalid credentials")
    u.failed_logins = 0
    u.locked_until = None
    audit.record(db, actor=u.email, actor_type="user", action="auth.login")
    return _token_response(u, response)


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/api/auth/forward")
def forward_auth(request: Request, plaza_session: str | None = Cookie(default=None),
                 authorization: str | None = Header(default=None), x_api_key: str | None = Header(default=None),
                 x_forwarded_uri: str | None = Header(default=None), db: Session = Depends(get_db)):
    """Traefik forwardAuth (D8-03): /a/{agent}/… 요청의 사용자(쿠키·Bearer·API 키)를 확인하고,
    통과하면 에이전트 내부 키를 X-Api-Key 로 돌려 Traefik 이 백엔드 요청에 주입하게 한다(키는 클라이언트에 노출 안 됨)."""
    p = current_principal(authorization=authorization or (f"Bearer {plaza_session}" if plaza_session else None),
                          x_api_key=x_api_key, db=db)
    parts = (x_forwarded_uri or "").split("?")[0].strip("/").split("/")
    if len(parts) < 2 or parts[0] != "a":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "agent route expected")
    agent = db.get(Agent, parts[1])
    if agent is None or not agent.is_active or not p.can_access_agent(agent.id) \
            or not orgs.visible(db, p.actor, p.role, agent.id):  # 배치 범위 밖이면 Addon 화면·API 도 막는다
        raise HTTPException(status.HTTP_403_FORBIDDEN, "agent not accessible")
    return Response(status_code=200, headers={"X-Api-Key": agent_key(agent.id), "X-Plaza-User": p.actor})


@router.post("/api/auth/token")
def exchange_api_key(x_api_key: str = Header(), agent: str | None = None, db: Session = Depends(get_db)):
    """API 키 → 단명 서비스 JWT (aud=agent:{id} 선택). 외부 MCP/A2A 클라이언트용."""
    p = principal_from_api_key(db, x_api_key)
    if agent and not p.can_access_agent(agent):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "키 범위 밖 에이전트 / agent out of key scope")
    token = create_token(p.id, p.role, typ="service", scopes=p.scopes,
                         ttl_minutes=settings.service_token_ttl_minutes,
                         audience=f"agent:{agent}" if agent else None)
    audit.record(db, actor=p.actor, actor_type="service", action="auth.token_exchange", agent_id=agent)
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.service_token_ttl_minutes * 60}


@router.get("/api/auth/me")
def me(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    if p.type == "service":
        return {"id": p.id, "type": "service", "role": p.role, "scopes": p.scopes}
    return user_out(db.get(User, int(p.id)))


@router.post("/api/auth/password")
def change_password(body: PasswordChange, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    if p.type != "user":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "사용자 계정 전용 / users only")
    u = db.get(User, int(p.id))
    if not verify_password(body.current_password, u.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "현재 비밀번호 불일치 / current password mismatch")
    u.password_hash = hash_password(body.new_password)
    u.must_change_password = False
    audit.record(db, actor=u.email, actor_type="user", action="auth.password_changed", resource=f"user:{u.id}")
    return {"ok": True}
