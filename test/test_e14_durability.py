"""Epic 14 — 실행 내구성·운영 (D2-07 체크포인트·재시도·보상, D8-06 업그레이드·롤백·백업, NFR-O4).

에이전트는 템플릿 앱(ASGI), 계획 LLM 은 mock responder. 런타임은 FakeRuntime(백업·복원 호출 순서 기록).
오프라인 번들(D8-07)은 docker 가 필요해 test/impl/14th 라이브 시나리오에서 확인한다.
"""
import asyncio
import json
import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest
import yaml

from app import db as appdb
from app import ops
from app.agentspec import generator as gen
from app.agentspec.validate import validate_manifest
from app.db import utcnow
from app.llm.providers import ChatResult, MockProvider
from app.models import LlmRoute, Task
from app.orchestrator import executor
from app.orchestrator import service as orchestrator
from app.services import registry
from helpers import auth, load_template_app, make_user
from test_e6_registry import install, rt, serve, status_of, upload  # noqa: F401 — rt 는 픽스처


@pytest.fixture
def plan(monkeypatch):
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


def add_agent(tmp_path, monkeypatch, agent_id, type_="execution", mutate=None):
    app, manifest = load_template_app(tmp_path, type_, agent_id, monkeypatch, registry.agent_key(agent_id))
    if mutate:
        mutate(manifest)
    endpoint = f"http://{agent_id}.test"
    executor.register_app(endpoint, app)
    with appdb.SessionLocal() as s:
        registry.register(s, manifest, endpoint=endpoint, status="healthy")
    return endpoint


def counting(monkeypatch, fail=None):
    """executor.call 을 감싸 (agent.verb) 호출 횟수를 센다. fail(cap, n) 이 dict 를 주면 그 결과를 대신 돌려준다."""
    real = executor.call
    counts: dict[str, int] = {}

    async def call(cap, args, **kw):
        key = f"{cap['agent']}.{cap['verb']}"
        counts[key] = counts.get(key, 0) + 1
        injected = fail(cap, counts[key], args) if fail else None
        if isinstance(injected, BaseException):
            raise injected
        return injected if injected is not None else await real(cap, args, **kw)

    monkeypatch.setattr(executor, "call", call)
    return counts


def orchestrate(client, token, message, **kw):
    res = client.post("/api/orchestrate", json={"message": message, **kw}, headers=auth(token))
    assert res.status_code == 200, res.text
    return res.json()


TWO_STEPS = {"pattern": "sequential", "steps": [
    {"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "1+1"}},
    {"id": "s2", "agent": "calc", "capability": "calculate", "args": {"expression": "2*3"}}]}


def test_e14_01_checkpoint_resume_after_crash(client, sup_token, plan, tmp_path, monkeypatch):
    """D2-07: s1 완료 후 s2 도중 프로세스가 죽은 것처럼 → 복구 루프가 체크포인트에서 s2 만 이어서 실행."""
    add_agent(tmp_path, monkeypatch, "calc")
    plan["plan"] = TWO_STEPS
    crash = {"on": True}
    counts = counting(monkeypatch, lambda cap, n, args: RuntimeError("worker died")
                      if crash["on"] and args.get("expression") == "2*3" else None)
    with pytest.raises(RuntimeError, match="worker died"):
        client.post("/api/orchestrate", json={"message": "두 번 계산"}, headers=auth(sup_token))
    with appdb.SessionLocal() as s:
        task = s.query(Task).one()
        assert task.state == "running" and task.results == {}  # 결과는 체크포인트에만 있다
        task.heartbeat_at = utcnow() - timedelta(minutes=10)  # 진행 신호가 멈춤
        s.commit()
        tid = task.id
    crash["on"] = False
    assert asyncio.run(orchestrator.recover_stale()) == [tid]
    with appdb.SessionLocal() as s:
        task = s.get(Task, tid)
        assert task.state == "succeeded"
        assert task.results["s1"]["result"] == {"value": 2} and task.results["s2"]["result"] == {"value": 6}
    assert counts == {"calc.calculate": 3}  # s1 1회 + s2(죽음) 1회 + s2(재개) 1회 — s1 은 다시 안 함
    actions = [e["action"] for e in client.get("/api/audit", headers=auth(sup_token)).json()]
    assert "task.recovered" in actions
    assert asyncio.run(orchestrator.recover_stale()) == []  # 끝난 작업은 다시 잡지 않는다


def test_e14_02_fresh_running_task_not_stolen(client, sup_token):
    with appdb.SessionLocal() as s:
        s.add(Task(id="t-live", principal="u", message="m", plan={"steps": []}, results={}, state="running",
                   heartbeat_at=utcnow()))
        s.commit()
    assert asyncio.run(orchestrator.recover_stale()) == []


def test_e14_03_retry_transient_connect_and_idempotent_5xx(client, sup_token, plan, tmp_path, monkeypatch):
    """연결 실패는 항상 재시도, 5xx 는 idempotent capability 만."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "step_retry_backoff", 0.01)
    add_agent(tmp_path, monkeypatch, "calc")
    plan["plan"] = {"steps": [TWO_STEPS["steps"][0]]}
    counting(monkeypatch, lambda cap, n, args: {"ok": False, "error": "ConnectError", "transient": "connect"} if n == 1 else None)
    r = orchestrate(client, sup_token, "1+1")
    assert r["results"]["s1"]["ok"] is True and r["results"]["s1"]["attempts"] == 2
    assert any(e.get("name") == "retry" for e in r["events"])
    unavailable = {"ok": False, "status": 503, "error": "busy", "transient": "status"}
    counts = counting(monkeypatch, lambda cap, n, args: unavailable)
    r = orchestrate(client, sup_token, "1+1")
    assert r["results"]["s1"]["attempts"] == 1 and counts["calc.calculate"] == 1  # 멱등 아님 → 재시도 안 함
    add_agent(tmp_path, monkeypatch, "calc2",
              mutate=lambda m: m["spec"]["capabilities"][0].update(idempotent=True))
    plan["plan"] = {"steps": [{"id": "s1", "agent": "calc2", "capability": "calculate", "args": {"expression": "1+1"}}]}
    counts = counting(monkeypatch, lambda cap, n, args: unavailable)
    r = orchestrate(client, sup_token, "1+1")
    assert r["results"]["s1"]["attempts"] == 3 and counts["calc2.calculate"] == 3 and r["state"] == "failed"
    ev = client.get("/api/audit?action=tool.call", headers=auth(sup_token)).json()[0]
    assert ev["detail"]["attempts"] == 3


def test_e14_04_saga_compensation(client, sup_token, plan, tmp_path, monkeypatch):
    """D2-07: 뒤 단계 실패 → 앞 단계(게시글 생성)를 compensation(삭제)으로 되돌린다."""
    def comp(m):
        m["spec"]["capabilities"][0]["compensation"] = {"capability": "manage",
                                                         "args": {"action": "delete", "id": "{{result.id}}"}}
        assert validate_manifest(m) == []
    endpoint = add_agent(tmp_path, monkeypatch, "board", type_="app", mutate=comp)
    add_agent(tmp_path, monkeypatch, "calc")
    plan["plan"] = {"pattern": "sequential", "steps": [
        {"id": "s1", "agent": "board", "capability": "manage", "args": {"action": "create", "title": "임시 글"}},
        {"id": "s2", "agent": "calc", "capability": "calculate", "args": {"expression": "1/0"}}]}
    r = orchestrate(client, sup_token, "글 쓰고 계산")
    assert r["state"] == "failed" and r["results"]["s2"]["ok"] is False
    c = r["results"]["s1"]["compensated"]
    assert c["ok"] is True and c["capability"] == "manage" and c["args"] == {"action": "delete", "id": r["results"]["s1"]["result"]["id"]}
    assert any(e.get("name") == "compensation" for e in r["events"])
    left = asyncio.run(executor.call({"agent": "board", "verb": "manage", "endpoint": endpoint, "source": "zip"},
                                     {"action": "list"}, principal="t", task_id="t"))
    assert left["result"] == []  # 되돌려졌다
    assert client.get("/api/audit?action=tool.compensated", headers=auth(sup_token)).json()


def test_e14_05_compensation_must_be_declared():
    m = gen.build_manifest("comp-x", "X", "app")
    m["spec"]["capabilities"][0]["compensation"] = {"capability": "undo"}
    assert any("compensation" in e for e in validate_manifest(m))


def _version(agent_id, version, extra_cap=False):
    files = gen.scaffold(agent_id, agent_id.title(), "app")
    m = gen.manifest_of(files)
    m["metadata"]["version"] = version
    if extra_cap:  # 선언만 있고 서빙하지 않는 capability → 계약 시험 실패 → 롤백
        m["spec"]["capabilities"].append({"verb": "extra", "domain": "app.extra", "description": "x"})
    files["agent.yaml"] = yaml.safe_dump(m, sort_keys=False, allow_unicode=True).encode()
    return gen.pack(files)


def test_e14_06_upgrade_backs_up_and_restores_on_rollback(client, sup_token, rt, tmp_path, monkeypatch):
    """NFR-O4: 업그레이드 = 이미지 태그 고정 + 사전 백업, 실패 시 백업 복원 후 이전 태그로 기동."""
    serve(tmp_path, monkeypatch, "upg")
    assert install(client, sup_token, _version("upg", "1.0.0"))["status"] == "succeeded"
    rt.calls.clear()
    st = install(client, sup_token, _version("upg", "1.1.0"))
    assert st["status"] == "succeeded" and rt.calls == [("build", "upg"), ("backup", "upg"), ("up", "upg")]
    assert st["steps"][4]["detail"]["image_tag"] == "upg:1.1.0" and st["steps"][4]["detail"]["pre_upgrade_backup"]
    rt.calls.clear()
    st = install(client, sup_token, _version("upg", "1.2.0", extra_cap=True))
    assert st["status"] == "rolled_back"
    assert rt.calls == [("build", "upg"), ("backup", "upg"), ("up", "upg"), ("down", "upg"), ("restore", "upg"),
                        ("up", "upg")]
    a = client.get("/api/agents/upg", headers=auth(sup_token)).json()
    assert a["version"] == "1.1.0" and [v["version"] for v in a["versions"]] == ["1.1.0", "1.0.0"]  # 실패 버전 흔적 없음


def test_e14_07_backup_failure_aborts_upgrade(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "upg2")
    assert install(client, sup_token, _version("upg2", "1.0.0"))["status"] == "succeeded"
    rt.fail.add(("backup", "upg2"))
    st = install(client, sup_token, _version("upg2", "1.1.0"))
    assert st["status"] == "failed" and st["step"] == 5 and "백업 실패" in st["error"]
    assert client.get("/api/agents/upg2", headers=auth(sup_token)).json()["version"] == "1.0.0"


def test_e14_08_backup_api(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "bk")
    assert install(client, sup_token, gen.pack(gen.scaffold("bk", "Bk", "app")))["status"] == "succeeded"
    b = client.post("/api/agents/bk/backup", headers=auth(sup_token))
    assert b.status_code == 200 and b.json()["backup"]
    listed = client.get("/api/agents/bk/backups", headers=auth(sup_token)).json()["backups"]
    assert listed[0]["backup"] == b.json()["backup"]
    assert client.post("/api/agents/bk/restore", json={"backup": b.json()["backup"]}, headers=auth(sup_token)).status_code == 200
    assert client.post("/api/agents/bk/restore", json={"backup": "20990101T000000Z"}, headers=auth(sup_token)).status_code == 404
    assert client.post("/api/agents/bk/restore", json={"backup": "../x"}, headers=auth(sup_token)).status_code == 422
    assert client.post("/api/agents/assistant/backup", headers=auth(sup_token)).status_code == 409
    _, user = make_user(client, sup_token, "u14@example.test")
    assert client.post("/api/agents/bk/backup", headers=auth(user)).status_code == 403
    actions = {e["action"] for e in client.get("/api/audit", headers=auth(sup_token)).json()}
    assert {"agent.backup", "agent.restored"} <= actions


def test_e14_09_platform_backup_sqlite(client, sup_token, rt):
    """D8-06: 플랫폼 DB(local=SQLite) 온라인 백업 + 설치 에이전트 볼륨(전체 백업 API)."""
    out = client.post("/api/admin/backup", headers=auth(sup_token))
    assert out.status_code == 200, out.text
    path = Path(out.json()["platform"]["file"])
    with sqlite3.connect(path) as c:
        tables = {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    assert {"users", "audit_events", "tasks", "secrets"} <= tables
    _, admin = make_user(client, sup_token, "a14@example.test", role="admin")
    assert client.post("/api/admin/backup", headers=auth(admin)).status_code == 403  # supervisor 전용
    assert ops.main(["nope"]) == 2
