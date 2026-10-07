"""Epic 4 — Orchestrator: 의도·계획·레지스트리 라우팅·실행 패턴·도구 실행·휴먼 승인 (D2-01/02/03/04/06, NFR-S4, US8).

실제 템플릿 에이전트(service·reviewer·execution·hitl)를 ASGI 로 띄워 내부 REST 로 호출하고,
계획 LLM 은 mock 공급자의 responder 를 바꿔 결정적으로 만든다.
"""
import json

import pytest

from app import db as appdb
from app.core.config import settings
from app.llm.providers import ChatResult, MockProvider
from app.models import Approval, LlmRoute
from app.orchestrator import executor
from app.services import registry
from helpers import auth, load_template_app, make_user

AGENTS = [("text-svc", "service"), ("guard", "reviewer"), ("calc", "execution"), ("ops", "hitl")]


@pytest.fixture
def plan_llm(monkeypatch):
    """plan 을 지정하면 orchestrator 시스템 프롬프트에 그 JSON 을 답한다. 그 외는 echo."""
    holder = {"plan": None}
    default = MockProvider.responder

    def responder(model, req):
        if req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator"):
            content = holder["plan"] if isinstance(holder["plan"], str) else json.dumps(holder["plan"] or {"steps": []})
            return ChatResult(content=content, model=model)
        return default(model, req)

    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    return holder


@pytest.fixture
def world(client, tmp_path, monkeypatch, plan_llm):
    with appdb.SessionLocal() as s:
        for alias in ("plaza/orchestrator", "plaza/chat"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        for agent_id, type_ in AGENTS:
            app, manifest = load_template_app(tmp_path, type_, agent_id, monkeypatch, registry.agent_key(agent_id))
            endpoint = f"http://{agent_id}.test"
            executor.register_app(endpoint, app)
            registry.register(s, manifest, endpoint=endpoint, status="healthy")
    yield plan_llm
    executor.clear_apps()


def orchestrate(client, token, message, **kw):
    res = client.post("/api/orchestrate", json={"message": message, **kw}, headers=auth(token))
    assert res.status_code == 200, res.text
    return res.json()


def types(events):
    return [e["type"] for e in events]


def test_e4_01_llm_plan_sequential_pipeline(client, sup_token, world):
    world["plan"] = {"pattern": "sequential", "steps": [
        {"id": "s1", "agent": "text-svc", "capability": "process", "args": {"text": "call 010-1234-5678", "op": "upper"}},
        {"id": "s2", "agent": "guard", "capability": "review", "args": {"text": "{{s1.text}}"}}]}
    r = orchestrate(client, sup_token, "대문자로 바꾸고 검토해줘")
    assert r["state"] == "succeeded" and r["plan"]["source"] == "llm"
    assert r["plan"]["steps"][1]["depends_on"] == ["s1"]
    assert r["results"]["s1"]["result"]["text"] == "CALL 010-1234-5678"
    assert r["results"]["s2"]["args"]["text"] == "CALL 010-1234-5678"  # {{s1.text}} 치환
    assert r["results"]["s2"]["result"]["verdict"] == "revise"
    t = types(r["events"])
    assert t[0] == "RUN_STARTED" and t[-1] == "RUN_FINISHED"
    assert t.index("TOOL_CALL_RESULT") < t.index("TEXT_MESSAGE_START")
    assert {"TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "STEP_STARTED", "STEP_FINISHED"} <= set(t)


def test_e4_02_parallel_pattern(client, sup_token, world):
    world["plan"] = {"pattern": "parallel", "steps": [
        {"id": "a", "agent": "calc", "capability": "calculate", "args": {"expression": "6*7"}},
        {"id": "b", "agent": "text-svc", "capability": "process", "args": {"text": "x y", "op": "wordcount"}}]}
    r = orchestrate(client, sup_token, "두 가지 동시에")
    assert r["plan"]["pattern"] == "parallel" and all(not s["depends_on"] for s in r["plan"]["steps"])
    assert r["results"]["a"]["result"]["value"] == 42 and r["results"]["b"]["result"]["words"] == 2


def test_e4_03_rule_fallback_when_llm_output_invalid(client, sup_token, world):
    world["plan"] = "not json at all"
    r = orchestrate(client, sup_token, "이 텍스트 요약 해줘: 첫 문장입니다. 둘째 문장입니다.")
    assert r["plan"]["source"] == "rules" and r["plan"]["llm_error"]
    assert r["plan"]["steps"][0]["agent"] == "text-svc" and r["results"]["s1"]["ok"] is True


def test_e4_04_registry_miss_then_general_answer(client, sup_token, world):
    world["plan"] = {"steps": [{"id": "s1", "agent": "ghost", "capability": "haunt", "args": {}}]}
    r = orchestrate(client, sup_token, "zzz qqq")
    misses = [e["value"] for e in r["events"] if e["type"] == "CUSTOM" and e["name"] == "registry_miss"]
    assert misses == [{"agent": "ghost", "capability": "haunt"}]
    assert r["state"] == "succeeded" and r["answer"].startswith("echo:")  # general 폴백


def test_e4_05_agent_scope_limits_routing(client, sup_token, world):
    world["plan"] = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "1+1"}}]}
    r = orchestrate(client, sup_token, "계산", agent_scope="text-svc")
    assert r["plan"]["steps"] == [] and r["plan"]["misses"]  # 스코프 밖 에이전트는 miss


def test_e4_06_dependency_failure_skips_dependents(client, sup_token, world):
    world["plan"] = {"pattern": "sequential", "steps": [
        {"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "import os"}},
        {"id": "s2", "agent": "guard", "capability": "review", "args": {"text": "{{s1}}"}}]}
    r = orchestrate(client, sup_token, "실패 전파")
    assert r["state"] == "failed"
    assert r["results"]["s1"]["ok"] is False and r["results"]["s2"]["error"].startswith("skipped")


def test_e4_07_tool_calls_are_audited(client, sup_token, world):
    world["plan"] = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "2+2"}}]}
    orchestrate(client, sup_token, "감사")
    ev = client.get("/api/audit?action=tool.call", headers=auth(sup_token)).json()
    assert ev and ev[0]["agent_id"] == "calc" and ev[0]["args_hash"] and ev[0]["result_hash"]


HITL_PLAN = {"steps": [{"id": "s1", "agent": "ops", "capability": "execute_action", "args": {"action": "restart-db"}}]}


def test_e4_08_hitl_pending_then_approved(client, sup_token, world, monkeypatch):
    """US8: hitl_pending 카드 → 승인 → 재개. 본인 승인 금지(four-eyes), user 는 승인 불가."""
    monkeypatch.setattr(settings, "hitl_allow_self_approval", False)
    world["plan"] = HITL_PLAN
    r = orchestrate(client, sup_token, "DB 재시작")
    assert r["state"] == "waiting_approval" and r["pending"]["capability"] == "execute_action"
    assert any(e["type"] == "CUSTOM" and e["name"] == "approval_required" for e in r["events"])
    ap_id = r["pending"]["approval_id"]
    _, user_tok = make_user(client, sup_token, "u@example.test")
    _, admin_tok = make_user(client, sup_token, "approver@example.test", "admin")
    assert client.post(f"/api/approvals/{ap_id}/approve", headers=auth(user_tok)).status_code == 403
    assert client.post(f"/api/approvals/{ap_id}/approve", headers=auth(sup_token)).status_code == 403  # 본인
    assert [a["id"] for a in client.get("/api/approvals", headers=auth(admin_tok)).json()] == [ap_id]
    done = client.post(f"/api/approvals/{ap_id}/approve", json={"reason": "점검 시간"}, headers=auth(admin_tok)).json()
    assert done["state"] == "succeeded" and done["results"]["s1"]["result"]["approval_id"] == ap_id
    assert client.post(f"/api/approvals/{ap_id}/approve", headers=auth(admin_tok)).status_code == 409
    actions = {e["action"] for e in client.get("/api/audit", headers=auth(sup_token)).json()}
    assert {"approval.requested", "approval.approved", "tool.call"} <= actions


def test_e4_09_hitl_rejected(client, sup_token, world, monkeypatch):
    monkeypatch.setattr(settings, "hitl_allow_self_approval", True)
    world["plan"] = HITL_PLAN
    ap_id = orchestrate(client, sup_token, "DB 재시작")["pending"]["approval_id"]
    r = client.post(f"/api/approvals/{ap_id}/reject", json={"reason": "업무 시간"}, headers=auth(sup_token)).json()
    assert r["approval"]["status"] == "rejected" and r["state"] == "failed"
    assert r["results"]["s1"]["error"] == "approval rejected"


def test_e4_10_hitl_expiry_cancels_task(client, sup_token, world):
    world["plan"] = HITL_PLAN
    r = orchestrate(client, sup_token, "DB 재시작")
    with appdb.SessionLocal() as s:  # 만료 시각을 과거로
        ap = s.get(Approval, r["pending"]["approval_id"])
        ap.expires_at = ap.created_at.replace(year=2000)
        s.commit()
    assert client.get("/api/approvals", headers=auth(sup_token)).json() == []
    task = client.get(f"/api/tasks/{r['task_id']}", headers=auth(sup_token)).json()
    assert task["state"] == "canceled"
    assert client.post(f"/api/approvals/{r['pending']['approval_id']}/approve",
                       headers=auth(sup_token)).status_code == 409


def test_e4_11_no_agents_general_answer_and_catalog(client, sup_token, plan_llm):
    with appdb.SessionLocal() as s:
        s.merge(LlmRoute(alias="plaza/chat", targets=["mock/echo"]))
        s.commit()
    r = orchestrate(client, sup_token, "안녕하세요")
    assert r["plan"]["source"] == "none" and r["answer"] == "echo: 안녕하세요"
    ids = [a["id"] for a in client.get("/api/agents", headers=auth(sup_token)).json()]
    assert ids[:2] == ["assistant", "orchestrator"]  # 내장 2종


def test_e4_12_task_visibility(client, sup_token, world):
    world["plan"] = {"steps": []}
    r = orchestrate(client, sup_token, "zzz")
    _, user_tok = make_user(client, sup_token, "other@example.test")
    assert client.get(f"/api/tasks/{r['task_id']}", headers=auth(user_tok)).status_code == 404
    assert client.get(f"/api/tasks/{r['task_id']}", headers=auth(sup_token)).status_code == 200
