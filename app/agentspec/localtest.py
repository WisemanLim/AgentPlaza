"""plaza test (D4-05 로컬 개발·계약 시험): 구조·문법·SQL·런타임 계약(REST·MCP·A2A 카드)·시나리오(evals/*.yaml).

런타임 검사는 별 프로세스에서 에이전트 앱을 띄워(ASGI TestClient) 플랫폼에 올리기 전에 같은 계약 시험을 돈다.
결과는 JSON 과(선택) 마크다운 보고서(wds-test result.md 형식)로 남긴다.
"""
import ast
import json
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.agentspec.validate import validate_text
from app.registry.gate import check_sql

PROBE = r'''
import json, os, sys, glob, yaml
sys.path.insert(0, "backend")
os.environ.update({"AGENT_MANIFEST": "agent.yaml", "AGENT_API_KEY": "plaza-test-key", "AGENT_DATA_DIR": sys.argv[1],
                   "AGENT_MIGRATIONS": "database/migrations"})
import importlib.util as u
from fastapi.testclient import TestClient
spec = u.spec_from_file_location("agent_main", "backend/main.py"); mod = u.module_from_spec(spec); spec.loader.exec_module(mod)
m = yaml.safe_load(open("agent.yaml", encoding="utf-8"))
declared = sorted(c["verb"] for c in m["spec"]["capabilities"])
H = {"x-api-key": "plaza-test-key"}
out = {"checks": [], "evals": []}
def chk(name, ok, detail=""):
    out["checks"].append({"check": name, "ok": bool(ok), "detail": str(detail)[:300]})
with TestClient(mod.app) as c:
    r = c.get("/health"); chk("runtime:/health", r.status_code == 200 and r.json().get("agent") == m["metadata"]["id"], r.text)
    chk("runtime:auth", c.get("/api/capabilities").status_code == 401, "x-api-key 없이 401")
    served = sorted(x["verb"] for x in c.get("/api/capabilities", headers=H).json())
    chk("contract:rest", served == declared, f"declared={declared} served={served}")
    meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": meta}},
               headers={**H, "accept": "application/json, text/event-stream", "mcp-protocol-version": "2026-07-28",
                        "mcp-method": "tools/list"})
    tools = sorted(t["name"] for t in r.json().get("result", {}).get("tools", [])) if r.status_code == 200 else []
    chk("contract:mcp", tools == declared, f"2026-07-28 tools={tools}")
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {
        "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "plaza-test", "version": "1"}}},
        headers={**H, "accept": "application/json, text/event-stream", "mcp-method": "initialize"})
    ver = r.json().get("result", {}).get("protocolVersion") if r.status_code == 200 else None
    h2 = {**H, "accept": "application/json, text/event-stream", "mcp-protocol-version": "2025-11-25",
          **({"mcp-session-id": r.headers["mcp-session-id"]} if r.headers.get("mcp-session-id") else {})}
    c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
           headers={**h2, "mcp-method": "notifications/initialized"})
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
               headers={**h2, "mcp-method": "tools/list"})
    tools2 = sorted(t["name"] for t in r.json().get("result", {}).get("tools", [])) if r.status_code == 200 else []
    chk("contract:mcp-initialize", ver == "2025-11-25" and tools2 == declared, f"2025-11-25 version={ver} tools={tools2}")
    r = c.get("/.well-known/agent-card.json")
    skills = sorted(s["id"] for s in r.json().get("skills", [])) if r.status_code == 200 else []
    chk("contract:a2a-card", skills == declared, f"skills={skills}")
    for f in sorted(glob.glob("evals/*.yaml")):
        for case in yaml.safe_load(open(f, encoding="utf-8")) or []:
            res = c.post(f"/api/invoke/{case['capability']}", json=case.get("args", {}), headers=H)
            got = res.json().get("result") if res.status_code == 200 else {"status": res.status_code, "detail": res.text[:200]}
            exp, fails = case.get("expect", {}), []
            dump = json.dumps(got, ensure_ascii=False)
            if "equals" in exp and got != exp["equals"]: fails.append(f"equals {exp['equals']}")
            for s in exp.get("contains", []):
                if str(s) not in dump: fails.append(f"contains {s}")
            for k in exp.get("keys", []):
                if not isinstance(got, dict) or k not in got: fails.append(f"key {k}")
            if exp.get("type") == "list" and not isinstance(got, list): fails.append("type list")
            if exp.get("type") == "dict" and not isinstance(got, dict): fails.append("type dict")
            out["evals"].append({"id": case.get("id"), "file": f, "capability": case["capability"], "ok": res.status_code == 200 and not fails,
                                 "fails": fails, "result": dump[:300]})
print("PLAZA_TEST_JSON=" + json.dumps(out, ensure_ascii=False))
'''


def run(src: Path, timeout: int = 120) -> dict:
    src = src.resolve()
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail[:300]})

    text = (src / "agent.yaml").read_text(encoding="utf-8") if (src / "agent.yaml").is_file() else ""
    m, errs = validate_text(text) if text else (None, ["agent.yaml 없음"])
    chk("structure:agent.yaml", not errs, "; ".join(errs))
    report = {"agent": (m or {}).get("metadata", {}).get("id"), "version": (m or {}).get("metadata", {}).get("version"),
              "at": datetime.now(UTC).isoformat(timespec="seconds"), "checks": checks, "evals": []}
    if m is None or errs:
        return {**report, "ok": False}
    missing = [p for p in ("compose.yaml", "backend/main.py", "backend/Dockerfile") if not (src / p).is_file()]
    chk("structure:files", not missing, f"missing={missing}")
    bad = []
    for f in src.rglob("*.py"):
        try:
            ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError as exc:
            bad.append(f"{f.relative_to(src)}:{exc.lineno}")
    chk("syntax:python", not bad, ", ".join(bad))
    if m["spec"].get("ui", {}).get("hasFrontend"):
        comps = [f for f in (src / "frontend").rglob("*") if f.suffix in (".tsx", ".jsx", ".ts", ".js") and "node_modules" not in f.parts]
        no_export = [str(f.relative_to(src)) for f in comps if re.search(r"\.(tsx|jsx)$", f.name)
                     and "export default" not in f.read_text(encoding="utf-8", errors="ignore")]
        chk("syntax:react-export", not no_export, f"export default 없음: {no_export}")
    sql_errs = [e for f in sorted(src.glob("database/migrations/*.sql")) for e in check_sql(f.name, f.read_text(encoding="utf-8"))]
    chk("sql:ddl-only", not sql_errs, "; ".join(sql_errs))
    with tempfile.TemporaryDirectory() as data:
        r = subprocess.run([sys.executable, "-c", PROBE, data], cwd=src, capture_output=True, text=True, timeout=timeout)
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("PLAZA_TEST_JSON=")), None)
    if line is None:
        chk("runtime:start", False, (r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else "no output")
    else:
        probe = json.loads(line.split("=", 1)[1])
        checks += probe["checks"]
        report["evals"] = probe["evals"]
    report["ok"] = all(c["ok"] for c in checks) and all(e["ok"] for e in report["evals"])
    return report


def markdown(rep: dict) -> str:
    total = len(rep["checks"]) + len(rep["evals"])
    passed = sum(c["ok"] for c in rep["checks"]) + sum(e["ok"] for e in rep["evals"])
    lines = [f"# 시험 결과 / Test Result — plaza test {rep['agent']} {rep['version']}", "",
             f"- 일자 Date: {rep['at']}", "", "## 요약 / Summary", "",
             f"- 전체 Total: {total}, 통과 Pass: {passed}, 실패 Fail: {total - passed}, 최종 Verdict: **{'PASS' if rep['ok'] else 'FAIL'}**",
             "", "## 케이스 / Cases", "", "| id | 결과 result | 비고 note |", "|----|-------------|-----------|"]
    lines += [f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} | {c['detail'] if not c['ok'] else ''} |" for c in rep["checks"]]
    lines += [f"| eval:{e['id']} ({e['capability']}) | {'PASS' if e['ok'] else 'FAIL'} | {', '.join(e['fails'])} |" for e in rep["evals"]]
    return "\n".join(lines) + "\n"
