"""Epic 24 — 품질 기준 상향: MCP 계약 시험 두 핸드셰이크(NFR-P1, PRD Q8) · 접근성(NFR-U4, PRD Q9 — 콘솔 E2E axe, web/e2e/a11y.e2e.mjs).

설치 7단계·plaza test 가 2026-07-28(server/discover) 와 2025-11-25(initialize) 를 각각 명시적으로 시험한다.
"""
import asyncio
import json
import subprocess
import sys

from fastapi.responses import JSONResponse

from app.agentspec import generator as gen
from app.orchestrator import executor
from app.registry import pipeline
from app.services import registry
from helpers import load_template_app


def no_initialize(app):
    """2025-11-25 initialize 를 거부하는 에이전트(2026-07-28 만 지원)."""
    async def wrapped(scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "POST" and scope["path"].endswith("/mcp"):
            msgs, body, more = [], b"", True
            while more:
                m = await receive()
                msgs.append(m)
                body += m.get("body", b"")
                more = m.get("more_body", False)
            if json.loads(body or b"{}").get("method") == "initialize":
                await JSONResponse({"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}})(
                    scope, receive, send)
                return
            it = iter(msgs)

            async def replay():
                return next(it, {"type": "http.request", "body": b"", "more_body": False})
            return await app(scope, replay, send)
        return await app(scope, receive, send)
    return wrapped


def test_e24_01_install_contract_both_handshakes(tmp_path, monkeypatch):
    app, manifest = load_template_app(tmp_path, "service", "dual", monkeypatch, registry.agent_key("dual"))
    executor.register_app("http://dual.test", app)
    try:
        assert asyncio.run(pipeline.protocol_contract("http://dual.test", manifest)) == []
    finally:
        executor.clear_apps()


def test_e24_02_install_contract_rejects_missing_initialize(tmp_path, monkeypatch):
    app, manifest = load_template_app(tmp_path, "service", "newonly", monkeypatch, registry.agent_key("newonly"))
    executor.register_app("http://newonly.test", no_initialize(app))
    try:
        errs = asyncio.run(pipeline.protocol_contract("http://newonly.test", manifest))
    finally:
        executor.clear_apps()
    assert len(errs) == 1 and errs[0].startswith("MCP 2025-11-25(initialize) 계약 시험 실패")


def test_e24_03_plaza_test_reports_initialize(tmp_path):
    src = tmp_path / "svc"
    for rel, data in gen.scaffold("svc-24", "Svc", "service").items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    r = subprocess.run([sys.executable, "-m", "plaza", "test", str(src), "--report", str(tmp_path / "rep")],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    rep = json.loads((tmp_path / "rep" / "result.json").read_text())
    checks = {c["check"]: c for c in rep["checks"]}
    assert checks["contract:mcp"]["ok"] and checks["contract:mcp-initialize"]["ok"]
    assert "2025-11-25 version=2025-11-25" in checks["contract:mcp-initialize"]["detail"]
