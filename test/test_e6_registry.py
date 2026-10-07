"""Epic 6 — 패키지·레지스트리 8단계 (D5-01/02/05/06/07, D4-07 내보내기, NFR-S1·S2·I2·I6).

런타임은 FakeRuntime(호출 기록·실패 주입), 에이전트 백엔드는 템플릿 앱을 ASGI 로 연결해 헬스·계약 시험까지 돈다.
실제 Docker 빌드·기동은 Epic 7(runtime 서비스) 시나리오에서 확인한다.
"""
import io
import json
import stat
import zipfile
from pathlib import Path

import pytest
import yaml

from app import db as appdb
from app.agentspec import generator as gen
from app.core.config import settings
from app.models import Agent, AgentVersion, ApiKey, Capability
from app.orchestrator import executor
from app.registry import pipeline
from app.runtime.driver import FakeRuntime, set_runtime
from app.services import registry
from helpers import auth, load_template_app, make_user


@pytest.fixture
def rt(tmp_path, monkeypatch):
    fake = FakeRuntime()
    set_runtime(fake)
    monkeypatch.setattr(settings, "data_dir", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "health_timeout_seconds", 2.0)
    yield fake
    set_runtime(None)
    executor.clear_apps()


def agent_zip(agent_id, type_="app", version="0.1.0", mutate=None, extra=None) -> bytes:
    files = gen.scaffold(agent_id, agent_id.title(), type_)
    if version != "0.1.0":
        m = gen.manifest_of(files)
        m["metadata"]["version"] = version
        files["agent.yaml"] = yaml.safe_dump(m, sort_keys=False, allow_unicode=True).encode()
    if mutate:
        files = mutate(files)
    files.update(extra or {})
    return gen.pack(files)


def serve(tmp_path, monkeypatch, agent_id, type_="app"):
    """설치될 에이전트의 백엔드를 endpoint 에 연결한다(실 컨테이너 대신)."""
    app, _ = load_template_app(tmp_path / "srv", type_, agent_id, monkeypatch, registry.agent_key(agent_id))
    executor.register_app(pipeline.endpoint_for(agent_id), app)


def upload(client, token, *blobs, env=None, force=False):
    files = [("files", (f"a{i}.zip", b, "application/zip")) for i, b in enumerate(blobs)]
    res = client.post("/api/agents/upload", files=files, data={"env": json.dumps(env or {}), "force": str(force).lower()},
                      headers=auth(token))
    assert res.status_code == 202, res.text
    return res.json()


def status_of(client, token, install_id):
    return client.get(f"/api/agents/installs/{install_id}", headers=auth(token)).json()


def install(client, token, blob, **kw):
    out = upload(client, token, blob, **kw)[0]
    return status_of(client, token, out["install_id"])


def test_e6_01_happy_path_8_steps(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "board")
    st = install(client, sup_token, agent_zip("board"))
    assert st["status"] == "succeeded", st
    # 3단계: 서명 없음 = 경고(미검증 배지, NFR-S2) · 4단계: MIT = G1
    assert [s["status"] for s in st["steps"]] == ["ok", "ok", "warn", "ok", "ok", "ok", "ok", "ok"]
    assert st["steps"][2]["detail"]["signature"] == "unverified" and any("미검증" in w for w in st["warnings"])
    assert st["steps"][3]["detail"]["grade"] == "G1"
    assert rt.calls == [("build", "board"), ("up", "board")]
    a = client.get("/api/agents/board", headers=auth(sup_token)).json()
    assert a["status"] == "healthy" and a["capabilities"][0]["verb"] == "manage"
    assert a["versions"][0]["current"] is True and a["versions"][0]["signature"] == "unverified"
    workdir = Path(settings.data_dir) / "installed" / "board" / "0.1.0"
    compose = yaml.safe_load((workdir / "compose.plaza.yaml").read_text())
    assert "ports" not in compose["services"]["board-be"] and compose["services"]["board-be"]["profiles"] == ["federated"]
    env = (workdir / ".env").read_text()
    assert f"AGENT_API_KEY={registry.agent_key('board')}" in env and "LLM_API_KEY=ap_sk_" in env
    assert stat.S_IMODE((workdir / ".env").stat().st_mode) == 0o600
    assert (Path(settings.data_dir) / "artifacts" / "board" / "0.1.0.zip").is_file()
    ui = client.get("/api/agents/board/ui", headers=auth(sup_token)).json()
    assert ui["nav_visible"] is True and ui["src"].endswith("/a/board/ui/")
    assert ui["src"].startswith(ui["origin"]) and ui["origin"] == settings.public_apps_url  # 콘솔과 다른 오리진
    assert client.get("/api/audit?action=agent.installed", headers=auth(sup_token)).json()


def test_e6_02_multi_upload(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "one", "service")
    serve(tmp_path, monkeypatch, "two", "reviewer")
    out = upload(client, sup_token, agent_zip("one", "service"), agent_zip("two", "reviewer"))
    assert len(out) == 2 and all(status_of(client, sup_token, o["install_id"])["status"] == "succeeded" for o in out)


def _zip(entries: list[tuple]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data, *mode in entries:
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED  # ZipInfo 기본은 STORED(무압축)
            if mode:
                info.external_attr = mode[0] << 16
            z.writestr(info, data)
    return buf.getvalue()


@pytest.mark.parametrize("blob,needle", [
    (_zip([("../evil.py", b"x")]), "zip-slip"),
    (_zip([("/etc/cron.d/x", b"x")]), "zip-slip"),
    (_zip([("link", b"/etc/passwd", stat.S_IFLNK | 0o777)]), "심볼릭 링크"),
    (_zip([("inner.zip", b"PK..")]), "중첩 아카이브"),
    (_zip([("bomb.txt", b"0" * 5_000_000)]), "압축 폭탄"),
    (b"not a zip file", "zip 형식"),
    (_zip([("README.md", b"hi")]), "agent.yaml 없음"),
    (_zip([("Board-meta.json", b"{}")]), "v1 flat zip"),
], ids=["zip-slip", "absolute", "symlink", "nested", "bomb", "not-zip", "no-manifest", "v1-flat"])
def test_e6_03_malicious_corpus_rejected(client, sup_token, rt, blob, needle):
    """NFR-S1: zip-slip·심볼릭 링크·압축 폭탄·중첩 아카이브 거부."""
    st = install(client, sup_token, blob)
    assert st["status"] == "failed" and st["step"] == 2 and needle in st["error"], st["error"]
    assert rt.calls == []


def test_e6_04_upload_size_limit(client, sup_token, rt, monkeypatch):
    monkeypatch.setattr(settings, "upload_max_mb", 0)
    out = upload(client, sup_token, agent_zip("big"))
    assert "크기 초과" in out[0]["error"]


@pytest.mark.parametrize("sql,ok", [
    ("CREATE TABLE t (id INTEGER);\nCREATE INDEX IF NOT EXISTS ix ON t (id);", True),
    ("INSERT INTO t VALUES (1);", False),
    ("ATTACH DATABASE '/etc/passwd' AS x;", False),
    ("PRAGMA writable_schema=1;", False),
], ids=["ddl", "insert", "attach", "pragma"])
def test_e6_05_sql_ddl_only(client, sup_token, rt, tmp_path, monkeypatch, sql, ok):
    serve(tmp_path, monkeypatch, "sqlx")
    st = install(client, sup_token, agent_zip("sqlx", extra={"database/migrations/002_x.sql": sql.encode()}))
    assert (st["status"] == "succeeded") is ok, st["error"]
    if not ok:
        assert "DDL 만 허용" in st["error"]


def test_e6_06_fts5_template_passes_and_forbidden_items(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "kb", "rag")
    assert install(client, sup_token, agent_zip("kb", "rag"))["status"] == "succeeded"
    bad = install(client, sup_token, agent_zip("sock", extra={"backend/extra.py": b'P = "/var/run/docker.sock"\n'}))
    assert bad["status"] == "failed" and "docker.sock" in bad["error"]
    serve(tmp_path, monkeypatch, "warn")
    w = install(client, sup_token, agent_zip("warn", extra={"backend/tool.py": b"import subprocess\n"}))
    assert w["status"] == "succeeded" and any("subprocess" in x for x in w["warnings"])
    syntax = install(client, sup_token, agent_zip("syn", extra={"backend/broken.py": b"def x(:\n"}))
    assert "Python 문법 오류" in syntax["error"]


def _set_spec(**spec):
    def mutate(files):
        m = gen.manifest_of(files)
        m["spec"].update(spec)
        files["agent.yaml"] = yaml.safe_dump(m, sort_keys=False).encode()
        return files
    return mutate


def test_e6_07_policy_gates(client, sup_token, rt, tmp_path, monkeypatch):
    """NFR-I2: in-process 거부(컨테이너 기본) · docker:true 거부 · 내장 id 예약 · federation 은 경로 C."""
    assert "in-process" in install(client, sup_token, agent_zip("inp", mutate=_set_spec(runtime={"mode": "inprocess"})))["error"]
    assert "NFR-I3" in install(client, sup_token, agent_zip("dock", mutate=_set_spec(permissions={"docker": True})))["error"]
    assert "예약된 내장 id" in install(client, sup_token, agent_zip("assistant"))["error"]
    fed = gen.pack(gen.scaffold("remote1", "Remote", "federation", federation_url="https://x.example/card.json"))
    assert "경로 C" in install(client, sup_token, fed)["error"]


def test_e6_08_required_env(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "px", "tool-proxy")
    assert "required_env 누락" in install(client, sup_token, agent_zip("px", "tool-proxy"))["error"]
    st = install(client, sup_token, agent_zip("px", "tool-proxy"), env={"TOOL_BASE_URL": "https://api.example", "EVIL": "1"})
    assert st["status"] == "succeeded"
    env = (Path(settings.data_dir) / "installed" / "px" / "0.1.0" / ".env").read_text()
    assert "TOOL_BASE_URL=https://api.example" in env and "EVIL" not in env  # 선언된 키만 주입


def test_e6_09_versions_upgrade_force(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "vv")
    assert install(client, sup_token, agent_zip("vv"))["status"] == "succeeded"
    assert "버전은 현재" in install(client, sup_token, agent_zip("vv"))["error"]
    assert install(client, sup_token, agent_zip("vv"), force=True)["status"] == "succeeded"
    assert install(client, sup_token, agent_zip("vv", version="0.2.0"))["status"] == "succeeded"
    versions = client.get("/api/agents/vv", headers=auth(sup_token)).json()["versions"]
    assert {v["version"]: v["current"] for v in versions} == {"0.1.0": False, "0.2.0": True}


def test_e6_10_upgrade_failure_rolls_back(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "up")
    install(client, sup_token, agent_zip("up"))
    rt.fail.add(("up", "up"))
    st = install(client, sup_token, agent_zip("up", version="0.2.0"))
    assert st["status"] == "rolled_back" and st["step"] == 7
    a = client.get("/api/agents/up", headers=auth(sup_token)).json()
    assert a["version"] == "0.1.0" and [v["version"] for v in a["versions"] if v["current"]] == ["0.1.0"]
    assert not (Path(settings.data_dir) / "installed" / "up" / "0.2.0").exists()


def test_e6_11_new_install_failures_leave_no_trace(client, sup_token, rt, tmp_path, monkeypatch):
    rt.fail.add(("build", "bf"))
    st = install(client, sup_token, agent_zip("bf"))
    assert st["status"] == "failed" and st["step"] == 5
    # 헬스 실패: endpoint 에 백엔드를 연결하지 않음 → 시간 초과 → 롤백, 카탈로그 없음
    st = install(client, sup_token, agent_zip("nohealth"))
    assert st["status"] == "rolled_back" and "health" in st["error"]
    with appdb.SessionLocal() as s:
        assert s.get(Agent, "bf") is None and s.get(Agent, "nohealth") is None
        assert not s.query(Capability).filter(Capability.agent_id == "nohealth").count()
    assert not (Path(settings.data_dir) / "installed" / "nohealth").exists()  # 빈 상위 디렉터리도 남기지 않음
    assert not (Path(settings.data_dir) / "installed" / "bf").exists()


def test_e6_12_contract_mismatch_rolls_back(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "liar", "service")  # 실제로는 process 를 노출
    st = install(client, sup_token, agent_zip("liar", "app"))  # 선언은 manage
    assert st["status"] == "rolled_back" and "capability 불일치" in st["error"]


def test_e6_13_delete_removes_all_traces_within_60s(client, sup_token, rt, tmp_path, monkeypatch):
    """NFR-I6: 컨테이너·볼륨·라우트·카탈로그·노출·파일 60초 내 제거."""
    serve(tmp_path, monkeypatch, "gone")
    install(client, sup_token, agent_zip("gone"))
    res = client.delete("/api/agents/gone", headers=auth(sup_token)).json()
    assert res["seconds"] < 60 and ("down", "gone") in rt.calls
    with appdb.SessionLocal() as s:
        assert s.get(Agent, "gone") is None
        assert not s.query(Capability).filter(Capability.agent_id == "gone").count()
        assert not s.query(AgentVersion).filter(AgentVersion.agent_id == "gone").count()
        assert all(k.revoked_at for k in s.query(ApiKey).filter(ApiKey.name == "agent:gone"))
    assert not (Path(settings.data_dir) / "installed" / "gone").exists()
    assert not (Path(settings.data_dir) / "artifacts" / "gone").exists()
    assert client.delete("/api/agents/assistant", headers=auth(sup_token)).status_code == 409


def test_e6_14_toggle_inactive_hides_from_routing_and_nav(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "tog")
    install(client, sup_token, agent_zip("tog"))
    client.patch("/api/agents/tog", json={"is_active": False}, headers=auth(sup_token))
    with appdb.SessionLocal() as s:
        assert not [c for c in registry.routable(s) if c["agent"] == "tog"]
    assert client.get("/api/agents/tog/ui", headers=auth(sup_token)).json()["nav_visible"] is False


def test_e6_15_export_and_rollback_endpoint(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "ex")
    install(client, sup_token, agent_zip("ex"))
    install(client, sup_token, agent_zip("ex", version="0.3.0"))
    der = client.post("/api/agents/ex/export", json={"new_id": "ex-copy"}, headers=auth(sup_token))
    m = gen.manifest_of(gen.read_zip(der.content))
    assert m["metadata"]["id"] == "ex-copy" and m["metadata"]["provenance"]["baseVersion"] == "0.3.0"
    sa = gen.read_zip(client.post("/api/agents/ex/export-standalone", headers=auth(sup_token)).content)
    assert yaml.safe_load(sa["compose.yaml"])["services"]["ex-be"]["profiles"] == ["standalone"]
    rb = client.post("/api/agents/ex/rollback", json={"version": "0.1.0"}, headers=auth(sup_token)).json()
    assert status_of(client, sup_token, rb["install_id"])["status"] == "succeeded"
    assert client.get("/api/agents/ex", headers=auth(sup_token)).json()["version"] == "0.1.0"


def test_e6_16_rbac_upload_admin_only(client, sup_token, rt):
    _, user_tok = make_user(client, sup_token, "dev2@example.test")
    files = [("files", ("a.zip", agent_zip("rb"), "application/zip"))]
    assert client.post("/api/agents/upload", files=files, headers=auth(user_tok)).status_code == 403
