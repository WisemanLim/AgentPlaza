"""Epic 16 — LLM·프로토콜 확장 (D1-02 OpenAI 호환 서버, D1-04 CLI 브리지, D7-05 에이전트=모델·OpenAPI→도구,
D7-06 AG-UI 표준·ACP, NFR-P4 재연결 재개).

가짜 REST 서비스·가짜 OpenAI 호환 서버는 ASGI 로 붙이고, CLI 브리지는 실제 HTTP 서버(스레드)와 가짜 CLI 프로세스로 돈다.
"""
import json
import os
import sys
import threading
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app import db as appdb
from app.assistant import agui
from app.llm.providers import ChatResult, MockProvider, OpenAICompatProvider
from app.models import LlmModel, LlmRoute
from app.orchestrator import executor
from app.services import registry
from helpers import auth, load_template_app, make_user

ROOT = Path(__file__).resolve().parents[1]
FAKE = ROOT / "bridge" / "fake"


@pytest.fixture
def plan(client, monkeypatch):
    holder = {"plan": {"steps": []}}
    default = MockProvider.responder

    def responder(model, req):
        if req.messages and req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator"):
            return ChatResult(content=json.dumps(holder["plan"]), model=model)
        return default(model, req)

    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    with appdb.SessionLocal() as s:
        for alias in ("plaza/orchestrator", "plaza/chat"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()
    yield holder
    executor.clear_apps()
    OpenAICompatProvider.TRANSPORTS.clear()


def add_calc(tmp_path, monkeypatch, agent_id="calc"):
    app, manifest = load_template_app(tmp_path, "execution", agent_id, monkeypatch, registry.agent_key(agent_id))
    executor.register_app(f"http://{agent_id}.test", app)
    with appdb.SessionLocal() as s:
        registry.register(s, manifest, endpoint=f"http://{agent_id}.test", status="healthy")


# ---------------- D7-05 OpenAPI → 도구 ----------------

def rest_app(extra: bool = False) -> FastAPI:
    app = FastAPI(title="Inventory API", version="2.1.0")
    items: dict[int, dict] = {}

    class ItemIn(BaseModel):
        name: str
        qty: int = 1

    @app.post("/items", operation_id="createItem", summary="재고 품목 등록")
    def create(body: ItemIn, x_api_key: str = Header()):
        if x_api_key != "inv-key":
            raise HTTPException(401)
        items[len(items) + 1] = body.model_dump()
        return {"id": len(items), **body.model_dump()}

    @app.get("/items/{item_id}", operation_id="getItem", summary="품목 조회")
    def get(item_id: int, verbose: bool = False):
        return {"id": item_id, **items.get(item_id, {}), "verbose": verbose}

    if extra:
        @app.delete("/items/{item_id}", operation_id="deleteItem")
        def delete(item_id: int):
            return {"deleted": item_id}
    return app


def test_e16_01_openapi_to_tools(client, sup_token, plan):
    """D7-05: OpenAPI 문서 → capability(=MCP 도구). 경로·쿼리·본문 매핑, 인증 헤더, 핀 변경 감지."""
    executor.register_app("http://inv.test", rest_app())
    res = client.post("/api/agents/link", json={"kind": "openapi", "url": "http://inv.test/openapi.json", "id": "inventory",
                                                "auth_header": "x-api-key", "auth_value": "inv-key"}, headers=auth(sup_token))
    assert res.status_code == 201, res.text
    caps = {c["verb"]: c for c in res.json()["capabilities"]}
    assert set(caps) == {"create_item", "get_item"} and res.json()["source"] == "link"
    plan["plan"] = {"pattern": "sequential", "steps": [
        {"id": "s1", "agent": "inventory", "capability": "create_item", "args": {"name": "볼트", "qty": 30}},
        {"id": "s2", "agent": "inventory", "capability": "get_item", "args": {"item_id": "{{s1.id}}", "verbose": True}}]}
    r = client.post("/api/orchestrate", json={"message": "볼트 30개 등록 후 조회"}, headers=auth(sup_token)).json()
    assert r["results"]["s1"]["result"] == {"id": 1, "name": "볼트", "qty": 30}
    assert r["results"]["s2"]["result"] == {"id": 1, "name": "볼트", "qty": 30, "verbose": True}
    executor.register_app("http://inv.test", rest_app(extra=True))  # 원격 문서가 바뀜 → rug-pull 의심
    rv = client.post("/api/agents/inventory/revalidate", headers=auth(sup_token)).json()
    assert rv["changed"] is True and rv["status"] == "unhealthy"


def test_e16_02_openapi_rejects_bad_specs(client, sup_token, plan):
    bad = FastAPI(openapi_url="/spec.json")
    executor.register_app("http://bad.test", bad)  # paths 없음
    res = client.post("/api/agents/link", json={"kind": "openapi", "url": "http://bad.test/spec.json"}, headers=auth(sup_token))
    assert res.status_code == 422 and "operation 없음" in res.json()["detail"]


# ---------------- D7-05 에이전트 = 모델 ----------------

def test_e16_03_agents_as_models(client, sup_token, plan, tmp_path, monkeypatch):
    add_calc(tmp_path, monkeypatch)
    ids = {m["id"] for m in client.get("/v1/models", headers=auth(sup_token)).json()["data"]}
    assert {"agent/calc", "agent/orchestrator", "plaza/chat"} <= ids
    plan["plan"] = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "6*7"}}]}
    body = {"model": "agent/calc", "messages": [{"role": "user", "content": "6 곱하기 7"}]}
    res = client.post("/v1/chat/completions", json=body, headers=auth(sup_token))
    assert res.status_code == 200 and res.headers["x-plaza-agent"] == "calc"
    out = res.json()
    assert '"value": 42' in out["choices"][0]["message"]["content"] and out["plaza"]["state"] == "succeeded"
    res = client.post("/v1/chat/completions", json={**body, "stream": True}, headers=auth(sup_token))
    chunks = [json.loads(ln[6:]) for ln in res.text.splitlines() if ln.startswith("data: {")]
    text = "".join(c["choices"][0]["delta"].get("content", "") for c in chunks)
    assert res.headers["content-type"].startswith("text/event-stream") and "42" in text and res.text.endswith("data: [DONE]\n\n")
    key = client.post("/api/api-keys", json={"name": "owui", "agents": ["other"]}, headers=auth(sup_token)).json()["key"]
    assert client.post("/v1/chat/completions", json=body, headers={"Authorization": f"Bearer {key}"}).status_code == 403
    assert "agent/calc" not in {m["id"] for m in client.get("/v1/models", headers={"Authorization": f"Bearer {key}"}).json()["data"]}
    assert client.post("/v1/chat/completions", json={**body, "model": "agent/ghost"}, headers=auth(sup_token)).status_code == 404


# ---------------- D1-02 OpenAI 호환 서버 ----------------

def fake_openai(require_key: str | None = None) -> FastAPI:
    app = FastAPI()

    def check(authorization):
        if require_key and authorization != f"Bearer {require_key}":
            raise HTTPException(401, "bad key")

    @app.get("/v1/models")
    def models(authorization: str | None = Header(default=None)):
        check(authorization)
        return {"object": "list", "data": [{"id": "qwen3-8b", "object": "model"}]}

    @app.post("/v1/chat/completions")
    def chat(body: dict, authorization: str | None = Header(default=None)):
        check(authorization)
        last = body["messages"][-1]["content"]
        return {"id": "x", "object": "chat.completion", "model": body["model"],
                "choices": [{"index": 0, "message": {"role": "assistant", "content": f"vllm:{body['model']}:{last}"},
                             "finish_reason": "stop"}], "usage": {"prompt_tokens": 3, "completion_tokens": 2}}
    return app


def test_e16_04_openai_compatible_server_registry(client, sup_token, plan):
    OpenAICompatProvider.TRANSPORTS["http://vllm.test/v1"] = httpx.ASGITransport(app=fake_openai("srv-key"))
    h = auth(sup_token)
    assert client.put("/api/llm/servers/ollama", json={"base_url": "http://x/v1"}, headers=h).status_code == 422  # 예약어
    res = client.put("/api/llm/servers/vllm", json={"base_url": "http://vllm.test/v1", "local": True, "api_key": "srv-key"}, headers=h)
    assert res.status_code == 200 and res.json() == {"name": "vllm", "base_url": "http://vllm.test/v1", "local": True, "has_key": True}
    assert "srv-key" not in json.dumps(client.get("/api/llm/servers", headers=h).json())  # 키는 시크릿 저장소에만
    assert client.get("/api/llm/servers/vllm/models", headers=h).json()["models"] == ["qwen3-8b"]
    model = {"provider": "vllm", "model_id": "qwen3-8b", "local": True, "context": 32768, "tool_call": True, "vision": False,
             "license": "Apache-2.0"}
    assert client.post("/api/llm/models", json=model, headers=h).status_code == 201
    with appdb.SessionLocal() as s:
        s.merge(LlmRoute(alias="t/vllm", targets=["vllm/qwen3-8b"]))
        s.commit()
    res = client.post("/v1/chat/completions", json={"model": "t/vllm", "messages": [{"role": "user", "content": "hi"}]},
                      headers=h | {"X-Plaza-Data-Class": "L3"})
    assert res.status_code == 200 and res.json()["choices"][0]["message"]["content"] == "vllm:qwen3-8b:hi"
    assert res.headers["x-plaza-model"] == "vllm/qwen3-8b"  # 로컬 서버라 L3 도 허용
    assert client.delete("/api/llm/servers/vllm", headers=h).status_code == 200
    assert next(m for m in client.get("/api/llm/models", headers=h).json() if m["id"] == "vllm/qwen3-8b")["enabled"] is False


# ---------------- D1-04 CLI 브리지 · D7-06 ACP ----------------

@pytest.fixture
def bridge(monkeypatch):
    from bridge import cli_bridge
    monkeypatch.setattr(cli_bridge, "TOKEN", "bridge-token")
    monkeypatch.setenv("CLI_BRIDGE_BACKENDS", json.dumps({
        "fake-claude": {"cmd": [sys.executable, str(FAKE / "fake_claude.py"), "{prompt}"], "protocol": "ndjson"},
        "fake-acp": {"cmd": [sys.executable, str(FAKE / "fake_acp.py")], "protocol": "acp"}}))
    srv = cli_bridge.serve(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1"
    srv.shutdown()


def test_e16_05_cli_bridge_as_public_backend(client, sup_token, plan, bridge):
    """D1-04: CLI 브리지 = OpenAI 호환 서버(local=false). 퍼블릭 취급이라 L2 이상은 정책상 차단."""
    h = auth(sup_token)
    client.put("/api/llm/servers/cli", json={"base_url": bridge, "local": False, "api_key": "bridge-token"}, headers=h)
    assert client.get("/api/llm/servers/cli/models", headers=h).json()["models"] == ["fake-acp", "fake-claude"]
    for mid in ("fake-claude", "fake-acp"):
        client.post("/api/llm/models", json={"provider": "cli", "model_id": mid, "local": False, "context": 200000,
                                             "tool_call": False, "vision": False, "license": "Proprietary"}, headers=h)
    with appdb.SessionLocal() as s:
        s.merge(LlmRoute(alias="plaza/cli", targets=["cli/fake-claude"]))
        s.merge(LlmRoute(alias="plaza/acp", targets=["cli/fake-acp"]))
        s.commit()
    msg = {"messages": [{"role": "user", "content": "리팩터링 계획 세워줘"}]}
    res = client.post("/v1/chat/completions", json={"model": "plaza/cli", **msg}, headers=h | {"X-Plaza-Data-Class": "L0"})
    assert res.status_code == 200 and res.json()["choices"][0]["message"]["content"].startswith("fake-claude: 리팩터링")
    res = client.post("/v1/chat/completions", json={"model": "plaza/cli", "stream": True, **msg}, headers=h | {"X-Plaza-Data-Class": "L1"})
    assert "리팩터링" in "".join(json.loads(ln[6:])["choices"][0]["delta"].get("content", "")
                               for ln in res.text.splitlines() if ln.startswith("data: {"))
    assert client.post("/v1/chat/completions", json={"model": "plaza/cli", **msg}, headers=h).status_code == 403  # L2 기본
    acp = client.post("/v1/chat/completions", json={"model": "plaza/acp", **msg}, headers=h | {"X-Plaza-Data-Class": "L0"})
    assert "fake-acp:" in acp.json()["choices"][0]["message"]["content"] and "(permission denied)" in acp.json()["choices"][0]["message"]["content"]
    assert httpx.get(bridge + "/models", headers={"Authorization": "Bearer wrong"}).status_code == 401


@pytest.mark.parametrize("event,delta,final", [
    ({"type": "assistant", "message": {"content": [{"type": "text", "text": "안녕"}]}}, "안녕", None),
    ({"type": "stream_event", "event": {"delta": {"type": "text_delta", "text": "조"}}}, "조", None),
    ({"type": "result", "is_error": False, "result": "최종"}, "", "최종"),
    ({"type": "item.completed", "item": {"type": "agent_message", "text": "codex 답"}}, "codex 답", None),
    ({"msg": {"type": "agent_message", "message": "구형 codex"}}, "구형 codex", None),
    ({"type": "message", "role": "assistant", "content": "gemini 답", "delta": True}, "gemini 답", None),
    ({"type": "system", "subtype": "init"}, "", None)])
def test_e16_06_ndjson_shapes(event, delta, final):
    from bridge.cli_bridge import text_from_event
    assert text_from_event(event) == (delta, final)


def test_e16_07_ndjson_error_and_acp_direct():
    from bridge.cli_bridge import BridgeError, run_acp, text_from_event
    with pytest.raises(BridgeError):
        text_from_event({"type": "result", "is_error": True, "result": "rate limited"})
    out = "".join(run_acp([sys.executable, str(FAKE / "fake_acp.py")], "[user]\n안녕 반가워"))
    assert out.startswith("fake-acp: 안녕 반가워") and "(permission denied)" in out


# ---------------- D7-06 AG-UI · NFR-P4 재연결 ----------------

def stream_events(res) -> list[dict]:
    return [json.loads(ln[6:]) for ln in res.text.splitlines() if ln.startswith("data: ")]


def test_e16_08_agui_events_conform(client, sup_token, plan, tmp_path, monkeypatch):
    """도구 호출·승인·LLM 단독 세 가지 흐름의 이벤트가 AG-UI 이름·필수 필드·순서를 지킨다."""
    res = client.post("/api/chat/stream", json={"message": "안녕"}, headers=auth(sup_token))
    assert agui.check(stream_events(res)) == []
    add_calc(tmp_path, monkeypatch)
    plan["plan"] = {"pattern": "parallel", "steps": [
        {"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "1+1"}},
        {"id": "s2", "agent": "calc", "capability": "calculate", "args": {"expression": "2+2"}}]}
    ev = stream_events(client.post("/api/chat/stream", json={"message": "두 개 계산"}, headers=auth(sup_token)))
    assert agui.check(ev) == [] and sum(e["type"] == "TOOL_CALL_RESULT" for e in ev) == 2
    bad = [{"type": "RUN_STARTED", "threadId": "t", "runId": "r"}, {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m", "delta": ""},
           {"type": "TOOL_CALL_RESULT", "toolCallId": "x", "messageId": "x", "content": "{}"}, {"type": "WHATEVER"}]
    assert len(agui.check(bad)) >= 3


def test_e16_09_resume_from_last_event_id(client, sup_token, plan):
    res = client.post("/api/chat/stream", json={"message": "재개 시험"}, headers=auth(sup_token))
    sid = res.headers["x-plaza-stream"]
    frames = [ln for ln in res.text.splitlines() if ln.startswith(("id: ", "data: "))]
    ids = [int(ln[4:]) for ln in frames if ln.startswith("id: ")]
    assert ids == list(range(1, len(ids) + 1))  # seq 는 1부터 빈틈없이
    first = stream_events(res)
    assert first[0] == {"type": "CUSTOM", "name": "stream", "value": {"id": sid}} and first[-1]["name"] == "stream_end"
    cut = 3  # 3번째 이벤트까지 받고 끊겼다고 가정
    replay = client.get(f"/api/chat/streams/{sid}", headers=auth(sup_token) | {"Last-Event-ID": str(cut)})
    assert stream_events(replay) == first[cut:]
    assert stream_events(client.get(f"/api/chat/streams/{sid}?after=0", headers=auth(sup_token))) == first
    _, other = make_user(client, sup_token, "u16@example.test")
    assert client.get(f"/api/chat/streams/{sid}", headers=auth(other)).status_code == 404


def test_e16_10_disconnect_keeps_running_and_resumes(client, sup_token, plan):
    """끊겨도 실행은 계속된다(NFR-P4): 첫 이벤트만 읽고 연결을 닫은 뒤, 재연결로 나머지와 종료까지 받는다."""
    with client.stream("POST", "/api/chat/stream", json={"message": "끊김 시험"}, headers=auth(sup_token)) as res:
        sid = res.headers["x-plaza-stream"]
        for line in res.iter_lines():
            if line.startswith("id: "):
                break
    rest = stream_events(client.get(f"/api/chat/streams/{sid}?after=1", headers=auth(sup_token)))
    types = [e["type"] for e in rest]
    assert "RUN_FINISHED" in types and rest[-1] == {"type": "CUSTOM", "name": "stream_end"}
    assert agui.check([e for e in rest]) == []
