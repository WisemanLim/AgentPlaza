"""agent.yaml 검증기 (D4-04): JSON Schema + 의미 규칙(DP2·NFR-I2·NFR-I3) + v1 meta.json 변환(10.6)."""
import json
from functools import lru_cache
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).with_name("agent.schema.json")


@lru_cache
def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def load(text: str) -> dict:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("agent.yaml 최상위는 매핑이어야 함 / top-level must be a mapping")
    return data


def validate_manifest(m: dict) -> list[str]:
    """오류 목록(빈 목록 = 통과). 경로는 'spec.permissions.docker' 형식."""
    errors = [f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
              for e in sorted(_validator().iter_errors(m), key=lambda e: list(map(str, e.absolute_path)))]
    if errors:
        return errors
    spec = m["spec"]
    caps = spec.get("capabilities", [])
    verbs = [c["verb"] for c in caps]
    if len(verbs) != len(set(verbs)):
        errors.append("spec.capabilities: verb 중복 / duplicate verb")
    for c in caps:  # 보상 capability 는 같은 에이전트에 선언돼 있어야 한다(D2-07)
        comp = c.get("compensation")
        if comp and comp["capability"] not in verbs:
            errors.append(f"spec.capabilities.{c['verb']}.compensation: 선언되지 않은 capability {comp['capability']}")
    if spec.get("permissions", {}).get("docker", False):
        errors.append("spec.permissions.docker: 항상 false 여야 함 (NFR-I3)")
    if spec.get("dependencies"):
        errors.append("spec.dependencies: 비어 있어야 M1 단독 구동 가능 (DP2) — optionalServices 사용")
    if spec["type"] == "federation":
        if "federation" not in spec:
            errors.append("spec.federation: federation 유형은 kind·url 필수")
    else:
        if not caps:
            errors.append("spec.capabilities: 최소 1개 필요")
        if "federation" in spec:
            errors.append("spec.federation: federation 유형 전용 필드")
    if spec["type"] == "hitl" and not any(c.get("humanApprovalRequired") for c in caps) \
            and not spec.get("governance", {}).get("humanApprovalRequired"):
        errors.append("spec: hitl 유형은 humanApprovalRequired capability 가 1개 이상 필요")
    ui = spec.get("ui", {})
    if ui.get("hasFrontend") and ui.get("mount", "iframe") == "none":
        errors.append("spec.ui.mount: hasFrontend=true 면 none 불가")
    return errors


def validate_text(text: str) -> tuple[dict | None, list[str]]:
    try:
        m = load(text)
    except (yaml.YAMLError, ValueError) as exc:
        return None, [f"<yaml>: {exc}"]
    return m, validate_manifest(m)


V1_TYPES = {"board": "app", "app": "app", "rag": "rag", "service": "service", "tool_proxy": "tool-proxy",
            "toolproxy": "tool-proxy", "reviewer": "reviewer", "hitl": "hitl", "memory": "memory"}


def from_v1_meta(meta: dict) -> dict:
    """v1 {Name}-meta.json → agent.yaml (PRD 10.6 매핑: agent_type→spec.type, capabilities, governance,
    required_env→env.required, min_platform_version→platform.min). 알 수 없는 필드는 버린다."""
    name = meta.get("name") or meta.get("agent_name") or "agent"
    agent_id = "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-") or "agent"
    caps = []
    for c in meta.get("capabilities", []):
        if isinstance(c, str):
            c = {"verb": c}
        verb = str(c.get("verb") or c.get("name") or "run").lower().replace("-", "_")
        caps.append({"verb": verb, "domain": str(c.get("domain") or f"addon.{agent_id}"),
                     "description": c.get("description") or verb})
    gov = meta.get("governance", {})
    return {
        "apiVersion": "agentplaza/v1",
        "kind": "Agent",
        "metadata": {"id": agent_id[:41], "name": name, "version": meta.get("version", "1.0.0"),
                     "license": meta.get("license", "UNLICENSED"),
                     "description": meta.get("description", name),
                     "provenance": {"convertedFrom": "v1-meta.json"}},
        "spec": {
            "type": V1_TYPES.get(str(meta.get("agent_type", "service")).lower(), "service"),
            "platform": {"min": str(meta.get("min_platform_version", "2.0.0"))},
            "capabilities": caps or [{"verb": "run", "domain": f"addon.{agent_id}", "description": name}],
            "governance": {
                "dataClassification": gov.get("data_classification", "internal"),
                "humanApprovalRequired": bool(gov.get("human_approval_required", False)),
                "auditLevel": gov.get("audit_level", "standard"),
            },
            "env": {"required": list(meta.get("required_env", []))},
            "permissions": {"docker": False},
            "runtime": {"mode": "container"},
        },
    }
