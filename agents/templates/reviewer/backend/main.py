"""{{AGENT_NAME}} — reviewer 유형: 응답·도구 결과의 위험을 검토해 pass / revise / block 을 판정한다."""
import re

from agentplaza_sdk import Agent, create_app

agent = Agent.from_manifest("agent.yaml")

# 한국어 PII 패턴 + 흔한 프롬프트 인젝션 문구(가드레일 기본값, D9-06 의 축소판)
PII = {
    "rrn": r"\b\d{6}-?[1-4]\d{6}\b",
    "phone": r"\b01[016789]-?\d{3,4}-?\d{4}\b",
    "email": r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    "card": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
}
INJECTION = [r"ignore (all )?previous instructions", r"이전 지시(를|는)? 무시", r"system prompt", r"시스템 프롬프트"]


@agent.capability("review")
def review(payload: dict, ctx):
    text = payload["text"]
    findings = [{"type": "pii", "kind": k, "count": len(re.findall(p, text))}
                for k, p in PII.items() if re.search(p, text)]
    findings += [{"type": "injection", "pattern": p} for p in INJECTION if re.search(p, text, re.I)]
    if any(f["type"] == "injection" for f in findings):
        verdict = "block"
    elif findings:
        verdict = "revise"
    else:
        verdict = "pass"
    redacted = text
    for p in PII.values():
        redacted = re.sub(p, "[REDACTED]", redacted)
    return {"verdict": verdict, "findings": findings, "redacted": redacted if verdict != "pass" else None}


app = create_app(agent)
