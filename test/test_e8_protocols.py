"""Epic 8 — 표준 프로토콜 MCP·A2A (D7-01/02/03/04, D6-04 경로 C, NFR-P1·P2·P3, US5·US6).

모든 프로토콜 시험은 공식 클라이언트(mcp 2.x ClientSession, a2a-sdk ClientFactory)로 한다. 네트워크 없이 ASGI 전송.
"""
import asyncio
import base64
import json
import uuid

import httpx
import httpx2
import pytest
from a2a.client import ClientConfig, ClientFactory
from a2a.helpers import get_data_parts, new_data_part, new_text_part
from a2a.types import GetTaskRequest, Message, Role, SendMessageRequest
from google.protobuf.json_format import MessageToDict
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app import db as appdb
from app.agentspec import generator as gen
from app.llm.providers import ChatResult, MockProvider
from app.main import app as platform
from app.models import LlmRoute
from app.orchestrator import executor
from app.protocols import card as cards
from app.protocols import keys
from app.registry import pipeline
from app.services import registry
from helpers import auth, load_template_app

GW = "http://gw.test"


def run(coro):
    return asyncio.run(coro)


async def mcp_flow(app, url, headers, calls=(), mode="discover"):
    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), headers=headers) as http, \
            streamable_http_client(url, http_client=http) as (r, w):
        async with ClientSession(r, w) as s:
            if mode == "discover":
                await s.discover()
            else:
                init = await s.initialize()
                assert init.protocol_version == "2025-11-25"
            tools = [t.name for t in (await s.list_tools()).tools]
            results = [await s.call_tool(name, args) for name, args in calls]
    return tools, results


async def a2a_send(app, base, headers, parts, verifier=True):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), headers=headers) as hc:
        factory = ClientFactory(ClientConfig(httpx_client=hc, streaming=False))
        client = await factory.create_from_url(base, signature_verifier=cards.verify if verifier else None)
        msg = Message(role=Role.ROLE_USER, message_id=str(uuid.uuid4()), parts=parts)
        final = None
        async for ev in client.send_message(SendMessageRequest(message=msg)):
            final = ev
        task = final.task
        got = await client.get_task(GetTaskRequest(id=task.id))
        return task, got


def state_of(task) -> str:
    return MessageToDict(task.status).get("state", "")


def data_of(task) -> dict:
    return get_data_parts(list(task.artifacts[0].parts))[0] if task.artifacts else {}


@pytest.fixture
def agents(client, tmp_path, monkeypatch):
    """calc(execution)·ops(hitl)·kb(rag) 를 설치된 것처럼 카탈로그 등록 + ASGI 연결."""
    with appdb.SessionLocal() as s:
        for aid, t in (("calc", "execution"), ("ops", "hitl"), ("kb", "rag")):
            app, m = load_template_app(tmp_path, t, aid, monkeypatch, registry.agent_key(aid))
            executor.register_app(pipeline.endpoint_for(aid), app)
            registry.register(s, m, endpoint=pipeline.endpoint_for(aid), status="healthy")
    yield
    executor.clear_apps()


def test_e8_01_agent_sdk_mcp_both_protocol_versions(tmp_path, monkeypatch):
    """D7-01·NFR-P1: 에이전트 자체 /mcp — 2026-07-28(server/discover)·2025-11-25(initialize) 모두."""
    app, _ = load_template_app(tmp_path, "execution", "calc", monkeypatch, "k1")
    url, h = "http://calc.test/mcp", {"x-api-key": "k1"}
    for mode in ("discover", "initialize"):
        tools, res = run(mcp_flow(app, url, h, [("calculate", {"expression": "6*7"}), ("calculate", {"bad": 1})], mode))
        assert tools == ["calculate"]
        assert res[0].structured_content == {"value": 42} and res[0].is_error is False
        assert res[1].is_error and "invalid arguments" in res[1].content[0].text
    with pytest.raises(BaseException):
        run(mcp_flow(app, url, {}, []))  # 키 없음 → 거부


def test_e8_02_agent_sdk_a2a(tmp_path, monkeypatch):
    """D7-03·NFR-P2: 서명 카드 검증 + SendMessage(Data Part/텍스트) → COMPLETED, GetTask, 승인 필요는 FAILED."""
    calc, _ = load_template_app(tmp_path, "execution", "calc", monkeypatch, "k1", public_url="http://calc.test")
    task, got = run(a2a_send(calc, "http://calc.test", {"x-api-key": "k1"},
                             [new_data_part({"capability": "calculate", "args": {"expression": "2+3"}})]))
    assert state_of(task) == "TASK_STATE_COMPLETED" and data_of(task) == {"value": 5}
    assert state_of(got) == "TASK_STATE_COMPLETED"
    task, _ = run(a2a_send(calc, "http://calc.test", {"x-api-key": "k1"}, [new_text_part("10/4")]))
    assert data_of(task) == {"value": 2.5}  # 단일 capability: 텍스트 → 필수 문자열 필드
    ops, _ = load_template_app(tmp_path, "hitl", "ops", monkeypatch, "k2", public_url="http://ops.test")
    task, _ = run(a2a_send(ops, "http://ops.test", {"x-api-key": "k2"},
                           [new_data_part({"capability": "execute_action", "args": {"action": "drop"}})]))
    assert state_of(task) == "TASK_STATE_FAILED"  # 승인 없이 실행 불가(DP8)
    task, _ = run(a2a_send(ops, "http://ops.test", {"x-api-key": "k2"}, [new_text_part("anything")]))
    assert state_of(task) == "TASK_STATE_FAILED"  # capability 2개 → 지정 필요


def test_e8_03_platform_mcp_gateway_us5(client, sup_token, agents):
    """US5: Cursor 등 외부 클라이언트가 /mcp/{agent} 에 x-api-key 로 연결 → tools/list·tools/call. 범위·비활성·무인증 거부."""
    key = client.post("/api/api-keys", json={"name": "cursor", "agents": ["calc"]}, headers=auth(sup_token)).json()["key"]
    tools, res = run(mcp_flow(platform, f"{GW}/mcp/calc", {"x-api-key": key}, [("calculate", {"expression": "1+1"})]))
    assert tools == ["calculate"] and res[0].structured_content == {"value": 2}
    tools, _ = run(mcp_flow(platform, f"{GW}/mcp/calc", {"x-api-key": key}, [], mode="initialize"))
    assert tools == ["calculate"]
    ev = client.get("/api/audit?action=tool.call", headers=auth(sup_token)).json()
    assert ev[0]["agent_id"] == "calc" and ev[0]["detail"]["channel"] == "mcp"
    for path, headers, code in (("/mcp/kb", {"x-api-key": key}, 403), ("/mcp/calc", {}, 401), ("/mcp/ghost", {"x-api-key": key}, 404)):
        res = run(_post_raw(path, headers))
        assert res.status_code == code, (path, res.status_code, res.text)
    client.patch("/api/agents/calc", json={"is_active": False}, headers=auth(sup_token))
    assert run(_post_raw("/mcp/calc", auth(sup_token))).status_code == 403


async def _post_raw(path, headers):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=platform), base_url=GW) as c:
        return await c.post(path, json=body, headers={**headers, "accept": "application/json, text/event-stream",
                                                     "mcp-protocol-version": "2026-07-28", "mcp-method": "tools/list"})


def test_e8_04_mcp_cannot_bypass_human_approval(client, sup_token, agents):
    """DP8: 승인 필요 capability 는 MCP 로 직접 실행 불가 + 원장 기록."""
    _, res = run(mcp_flow(platform, f"{GW}/mcp/ops", auth(sup_token), [("execute_action", {"action": "drop-db"})]))
    assert res[0].is_error and "승인" in res[0].content[0].text
    assert client.get("/api/audit?action=tool.approval_bypass_blocked", headers=auth(sup_token)).json()


@pytest.fixture
def mock_plans(monkeypatch):
    holder = {"plan": {"steps": []}}
    default = MockProvider.responder

    def responder(model, req):
        if req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator"):
            return ChatResult(content=json.dumps(holder["plan"]), model=model)
        return default(model, req)

    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    with appdb.SessionLocal() as s:
        for alias in ("plaza/orchestrator", "plaza/chat"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()
    return holder


def test_e8_05_orchestrator_as_mcp_tool_and_a2a(client, sup_token, agents, mock_plans):
    """PRD 4.2: Orchestrator 를 MCP tool orchestrate 와 A2A Task 로 외부에서 호출."""
    mock_plans["plan"] = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "3*3"}}]}
    tools, res = run(mcp_flow(platform, f"{GW}/mcp/orchestrator", auth(sup_token), [("orchestrate", {"message": "3 곱하기 3"})]))
    assert tools == ["orchestrate"] and res[0].structured_content["state"] == "succeeded"
    card = client.get("/a/orchestrator/.well-known/agent-card.json").json()
    assert card["signatures"] and card["supportedInterfaces"][0]["url"] == f"{GW}/a/orchestrator/a2a"
    task, _ = run(a2a_send(platform, f"{GW}/a/orchestrator", auth(sup_token), [new_text_part("3 곱하기 3")]))
    assert state_of(task) == "TASK_STATE_COMPLETED" and data_of(task)["state"] == "succeeded"
    unauth = run(_a2a_raw("/a/orchestrator/a2a", {}))
    assert unauth.status_code == 401


async def _a2a_raw(path, headers):
    body = {"jsonrpc": "2.0", "id": 1, "method": "GetTask", "params": {"id": "x"}}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=platform), base_url=GW) as c:
        return await c.post(path, json=body, headers={**headers, "A2A-Version": "1.0"})


def test_e8_06_platform_a2a_card_and_proxy(client, sup_token, agents):
    """D7-03: 공개 서명 카드(생성물 = agent.yaml) + 인증 프록시로 에이전트 A2A 호출."""
    card = client.get("/a/calc/.well-known/agent-card.json")
    assert card.status_code == 200  # 무인증 공개
    c = card.json()
    assert [s["id"] for s in c["skills"]] == ["calculate"] and c["supportedInterfaces"][0]["url"] == f"{GW}/a/calc/a2a"
    protected = json.loads(base64.urlsafe_b64decode(c["signatures"][0]["protected"] + "=="))
    assert protected["alg"] == "EdDSA" and protected["kid"] == client.get("/.well-known/jwks.json").json()["keys"][0]["kid"]
    task, _ = run(a2a_send(platform, f"{GW}/a/calc", auth(sup_token),
                           [new_data_part({"capability": "calculate", "args": {"expression": "7*6"}})]))
    assert state_of(task) == "TASK_STATE_COMPLETED" and data_of(task) == {"value": 42}
    assert run(_a2a_raw("/a/calc/a2a", {})).status_code == 401
    assert client.get("/a/ghost/.well-known/agent-card.json").status_code == 404
    assert client.get("/a/calc/mcp/server.json").status_code == 401
    sj = client.get("/a/calc/mcp/server.json", headers=auth(sup_token)).json()
    assert sj["remotes"][0]["url"] == f"{GW}/mcp/calc"


def test_e8_07_link_remote_a2a_and_mcp_us6(client, sup_token, tmp_path, monkeypatch, mock_plans):
    """US6·D6-04·D7-02·D7-04: 코드 설치 없이 원격 A2A Card / MCP 서버 등록 → 계약 시험 → Orchestrator 가 라우팅."""
    rem_a2a, _ = load_template_app(tmp_path, "execution", "rcalc", monkeypatch, "rk", public_url="http://remote-a2a.test")
    executor.register_app("http://remote-a2a.test", rem_a2a)
    rem_mcp, _ = load_template_app(tmp_path, "reviewer", "rguard", monkeypatch, "rk2")
    executor.register_app("http://remote-mcp.test", rem_mcp)
    try:
        a = client.post("/api/agents/link", json={"kind": "a2a", "url": "http://remote-a2a.test", "id": "partner-calc",
                                                  "auth_header": "x-api-key", "auth_value": "rk"}, headers=auth(sup_token))
        assert a.status_code == 201, a.text
        assert a.json()["source"] == "link" and a.json()["trust"] == "external"
        assert a.json()["federation"]["signature"] == "valid-platform"
        m = client.post("/api/agents/link", json={"kind": "mcp", "url": "http://remote-mcp.test/mcp", "id": "partner-guard",
                                                  "auth_header": "x-api-key", "auth_value": "rk2"}, headers=auth(sup_token))
        assert m.status_code == 201 and [c["verb"] for c in m.json()["capabilities"]] == ["review"]
        mock_plans["plan"] = {"pattern": "sequential", "steps": [
            {"id": "s1", "agent": "partner-calc", "capability": "calculate", "args": {"expression": "20+22"}},
            {"id": "s2", "agent": "partner-guard", "capability": "review", "args": {"text": "결과 {{s1.value}}"}}]}
        r = client.post("/api/orchestrate", json={"message": "원격 계산 후 검토"}, headers=auth(sup_token)).json()
        assert r["state"] == "succeeded", r["results"]
        assert r["results"]["s1"]["result"] == {"value": 42} and r["results"]["s2"]["result"]["verdict"] == "pass"
        assert client.post("/api/agents/partner-guard/revalidate", headers=auth(sup_token)).json()["ok"] is True
        swapped, _ = load_template_app(tmp_path / "v2", "service", "rguard", monkeypatch, "rk2")  # 원격이 조용히 도구 변경
        executor.register_app("http://remote-mcp.test", swapped)
        rv = client.post("/api/agents/partner-guard/revalidate", headers=auth(sup_token)).json()
        assert rv == {"ok": False, "status": "unhealthy", "changed": True}
        assert client.get("/api/audit?action=agent.rug_pull_suspected", headers=auth(sup_token)).json()
        bad = client.post("/api/agents/link", json={"kind": "a2a", "url": "http://nowhere.invalid"}, headers=auth(sup_token))
        assert bad.status_code == 422 and "계약 시험 실패" in bad.json()["detail"]
    finally:
        executor.clear_apps()


def test_e8_08_generated_vs_runtime_contract(tmp_path, monkeypatch):
    """NFR-P3: 선언(agent.yaml)과 실제 노출(MCP tools·카드 skills·서명)이 다르면 계약 시험이 잡는다."""
    good, m = load_template_app(tmp_path, "execution", "calc", monkeypatch, registry.agent_key("calc"))
    executor.register_app("http://calc-be:8000", good)
    assert run(pipeline.protocol_contract("http://calc-be:8000", m)) == []
    liar, _ = load_template_app(tmp_path / "l", "service", "calc", monkeypatch, registry.agent_key("calc"), signed=False)
    executor.register_app("http://calc-be:8000", liar)
    errs = run(pipeline.protocol_contract("http://calc-be:8000", m))
    assert sum("tools 불일치" in e for e in errs) == 2 and any("Agent Card" in e for e in errs)  # 2026-07-28·2025-11-25 각각
    executor.clear_apps()


def test_e8_09_jwks_and_standalone_export_artifacts(client, sup_token, tmp_path, monkeypatch):
    jw = client.get("/.well-known/jwks.json").json()["keys"][0]
    assert jw["kty"] == "OKP" and jw["crv"] == "Ed25519" and jw["kid"] == keys.kid()
    files = gen.scaffold("exp", "Exp", "service")
    m = gen.manifest_of(files)
    card = cards.signed_card(m, "http://127.0.0.1:8001/a2a")
    cards.verify(card)  # 플랫폼 키로 검증
    card.description = "tampered"
    with pytest.raises(Exception):
        cards.verify(card)


def test_e8_10_platform_key_concurrent_first_start(tmp_path):
    """여러 워커 동시 첫 기동에도 서명 키는 하나(원자적 게시) — 모든 프로세스가 같은 kid."""
    import subprocess
    import sys
    code = ("import os; os.environ['DATA_DIR']=%r; from app.protocols import keys; print(keys.kid())" % str(tmp_path))
    procs = [subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
             for _ in range(6)]
    outs = [p.communicate(timeout=60) for p in procs]
    assert all(p.returncode == 0 for p in procs), [e for _, e in outs]
    kids = {o.strip() for o, _ in outs}
    assert len(kids) == 1 and not list(tmp_path.glob("keys/.*.tmp"))
