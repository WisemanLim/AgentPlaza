"""Epic 5 — AI Assistant API: AG-UI SSE 채팅·세션·도구/승인 UX·스코프 채팅 (D3-01/02/03, NFR-C3, US8).

SSE 는 'data: {AG-UI event}' 프레임. 강등(LLM 단독)·Orchestrator 경로를 모두 본다.
"""
import json
from datetime import timedelta

import pytest

from app import db as appdb
from app.core.config import settings
from app.llm.providers import ChatResult, MockProvider
from app.models import ChatSession, LlmModel, LlmRoute
from app.orchestrator import executor
from app.services import registry
from helpers import auth, load_template_app, make_user


def sse(res) -> list[dict]:
    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith("text/event-stream")
    return [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith("data: ")]


def text_of(events) -> str:
    return "".join(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT")


def custom(events, name):
    return [e["value"] for e in events if e["type"] == "CUSTOM" and e["name"] == name]


ENVELOPE = ("stream", "stream_end")  # 전송 계층 이벤트(재연결용, Epic 16) — 실행 이벤트 순서 검사에서는 뺀다


def send(client, token, message, **kw):
    events = sse(client.post("/api/chat/stream", json={"message": message, **kw}, headers=auth(token)))
    return [e for e in events if not (e["type"] == "CUSTOM" and e.get("name") in ENVELOPE)]


@pytest.fixture
def llm_only(client):
    with appdb.SessionLocal() as s:
        s.merge(LlmModel(id="mock/fail-local", provider="mock", model_id="fail", local=True, context=8192,
                         tool_call=False, vision=False, license="test"))
        for alias in ("plaza/chat", "plaza/orchestrator"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()
    return client


@pytest.fixture
def plan_llm(monkeypatch):
    holder = {"plan": {"steps": []}}
    default = MockProvider.responder

    def responder(model, req):
        if req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator"):
            return ChatResult(content=json.dumps(holder["plan"]), model=model)
        return default(model, req)

    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    return holder


@pytest.fixture
def with_agents(llm_only, tmp_path, monkeypatch, plan_llm):
    with appdb.SessionLocal() as s:
        for agent_id, type_ in (("calc", "execution"), ("ops", "hitl")):
            app, manifest = load_template_app(tmp_path, type_, agent_id, monkeypatch, registry.agent_key(agent_id))
            executor.register_app(f"http://{agent_id}.test", app)
            registry.register(s, manifest, endpoint=f"http://{agent_id}.test", status="healthy")
    yield plan_llm
    executor.clear_apps()


def test_e5_01_llm_only_streaming_and_session(llm_only, sup_token):
    ev = send(llm_only, sup_token, "안녕하세요 어시스턴트")
    t = [e["type"] for e in ev]
    assert t[0] == "CUSTOM" and t[1] == "RUN_STARTED" and t[-1] == "RUN_FINISHED"
    assert custom(ev, "mode") == ["llm-only"]
    assert text_of(ev) == "echo: 안녕하세요 어시스턴트"
    assert sum(1 for x in t if x == "TEXT_MESSAGE_CONTENT") > 1  # 토큰 단위 스트리밍
    sid = custom(ev, "session")[0]["id"]
    s = llm_only.get(f"/api/sessions/{sid}", headers=auth(sup_token)).json()
    assert s["title"] == "안녕하세요 어시스턴트"
    assert [m["role"] for m in s["messages"]] == ["user", "assistant"]


def test_e5_02_history_is_passed(llm_only, sup_token, monkeypatch):
    monkeypatch.setattr(MockProvider, "responder", staticmethod(
        lambda model, req: ChatResult(content=f"n={len(req.messages)}", model=model)))
    sid = custom(send(llm_only, sup_token, "첫째"), "session")[0]["id"]
    second = send(llm_only, sup_token, "둘째", session_id=sid)
    assert custom(second, "session")[0]["id"] == sid
    assert text_of(second) == "n=4"  # system + (user, assistant) + user


def test_e5_03_orchestrator_path_tool_events(llm_only, with_agents, sup_token):
    with_agents["plan"] = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate",
                                      "args": {"expression": "40+2"}}]}
    ev = send(llm_only, sup_token, "40 더하기 2")
    t = [e["type"] for e in ev]
    assert {"TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "TOOL_CALL_RESULT"} <= set(t)
    result = json.loads(next(e for e in ev if e["type"] == "TOOL_CALL_RESULT")["content"])
    assert result["result"]["value"] == 42
    sid = custom(ev, "session")[0]["id"]
    msgs = llm_only.get(f"/api/sessions/{sid}", headers=auth(sup_token)).json()["messages"]
    assert msgs[-1]["role"] == "assistant" and msgs[-1]["meta"]["results"]["s1"]["ok"] is True


def test_e5_04_approval_card_then_resume_appends_answer(llm_only, with_agents, sup_token, monkeypatch):
    monkeypatch.setattr(settings, "hitl_allow_self_approval", True)
    with_agents["plan"] = {"steps": [{"id": "s1", "agent": "ops", "capability": "execute_action",
                                      "args": {"action": "deploy"}}]}
    ev = send(llm_only, sup_token, "배포해줘")
    card = custom(ev, "approval_required")[0]
    assert any(e["type"] == "STATE_SNAPSHOT" for e in ev)
    assert ev[-1]["type"] == "RUN_FINISHED" and ev[-1]["result"]["state"] == "waiting_approval"
    sid = custom(ev, "session")[0]["id"]
    kinds = [m["kind"] for m in llm_only.get(f"/api/sessions/{sid}", headers=auth(sup_token)).json()["messages"]]
    assert kinds == ["text", "approval"]
    llm_only.post(f"/api/approvals/{card['approval_id']}/approve", headers=auth(sup_token))
    msgs = llm_only.get(f"/api/sessions/{sid}", headers=auth(sup_token)).json()["messages"]
    assert msgs[-1]["kind"] == "text" and msgs[-1]["task_id"]


def test_e5_05_agent_scoped_chat(llm_only, with_agents, sup_token):
    with_agents["plan"] = {"steps": [{"id": "s1", "agent": "ops", "capability": "history", "args": {}}]}
    ev = send(llm_only, sup_token, "기록", agent_scope="calc")
    assert custom(ev, "session")[0]["agent_scope"] == "calc"
    assert custom(ev, "registry_miss") == [{"agent": "ops", "capability": "history"}]


def test_e5_06_sessions_crud_search_export_delete(llm_only, sup_token):
    a = custom(send(llm_only, sup_token, "보안 정책 질문"), "session")[0]["id"]
    custom(send(llm_only, sup_token, "점심 메뉴"), "session")
    h = auth(sup_token)
    assert [s["id"] for s in llm_only.get("/api/sessions?q=보안", headers=h).json()] == [a]
    assert llm_only.patch(f"/api/sessions/{a}", json={"title": "정책", "folder": "work"}, headers=h).json()["folder"] == "work"
    assert [s["id"] for s in llm_only.get("/api/sessions?folder=work", headers=h).json()] == [a]
    llm_only.patch(f"/api/sessions/{a}", json={"archived": True}, headers=h)
    assert a not in [s["id"] for s in llm_only.get("/api/sessions", headers=h).json()]
    assert a in [s["id"] for s in llm_only.get("/api/sessions?archived=true", headers=h).json()]
    md = llm_only.get(f"/api/sessions/{a}/export?format=md", headers=h)
    assert md.headers["content-type"].startswith("text/markdown") and "보안 정책 질문" in md.text
    assert json.loads(llm_only.get(f"/api/sessions/{a}/export", headers=h).text)["id"] == a
    _, other = make_user(llm_only, sup_token, "peer@example.test")
    assert llm_only.get(f"/api/sessions/{a}", headers=auth(other)).status_code == 404
    assert llm_only.delete(f"/api/sessions/{a}", headers=h).json()["messages"] == 2
    assert llm_only.get(f"/api/sessions/{a}", headers=h).status_code == 404
    assert llm_only.get("/api/audit?action=session.deleted", headers=h).json()


def test_e5_07_retention_purge(llm_only, sup_token):
    sid = custom(send(llm_only, sup_token, "오래된 대화"), "session")[0]["id"]
    with appdb.SessionLocal() as s:
        old = s.get(ChatSession, sid)
        old.updated_at = old.updated_at - timedelta(days=settings.retention_chat_days + 1)
        s.commit()
    assert llm_only.post("/api/admin/retention/run", headers=auth(sup_token)).json()["purged_sessions"] == 1
    assert llm_only.get(f"/api/sessions/{sid}", headers=auth(sup_token)).status_code == 404


def test_e5_08_degraded_and_unavailable_events(llm_only, sup_token):
    with appdb.SessionLocal() as s:
        s.merge(LlmRoute(alias="plaza/chat", targets=["mock/fail-local", "mock/echo"]))
        s.commit()
    ev = send(llm_only, sup_token, "저하")
    assert custom(ev, "degraded") == [{"from": "mock/fail-local", "model": "mock/echo"}]
    with appdb.SessionLocal() as s:
        s.merge(LlmRoute(alias="plaza/chat", targets=["mock/fail-local"]))
        s.commit()
    ev = send(llm_only, sup_token, "불가")
    assert ev[-1]["type"] == "RUN_ERROR"
    sid = custom(ev, "session")[0]["id"]
    assert llm_only.get(f"/api/sessions/{sid}", headers=auth(sup_token)).json()["messages"][-1]["kind"] == "error"


def test_e5_09_invalid_data_class(llm_only, sup_token):
    res = llm_only.post("/api/chat/stream", json={"message": "x", "data_class": "L9"}, headers=auth(sup_token))
    assert res.status_code == 422
