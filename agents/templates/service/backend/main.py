"""{{AGENT_NAME}} — service 유형: 화면 없는 텍스트 처리 서비스. 요약은 LLM 이 있으면 쓰고 없으면 규칙 폴백."""
import re

from agentplaza_sdk import Agent, CapabilityError, create_app

agent = Agent.from_manifest("agent.yaml")


@agent.capability("process")
async def process(payload: dict, ctx):
    text, op = payload["text"], payload.get("op", "wordcount")
    if op == "upper":
        return {"text": text.upper()}
    if op == "lower":
        return {"text": text.lower()}
    if op == "wordcount":
        return {"words": len(re.findall(r"\S+", text)), "chars": len(text)}
    if op == "summarize":
        if ctx.llm.available:
            summary = await ctx.llm.chat([{"role": "system", "content": "Summarize in one sentence."},
                                          {"role": "user", "content": text}])
            return {"summary": summary, "source": "llm"}
        return {"summary": re.split(r"(?<=[.!?。])\s+", text.strip())[0], "source": "rule"}
    raise CapabilityError(f"unknown op: {op}")


app = create_app(agent)
