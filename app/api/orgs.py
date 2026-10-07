"""조직·그룹·구성원(UI K02) · 에이전트 배치 범위(FL-07, deploy_scope) API (PRD Q7·Q12).

조직 생성·삭제 = supervisor · 구성원·그룹 관리 = supervisor 또는 그 조직의 조직 admin · 배치 범위 지정 = 플랫폼 admin 이상.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin, require_supervisor, require_user
from app.db import get_db
from app.models import Agent, AgentScope, GroupMember, Org, OrgGroup, OrgMember, User
from app.services import audit, orgs

router = APIRouter(prefix="/api", tags=["orgs"], dependencies=[Depends(require_user)])


class OrgIn(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")
    name: str = Field(min_length=1, max_length=120)


class MemberIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(default="member", pattern="^(member|admin)$")


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class GroupMemberIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class ScopeIn(BaseModel):
    org_id: str = orgs.DEFAULT
    kind: str = Field(pattern="^(org|group|user)$")
    ids: list = Field(default_factory=list, max_length=500)


def _err(exc: orgs.OrgError) -> HTTPException:
    return HTTPException(exc.code, str(exc))


def _org(db: Session, org_id: str) -> Org:
    o = db.get(Org, org_id)
    if o is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "조직 없음 / org not found")
    return o


def _manage(db: Session, p: Principal, org_id: str) -> Org:
    o = _org(db, org_id)
    if not orgs.is_org_admin(db, p.actor, p.role, org_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "supervisor 또는 조직 admin 만 / org admin only")
    return o


@router.get("/orgs")
def list_orgs(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    """supervisor = 전체, 그 밖 = 내가 속한 조직(내 역할 포함)."""
    orgs.default_org(db)
    db.commit()
    mine = {m.org_id: m.role for m in db.execute(select(OrgMember).join(User, User.id == OrgMember.user_id)
                                                  .where(User.email == p.actor)).scalars()}
    rows = db.execute(select(Org).order_by(Org.id)).scalars()
    return [{**orgs.org_out(db, o), "my_role": mine.get(o.id)} for o in rows
            if p.role == "supervisor" or o.id in mine]


@router.post("/orgs", status_code=201)
def create_org(body: OrgIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    if db.get(Org, body.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 있는 조직 / duplicate")
    o = Org(id=body.id, name=body.name)
    db.add(o)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.created", resource=f"org:{o.id}")
    return orgs.org_out(db, o)


@router.get("/orgs/{org_id}")
def get_org(org_id: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    o = _org(db, org_id)
    member = db.execute(select(OrgMember.id).join(User, User.id == OrgMember.user_id)
                        .where(OrgMember.org_id == org_id, User.email == p.actor)).first()
    if p.role != "supervisor" and not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "조직 없음 / org not found")
    return orgs.org_out(db, o, detail=True) | {"can_manage": orgs.is_org_admin(db, p.actor, p.role, org_id)}


@router.delete("/orgs/{org_id}")
def delete_org(org_id: str, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    if org_id == orgs.DEFAULT:
        raise HTTPException(status.HTTP_409_CONFLICT, "기본 조직은 지울 수 없음 / default org")
    o = _org(db, org_id)
    gids = list(db.execute(select(OrgGroup.id).where(OrgGroup.org_id == org_id)).scalars())
    db.execute(delete(GroupMember).where(GroupMember.group_id.in_(gids)))
    for model in (OrgGroup, OrgMember, AgentScope):
        db.execute(delete(model).where(model.org_id == org_id))
    db.delete(o)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.deleted", resource=f"org:{org_id}")
    return {"deleted": org_id}


@router.put("/orgs/{org_id}/members")
def put_member(org_id: str, body: MemberIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    _manage(db, p, org_id)
    try:
        m = orgs.set_member(db, org_id, body.email, body.role)
    except orgs.OrgError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.member_set", resource=f"org:{org_id}",
                 detail={"user_id": m.user_id, "role": m.role})
    return {"org_id": org_id, "user_id": m.user_id, "role": m.role}


@router.delete("/orgs/{org_id}/members/{user_id}")
def delete_member(org_id: str, user_id: int, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    _manage(db, p, org_id)
    try:
        orgs.remove_member(db, org_id, user_id)
    except orgs.OrgError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.member_removed", resource=f"org:{org_id}",
                 detail={"user_id": user_id})
    return {"removed": user_id}


@router.post("/orgs/{org_id}/groups", status_code=201)
def create_group(org_id: str, body: GroupIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    _manage(db, p, org_id)
    try:
        g = orgs.add_group(db, org_id, body.name)
    except orgs.OrgError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.group_created", resource=f"org:{org_id}",
                 detail={"group": g.id, "name": g.name})
    return {"id": g.id, "org_id": org_id, "name": g.name, "members": []}


@router.delete("/orgs/{org_id}/groups/{gid}")
def delete_group(org_id: str, gid: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    _manage(db, p, org_id)
    try:
        g = orgs.group_of(db, org_id, gid)
    except orgs.OrgError as exc:
        raise _err(exc) from None
    db.execute(delete(GroupMember).where(GroupMember.group_id == gid))
    db.delete(g)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.group_deleted", resource=f"org:{org_id}",
                 detail={"group": gid})
    return {"deleted": gid}


@router.put("/orgs/{org_id}/groups/{gid}/members")
def put_group_member(org_id: str, gid: str, body: GroupMemberIn, p: Principal = Depends(require_user),
                     db: Session = Depends(get_db)):
    _manage(db, p, org_id)
    try:
        orgs.add_group_member(db, org_id, gid, body.email)
    except orgs.OrgError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="org.group_member_added", resource=f"org:{org_id}",
                 detail={"group": gid})
    return {"group": gid, "email": body.email.lower()}


@router.delete("/orgs/{org_id}/groups/{gid}/members/{user_id}")
def delete_group_member(org_id: str, gid: str, user_id: int, p: Principal = Depends(require_user),
                        db: Session = Depends(get_db)):
    _manage(db, p, org_id)
    n = db.execute(delete(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == user_id)).rowcount
    db.commit()
    if not n:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "그룹 구성원 아님 / not a group member")
    return {"removed": user_id}


# ---- 배치 범위(deploy_scope) ----

@router.get("/agents/{agent_id}/scope")
def get_scope(agent_id: str, _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return {"agent_id": agent_id, "scope": orgs.scope_out(db.get(AgentScope, agent_id))}


@router.put("/agents/{agent_id}/scope")
def put_scope(agent_id: str, body: ScopeIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    a = db.get(Agent, agent_id)
    if a is None or a.builtin:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "에이전트 없음(내장 제외) / not found")
    try:
        s = orgs.set_scope(db, agent_id, org_id=body.org_id, kind=body.kind, ids=body.ids, actor=p.actor)
    except orgs.OrgError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.scope_set",
                 detail={"org": s.org_id, "kind": s.kind, "ids": s.ids})
    return {"agent_id": agent_id, "scope": orgs.scope_out(s)}


@router.delete("/agents/{agent_id}/scope")
def delete_scope(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    n = db.execute(delete(AgentScope).where(AgentScope.agent_id == agent_id)).rowcount
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.scope_cleared",
                 detail={"removed": n})
    return {"agent_id": agent_id, "scope": None}
