"""의도 분류·계획 (D2-01) + 레지스트리 라우팅 검증 (D2-02).

1차: 게이트웨이 별칭 plaza/orchestrator 의 구조화 출력(JSON). 2차: 키워드 규칙 매처(keyword_rules) 폴백.
계획에 레지스트리에 없는 (agent, capability) 가 있으면 제거하고 registry_miss 로 남긴다.
"""
import json
import re

from sqlalchemy.orm import Session

from app.llm.providers import ChatRequest
from app.llm.router import AllTargetsFailed, Caller, NoRoute, PolicyDenied, Router

SYSTEM = (
    "You are the AgentPlaza orchestrator. Map the user request to the capabilities below.\n"
    "Respond with ONLY a JSON object: {\"steps\": [{\"id\": \"s1\", \"agent\": <agent id>, \"capability\": <verb>, "
    "\"args\": {...}, \"depends_on\": []}], \"pattern\": \"sequential\" | \"parallel\"}.\n"
    "Rules: use a capability whenever the request plausibly matches it (requests may be in Korean); fill args from the "
    "request and respect enum values; a later step may reference an earlier result with \"{{s1}}\" or \"{{s1.field}}\". "
    "Return {\"steps\": []} only when no capability fits.\n"
    "Example: 'board 에 \"공지\" 글 등록' with board.manage(action*: create|list|get|delete, title) → "
    "{\"steps\": [{\"id\": \"s1\", \"agent\": \"board\", \"capability\": \"manage\", "
    "\"args\": {\"action\": \"create\", \"title\": \"공지\"}, \"depends_on\": []}], \"pattern\": \"sequential\"}\n"
    "Example: 'board 글 목록 보여줘' → {\"steps\": [{\"id\": \"s1\", \"agent\": \"board\", \"capability\": \"manage\", "
    "\"args\": {\"action\": \"list\"}, \"depends_on\": []}], \"pattern\": \"sequential\"} — pick the enum value that matches "
    "the requested operation (list/get/delete are not create).\n\n"
    "Capabilities:\n"
)


def _field(name: str, prop: dict, required: bool) -> str:
    enum = f": {'|'.join(map(str, prop['enum']))}" if "enum" in prop else ""
    return f"{name}{'*' if required else ''}{enum}"


def _catalog_text(caps: list[dict]) -> str:
    lines = []
    for c in caps:
        props = c["input_schema"].get("properties", {})
        req = c["input_schema"].get("required", [])
        fields = ", ".join(_field(k, v, k in req) for k, v in props.items())
        lines.append(f"- {c['agent']}.{c['verb']} [{c['agent_name']}] ({c['domain']}): {c['description']} | args: {fields}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object")
    return json.loads(m.group(0))


def _fill_args(cap: dict, message: str) -> dict:
    """규칙 폴백용 인자: 필수 문자열 필드 = 원문, 필수 enum = 첫 값."""
    args = {}
    props = cap["input_schema"].get("properties", {})
    for k in cap["input_schema"].get("required", []):
        p = props.get(k, {})
        if "enum" in p:
            args[k] = p["enum"][0]
        elif p.get("type", "string") == "string":
            args[k] = message
    return args


def rule_plan(message: str, caps: list[dict]) -> dict:
    text = message.lower()
    scored = sorted(((sum(1 for kw in c["keywords"] if kw in text), c) for c in caps), key=lambda x: -x[0])
    if not scored or scored[0][0] == 0:
        return {"source": "rules", "steps": [], "pattern": "sequential", "misses": []}
    best = scored[0][1]
    return {"source": "rules", "pattern": "sequential", "misses": [],
            "steps": [{"id": "s1", "agent": best["agent"], "capability": best["verb"],
                       "args": _fill_args(best, message), "depends_on": []}]}


def validate(plan: dict, caps: list[dict]) -> dict:
    index = {(c["agent"], c["verb"]) for c in caps}
    steps, misses, seen = [], list(plan.get("misses", [])), set()
    for i, s in enumerate(plan.get("steps") or []):
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or f"s{i + 1}")
        if sid in seen:
            sid = f"{sid}_{i}"
        key = (s.get("agent"), s.get("capability"))
        if key not in index:
            misses.append({"agent": key[0], "capability": key[1]})
            continue
        seen.add(sid)
        steps.append({"id": sid, "agent": key[0], "capability": key[1],
                      "args": s.get("args") if isinstance(s.get("args"), dict) else {},
                      "depends_on": [d for d in s.get("depends_on") or [] if isinstance(d, str)]})
    known = {s["id"] for s in steps}
    for s in steps:  # 제거된 단계에 대한 의존은 끊는다
        s["depends_on"] = [d for d in s["depends_on"] if d in known]
    pattern = plan.get("pattern") if plan.get("pattern") in ("sequential", "parallel") else "sequential"
    if pattern == "sequential":  # 명시 의존이 없으면 순서대로 연결
        for prev, cur in zip(steps, steps[1:], strict=False):
            if not cur["depends_on"]:
                cur["depends_on"] = [prev["id"]]
    return {**plan, "steps": steps, "misses": misses, "pattern": pattern}


async def make_plan(db: Session, router: Router, message: str, caps: list[dict], caller: Caller,
                    level: str = "L2") -> dict:
    if not caps:
        return {"source": "none", "steps": [], "pattern": "sequential", "misses": []}
    req = ChatRequest(messages=[{"role": "system", "content": SYSTEM + _catalog_text(caps)},
                                {"role": "user", "content": message}],
                      temperature=0, response_format={"type": "json_object"})
    try:
        res, meta = await router.complete(db, "plaza/orchestrator", req, level=level, caller=caller)
        plan = validate({**_extract_json(res.content), "source": "llm", "model": meta.model}, caps)
    except (ValueError, KeyError, TypeError, AllTargetsFailed, NoRoute, PolicyDenied) as exc:
        return {**rule_plan(message, caps), "llm_error": type(exc).__name__}
    if plan["steps"]:
        return plan
    rules = rule_plan(message, caps)  # 소형 로컬 모델이 빈 계획을 내면 규칙으로 보완
    return {**rules, "misses": plan["misses"], "llm_empty": True} if rules["steps"] else plan
