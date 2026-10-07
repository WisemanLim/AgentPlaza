"""AI Assistant 에이전트 = pydantic-ai Agent (D3-01·D3-03, PRD Q2).

모델은 pydantic-ai FunctionModel 로 플랫폼 게이트웨이 라우터에 잇는다 — 별칭·폴백·데이터 등급·예산·PII 마스킹·계량이
그대로 적용되고, 라우터의 저하(degraded)·불가(llm_unavailable) 신호는 같은 AG-UI 이벤트로 내보낸다.
대화 기록은 pydantic-ai 메시지(ModelRequest/ModelResponse)로, 맞춤지침·기억·지식 근거는 instructions 로 넘긴다.
"""
import base64
from collections.abc import AsyncIterator, Awaitable, Callable

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (ModelMessage, ModelRequest, ModelResponse, SystemPromptPart, TextPart,
                                  UserPromptPart)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from sqlalchemy.orm import Session

from app.llm.providers import ChatRequest
from app.llm.router import AllTargetsFailed, Caller, NoRoute, PolicyDenied, RouteMeta, get_router

BASE = "You are a helpful assistant. Reply in the user's language."
Emit = Callable[[dict], Awaitable[None]]


def _content(content) -> str | list[dict]:
    """pydantic-ai 사용자 입력 → OpenAI chat content (이미지는 data URI image_url)."""
    if isinstance(content, str):
        return content
    parts: list[dict] = []
    for c in content:
        if isinstance(c, str):
            parts.append({"type": "text", "text": c})
        elif isinstance(c, BinaryContent) and c.is_image:
            url = f"data:{c.media_type};base64,{base64.b64encode(c.data).decode()}"
            parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts


def to_openai(messages: list[ModelMessage], instructions: str | None) -> list[dict]:
    out: list[dict] = [{"role": "system", "content": instructions}] if instructions else []
    for m in messages:
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, SystemPromptPart):
                    out.append({"role": "system", "content": p.content})
                elif isinstance(p, UserPromptPart):
                    out.append({"role": "user", "content": _content(p.content)})
        elif isinstance(m, ModelResponse):
            text = "".join(p.content for p in m.parts if isinstance(p, TextPart))
            out.append({"role": "assistant", "content": text})
    return out


def history_of(past: list[dict]) -> list[ModelMessage]:
    """플랫폼 대화 기록({role, content}) → pydantic-ai 메시지."""
    msgs: list[ModelMessage] = []
    for m in past:
        if m["role"] == "user":
            msgs.append(ModelRequest(parts=[UserPromptPart(content=m["content"])]))
        elif m["role"] == "assistant":
            msgs.append(ModelResponse(parts=[TextPart(content=m["content"])]))
    return msgs


def gateway_model(db: Session, alias: str, level: str, caller: Caller, holder: dict) -> FunctionModel:
    """pydantic-ai 모델 → 게이트웨이 라우터(stream). holder["meta"] 에 라우팅 결과(모델·저하)를 남긴다."""
    async def stream(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str]:
        meta, chunks = await get_router().stream(db, alias, ChatRequest(messages=to_openai(messages, info.instructions)),
                                                 level=level, caller=caller)
        holder["meta"] = meta
        async for c in chunks:
            if c.get("delta"):
                yield c["delta"]
    return FunctionModel(stream_function=stream, model_name=f"plaza:{alias}")


async def converse(db: Session, *, message: str | list, past: list[dict], context: str | None, level: str,
                   caller: Caller, emit: Emit, msg_id: str, alias: str = "plaza/chat") -> str | None:
    """Assistant 대화 한 턴: pydantic-ai Agent 로 스트리밍하고 AG-UI TEXT_MESSAGE_* 로 내보낸다. 실패면 None."""
    holder: dict = {}
    instructions = BASE + (f"\n\n{context}" if context else "")
    agent = Agent(gateway_model(db, alias, level, caller, holder), instructions=instructions)
    parts: list[str] = []
    started = False
    try:
        async with agent.run_stream(message, message_history=history_of(past)) as result:
            meta: RouteMeta | None = holder.get("meta")
            if meta is not None and meta.degraded:  # UI 저하 배지(MSG-011)
                await emit({"type": "CUSTOM", "name": "degraded", "value": {"from": meta.fallback_from,
                                                                            "model": meta.model}})
            await emit({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})
            started = True
            async for delta in result.stream_text(delta=True, debounce_by=None):  # 토큰 단위 그대로(D3-01)
                if delta:
                    parts.append(delta)
                    await emit({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": delta})
    except (AllTargetsFailed, NoRoute, PolicyDenied) as exc:
        await emit({"type": "CUSTOM", "name": "llm_unavailable", "value": {"reason": type(exc).__name__}})
        return None
    except UnexpectedModelBehavior:  # 빈 응답 — 빈 답변으로 끝낸다
        if "meta" not in holder:
            await emit({"type": "CUSTOM", "name": "llm_unavailable", "value": {"reason": "EmptyResponse"}})
            return None
        if not started:
            await emit({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})
    await emit({"type": "TEXT_MESSAGE_END", "messageId": msg_id})
    return "".join(parts)
