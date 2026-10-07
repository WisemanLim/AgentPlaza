"""Epic 9 — 마켓플레이스 설치 3경로 (D6-01 스토어 API, D6-02 경로 A, D6-03 경로 B, D6-04 경로 C, US2·US6).

런타임은 FakeRuntime, 에이전트 백엔드는 템플릿 앱(ASGI). 카탈로그는 저장소의 market/catalog.json(큐레이션).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.responses import Response

from app.agentspec import generator as gen
from app.core.config import settings
from app.orchestrator import executor
from app.registry import pipeline
from app.runtime.driver import FakeRuntime, set_runtime
from app.services import registry
from helpers import auth, load_template_app, make_user

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def rt(tmp_path, monkeypatch):
    fake = FakeRuntime()
    set_runtime(fake)
    monkeypatch.setattr(settings, "data_dir", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "health_timeout_seconds", 2.0)
    monkeypatch.setattr(settings, "market_catalog", str(ROOT / "market" / "catalog.json"))
    yield fake
    set_runtime(None)
    executor.clear_apps()


def serve(tmp_path, monkeypatch, agent_id, type_):
    app, _ = load_template_app(tmp_path / "srv" / agent_id, type_, agent_id, monkeypatch, registry.agent_key(agent_id))
    executor.register_app(pipeline.endpoint_for(agent_id), app)


def status_of(client, token, install_id):
    return client.get(f"/api/agents/installs/{install_id}", headers=auth(token)).json()


def test_e9_01_categories_and_search(client, sup_token, rt):
    """D6-01: 3축 분류(업무·업종·도메인) + 검색·필터 + 신뢰 배지."""
    h = auth(sup_token)
    cats = client.get("/api/market/categories", headers=h).json()
    assert {i["industry"] for i in cats["industries"]} >= {"-", "J", "C", "H", "M"} and len(cats["work"]) == 19
    assert [x["id"] for x in client.get("/api/market/listings?q=게시판", headers=h).json()] == ["board"]
    assert [x["id"] for x in client.get("/api/market/listings?category=ict-governance", headers=h).json()] == ["pii-guard"]
    assert [x["id"] for x in client.get("/api/market/listings?type=rag", headers=h).json()] == ["knowledge-rag"]
    allx = client.get("/api/market/listings", headers=h).json()
    assert len(allx) == 8 and all({"official", "signature:unverified", "publisher:verified"} <= set(x["badges"]) for x in allx)
    detail = client.get("/api/market/listings/board", headers=h).json()
    assert "docker compose --profile standalone" in detail["readme"] and detail["capabilities"] == ["manage"]
    assert client.get("/api/market/listings/nope", headers=h).status_code == 404


def test_e9_02_path_a_install_us2(client, sup_token, rt, tmp_path, monkeypatch):
    """US2: 마켓에서 골라 코드 편집 0 으로 설치 → 콘솔 네비 노출."""
    serve(tmp_path, monkeypatch, "board", "app")
    r = client.post("/api/market/install/board", json={}, headers=auth(sup_token)).json()
    st = status_of(client, sup_token, r["install_id"])
    assert r["path"] == "A" and st["status"] == "succeeded" and st["source"] == "market" and st["source_ref"] == "board@1.0.0"
    a = client.get("/api/agents/board", headers=auth(sup_token)).json()
    assert a["trust"] == "official" and a["source"] == "market" and a["nav_visible"] is True
    x = client.get("/api/market/listings?q=board", headers=auth(sup_token)).json()[0]
    assert x["installed"] == {"version": "1.0.0", "status": "healthy", "update_available": False}


def test_e9_03_required_env_form(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "http-tool", "tool-proxy")
    bad = client.post("/api/market/install/http-tool", json={}, headers=auth(sup_token))
    assert bad.status_code == 422 and "TOOL_BASE_URL" in bad.json()["detail"]
    ok = client.post("/api/market/install/http-tool", json={"env": {"TOOL_BASE_URL": "https://api.example"}},
                     headers=auth(sup_token)).json()
    assert status_of(client, sup_token, ok["install_id"])["status"] == "succeeded"


def _temp_catalog(tmp_path, monkeypatch, mutate) -> Path:
    d = tmp_path / "market"
    shutil.copytree(ROOT / "market", d)
    cat = json.loads((d / "catalog.json").read_text())
    mutate(cat)
    (d / "catalog.json").write_text(json.dumps(cat))
    monkeypatch.setattr(settings, "market_catalog", str(d / "catalog.json"))
    return d


def test_e9_04_artifact_digest_mismatch_rejected(client, sup_token, rt, tmp_path, monkeypatch):
    def tamper(cat):
        next(x for x in cat["listings"] if x["id"] == "calculator")["source"]["sha256"] = "0" * 64
    _temp_catalog(tmp_path, monkeypatch, tamper)
    res = client.post("/api/market/install/calculator", json={}, headers=auth(sup_token))
    assert res.status_code == 422 and "sha256" in res.json()["detail"]


def test_e9_05_update_available_then_upgrade(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "calculator", "execution")
    old = gen.scaffold("calculator", "Calculator", "execution")  # 0.1.0 을 직접 설치(경로 B)
    up = client.post("/api/agents/upload", files=[("files", ("c.zip", gen.pack(old), "application/zip"))],
                     headers=auth(sup_token)).json()
    assert status_of(client, sup_token, up[0]["install_id"])["status"] == "succeeded"
    x = client.get("/api/market/listings?q=calculator", headers=auth(sup_token)).json()[0]
    assert x["installed"]["update_available"] is True
    r = client.post("/api/market/install/calculator", json={}, headers=auth(sup_token)).json()
    assert status_of(client, sup_token, r["install_id"])["status"] == "succeeded"
    assert client.get("/api/agents/calculator", headers=auth(sup_token)).json()["version"] == "1.0.0"


def test_e9_06_path_b_zip_url(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "dl", "service")
    blob = gen.pack(gen.scaffold("dl", "Dl", "service"))
    files = FastAPI()

    @files.get("/dl.zip")
    def _zip():
        return Response(blob, media_type="application/zip")
    executor.register_app("https://files.test", files)
    import hashlib
    ok = client.post("/api/agents/install-url", json={"url": "https://files.test/dl.zip",
                                                      "sha256": hashlib.sha256(blob).hexdigest()}, headers=auth(sup_token))
    assert status_of(client, sup_token, ok.json()["install_id"])["status"] == "succeeded"
    bad = client.post("/api/agents/install-url", json={"url": "https://files.test/dl.zip", "sha256": "1" * 64},
                      headers=auth(sup_token))
    assert bad.status_code == 422
    assert client.post("/api/agents/install-url", json={"url": "ftp://x/y.zip"}, headers=auth(sup_token)).status_code == 422
    assert client.post("/api/agents/install-url", json={"url": "https://files.test/missing.zip"},
                       headers=auth(sup_token)).status_code == 422


def test_e9_07_path_b_git_subdir(client, sup_token, rt, tmp_path, monkeypatch):
    serve(tmp_path, monkeypatch, "gitagent", "memory")
    repo = tmp_path / "repo"
    sub = repo / "agents" / "gitagent"
    for rel, data in gen.scaffold("gitagent", "Git Agent", "memory").items():
        (sub / rel).parent.mkdir(parents=True, exist_ok=True)
        (sub / rel).write_bytes(data)
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "."], ["git", "commit", "-q", "-m", "init"]):
        subprocess.run(cmd, cwd=repo, env=env, check=True)
    r = client.post("/api/agents/install-git", json={"url": f"file://{repo}", "path": "agents/gitagent", "ref": "main"},
                    headers=auth(sup_token))
    assert r.status_code == 202, r.text
    st = status_of(client, sup_token, r.json()["install_id"])
    assert st["status"] == "succeeded" and st["source"] == "git"
    assert client.post("/api/agents/install-git", json={"url": f"file://{repo}", "path": "../etc"},
                       headers=auth(sup_token)).status_code == 422
    assert client.post("/api/agents/install-git", json={"url": f"file://{repo}", "path": "nope"},
                       headers=auth(sup_token)).status_code == 422


def test_e9_08_path_c_remote_listing_us6(client, sup_token, rt, tmp_path, monkeypatch):
    rem, _ = load_template_app(tmp_path / "rem", "execution", "remcalc", monkeypatch, "rk", public_url="http://partner.test")
    executor.register_app("http://partner.test", rem)

    def add_remote(cat):
        cat["listings"].append({"id": "partner-calc", "version": "1.0.0", "type": "federation", "name": "Partner Calc",
                                "description": "원격 A2A", "categories": ["common-utility"], "industry": "-",
                                "work": "W19", "domain": "common", "tags": [], "publisher": {"id": "partner"},
                                "license": "external", "trust": "external", "capabilities": ["calculate"],
                                "required_env": [], "source": {"type": "remote-a2a", "card_url": "http://partner.test"}})
    _temp_catalog(tmp_path, monkeypatch, add_remote)
    r = client.post("/api/market/install/partner-calc", json={"auth_header": "x-api-key", "auth_value": "rk"},
                    headers=auth(sup_token))
    assert r.status_code == 202 and r.json()["path"] == "C"
    a = client.get("/api/agents/partner-calc", headers=auth(sup_token)).json()
    assert a["source"] == "link" and a["trust"] == "external" and a["capabilities"][0]["verb"] == "calculate"


def test_e9_09_rbac_browse_vs_install(client, sup_token, rt):
    _, user_tok = make_user(client, sup_token, "shopper@example.test")
    assert client.get("/api/market/listings", headers=auth(user_tok)).status_code == 200
    assert client.post("/api/market/install/board", json={}, headers=auth(user_tok)).status_code == 403


def test_e9_10_catalog_matches_artifacts():
    """정적 카탈로그 무결성: 모든 zip 산출물의 sha256·manifest 가 카탈로그와 일치."""
    import hashlib
    cat = json.loads((ROOT / "market" / "catalog.json").read_text())
    for x in cat["listings"]:
        data = (ROOT / "market" / x["source"]["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == x["source"]["sha256"], x["id"]
        m = yaml.safe_load(gen.read_zip(data)["agent.yaml"])
        assert (m["metadata"]["id"], m["metadata"]["version"]) == (x["id"], x["version"])
