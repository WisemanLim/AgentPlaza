"""Epic 23 — 조직·부서 단위 배치 (PRD Q7·Q12, UI K02·FL-07): 기본 조직 + 그룹 + deploy_scope.

범위 밖 사용자에게는 에이전트 목록·네비·계획(도구)·MCP·Addon 화면(forwardAuth)에서 빠진다. 데이터 분리(X09)는 하지 않는다.
"""
import json

import pytest

from app import db as appdb
from app.llm.providers import ChatResult, MockProvider
from app.models import LlmRoute
from app.orchestrator import executor
from app.services import registry
from helpers import auth, load_template_app, make_user

META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}


@pytest.fixture
def world(client, sup_token, tmp_path, monkeypatch):
    """calc(실행형) 에이전트 + 사용자 3명(영업 2·개발 1) + 계획 LLM(항상 calc.calculate)."""
    with appdb.SessionLocal() as s:
        app, manifest = load_template_app(tmp_path, "execution", "calc", monkeypatch, registry.agent_key("calc"))
        executor.register_app("http://calc.test", app)
        registry.register(s, manifest, endpoint="http://calc.test", status="healthy")
        for alias in ("plaza/orchestrator", "plaza/chat"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()
    plan = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "2+3"}}]}
    default = MockProvider.responder
    monkeypatch.setattr(MockProvider, "responder", staticmethod(
        lambda model, req: ChatResult(content=json.dumps(plan), model=model)
        if req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator") else default(model, req)))
    users = {name: make_user(client, sup_token, f"{name}@example.test") for name in ("sales1", "sales2", "dev1")}
    yield {k: v[1] for k, v in users.items()} | {"ids": {k: v[0]["id"] for k, v in users.items()}}
    executor.clear_apps()


def ids_of(client, token):
    return [a["id"] for a in client.get("/api/agents", headers=auth(token)).json()]


def test_e23_01_default_org_and_membership(client, sup_token, world):
    h = auth(sup_token)
    orgs = client.get("/api/orgs", headers=h).json()
    assert [o["id"] for o in orgs] == ["default"] and orgs[0]["members"] == 4  # supervisor + 3
    assert client.get("/api/orgs", headers=auth(world["dev1"])).json()[0]["my_role"] == "member"
    assert client.post("/api/orgs", json={"id": "acme-kr", "name": "Acme 한국"}, headers=auth(world["dev1"])).status_code == 403
    assert client.post("/api/orgs", json={"id": "acme-kr", "name": "Acme 한국"}, headers=h).status_code == 201
    assert client.get("/api/orgs/acme-kr", headers=auth(world["dev1"])).status_code == 404  # 구성원 아님
    assert client.delete("/api/orgs/default", headers=h).status_code == 409


def test_e23_02_org_admin_manages_own_org_only(client, sup_token, world):
    h = auth(sup_token)
    client.post("/api/orgs", json={"id": "other", "name": "Other"}, headers=h)
    assert client.put("/api/orgs/default/members", json={"email": "sales1@example.test", "role": "admin"},
                      headers=auth(world["dev1"])).status_code == 403
    client.put("/api/orgs/default/members", json={"email": "sales1@example.test", "role": "admin"}, headers=h)
    a = auth(world["sales1"])  # 플랫폼 역할은 user 지만 기본 조직의 조직 admin
    g = client.post("/api/orgs/default/groups", json={"name": "영업팀"}, headers=a)
    assert g.status_code == 201
    assert client.post("/api/orgs/default/groups", json={"name": "영업팀"}, headers=a).status_code == 409
    assert client.put(f"/api/orgs/default/groups/{g.json()['id']}/members", json={"email": "sales2@example.test"},
                      headers=a).status_code == 200
    assert client.post("/api/orgs/other/groups", json={"name": "x"}, headers=a).status_code == 403
    assert client.put(f"/api/orgs/default/groups/{g.json()['id']}/members", json={"email": "nobody@example.test"},
                      headers=a).status_code == 404
    detail = client.get("/api/orgs/default", headers=a).json()
    assert detail["can_manage"] is True and detail["groups"][0]["members"][0]["email"] == "sales2@example.test"
    assert {m["email"]: m["role"] for m in detail["members"]}["sales1@example.test"] == "admin"
    # 조직 admin 이라도 에이전트 배치 범위는 플랫폼 admin 이상
    assert client.put("/api/agents/calc/scope", json={"kind": "org"}, headers=a).status_code == 403


def test_e23_03_group_scope_hides_agent_everywhere(client, sup_token, world):
    """그룹 배치: 영업팀만 calc 를 본다 — 목록·네비·계획(도구)·MCP·forwardAuth·/v1 모델."""
    h = auth(sup_token)
    gid = client.post("/api/orgs/default/groups", json={"name": "영업팀"}, headers=h).json()["id"]
    for who in ("sales1", "sales2"):
        client.put(f"/api/orgs/default/groups/{gid}/members", json={"email": f"{who}@example.test"}, headers=h)
    r = client.put("/api/agents/calc/scope", json={"org_id": "default", "kind": "group", "ids": [gid]}, headers=h)
    assert r.status_code == 200 and r.json()["scope"]["kind"] == "group"
    sales, dev = world["sales1"], world["dev1"]
    assert "calc" in ids_of(client, sales) and "calc" not in ids_of(client, dev)
    assert client.get("/api/agents/calc", headers=auth(dev)).status_code == 404
    assert "calc" in ids_of(client, sup_token)  # supervisor 는 항상
    ok = client.post("/api/orchestrate", json={"message": "2+3"}, headers=auth(sales)).json()
    assert ok["results"]["s1"]["ok"] is True
    miss = client.post("/api/orchestrate", json={"message": "2+3"}, headers=auth(dev)).json()
    assert "s1" not in (miss["results"] or {})  # 계획 후보에서 빠짐 — 실행되지 않음
    assert not any(st.get("agent") == "calc" and st["id"] in (miss["results"] or {}) for st in miss["plan"]["steps"])
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": META}}
    hdr = {"accept": "application/json, text/event-stream", "mcp-protocol-version": "2026-07-28", "mcp-method": "tools/list"}
    assert client.post("/mcp/calc", json=body, headers=auth(sales) | hdr).status_code == 200
    assert client.post("/mcp/calc", json=body, headers=auth(dev) | hdr).status_code == 403
    fwd = {"x-forwarded-uri": "/a/calc/api/capabilities"}
    assert client.get("/api/auth/forward", headers=auth(sales) | fwd).status_code == 200
    assert client.get("/api/auth/forward", headers=auth(dev) | fwd).status_code == 403
    models = lambda tok: [m["id"] for m in client.get("/v1/models", headers=auth(tok)).json()["data"]]  # noqa: E731
    assert "agent/calc" in models(sales) and "agent/calc" not in models(dev)
    assert client.get("/api/audit?action=agent.scope_set", headers=h).json()


def test_e23_04_user_and_org_scopes_and_clear(client, sup_token, world):
    h = auth(sup_token)
    client.put("/api/agents/calc/scope", json={"kind": "user", "ids": [world["ids"]["dev1"]]}, headers=h)
    assert "calc" in ids_of(client, world["dev1"]) and "calc" not in ids_of(client, world["sales1"])
    client.post("/api/orgs", json={"id": "lab", "name": "연구소"}, headers=h)
    client.put("/api/orgs/lab/members", json={"email": "sales2@example.test"}, headers=h)
    client.put("/api/agents/calc/scope", json={"org_id": "lab", "kind": "org"}, headers=h)
    assert "calc" in ids_of(client, world["sales2"]) and "calc" not in ids_of(client, world["dev1"])
    bad = client.put("/api/agents/calc/scope", json={"org_id": "lab", "kind": "user", "ids": [world["ids"]["dev1"]]}, headers=h)
    assert bad.status_code == 422  # 그 조직 구성원이 아님
    assert client.put("/api/agents/calc/scope", json={"org_id": "nope", "kind": "org"}, headers=h).status_code == 404
    client.delete("/api/agents/calc/scope", headers=h)
    assert all("calc" in ids_of(client, world[u]) for u in ("sales1", "sales2", "dev1"))  # 범위 없음 = 모두
    client.delete("/api/orgs/lab/members/" + str(world["ids"]["sales2"]), headers=h)
    assert client.get("/api/orgs/lab", headers=h).json()["members"] == []


def test_e23_05_market_install_with_deploy_scope(client, sup_token, world):
    """도입 위저드(E04 2단계)의 배치 대상이 설치 요청과 함께 저장된다."""
    h = auth(sup_token)
    gid = client.post("/api/orgs/default/groups", json={"name": "개발팀"}, headers=h).json()["id"]
    r = client.post("/api/market/install/board", json={"deploy_scope": {"org_id": "default", "kind": "group", "ids": [gid]}},
                    headers=h)
    assert r.status_code == 202, r.text
    assert client.get("/api/agents/board/scope", headers=h).json()["scope"]["ids"] == [gid]
    bad = client.post("/api/market/install/board", json={"deploy_scope": {"kind": "group", "ids": ["nope"]}}, headers=h)
    assert bad.status_code == 422
