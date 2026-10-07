"""조직·그룹(부서)·배치 범위 (PRD Q7·Q12, UI K02·FL-07).

- 기본 조직(default)에 모든 사용자가 들어간다(새 사용자 자동 가입). 조직 admin = 그 조직의 구성원·그룹 관리.
- 에이전트 배치 범위(agent_scopes): 행이 없으면 모두에게 보인다. org = 그 조직 구성원, group = 고른 그룹 구성원,
  user = 고른 사용자. 범위 밖 사용자에게는 에이전트 목록·네비·계획(도구)·MCP·A2A·Addon 화면에서 빠진다.
- supervisor 는 항상 보인다(운영). API 키(서비스 주체)는 키의 agents 범위로 통제한다.
- 데이터 분리(멀티테넌시 X09)는 하지 않는다 — 노출 범위 통제다.
"""
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import AgentScope, GroupMember, Org, OrgGroup, OrgMember, User

DEFAULT = "default"
KINDS = ("org", "group", "user")


class OrgError(ValueError):
    def __init__(self, msg: str, code: int = 422):
        super().__init__(msg)
        self.code = code


def default_org(db: Session) -> Org:
    o = db.get(Org, DEFAULT)
    if o is None:
        o = Org(id=DEFAULT, name="기본 조직")
        db.add(o)
        db.flush()
    return o


def join_default(db: Session, user: User) -> None:
    """새 사용자 = 기본 조직 구성원(호출부가 commit)."""
    default_org(db)
    if not db.execute(select(OrgMember.id).where(OrgMember.org_id == DEFAULT, OrgMember.user_id == user.id)).first():
        db.add(OrgMember(org_id=DEFAULT, user_id=user.id, role="member"))


def _user_id(db: Session, actor: str) -> int | None:
    return db.execute(select(User.id).where(User.email == actor)).scalar_one_or_none()


def hidden_agents(db: Session, actor: str | None, role: str | None) -> set[str]:
    """이 주체에게 보이지 않는 에이전트 id 집합(범위 행이 있고 조건을 못 맞춘 것)."""
    if role == "supervisor" or not actor or actor.startswith("service:"):
        return set()
    scopes = list(db.execute(select(AgentScope)).scalars())
    if not scopes:
        return set()
    uid = _user_id(db, actor)
    orgs = set(db.execute(select(OrgMember.org_id).where(OrgMember.user_id == uid)).scalars()) if uid else set()
    groups = set(db.execute(select(GroupMember.group_id).where(GroupMember.user_id == uid)).scalars()) if uid else set()
    hidden = set()
    for sc in scopes:
        ids = set(sc.ids or [])
        ok = (sc.kind == "org" and sc.org_id in orgs) or (sc.kind == "group" and bool(groups & ids)) \
            or (sc.kind == "user" and uid in ids)
        if not ok:
            hidden.add(sc.agent_id)
    return hidden


def visible(db: Session, actor: str | None, role: str | None, agent_id: str) -> bool:
    return agent_id not in hidden_agents(db, actor, role)


# ---- 관리 ----

def is_org_admin(db: Session, actor: str, role: str, org_id: str) -> bool:
    if role == "supervisor":
        return True
    uid = _user_id(db, actor)
    return bool(uid and db.execute(select(OrgMember.id).where(OrgMember.org_id == org_id, OrgMember.user_id == uid,
                                                             OrgMember.role == "admin")).first())


def org_out(db: Session, o: Org, *, detail: bool = False) -> dict:
    members = list(db.execute(select(OrgMember, User).join(User, User.id == OrgMember.user_id)
                              .where(OrgMember.org_id == o.id).order_by(User.email)).all())
    groups = list(db.execute(select(OrgGroup).where(OrgGroup.org_id == o.id).order_by(OrgGroup.name)).scalars())
    out = {"id": o.id, "name": o.name, "members": len(members), "groups": len(groups), "created_at": o.created_at}
    if detail:
        gm: dict[str, list] = {}
        for g, u in db.execute(select(GroupMember, User).join(User, User.id == GroupMember.user_id)
                               .where(GroupMember.group_id.in_([g.id for g in groups]))).all():
            gm.setdefault(g.group_id, []).append({"user_id": u.id, "email": u.email})
        out["members"] = [{"user_id": u.id, "email": u.email, "role": m.role} for m, u in members]
        out["groups"] = [{"id": g.id, "name": g.name, "members": gm.get(g.id, [])} for g in groups]
        out["agents"] = [scope_out(s) for s in db.execute(select(AgentScope).where(AgentScope.org_id == o.id)).scalars()]
    return out


def user_by_email(db: Session, email: str) -> User:
    u = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if u is None:
        raise OrgError("사용자 없음 / user not found", 404)
    return u


def set_member(db: Session, org_id: str, email: str, role: str) -> OrgMember:
    if role not in ("member", "admin"):
        raise OrgError("role ∈ member | admin")
    u = user_by_email(db, email)
    m = db.execute(select(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == u.id)).scalar_one_or_none()
    m = m or OrgMember(org_id=org_id, user_id=u.id)
    m.role = role
    db.add(m)
    db.commit()
    return m


def remove_member(db: Session, org_id: str, user_id: int) -> None:
    gids = list(db.execute(select(OrgGroup.id).where(OrgGroup.org_id == org_id)).scalars())
    db.execute(delete(GroupMember).where(GroupMember.group_id.in_(gids), GroupMember.user_id == user_id))
    n = db.execute(delete(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == user_id)).rowcount
    db.commit()
    if not n:
        raise OrgError("구성원 아님 / not a member", 404)


def add_group(db: Session, org_id: str, name: str) -> OrgGroup:
    if db.execute(select(OrgGroup.id).where(OrgGroup.org_id == org_id, OrgGroup.name == name)).first():
        raise OrgError("같은 이름의 그룹 / duplicate group", 409)
    g = OrgGroup(id=str(uuid.uuid4()), org_id=org_id, name=name)
    db.add(g)
    db.commit()
    return g


def group_of(db: Session, org_id: str, gid: str) -> OrgGroup:
    g = db.get(OrgGroup, gid)
    if g is None or g.org_id != org_id:
        raise OrgError("그룹 없음 / group not found", 404)
    return g


def add_group_member(db: Session, org_id: str, gid: str, email: str) -> None:
    group_of(db, org_id, gid)
    u = user_by_email(db, email)
    if not db.execute(select(OrgMember.id).where(OrgMember.org_id == org_id, OrgMember.user_id == u.id)).first():
        raise OrgError("조직 구성원만 그룹에 넣을 수 있음 / not an org member")
    if not db.execute(select(GroupMember.id).where(GroupMember.group_id == gid, GroupMember.user_id == u.id)).first():
        db.add(GroupMember(group_id=gid, user_id=u.id))
        db.commit()


# ---- 배치 범위 ----

def scope_out(s: AgentScope | None) -> dict | None:
    return None if s is None else {"agent_id": s.agent_id, "org_id": s.org_id, "kind": s.kind, "ids": s.ids,
                                   "updated_by": s.updated_by, "updated_at": s.updated_at}


def set_scope(db: Session, agent_id: str, *, org_id: str, kind: str, ids: list, actor: str) -> AgentScope:
    if kind not in KINDS:
        raise OrgError(f"kind ∈ {KINDS}")
    if db.get(Org, org_id) is None:
        raise OrgError("조직 없음 / org not found", 404)
    if kind == "group":
        valid = set(db.execute(select(OrgGroup.id).where(OrgGroup.org_id == org_id)).scalars())
        if not ids or not set(ids) <= valid:
            raise OrgError("그 조직의 그룹 id 목록이 필요 / group ids of the org required")
    elif kind == "user":
        members = set(db.execute(select(OrgMember.user_id).where(OrgMember.org_id == org_id)).scalars())
        if not ids or not set(ids) <= members:
            raise OrgError("그 조직 구성원의 사용자 id 목록이 필요 / user ids of org members required")
    else:
        ids = []
    s = db.get(AgentScope, agent_id) or AgentScope(agent_id=agent_id)
    s.org_id, s.kind, s.ids, s.updated_by, s.updated_at = org_id, kind, list(ids), actor, utcnow()
    db.add(s)
    db.commit()
    return s
