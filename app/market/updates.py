"""업데이트 알림·자동 갱신·롤백 (D6-07, UI E11).

- 설치 목록 = 내장이 아닌 에이전트 + 같은 id 의 카탈로그 리스팅(정적·DB·원격 레지스트리)
- 권한 변화(egress·시크릿·필수 env·승인 필요 도구·데이터 등급 상향)가 있으면 재동의 없이는 갱신하지 않는다(자동 갱신도 건너뜀)
- 유료 리스팅은 새 버전을 덮는 라이선스가 있어야 갱신(NFR-C4)
- 갱신 = 설치 파이프라인(사전 백업 → 실패 시 롤백, NFR-O4). 이전 버전 롤백은 /api/agents/{id}/rollback
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market import catalog, licensing, payments, remote
from app.models import Agent, AgentVersion, Install
from app.registry import pipeline
from app.registry.pipeline import semver
from app.services import audit, sysconfig
from app.services import notify as alerts

AUTO_KEY = "market.auto_update"
NOTICE_KEY = "market.update_notices"
LEVELS = ("public", "internal", "confidential", "restricted")


class UpdateError(Exception):
    def __init__(self, msg: str, code: int = 409, detail: dict | None = None):
        super().__init__(msg)
        self.code, self.detail = code, detail or {}


def _perms_of_manifest(m: dict) -> dict:
    spec = m.get("spec", {})
    env = spec.get("env", {})
    return {"egress": (spec.get("permissions") or {}).get("network", {}).get("egress", []),
            "secretRefs": env.get("secretRefs", []), "required_env": env.get("required", []),
            "approval": [c["verb"] for c in spec.get("capabilities", []) if c.get("humanApprovalRequired")],
            "capabilities": [c["verb"] for c in spec.get("capabilities", [])],
            "dataClassification": spec.get("governance", {}).get("dataClassification")}


def _perms_of_listing(x: dict) -> dict:
    p = x.get("permissions") or {}
    return {"egress": p.get("egress", []), "secretRefs": p.get("secretRefs", []), "required_env": x.get("required_env", []),
            "approval": x.get("approval", []), "capabilities": x.get("capabilities", []),
            "dataClassification": p.get("dataClassification")}


def diff(cur: dict, new: dict) -> dict:
    added = {k: sorted(set(new[k]) - set(cur[k])) for k in ("egress", "secretRefs", "required_env", "approval",
                                                           "capabilities")}
    rank = lambda v: LEVELS.index(v) if v in LEVELS else 0
    raised = rank(new["dataClassification"]) > rank(cur["dataClassification"])
    out = {**{f"{k}_added": v for k, v in added.items()}, "data_class_raised": raised}
    out["needs_consent"] = raised or any(added[k] for k in ("egress", "secretRefs", "required_env", "approval"))
    return out


def auto_flags(db: Session) -> dict:
    return sysconfig.blob(db, AUTO_KEY)


def set_auto(db: Session, agent_id: str, enabled: bool) -> dict:
    cur = auto_flags(db)
    cur[agent_id] = bool(enabled)
    return sysconfig.put_blob(db, AUTO_KEY, cur)


def installed(db: Session) -> list[dict]:
    auto = auto_flags(db)
    listings = {x["id"]: x for x in catalog.load(db)}
    out = []
    for a in db.execute(select(Agent).where(Agent.builtin.is_(False)).order_by(Agent.id)).scalars():
        vers = list(db.execute(select(AgentVersion).where(AgentVersion.agent_id == a.id)
                               .order_by(AgentVersion.installed_at.desc())).scalars())
        cur = next((v for v in vers if v.current), None)
        x = listings.get(a.id)
        upd = None
        if x is not None and a.source != "link" and x["source"]["type"] not in catalog.REMOTE_TYPES \
                and semver(x["version"]) > semver(a.version):
            upd = {"version": x["version"], **diff(_perms_of_manifest(a.manifest), _perms_of_listing(x)),
                   "paid": payments.is_paid(x),
                   "licensed": bool(licensing.entitled(db, a.id, x["version"])) if payments.is_paid(x) else None}
        out.append({"agent_id": a.id, "name": a.name, "source": a.source, "version": a.version, "status": a.status,
                    "is_active": a.is_active, "listing": x is not None, "latest": x["version"] if x else None,
                    "origin": x.get("origin", "static") if x else None,
                    "installed_by": cur.installed_by if cur else None, "installed_at": cur.installed_at if cur else None,
                    "update": upd, "auto_update": bool(auto.get(a.id)),
                    "versions": [{"version": v.version, "current": v.current, "installed_at": v.installed_at,
                                  "signature": "verified" if v.signature_ok else "unverified"} for v in vers]})
    return out


def notify(db: Session, items: list[dict]) -> list[dict]:
    """새 버전을 처음 본 때 한 번 원장에 알림을 남긴다(콘솔은 설치됨 화면 배지로 보여 준다)."""
    seen = sysconfig.blob(db, NOTICE_KEY)
    fresh = [i for i in items if i["update"] and seen.get(i["agent_id"]) != i["update"]["version"]]
    for i in fresh:
        seen[i["agent_id"]] = i["update"]["version"]
        audit.record(db, actor="system", actor_type="system", agent_id=i["agent_id"], action="market.update_available",
                     resource=f"{i['agent_id']}@{i['update']['version']}", detail={"from": i["version"]})
        alerts.emit(db, "update_available", "info", f"업데이트: {i['agent_id']} {i['version']} → {i['update']['version']}",
                    "권한 변화 — 재동의 필요" if i["update"]["needs_consent"] else "",
                    resource=f"{i['agent_id']}@{i['update']['version']}")
    if fresh:
        sysconfig.put_blob(db, NOTICE_KEY, seen)
    return fresh


def _last_env(db: Session, agent_id: str) -> dict:
    i = db.execute(select(Install).where(Install.agent_id == agent_id, Install.status == "succeeded")
                   .order_by(Install.created_at.desc())).scalars().first()
    return dict(i.env) if i else {}


async def prepare(db: Session, agent_id: str, actor: str, *, consent: bool, kind: str = "update"):
    """갱신 준비 → (install, 산출물, 리스팅, env). 재동의·라이선스가 없으면 UpdateError."""
    item = next((i for i in installed(db) if i["agent_id"] == agent_id), None)
    if item is None:
        raise UpdateError("설치된 에이전트 없음 / not installed", 404)
    upd = item["update"]
    if upd is None:
        raise UpdateError("업데이트 없음 / already latest")
    if upd["needs_consent"] and not consent:
        raise UpdateError("권한 변화 — 재동의 필요 / permission change needs consent", 409, upd)
    if upd["paid"] and not upd["licensed"]:
        raise UpdateError(f"새 버전 {upd['version']} 을 덮는 라이선스 없음 / license required", 402, upd)
    x = catalog.get(agent_id, db)
    data = await catalog.artifact(x, headers=remote.headers_for(db, x, x["version"]))
    env = _last_env(db, agent_id)
    inst = pipeline.new_install(db, source="market", source_ref=f"{agent_id}@{x['version']}", created_by=actor, env=env)
    catalog.count(db, agent_id, x["version"], kind, actor)
    return inst, data, x, env


async def auto_update(db: Session) -> list[dict]:
    """자동 갱신(켜진 에이전트만): 재동의·라이선스가 필요한 건은 건너뛰고 알림만 남긴다."""
    items = installed(db)
    notify(db, items)
    auto = auto_flags(db)
    done = []
    for i in items:
        if not (i["update"] and auto.get(i["agent_id"])):
            continue
        try:
            inst, data, x, env = await prepare(db, i["agent_id"], "system:auto-update", consent=False, kind="update")
        except Exception as exc:
            done.append({"agent_id": i["agent_id"], "skipped": str(exc)})
            continue
        await pipeline.run(inst.id, data, trust=x.get("trust", "community"), env=env)
        db.refresh(inst)
        done.append({"agent_id": i["agent_id"], "install_id": inst.id, "status": inst.status})
    return done
