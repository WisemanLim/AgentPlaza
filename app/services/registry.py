"""에이전트 카탈로그·capability 인덱스 (D5-06·D2-02). 설치 파이프라인(Epic 6)과 Orchestrator 가 공유한다."""
import hashlib
import hmac
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Agent, Capability

BUILTINS = [
    {"id": "orchestrator", "name": "Orchestrator", "type": "service",
     "caps": [("orchestrate", "platform.orchestration", "의도 분류·계획·라우팅·도구 실행 / plan and route a request")]},
    {"id": "assistant", "name": "AI Assistant", "type": "app",
     "caps": [("chat", "platform.assistant", "대화형 어시스턴트 / conversational assistant")]},
]
STOP = {"the", "a", "an", "and", "or", "of", "to", "for", "with", "in", "on", "is", "are"}


def agent_key(agent_id: str) -> str:
    """에이전트 내부 호출 키. 저장하지 않고 필요할 때 파생한다(설치 시 AGENT_API_KEY 로 주입)."""
    secret = (settings.agent_key_secret or settings.jwt_secret).encode()
    return "ak_" + hmac.new(secret, f"agent:{agent_id}".encode(), hashlib.sha256).hexdigest()[:40]


def _text(v) -> str:
    return " ".join(v.values()) if isinstance(v, dict) else str(v or "")


def keywords_for(manifest: dict, cap: dict) -> list[str]:
    meta = manifest.get("metadata", {})
    raw = " ".join([cap["verb"].replace("_", " "), cap["domain"].replace(".", " ").replace("_", " "),
                    _text(cap.get("description")), meta.get("name", ""), _text(meta.get("displayName", ""))])
    words = {w.lower() for w in re.findall(r"\w{2,}", raw)} - STOP
    return sorted(words)


def register(db: Session, manifest: dict, *, endpoint: str | None, source: str = "zip", trust: str = "community",
             builtin: bool = False, status: str = "registered", commit: bool = True) -> Agent:
    """upsert. capability 는 매번 manifest 기준으로 다시 만든다(선언=인덱스, DP4)."""
    meta, spec = manifest["metadata"], manifest["spec"]
    a = db.get(Agent, meta["id"]) or Agent(id=meta["id"])
    a.name, a.type, a.version = meta.get("name", meta["id"]), spec["type"], meta["version"]
    a.endpoint, a.source, a.trust, a.builtin, a.status = endpoint, source, trust, builtin, status
    a.runtime_mode = spec.get("runtime", {}).get("mode", "container")
    a.manifest = manifest
    db.add(a)
    db.flush()
    db.execute(delete(Capability).where(Capability.agent_id == a.id))
    gov_hitl = spec.get("governance", {}).get("humanApprovalRequired", False)
    for c in spec.get("capabilities", []):
        db.add(Capability(agent_id=a.id, verb=c["verb"], domain=c["domain"], description=_text(c.get("description")),
                          input_schema=c.get("inputSchema", {}),
                          human_approval_required=bool(c.get("humanApprovalRequired", False) or gov_hitl),
                          keywords=keywords_for(manifest, c)))
    if commit:
        db.commit()
    return a


def bootstrap_builtins(db: Session) -> None:
    for b in BUILTINS:
        if db.get(Agent, b["id"]):
            continue
        manifest = {"apiVersion": "agentplaza/v1", "kind": "Agent",
                    "metadata": {"id": b["id"], "name": b["name"], "version": "0.1.0", "license": "Proprietary"},
                    "spec": {"type": b["type"], "capabilities": [{"verb": v, "domain": d, "description": t}
                                                                for v, d, t in b["caps"]],
                             "runtime": {"mode": "inprocess"}}}
        register(db, manifest, endpoint=None, source="builtin", trust="official", builtin=True, status="healthy",
                 commit=False)
    db.commit()


def routable(db: Session, agent_scope: str | None = None, viewer: tuple[str | None, str | None] | None = None) -> list[dict]:
    """라우팅 후보: 활성·비내장·정상 상태 에이전트의 capability. viewer=(actor, role) 면 배치 범위 밖 에이전트는 뺀다."""
    from app.services import orgs
    hidden = orgs.hidden_agents(db, *viewer) if viewer else set()
    q = (select(Capability, Agent).join(Agent, Agent.id == Capability.agent_id)
         .where(Agent.is_active.is_(True), Agent.builtin.is_(False), Agent.status.in_(("registered", "healthy"))))
    if agent_scope:
        q = q.where(Agent.id == agent_scope)
    out = []
    for cap, agent in db.execute(q).all():
        if agent.id in hidden:
            continue
        spec = agent.manifest.get("spec", {})
        decl = next((c for c in spec.get("capabilities", []) if c.get("verb") == cap.verb), {})
        out.append({"agent": agent.id, "agent_name": agent.name, "verb": cap.verb, "domain": cap.domain,
                    "description": cap.description, "input_schema": cap.input_schema,
                    "approval": cap.human_approval_required, "keywords": cap.keywords,
                    "endpoint": agent.endpoint, "source": agent.source,
                    "data_class": spec.get("governance", {}).get("dataClassification", "internal"),
                    "audit_level": spec.get("governance", {}).get("auditLevel", "standard"),
                    "egress": bool(spec.get("permissions", {}).get("network", {}).get("egress")),
                    "idempotent": bool(decl.get("idempotent")), "compensation": decl.get("compensation")})
    return out
