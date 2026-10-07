"""Epic 17 — 관측·평가 (D10-04 LLM 관측 UI 자체 경량, D10-05 평가·시험 표준, D4-05 plaza test, NFR-O1)."""
import json
import subprocess
import sys
from datetime import timedelta

import pytest

from app import db as appdb
from app.agentspec import generator as gen
from app.db import utcnow
from app.llm.providers import ChatResult, MockProvider
from app.models import LlmModel, LlmRoute, TraceSpan
from app.observability import flush
from app.orchestrator import executor
from app.services import registry
from helpers import auth, load_template_app, make_user


@pytest.fixture
def world(client, tmp_path, monkeypatch):
    holder = {"plan": {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "6*7"}}]},
              "judge": {"score": 0.9, "reason": "good"}}
    default = MockProvider.responder

    def responder(model, req):
        head = req.messages[0]["content"] if req.messages else ""
        if head.startswith("You are the AgentPlaza orchestrator"):
            return ChatResult(content=json.dumps(holder["plan"]), model=model)
        if head.startswith("You grade an AI assistant"):
            return ChatResult(content=json.dumps(holder["judge"]), model=model)
        return default(model, req)

    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    app, manifest = load_template_app(tmp_path, "execution", "calc", monkeypatch, registry.agent_key("calc"))
    executor.register_app("http://calc.test", app)
    with appdb.SessionLocal() as s:
        for alias in ("plaza/orchestrator", "plaza/chat"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.merge(LlmModel(id="mock/priced", provider="mock", model_id="echo", local=True, context=8192, tool_call=False,
                         vision=False, license="test", cost_in=0.5, cost_out=1.0))
        s.merge(LlmRoute(alias="t/priced", targets=["mock/priced"]))
        registry.register(s, manifest, endpoint="http://calc.test", status="healthy")
    yield holder
    executor.clear_apps()


def test_e17_01_traces_stored_and_browsable(client, sup_token, world):
    """D10-04·NFR-O1: 플랫폼 스팬이 저장되고 트레이스 트리로 조회된다(GenAI 속성, 프롬프트 원문 없음)."""
    r = client.post("/api/orchestrate", json={"message": "6 곱하기 7 비밀문구XYZ"}, headers=auth(sup_token)).json()
    flush()
    traces = client.get("/api/obs/traces", headers=auth(sup_token)).json()
    root = next(t for t in traces if t["name"] == "invoke_agent orchestrator")
    assert root["tools"] == ["calc.calculate"] and "mock/echo" in root["models"] and root["errors"] == 0
    detail = client.get(f"/api/obs/traces/{root['trace_id']}", headers=auth(sup_token)).json()["spans"]
    names = [s["name"] for s in detail]
    assert any(n.startswith("execute_tool calc.calculate") for n in names) and any(n.startswith("chat ") for n in names)
    tool = next(s for s in detail if s["name"].startswith("execute_tool"))
    assert tool["parent_id"] == root["span_id"] and tool["attributes"]["gen_ai.tool.name"] == "calculate"
    assert tool["attributes"]["plaza.task_id"] == r["task_id"]
    assert "비밀문구XYZ" not in json.dumps(detail, ensure_ascii=False)  # 프롬프트 원문은 수집하지 않는다
    assert client.get("/api/obs/traces/ffff", headers=auth(sup_token)).status_code == 404


def test_e17_02_usage_and_cost(client, sup_token, world):
    for _ in range(3):
        client.post("/v1/chat/completions", json={"model": "t/priced", "messages": [{"role": "user", "content": "hello there"}]},
                    headers=auth(sup_token) | {"X-Plaza-Data-Class": "L3"})
    u = client.get("/api/obs/usage?days=1", headers=auth(sup_token)).json()
    m = next(x for x in u["by_model"] if x["key"] == "mock/priced")
    assert m["calls"] == 3 and m["cost"] > 0 and m["p95_ms"] >= m["p50_ms"] and u["total"]["calls"] >= 3
    assert next(x for x in u["by_class"] if x["key"] == "L3")["calls"] >= 3


CASES = [
    {"id": "calc", "input": "6 곱하기 7", "expect": {"tool": "calc.calculate", "state": "succeeded", "contains": ["42"]}},
    {"id": "judge", "input": "6 곱하기 7 설명", "expect": {"judge": {"rubric": "정확한 값 42 를 말한다", "threshold": 0.7}}},
    {"id": "regex", "input": "6 곱하기 7", "expect": {"regex": r"\[s1\]"}},
]


def test_e17_03_eval_suite_run_and_regression(client, sup_token, world):
    """D10-05: 시나리오 실행·채점·점수, 다음 실행에서 회귀(통과→실패) 표시."""
    sid = client.post("/api/evals/suites", json={"name": "계산 회귀", "cases": CASES}, headers=auth(sup_token)).json()["id"]
    rid = client.post(f"/api/evals/suites/{sid}/runs", headers=auth(sup_token)).json()["run_id"]
    run = client.get(f"/api/evals/runs/{rid}", headers=auth(sup_token)).json()
    assert run["status"] == "done" and run["total"] == 3 and run["passed"] == 3 and run["score"] > 0.9
    assert next(x for x in run["results"] if x["id"] == "judge")["checks"][0]["score"] == 0.9
    world["plan"] = {"steps": []}  # 계획이 도구를 못 고르게 됨 → 회귀
    world["judge"] = {"score": 0.2, "reason": "wrong"}
    rid2 = client.post(f"/api/evals/suites/{sid}/runs", headers=auth(sup_token)).json()["run_id"]
    run2 = client.get(f"/api/evals/runs/{rid2}", headers=auth(sup_token)).json()
    assert run2["passed"] < 3 and run2["regressions"] >= 2
    calc = next(x for x in run2["results"] if x["id"] == "calc")
    assert calc["regression"] is True and not calc["passed"]
    listed = client.get(f"/api/evals/suites/{sid}/runs", headers=auth(sup_token)).json()
    assert [x["id"] for x in listed] == [rid2, rid]
    assert client.get("/api/evals/suites", headers=auth(sup_token)).json()[0]["last_run"]["id"] == rid2


def test_e17_04_suite_validation_and_rbac(client, sup_token, world):
    bad = [{"input": "x", "expect": {}}, {"input": "", "expect": {"contains": ["a"]}}, {"input": "x", "expect": {"regex": "("}}]
    for case in bad:
        assert client.post("/api/evals/suites", json={"name": "b", "cases": [case]}, headers=auth(sup_token)).status_code == 422
    _, user = make_user(client, sup_token, "u17@example.test")
    for path in ("/api/obs/usage", "/api/obs/traces", "/api/evals/suites"):
        assert client.get(path, headers=auth(user)).status_code == 403


def test_e17_05_playground_compare(client, sup_token, world):
    res = client.post("/api/evals/compare", json={"prompt": "안녕", "targets": ["plaza/chat", "t/priced", "nope/alias"]},
                      headers=auth(sup_token) | {"X-Plaza-Data-Class": "L1"}).json()["results"]
    assert res[0]["answer"] == "echo: 안녕" and res[1]["cost"] > 0 and "latency_ms" in res[0]
    assert "NoRoute" in res[2]["error"]


def test_e17_06_plaza_test_cli(tmp_path):
    """D4-05: 구조·문법·SQL·런타임 계약·시나리오 — 정상 PASS, 망가뜨리면 해당 항목 FAIL. 보고서 파일."""
    src = tmp_path / "svc"
    for rel, data in gen.scaffold("svc-x", "Svc", "service").items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    cmd = [sys.executable, "-m", "plaza", "test", str(src), "--report", str(tmp_path / "rep")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    md = (tmp_path / "rep" / "result.md").read_text()
    assert "최종 Verdict: **PASS**" in md and "eval:wordcount" in md
    (src / "database" / "migrations" / "001.sql").write_text("DELETE FROM items;")
    (src / "evals" / "smoke.yaml").write_text("- id: wrong\n  capability: process\n  args: {text: a, op: upper}\n  expect: {equals: {text: b}}\n")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert r.returncode == 1 and "FAIL sql:ddl-only" in r.stdout and "FAIL eval:wrong" in r.stdout
    rep = json.loads((tmp_path / "rep" / "result.json").read_text())
    assert rep["ok"] is False and any(c["check"] == "contract:mcp" and c["ok"] for c in rep["checks"])


def test_e17_07_span_retention(client, sup_token, world):
    with appdb.SessionLocal() as s:
        s.add(TraceSpan(trace_id="a" * 32, span_id="b" * 16, name="old", kind="internal", start=utcnow() - timedelta(days=30),
                        duration_ms=1, status="ok", attributes={}))
        s.commit()
    client.post("/api/admin/retention/run", headers=auth(sup_token))
    with appdb.SessionLocal() as s:
        assert s.query(TraceSpan).filter(TraceSpan.name == "old").count() == 0
