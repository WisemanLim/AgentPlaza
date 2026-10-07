"""Epic 21 — Assistant 에이전트 pydantic-ai 전환 (D3-01·D3-02·D3-03, PRD Q2).

Assistant 의 LLM 대화(강등·비전 모드)는 pydantic-ai Agent 로 돈다. 모델은 FunctionModel → 게이트웨이 라우터라서
별칭·폴백·데이터 등급·계량과 AG-UI 이벤트(저하·불가)는 그대로다. 기존 e5·e15·e16 시험이 회귀를 본다.
"""
import json

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart

from app import db as appdb
from app.assistant import agent as assistant_agent
from app.assistant.agui import check
from app.llm.providers import ChatResult, MockProvider
from app.models import LlmRoute
from helpers import auth


def sse(res):
    assert res.status_code == 200, res.text
    return [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith("data: ")]


def llm_only():
    with appdb.SessionLocal() as s:
        for alias in ("plaza/chat", "plaza/orchestrator"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()


def test_e21_01_message_conversion_roundtrip():
    """플랫폼 기록 ↔ pydantic-ai 메시지 ↔ OpenAI chat(instructions = system, 이미지 = data URI)."""
    past = [{"role": "user", "content": "첫째"}, {"role": "assistant", "content": "답"}]
    hist = assistant_agent.history_of(past)
    assert isinstance(hist[0], ModelRequest) and isinstance(hist[1], ModelResponse)
    img = BinaryContent(data=b"\x89PNG", media_type="image/png")
    msgs = [*hist, ModelRequest(parts=[UserPromptPart(content=["이건 뭐야", img])])]
    out = assistant_agent.to_openai(msgs, "지침")
    assert out[0] == {"role": "system", "content": "지침"}
    assert out[1] == {"role": "user", "content": "첫째"} and out[2] == {"role": "assistant", "content": "답"}
    assert out[3]["content"][0] == {"type": "text", "text": "이건 뭐야"}
    assert out[3]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_e21_02_llm_only_chat_runs_on_pydantic_ai(client, sup_token, monkeypatch):
    """강등 모드 대화가 pydantic-ai Agent.run_stream 을 거치고, 맞춤지침이 instructions(system)로 들어간다."""
    llm_only()
    calls, seen = [], []
    original = Agent.run_stream

    def spy(self, *a, **kw):
        calls.append(kw.get("message_history"))
        return original(self, *a, **kw)
    monkeypatch.setattr(Agent, "run_stream", spy)
    monkeypatch.setattr(MockProvider, "responder", staticmethod(
        lambda model, req: (seen.append(req.messages), ChatResult(content="pydantic 응답입니다", model=model))[1]))
    h = auth(sup_token)
    client.post("/api/me/memories", json={"kind": "instruction", "content": "항상 존댓말로 답한다"}, headers=h)
    ev = sse(client.post("/api/chat/stream", json={"message": "안녕"}, headers=h))
    text = "".join(e["delta"] for e in ev if e["type"] == "TEXT_MESSAGE_CONTENT")
    assert text == "pydantic 응답입니다" and len(calls) == 1
    system = seen[0][0]
    assert system["role"] == "system" and "helpful assistant" in system["content"] and "존댓말" in system["content"]
    assert check(ev) == []  # AG-UI 적합(D7-06)
    sid = next(e["value"]["id"] for e in ev if e.get("name") == "session")
    ev2 = sse(client.post("/api/chat/stream", json={"message": "둘째", "session_id": sid}, headers=h))
    assert len(calls[1]) == 2 and [m["role"] for m in seen[1]] == ["system", "user", "assistant", "user"]
    assert check(ev2) == []


def test_e21_03_unavailable_and_degraded_events_kept(client, sup_token):
    """라우터 불가 → llm_unavailable + RUN_ERROR, 폴백 → degraded(from·model) — pydantic-ai 전환 후에도 같은 이벤트."""
    from app.models import LlmModel
    with appdb.SessionLocal() as s:
        s.merge(LlmModel(id="mock/fail-local", provider="mock", model_id="fail", local=True, context=8192,
                         tool_call=False, vision=False, license="test"))
        s.merge(LlmRoute(alias="plaza/chat", targets=["mock/fail-local", "mock/echo"]))
        s.merge(LlmRoute(alias="plaza/orchestrator", targets=["mock/echo"]))
        s.commit()
    ev = sse(client.post("/api/chat/stream", json={"message": "저하"}, headers=auth(sup_token)))
    assert [e["value"] for e in ev if e.get("name") == "degraded"] == [{"from": "mock/fail-local", "model": "mock/echo"}]
    with appdb.SessionLocal() as s:
        s.merge(LlmRoute(alias="plaza/chat", targets=["mock/fail-local"]))
        s.commit()
    ev = sse(client.post("/api/chat/stream", json={"message": "불가"}, headers=auth(sup_token)))
    assert [e["value"]["reason"] for e in ev if e.get("name") == "llm_unavailable"] == ["AllTargetsFailed"]
    assert any(e["type"] == "RUN_ERROR" for e in ev)
