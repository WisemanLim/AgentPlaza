"""거버넌스 정책 엔진 (D9-05) — 데이터 등급·승인·감사 수준·도구 허용·게이트웨이 정책을 한 문서로 집행한다.

OPA/Rego 대신 정책을 데이터(settings 'policy.governance')로 두고 내장 평가기로 판정한다(계획표 가정).
판정 지점: LLM 라우터(등급별 모델), Orchestrator(도구 차단·승인 강제·감사 수준), 세션 내보내기, MCP 게이트웨이(툴 RBAC).
"""
import copy
import fnmatch
import time

from sqlalchemy.orm import Session

from app.models import ROLE_RANK
from app.services import sysconfig

KEY = "policy.governance"
LEVELS = ["L0", "L1", "L2", "L3"]
AUDIT_LEVELS = ["minimal", "standard", "full"]
CLASS_LEVEL = {"public": "L0", "internal": "L1", "confidential": "L3"}
DEFAULT = {
    "data": {
        "model_locality": {"L0": "any", "L1": "any", "L2": "local", "L3": "local"},  # D1-06 등급별 허용 모델
        "external_tool_max_level": "L2",  # 원격(link)·egress 에이전트 도구를 쓸 수 있는 최고 요청 등급(L3 차단, 조직이 L1 로 강화)
        "confidential_requires_cleared_agent": True,  # L3 요청은 dataClassification=confidential 에이전트만
        "approval_at_levels": [],  # 이 등급 요청의 모든 도구 호출에 휴먼 승인 강제
        "export_max_level": "L2",  # 세션 내보내기 허용 최고 등급
        "audit_level_min": "standard",  # 에이전트 auditLevel 이 이보다 낮으면 끌어올린다
    },
    "guardrails": {
        "injection": "block",  # block | flag | off — 프롬프트 인젝션(NFR-S6)
        "pii_mask_public": True,  # 퍼블릭(비로컬) 모델로 나가는 메시지의 한국어 PII 마스킹
        "scan_tool_results": True,  # 도구 결과의 간접 인젝션 탐지 → 리뷰어 게이트
        "tool_allowlist": ["*"],  # "agent.verb" 패턴
        "tool_denylist": [],
    },
    "reviewer": {"mode": "auto", "agent": None},  # off | auto(외부 결과·인젝션 의심 시) | always
    "gateway": {
        "rate_per_minute": {"user": 120, "service": 600, "anonymous": 30},
        "tool_rules": [],  # [{"tool": "ops-approval.*", "min_role": "admin"}] — MCP·Orchestrator 공통 툴 RBAC
    },
}
_cache: dict = {"at": 0.0, "value": None}


class PolicyError(ValueError):
    pass


def get(db: Session) -> dict:
    stored = sysconfig.blob(db, KEY)
    out = copy.deepcopy(DEFAULT)
    for section, values in stored.items():
        if section in out and isinstance(values, dict):
            out[section].update(values)
    return out


def cached(db_factory) -> dict:
    """요청마다 DB 를 읽지 않도록 5초 캐시(레이트리밋 미들웨어용)."""
    if _cache["value"] is None or time.monotonic() - _cache["at"] > 5:
        with db_factory() as db:
            _cache.update(value=get(db), at=time.monotonic())
    return _cache["value"]


def _validate(p: dict) -> None:
    d, g, r, gw = p["data"], p["guardrails"], p["reviewer"], p["gateway"]
    if set(d["model_locality"]) != set(LEVELS) or not set(d["model_locality"].values()) <= {"any", "local"}:
        raise PolicyError("data.model_locality: L0~L3 → any|local")
    for k in ("external_tool_max_level", "export_max_level"):
        if d[k] not in LEVELS:
            raise PolicyError(f"data.{k} ∈ L0..L3")
    if not set(d["approval_at_levels"]) <= set(LEVELS):
        raise PolicyError("data.approval_at_levels ⊂ L0..L3")
    if d["audit_level_min"] not in AUDIT_LEVELS:
        raise PolicyError(f"data.audit_level_min ∈ {AUDIT_LEVELS}")
    if g["injection"] not in ("block", "flag", "off"):
        raise PolicyError("guardrails.injection ∈ block|flag|off")
    for k in ("tool_allowlist", "tool_denylist"):
        if not isinstance(g[k], list) or not all(isinstance(x, str) for x in g[k]):
            raise PolicyError(f"guardrails.{k} 는 문자열 목록")
    if r["mode"] not in ("off", "auto", "always"):
        raise PolicyError("reviewer.mode ∈ off|auto|always")
    rates = gw["rate_per_minute"]
    if not isinstance(rates, dict) or not all(isinstance(v, int) and v >= 1 for v in rates.values()):
        raise PolicyError("gateway.rate_per_minute 는 {kind: 양의 정수}")
    for rule in gw["tool_rules"]:
        if not isinstance(rule, dict) or "tool" not in rule or rule.get("min_role") not in ROLE_RANK:
            raise PolicyError("gateway.tool_rules 항목 = {tool, min_role: user|admin|supervisor}")


def put(db: Session, changes: dict) -> dict:
    unknown = [k for k in changes if k not in DEFAULT]
    if unknown:
        raise PolicyError(f"알 수 없는 정책 섹션 / unknown: {unknown}")
    p = get(db)
    for section, values in changes.items():
        if not isinstance(values, dict):
            raise PolicyError(f"{section} 는 객체")
        bad = [k for k in values if k not in DEFAULT[section]]
        if bad:
            raise PolicyError(f"알 수 없는 키 {section}.{bad}")
        p[section].update(values)
    _validate(p)
    sysconfig.put_blob(db, KEY, p)
    _cache["value"] = None
    return p


# ---- 판정 ----

def level_gt(a: str, b: str) -> bool:
    return LEVELS.index(a) > LEVELS.index(b)


def local_only(p: dict, level: str) -> bool:
    return p["data"]["model_locality"].get(level, "local") == "local"


def tool_decision(p: dict, cap: dict, *, role: str, level: str) -> str | None:
    """None = 허용, 문자열 = 차단 사유. cap = registry.routable 항목."""
    name = f"{cap['agent']}.{cap['verb']}"
    g = p["guardrails"]
    if not any(fnmatch.fnmatch(name, pat) for pat in g["tool_allowlist"]) or \
            any(fnmatch.fnmatch(name, pat) for pat in g["tool_denylist"]):
        return f"도구 허용목록 밖 / not allowed: {name}"
    for rule in p["gateway"]["tool_rules"]:
        if fnmatch.fnmatch(name, rule["tool"]) and ROLE_RANK.get(role, 0) < ROLE_RANK[rule["min_role"]]:
            return f"{rule['min_role']} 이상만 / requires {rule['min_role']}: {name}"
    d = p["data"]
    if (cap.get("source") == "link" or cap.get("egress")) and level_gt(level, d["external_tool_max_level"]):
        return f"{level} 데이터는 외부 연결 에이전트로 보낼 수 없음(≤{d['external_tool_max_level']}) / external tool blocked"
    if level == "L3" and d["confidential_requires_cleared_agent"] and cap.get("data_class") != "confidential":
        return "L3(기밀) 요청은 confidential 등급 에이전트만 / agent not cleared for L3"
    return None


def needs_approval(p: dict, cap: dict, level: str) -> bool:
    return bool(cap.get("approval")) or level in p["data"]["approval_at_levels"]


def audit_level(p: dict, cap: dict) -> str:
    own = cap.get("audit_level") or "standard"
    floor = p["data"]["audit_level_min"]
    return max(own, floor, key=AUDIT_LEVELS.index)


def export_allowed(p: dict, level: str) -> bool:
    return not level_gt(level, p["data"]["export_max_level"])
