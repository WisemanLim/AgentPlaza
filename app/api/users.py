"""사용자 관리 (D9-02, UI K01). 하위권한만 제어: 자기 역할보다 낮은 역할만 생성·변경할 수 있다."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import user_out
from app.core.deps import Principal, require_admin
from app.core.security import hash_password, temp_password
from app.db import get_db
from app.models import ROLE_RANK, ROLES, User
from app.services import audit, orgs

router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require_admin)])


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+$")
    role: str = "user"
    locale: str = "ko"


class UserPatch(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    locale: str | None = None


def _check_role_grant(p: Principal, role: str) -> None:
    if role not in ROLES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"role ∈ {ROLES}")
    if ROLE_RANK[role] >= ROLE_RANK[p.role]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "자기 역할 이상은 부여 불가 / cannot grant role >= own")


@router.get("")
def list_users(db: Session = Depends(get_db)):
    return [user_out(u) for u in db.execute(select(User).order_by(User.id)).scalars()]


@router.post("", status_code=201)
def create_user(body: UserCreate, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    _check_role_grant(p, body.role)
    if db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 존재하는 이메일 / email exists")
    pw = temp_password()
    u = User(email=body.email.lower(), password_hash=hash_password(pw), role=body.role, locale=body.locale,
             must_change_password=True)
    db.add(u)
    db.flush()
    orgs.join_default(db, u)  # 기본 조직 구성원(PRD Q7)
    audit.record(db, actor=p.actor, actor_type=p.type, action="user.created", resource=f"user:{u.id}",
                 detail={"role": u.role})
    # 임시 비밀번호는 이 응답에서 1회만 노출한다(UI A04).
    return {**user_out(u), "temporary_password": pw}


@router.patch("/{user_id}")
def update_user(user_id: int, body: UserPatch, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "사용자 없음 / not found")
    if str(u.id) == p.id or ROLE_RANK[u.role] >= ROLE_RANK[p.role]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "자기 자신·동급 이상은 변경 불가 / cannot modify self or peers")
    if body.role is not None:
        _check_role_grant(p, body.role)
        u.role = body.role
    if body.is_active is not None:
        u.is_active = body.is_active
    if body.locale is not None:
        u.locale = body.locale
    audit.record(db, actor=p.actor, actor_type=p.type, action="user.updated", resource=f"user:{u.id}",
                 detail=body.model_dump(exclude_none=True))
    return user_out(u)
