"""Epic 10 — 콘솔 API·셋업 위저드·OTel (D10-01/02/03, NFR-O1, NFR-U1 흐름, NFR-C3 설정 반영)."""
import json
from datetime import timedelta

import pytest
from fastapi import FastAPI, Request
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app import db as appdb
from app.agentspec import generator as gen
from app.api import console
from app.core.config import settings
from app.llm.providers import ChatResult, MockProvider
from app.models import ChatSession, LlmModel, LlmRoute
from app.observability import provider
from app.orchestrator import executor
from app.registry import pipeline
from app.runtime.driver import FakeRuntime, set_runtime
from app.services import registry
from helpers import auth, load_template_app, make_user

_EXPORTER = InMemorySpanExporter()
provider().add_span_processor(SimpleSpanProcessor(_EXPORTER))


@pytest.fixture
def spans():
    _EXPORTER.clear()
    yield _EXPORTER
    _EXPORTER.clear()


@pytest.fixture
def routes(client):
    with appdb.SessionLocal() as s:
        s.merge(LlmModel(id="mock/fail-local", provider="mock", model_id="fail", local=True, context=8192,
                         tool_call=False, vision=False, license="test"))
        s.merge(LlmRoute(alias="plaza/t", targets=["mock/echo"]))
        s.merge(LlmRoute(alias="plaza/t-fb", targets=["mock/fail-local", "mock/echo"]))
        for alias in ("plaza/orchestrator", "plaza/chat"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()
    return client


def by_name(spans, prefix):
    return [s for s in spans.get_finished_spans() if s.name.startswith(prefix)]


def test_e10_01_llm_spans_genai_semconv(routes, sup_token, spans):
    """NFR-O1: LLM span 은 GenAI 규약 속성을 가진다. 프롬프트 원문은 수집하지 않는다."""
    secret = "주민번호 900101-1234567 포함 프롬프트"
    routes.post("/v1/chat/completions", json={"model": "plaza/t", "messages": [{"role": "user", "content": secret}]},
                headers=auth(sup_token) | {"X-Plaza-Data-Class": "L3"})
    s = by_name(spans, "chat plaza/t")[0]
    a = dict(s.attributes)
    assert a["gen_ai.operation.name"] == "chat" and a["gen_ai.system"] == "mock"
    assert a["gen_ai.request.model"] == "plaza/t" and a["gen_ai.response.model"] == "echo"
    assert a["gen_ai.usage.input_tokens"] > 0 and a["gen_ai.usage.output_tokens"] > 0 and a["plaza.data_class"] == "L3"
    assert not any(secret in str(v) for v in a.values())
    routes.post("/v1/chat/completions", json={"model": "plaza/t-fb", "messages": [{"role": "user", "content": "x"}],
                                              "stream": True}, headers=auth(sup_token) | {"X-Plaza-Data-Class": "L3"})
    st = dict(by_name(spans, "chat plaza/t-fb")[0].attributes)
    assert st["plaza.fallback_from"] == "mock/fail-local" and st["plaza.stream"] is True and st["plaza.degraded"] is True


@pytest.fixture
def plan(monkeypatch):
    holder = {"plan": {"steps": []}}
    default = MockProvider.responder

    def responder(model, req):
        if req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator"):
            return ChatResult(content=json.dumps(holder["plan"]), model=model)
        return default(model, req)
    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    return holder


def test_e10_02_tool_spans_parenting_and_traceparent(routes, sup_token, spans, plan):
    """invoke_agent(오케스트레이터) → execute_tool 이 한 트레이스로 이어지고, 에이전트 호출에 traceparent 가 실린다."""
    seen = {}
    probe = FastAPI()

    @probe.post("/api/invoke/{verb}")
    async def inv(verb: str, request: Request):
        seen.update(dict(request.headers))
        return {"result": {"ok": True}}
    m = gen.build_manifest("probe", "Probe", "service")
    with appdb.SessionLocal() as s:
        registry.register(s, m, endpoint="http://probe.test", status="healthy")
    executor.register_app("http://probe.test", probe)
    try:
        plan["plan"] = {"steps": [{"id": "s1", "agent": "probe", "capability": "process", "args": {"text": "t"}}]}
        sid = None
        res = routes.post("/api/chat/stream", json={"message": "probe"}, headers=auth(sup_token))
        for line in res.text.splitlines():
            if line.startswith("data: ") and '"session"' in line:
                sid = json.loads(line[6:])["value"]["id"]
    finally:
        executor.clear_apps()
    tool = by_name(spans, "execute_tool probe.process")[0]
    orch = by_name(spans, "invoke_agent orchestrator")[0]
    ta = dict(tool.attributes)
    assert ta["gen_ai.tool.name"] == "process" and ta["gen_ai.agent.id"] == "probe" and ta["plaza.capability"] == "probe.process"
    assert ta["plaza.session_id"] == sid
    assert tool.context.trace_id == orch.context.trace_id and tool.parent.span_id == orch.context.span_id
    assert seen["traceparent"].split("-")[1] == format(tool.context.trace_id, "032x")


def test_e10_03_dashboard_tiles(routes, sup_token):
    d = routes.get("/api/console/dashboard", headers=auth(sup_token)).json()
    assert [t["id"] for t in d["tiles"]] == ["agents", "approvals", "llm", "installs", "sessions", "runtime"]
    assert d["refresh_seconds"] == 30


def test_e10_04_settings_and_retention_applied(routes, sup_token):
    """L01: supervisor 만 변경, 값 검증, 보존 기간 설정이 실제 파기에 반영(NFR-C3)."""
    h = auth(sup_token)
    assert routes.get("/api/settings", headers=h).json()["retention_chat_days"] == settings.retention_chat_days
    assert routes.put("/api/settings", json={"retention_chat_days": 30}, headers=h).json()["retention_chat_days"] == 30
    assert routes.put("/api/settings", json={"retention_chat_days": 0}, headers=h).status_code == 422
    assert routes.put("/api/settings", json={"unknown": 1}, headers=h).status_code == 422
    _, admin = make_user(routes, sup_token, "adm@example.test", "admin")
    assert routes.put("/api/settings", json={"site_name": "X"}, headers=auth(admin)).status_code == 403
    with appdb.SessionLocal() as s:
        old = ChatSession(id="old-1", owner="root@example.test", title="old")
        s.add(old)
        s.commit()
        old.updated_at = old.updated_at - timedelta(days=31)
        s.commit()
    assert routes.post("/api/admin/retention/run", headers=h).json()["purged_sessions"] == 1


def test_e10_05_profile(routes, sup_token):
    h = auth(sup_token)
    assert routes.patch("/api/me/profile", json={"locale": "en", "theme": "dark"}, headers=h).json()["theme"] == "dark"
    p = routes.get("/api/me/profile", headers=h).json()
    assert p["locale"] == "en" and p["theme"] == "dark"
    assert routes.patch("/api/me/profile", json={"theme": "neon"}, headers=h).status_code == 422


def test_e10_06_setup_wizard_flow(routes, sup_token, tmp_path, monkeypatch):
    """D10-02·NFR-U1 흐름: 관리자 → LLM 연결 → 모델 pull → 기본 에이전트 → 완료(서버에 진행 저장)."""
    h = auth(sup_token)

    async def tags():
        return True, ["granite4.1:3b", "qwen3:8b", "llama3.2:3b"]
    monkeypatch.setattr(console, "_ollama_tags", tags)
    fake = FakeRuntime()
    set_runtime(fake)
    monkeypatch.setattr(settings, "data_dir", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "health_timeout_seconds", 2.0)
    try:
        prog = routes.get("/api/setup/progress", headers=h).json()
        assert prog["steps"][0] == {"id": "admin", "done": True} and prog["completed"] is False
        st = routes.get("/api/setup/llm", headers=h).json()
        assert st["ollama"]["reachable"] and "granite4.1:3b" in st["ollama"]["recommended"]
        assert set(st["public"]) == {"openai", "anthropic", "gemini", "openrouter"}
        assert routes.post("/api/setup/llm", json={"chat_model": "llama3.2:3b"}, headers=h).status_code == 409  # 조건부
        r = routes.post("/api/setup/llm", json={"chat_model": "granite4.1:3b", "reasoning_model": "qwen3:8b"},
                        headers=h).json()
        assert r["ok"] and r["warnings"] == []
        targets = {x["alias"]: x["targets"] for x in routes.get("/api/llm/routes", headers=h).json()}
        assert targets["plaza/orchestrator"][0] == "ollama/qwen3:8b" and targets["plaza/fast"][0] == "ollama/granite4.1:3b"
        assert routes.post("/api/setup/complete", headers=h).status_code == 409  # 남은 단계
        routes.post("/api/setup/skip", json={"step": "models"}, headers=h)
        app, _ = load_template_app(tmp_path / "srv", "app", "board", monkeypatch, registry.agent_key("board"))
        executor.register_app(pipeline.endpoint_for("board"), app)
        ag = routes.post("/api/setup/agents", json={"listings": ["board", "http-tool"]}, headers=h).json()
        assert ag["installs"][0]["install_id"] and "error" in ag["installs"][1]  # http-tool 은 필수 env
        done = routes.post("/api/setup/complete", headers=h).json()
        assert done["completed"] is True and all(s["done"] for s in done["steps"])
        assert routes.get("/api/agents/board", headers=h).json()["status"] == "healthy"
        rt = routes.get("/api/agents/board/runtime", headers=h).json()
        assert rt["mode"] == "container" and rt["containers"][0]["state"] == "running"
        _, user = make_user(routes, sup_token, "u10@example.test")
        assert routes.get("/api/setup/progress", headers=auth(user)).status_code == 403
    finally:
        set_runtime(None)
        executor.clear_apps()
