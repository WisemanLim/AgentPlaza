"""Epic 18 — 마켓 상거래·퍼블리셔 (D6-05 구매·라이선스, D6-06 퍼블리셔·게시·심사, D6-07 업데이트·레지스트리 API·번들, NFR-C4).

런타임은 FakeRuntime, 에이전트 백엔드는 템플릿 앱(ASGI). 서명은 실제 cosign, SBOM 은 syft(취약점 DB 없음 = 미스캔 경고).
원격 레지스트리는 가짜 ASGI 앱(https://remote.test)으로 흉내 낸다.
"""
import asyncio
import hashlib
import io
import json
import tarfile

import pytest
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app import db as appdb
from app.agentspec import generator as gen
from app.core.config import settings
from app.llm.providers import ChatResult, MockProvider
from app.market import licensing, updates
from app.models import LlmRoute
from app.orchestrator import executor
from app.services import registry
from app.supplychain import tools
from app.supplychain.publish import publish
from helpers import SUPERVISOR, auth, load_template_app, make_user
from test_e9_market import rt, serve, status_of  # noqa: F401 — rt 는 픽스처
from test_e12_supplychain import GW_CHECK, keypair

SUP = SUPERVISOR["email"]


def pkg(aid: str, version: str, priv: bytes | None, type_: str = "app", approval: bool = False) -> bytes:
    files = gen.scaffold(aid, aid.title(), type_)
    m = gen.manifest_of(files)
    m["metadata"]["version"] = version
    if approval:
        m["spec"]["capabilities"][0]["humanApprovalRequired"] = True
    files["agent.yaml"] = yaml.safe_dump(m, sort_keys=False, allow_unicode=True).encode()
    return publish(files, priv)[0] if priv else gen.pack(files)


def submit(client, token, data: bytes, publisher: str, listing: dict | None = None, overwrite=False):
    return client.post("/api/market/releases", files={"file": ("a.zip", data, "application/zip")},
                       data={"publisher": publisher, "listing": json.dumps(listing or {}),
                             "overwrite": str(overwrite).lower()}, headers=auth(token))


@pytest.fixture
def acme(client, sup_token):
    """퍼블리셔 acme(구성원 = admin) + 서명 키."""
    admin, admin_tok = make_user(client, sup_token, "pub-admin@example.test", role="admin")
    h = auth(sup_token)
    assert client.post("/api/market/publishers", json={"id": "acme", "name": "Acme", "members": [admin["email"]]},
                       headers=h).status_code == 201
    priv, pub = keypair()
    kid = client.post("/api/market/publishers/acme/keys", json={"name": "acme-1", "public_key": pub},
                      headers=auth(admin_tok)).json()["kid"]
    return {"priv": priv, "pub": pub, "kid": kid, "admin": admin_tok}


def test_e18_01_publishers_keys_rotation_rbac(client, sup_token, acme):
    """D6-06: 퍼블리셔 등록·구성원·키 회전(이전 키 철회)·권한."""
    h = auth(sup_token)
    _, other = make_user(client, sup_token, "other-admin@example.test", role="admin")
    _, user = make_user(client, sup_token, "u18@example.test")
    _, pub2 = keypair()
    assert client.post("/api/market/publishers/acme/keys", json={"name": "x", "public_key": pub2},
                       headers=auth(other)).status_code == 403
    assert client.post("/api/market/publishers", json={"id": "acme", "name": "dup"}, headers=h).status_code == 409
    r = client.post("/api/market/publishers/acme/keys", json={"name": "acme-2", "public_key": pub2, "rotate": True},
                    headers=auth(acme["admin"])).json()
    assert r["revoked"] == [acme["kid"]]
    p = next(x for x in client.get("/api/market/publishers", headers=h).json() if x["id"] == "acme")
    assert p["active_keys"] == 1 and len(p["keys"]) == 2 and p["members"] == ["pub-admin@example.test"]
    assert client.patch("/api/market/publishers/acme", json={"verified": True}, headers=h).json()["verified"] is True
    assert client.get("/api/market/publishers", headers=auth(user)).status_code == 403
    assert client.patch("/api/market/publishers/acme", json={"verified": False},
                        headers=auth(acme["admin"])).status_code == 403


def test_e18_02_submit_review_approve_listing(client, sup_token, acme, rt):
    """D6-06: admin 게시 → 자동 검사 통과 → 심사 대기 → supervisor 승인 → 리스팅·배지·원장."""
    h = auth(sup_token)
    res = submit(client, acme["admin"], pkg("acme-notes", "1.0.0", acme["priv"]), "acme",
                 {"name": {"ko": "노트", "en": "Notes"}, "tags": ["notes"], "categories": ["common-utility"]})
    assert res.status_code == 201, res.text
    rel = res.json()
    assert rel["status"] == "pending" and rel["gate"]["supply_chain"]["signature"] == "verified"
    assert rel["gate"]["license"]["grade"] == "G1" and rel["gate"]["errors"] == []
    assert "acme-notes" not in [x["id"] for x in client.get("/api/market/listings", headers=h).json()]
    assert client.post(f"/api/market/releases/{rel['id']}/approve", headers=auth(acme["admin"])).status_code == 403
    assert client.post(f"/api/market/releases/{rel['id']}/approve", headers=h).json()["status"] == "published"
    x = client.get("/api/market/listings/acme-notes", headers=h).json()
    assert x["origin"] == "release" and x["publisher"]["id"] == "acme" and x["name"]["en"] == "Notes"
    assert "signature:verified" in x["badges"] and x["trust"] == "community" and x["readme"]
    assert client.get("/api/audit?action=market.release.published", headers=h).json()
    # 서명 키 철회 → 자산 '미검증' 강등
    client.delete(f"/api/trust/keys/{acme['kid']}", headers=h)
    assert "signature:unverified" in client.get("/api/market/listings/acme-notes", headers=h).json()["badges"]


def test_e18_03_gate_blocks_and_conflicts(client, sup_token, acme, rt, monkeypatch):
    """자동 검사 실패 = 게시 불가(서명 없음·다른 퍼블리셔 키·Critical), id 소유권·중복 409, 거부 사유 필수."""
    h, adm = auth(sup_token), acme["admin"]
    r = submit(client, adm, pkg("acme-a", "1.0.0", None), "acme")
    assert r.status_code == 422 and "서명 키로 서명" in r.json()["detail"]["message"]
    other_priv, other_pub = keypair()
    client.post("/api/trust/keys", json={"name": "other", "public_key": other_pub}, headers=h)
    r = submit(client, adm, pkg("acme-b", "1.0.0", other_priv), "acme")
    assert r.status_code == 422 and r.json()["detail"]["gate"]["supply_chain"]["signature"] == "verified"
    finding = {"id": "CVE-1", "pkg": "x", "version": "1", "severity": "CRITICAL", "title": "t"}
    monkeypatch.setattr(tools, "trivy_scan", lambda d: {**GW_CHECK, "critical": 1, "findings": [finding]})
    r = submit(client, adm, pkg("acme-c", "1.0.0", acme["priv"]), "acme")
    assert r.status_code == 422 and "CRITICAL" in r.json()["detail"]["message"]
    blocked = client.get("/api/market/releases?status=blocked", headers=h).json()
    assert {b["listing_id"] for b in blocked} == {"acme-a", "acme-b", "acme-c"}
    monkeypatch.setattr(tools, "trivy_scan", lambda d: GW_CHECK)
    assert submit(client, adm, pkg("board", "2.0.0", acme["priv"]), "acme").status_code == 409  # 정적 board = agentplaza
    first = submit(client, adm, pkg("acme-d", "1.0.0", acme["priv"]), "acme").json()
    assert submit(client, adm, pkg("acme-d", "1.0.0", acme["priv"]), "acme").status_code == 409
    again = submit(client, adm, pkg("acme-d", "1.0.0", acme["priv"]), "acme", overwrite=True)
    assert again.status_code == 201 and again.json()["id"] != first["id"]
    assert client.post(f"/api/market/releases/{again.json()['id']}/reject", json={"reason": ""}, headers=h).status_code == 422
    rj = client.post(f"/api/market/releases/{again.json()['id']}/reject", json={"reason": "README 부족"}, headers=h).json()
    assert rj["status"] == "rejected" and rj["reason"] == "README 부족"
    assert client.post("/api/market/releases", files={"file": ("a.zip", b"nope", "application/zip")},
                       data={"publisher": "acme"}, headers=auth(adm)).status_code == 422


def test_e18_04_license_token_offline_checks(client, sup_token):
    """D6-05: Ed25519 토큰 오프라인 검증 — 변조·모르는 발급자·만료·버전 범위·호스트·대상."""
    assert licensing.in_range("1.4.2", "^1.0.0") and not licensing.in_range("2.0.0", "^1.0.0")
    assert licensing.in_range("0.3.1", "^0.3.0") and not licensing.in_range("0.4.0", "^0.3.0")
    assert licensing.in_range("1.5.0", ">=1.2.0 <2.0.0") and not licensing.in_range("1.1.0", ">=1.2.0 <2.0.0")
    with appdb.SessionLocal() as s:
        host = licensing.instance_id(s)
        tok = licensing.issue(s, listing="paid-x", publisher="acme", versions="^1.0.0", seats=2, days=30, host=host)
        body, checks = licensing.verify(s, tok, listing="paid-x", version="1.2.0")
        assert all(c["ok"] for c in checks) and body["seats"] == 2
        _, checks = licensing.verify(s, tok, listing="other", version="2.0.0")
        assert {c["check"] for c in checks if not c["ok"]} == {"target", "versions"}
        prefix, b, sig = tok.split(".")
        forged = json.loads(licensing._unb64(b)) | {"seats": 999}
        bad = ".".join([prefix, licensing._b64(json.dumps(forged).encode()), sig])
        with pytest.raises(licensing.LicenseError, match="서명"):
            licensing.verify(s, bad)
        with pytest.raises(licensing.LicenseError, match="형식"):
            licensing.verify(s, "garbage")
        raw = json.dumps({**json.loads(licensing._unb64(b)), "exp": 1, "host": "inst-elsewhere"},
                         separators=(",", ":")).encode()
        old = f"apl1.{licensing._b64(raw)}.{licensing._b64(licensing._issuer_private(s).sign(raw))}"
        _, checks = licensing.verify(s, old)
        assert {c["check"] for c in checks if not c["ok"]} == {"expiry", "host"}
    # 다른 마켓이 발급 → 발급자 등록 전 거부, 등록 후 통과
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    k = Ed25519PrivateKey.generate()
    pem = k.public_key().public_bytes(ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()
    from app.supplychain.trust import kid_of
    raw = json.dumps({"v": 1, "lid": "lic-ext", "iss": kid_of(pem), "listing": "paid-x", "versions": "*", "seats": 1,
                      "exp": None, "host": None}).encode()
    ext = f"apl1.{licensing._b64(raw)}.{licensing._b64(k.sign(raw))}"
    h = auth(sup_token)
    assert client.post("/api/licenses/verify", json={"key": ext, "listing": "paid-x"}, headers=h).status_code == 422
    client.post("/api/market/license-issuers", json={"name": "remote-market", "public_key": pem}, headers=h)
    v = client.post("/api/licenses/verify", json={"key": ext, "listing": "paid-x"}, headers=h).json()
    assert v["ok"] is True and v["payload"]["lid"] == "lic-ext"


PAID = {"pricing": {"model": "per_seat", "price": 10000, "currency": "KRW"}}


def test_e18_05_paid_listing_purchase_receipt_install(client, sup_token, acme, rt, tmp_path, monkeypatch):
    """D6-05·NFR-C4: 유료 리스팅 — 라이선스 없으면 설치 거부, mock 결제 → 영수증 + 라이선스 → 설치. 어댑터 없으면 키 입력만."""
    h = auth(sup_token)
    assert submit(client, sup_token, pkg("acme-pro", "1.0.0", acme["priv"]), "acme", PAID).json()["status"] == "published"
    x = client.get("/api/market/listings/acme-pro", headers=h).json()
    assert x["paid"] is True and x["pricing"]["price"] == 10000 and x["licensed"] is False
    assert client.post("/api/market/install/acme-pro", json={}, headers=h).status_code == 402
    monkeypatch.setattr(settings, "payment_adapter", "none")
    assert client.post("/api/market/purchase/acme-pro", json={}, headers=h).status_code == 409
    monkeypatch.setattr(settings, "payment_adapter", "mock")
    assert client.post("/api/market/purchase/board", json={}, headers=h).status_code == 422  # 무료
    r = client.post("/api/market/purchase/acme-pro", json={"seats": 2, "months": 3}, headers=h)
    assert r.status_code == 201, r.text
    pu, lic = r.json()["purchase"], r.json()["license"]
    assert pu["amount"] == 60000 and pu["adapter"] == "mock" and pu["adapter_ref"].startswith("mock_")
    assert lic["seats"] == 2 and lic["versions"] == "^1.0.0" and lic["valid"] is True
    rc = client.get(f"/api/market/purchases/{pu['id']}/receipt", headers=h)
    assert rc.headers["content-disposition"].startswith("attachment") and rc.json()["license"]["token"].startswith("apl1.")
    assert client.get("/api/market/listings/acme-pro", headers=h).json()["licensed"] is True
    serve(tmp_path, monkeypatch, "acme-pro", "app")
    res = client.post("/api/market/install/acme-pro", json={}, headers=h)
    assert res.status_code == 202, res.text
    assert status_of(client, sup_token, res.json()["install_id"])["status"] == "succeeded"
    assert client.get("/api/market/listings/acme-pro", headers=h).json()["stats"] == {"install": 1}
    assert client.get("/api/audit?action=market.purchase", headers=h).json()[0]["detail"]["amount"] == 60000
    # 영수증의 키를 그대로 다시 등록(재설치 등) — 같은 lid 갱신
    assert client.post("/api/licenses", json={"key": rc.json()["license"]["token"], "listing": "acme-pro"},
                       headers=h).status_code == 201
    assert len(client.get("/api/licenses?listing=acme-pro", headers=h).json()) == 1


@pytest.fixture
def plan_llm(monkeypatch):
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


def test_e18_06_seats_and_expiry_enforced_at_execution(client, sup_token, tmp_path, monkeypatch, plan_llm):
    """좌석 1 — 첫 사용자 배정, 두 번째 사용자 거부(license_blocked), 좌석 반납 후 허용, 철회 시 모두 거부."""
    with appdb.SessionLocal() as s:
        app, manifest = load_template_app(tmp_path, "execution", "calc", monkeypatch, registry.agent_key("calc"))
        executor.register_app("http://calc.test", app)
        registry.register(s, manifest, endpoint="http://calc.test", status="healthy")
        lic = licensing.register(s, licensing.issue(s, listing="calc", publisher="acme", versions="*", seats=1),
                                 "calc", "test")
        lid = lic.id
    plan_llm["plan"] = {"steps": [{"id": "s1", "agent": "calc", "capability": "calculate", "args": {"expression": "1+1"}}]}
    _, other = make_user(client, sup_token, "seat-b@example.test")

    def run(tok):
        return client.post("/api/orchestrate", json={"message": "1+1"}, headers=auth(tok)).json()["results"]["s1"]

    try:
        assert run(sup_token)["ok"] is True
        blocked = run(other)
        assert blocked["ok"] is False and "좌석 초과" in blocked["error"]
        h = auth(sup_token)
        assert client.get("/api/licenses", headers=h).json()[0]["holders"] == [SUP]
        assert client.delete(f"/api/licenses/{lid}/seats/{SUP}", headers=h).json() == {"released": SUP}
        assert run(other)["ok"] is True
        client.delete(f"/api/licenses/{lid}", headers=h)
        assert "유효한 라이선스 없음" in run(other)["error"]
        assert client.get("/api/audit?action=license.denied", headers=h).json()
    finally:
        executor.clear_apps()


def test_e18_07_updates_consent_auto_update_notice(client, sup_token, rt, tmp_path, monkeypatch):
    """D6-07: 설치됨 목록·업데이트 알림(1회) — 권한 변화는 재동의, 자동 갱신은 권한 변화 없을 때만."""
    h = auth(sup_token)
    serve(tmp_path, monkeypatch, "board", "app")
    st = status_of(client, sup_token, client.post("/api/market/install/board", json={}, headers=h).json()["install_id"])
    assert st["status"] == "succeeded"
    client.post("/api/market/publishers", json={"id": "agentplaza", "name": "AgentPlaza"}, headers=h)
    priv, pub = keypair()
    client.post("/api/market/publishers/agentplaza/keys", json={"name": "ap", "public_key": pub}, headers=h)
    assert submit(client, sup_token, pkg("board", "1.1.0", priv, approval=True), "agentplaza").status_code == 201
    item = next(i for i in client.get("/api/market/installed", headers=h).json() if i["agent_id"] == "board")
    assert item["update"]["version"] == "1.1.0" and item["update"]["approval_added"] == ["manage"]
    assert item["update"]["needs_consent"] is True and item["versions"][0]["version"] == "1.0.0"
    chk = client.post("/api/market/updates/check", headers=h).json()
    assert chk["new"] == ["board"] and client.post("/api/market/updates/check", headers=h).json()["new"] == []
    r = client.post("/api/market/updates/board", json={}, headers=h)
    assert r.status_code == 409 and r.json()["detail"]["update"]["approval_added"] == ["manage"]
    assert client.put("/api/market/auto-update/board", json={"enabled": True}, headers=h).json()["enabled"] is True
    with appdb.SessionLocal() as s:
        done = asyncio.run(updates.auto_update(s))
    assert "재동의" in done[0]["skipped"]
    r = client.post("/api/market/updates/board", json={"consent": True}, headers=h)
    assert r.status_code == 202 and status_of(client, sup_token, r.json()["install_id"])["status"] == "succeeded"
    assert client.get("/api/agents/board", headers=h).json()["version"] == "1.1.0"
    # 권한 변화 없는 1.2.0 → 자동 갱신
    assert submit(client, sup_token, pkg("board", "1.2.0", priv, approval=True), "agentplaza").status_code == 201
    with appdb.SessionLocal() as s:
        done = asyncio.run(updates.auto_update(s))
    assert done == [{"agent_id": "board", "install_id": done[0]["install_id"], "status": "succeeded"}]
    assert client.get("/api/agents/board", headers=h).json()["version"] == "1.2.0"
    assert len(client.get("/api/audit?action=market.update_available", headers=h).json()) == 2
    assert client.get("/api/market/listings/board", headers=h).json()["stats"] == {"install": 1, "update": 2}


def test_e18_08_registry_api_mcp_compatible(client, sup_token, acme, rt):
    """D6-07: /registry/v0.1 — server.json·_meta·페이지·검색·증분·버전·산출물(유료 = 라이선스 토큰)·호스트 공개."""
    h = auth(sup_token)
    submit(client, sup_token, pkg("acme-notes", "1.0.0", acme["priv"]), "acme")
    submit(client, sup_token, pkg("acme-notes", "1.1.0", acme["priv"]), "acme")
    submit(client, sup_token, pkg("acme-pro", "1.0.0", acme["priv"]), "acme", PAID)
    assert client.get("/registry/v0.1/servers").status_code == 401
    page = client.get("/registry/v0.1/servers?limit=4", headers=h).json()
    assert page["metadata"]["count"] == 4 and page["metadata"]["nextCursor"]
    e = page["servers"][0]
    assert e["server"]["$schema"].endswith("2025-12-11/server.schema.json") and e["server"]["name"] == "io.agentplaza/board"
    assert e["_meta"]["io.modelcontextprotocol.registry/official"]["isLatest"] is True
    ours = e["_meta"]["io.agentplaza/listing"]
    assert ours["artifact"]["url"] == "http://testserver/registry/v0.1/artifacts/board/1.0.0.zip"
    rest = client.get(f"/registry/v0.1/servers?limit=100&cursor={page['metadata']['nextCursor']}", headers=h).json()
    assert len(page["servers"]) + len(rest["servers"]) == 10 and "nextCursor" not in rest["metadata"]
    assert [x["server"]["name"] for x in client.get("/registry/v0.1/servers?search=notes", headers=h).json()["servers"]] \
        == ["io.agentplaza/acme-notes"]
    assert client.get("/registry/v0.1/servers?updated_since=2999-01-01T00:00:00Z", headers=h).json()["servers"] == []
    vers = client.get("/registry/v0.1/servers/io.agentplaza/acme-notes/versions", headers=h).json()["servers"]
    assert [v["server"]["version"] for v in vers] == ["1.0.0", "1.1.0"]
    assert client.get("/registry/v0.1/servers/io.agentplaza/acme-notes/versions/latest",
                      headers=h).json()["server"]["version"] == "1.1.0"
    old = client.get("/registry/v0.1/artifacts/acme-notes/1.0.0.zip", headers=h)
    assert old.status_code == 200 and hashlib.sha256(old.content).hexdigest() == vers[0]["_meta"]["io.agentplaza/listing"]["artifact"]["sha256"]
    assert client.get("/registry/v0.1/artifacts/acme-pro/1.0.0.zip", headers=h).status_code == 402
    with appdb.SessionLocal() as s:
        tok = licensing.issue(s, listing="acme-pro", publisher="acme", versions="^1.0.0", seats=1, host="inst-buyer")
    assert client.get("/registry/v0.1/artifacts/acme-pro/1.0.0.zip", headers=h | {"X-Plaza-License": tok}).status_code == 200
    assert client.get("/api/market/listings/acme-notes", headers=h).json()["stats"] == {"download": 1}
    client.put("/api/market/registry-exposure", json={"public": True}, headers=h)
    assert client.get("/registry/v0.1/servers?limit=1").status_code == 200


def _remote_app(entries: dict, zips: dict[str, bytes], token="remote-token"):
    """가짜 원격 레지스트리: Bearer 토큰 확인, 2페이지, 산출물 제공."""
    app = FastAPI()

    @app.get("/v0.1/servers")
    def servers(request: Request, cursor: str | None = None):
        if request.headers.get("authorization") != f"Bearer {token}":
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        if cursor:
            return {"servers": entries["page2"], "metadata": {"count": len(entries["page2"])}}
        return {"servers": entries["page1"], "metadata": {"count": len(entries["page1"]), "nextCursor": "p2"}}

    @app.get("/artifacts/{name}")
    def artifact(name: str):
        return Response(zips[name], media_type="application/zip")
    return app


def _ours(aid, version, data, **extra):
    return {"server": {"name": f"io.agentplaza/{aid}", "version": version, "description": aid},
            "_meta": {"io.agentplaza/listing": {
                "id": aid, "type": "app", "name": aid, "description": aid, "categories": [], "industry": "-",
                "work": "W19", "domain": "common", "tags": [], "publisher": {"id": "far", "name": "Far"},
                "license": "MIT", "trust": "community", "pricing": "free", "capabilities": ["manage"],
                "required_env": [], "permissions": {"egress": []},
                "artifact": {"url": f"https://remote.test/artifacts/{aid}.zip",
                             "sha256": hashlib.sha256(data).hexdigest()}, **extra}}}


def test_e18_09_remote_registry_sync_install(client, sup_token, rt, tmp_path, monkeypatch):
    """원격 레지스트리: 연결 시험(인증 실패 표시)·증분 동기화(2페이지)·id 충돌 건너뜀·MCP 서버 편입·체크섬 변경 거부·설치·삭제."""
    h = auth(sup_token)
    far = pkg("far-tool", "1.0.0", None)
    entries = {"page1": [_ours("far-tool", "1.0.0", far), _ours("board", "9.0.0", far)],
               "page2": [{"server": {"name": "io.github.example/weather", "title": "Weather", "version": "0.2.0",
                                     "remotes": [{"type": "streamable-http", "url": "https://mcp.example/weather"}]}},
                         {"server": {"name": "io.github.example/local-only", "version": "1.0.0",
                                     "packages": [{"registryType": "npm", "identifier": "x"}]}}]}
    executor.register_app("https://remote.test", _remote_app(entries, {"far-tool.zip": far}))
    try:
        bad = client.put("/api/market/registries/far", json={"url": "https://remote.test", "token": "wrong"}, headers=h)
        assert bad.json()["status"] == "auth_failed"
        assert client.put("/api/market/registries/far", json={"url": "ftp://x"}, headers=h).status_code == 422
        ok = client.put("/api/market/registries/far", json={"url": "https://remote.test", "token": "remote-token"},
                        headers=h).json()
        assert ok["status"] == "ok"
        rep = client.post("/api/market/registries/far/sync", json={}, headers=h).json()
        assert rep["added"] == ["far-tool", "io-github-example-weather"]
        assert {s["id"] for s in rep["skipped"]} == {"board", "io.github.example/local-only"}
        x = client.get("/api/market/listings/far-tool", headers=h).json()
        assert x["origin"] == "registry:far" and x["source"]["type"] == "zip-url"
        w = client.get("/api/market/listings/io-github-example-weather", headers=h).json()
        assert w["source"] == {"type": "remote-mcp", "url": "https://mcp.example/weather", "registry": "far"}
        serve(tmp_path, monkeypatch, "far-tool", "app")
        res = client.post("/api/market/install/far-tool", json={}, headers=h).json()
        assert status_of(client, sup_token, res["install_id"])["status"] == "succeeded"
        entries["page1"][0] = _ours("far-tool", "1.0.0", far + b"x")
        rep = client.post("/api/market/registries/far/sync", json={"full": True}, headers=h).json()
        assert {"id": "far-tool", "reason": "같은 버전의 체크섬 변경 — 거부 / digest changed"} in rep["skipped"]
        reg = client.get("/api/market/registries", headers=h).json()[0]
        assert reg["has_token"] is True and reg["count"] == 2 and "remote-token" not in json.dumps(reg)
        assert client.delete("/api/market/registries/far", headers=h).json() == {"removed_listings": 2}
        assert client.get("/api/market/listings/far-tool", headers=h).status_code == 404
    finally:
        executor.clear_apps()


def test_e18_10_offline_bundle_roundtrip_and_tamper(client, sup_token, rt):
    """번들 내보내기 → 가져오기(체크섬 검증·충돌은 덮어쓰기 확인) · 변조·SHA256SUMS 없음 거부."""
    h = auth(sup_token)
    data = client.get("/api/market/bundle?ids=board,calculator", headers=h).content
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        names = sorted(tar.getnames())
    assert names == ["SHA256SUMS", "artifacts/board-1.0.0.zip", "artifacts/calculator-1.0.0.zip", "catalog.json"]

    def post(blob, overwrite=False):
        return client.post("/api/market/bundle", files={"file": ("b.tar.gz", blob, "application/gzip")},
                           data={"overwrite": str(overwrite).lower()}, headers=h)

    assert {s["id"] for s in post(data).json()["skipped"]} == {"board", "calculator"}
    assert post(data, overwrite=True).json()["added"] == ["board", "calculator"]
    assert client.get("/api/market/listings/board", headers=h).json()["origin"] == "bundle"

    def rebuild(mutate):
        src = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")
        files = {m.name: src.extractfile(m).read() for m in src.getmembers()}
        mutate(files)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as out:
            for n, b in files.items():
                info = tarfile.TarInfo(n)
                info.size = len(b)
                out.addfile(info, io.BytesIO(b))
        return buf.getvalue()

    tampered = rebuild(lambda f: f.__setitem__("artifacts/board-1.0.0.zip", f["artifacts/board-1.0.0.zip"] + b"x"))
    r = post(tampered, overwrite=True)
    assert r.status_code == 422 and "체크섬 불일치" in r.json()["detail"]
    assert post(rebuild(lambda f: f.pop("SHA256SUMS")), overwrite=True).status_code == 422


def test_e18_11_ops_badges_hidden_rbac(client, sup_token):
    """운영 배지(Featured 기간·Validated)·숨김, admin 은 운영 배지 변경 불가."""
    h = auth(sup_token)
    _, admin = make_user(client, sup_token, "ops-admin@example.test", role="admin")
    assert client.patch("/api/market/listings/board/ops", json={"hidden": True}, headers=auth(admin)).status_code == 403
    client.patch("/api/market/listings/calculator/ops", json={"featured_until": "2999-12-31", "validated_ref": "QA-17"},
                 headers=h)
    client.patch("/api/market/listings/board/ops", json={"hidden": True}, headers=h)
    allx = client.get("/api/market/listings", headers=h).json()
    assert allx[0]["id"] == "calculator" and {"featured", "validated"} <= set(allx[0]["badges"])
    assert "board" not in [x["id"] for x in allx]
    assert client.get("/api/market/listings/board", headers=h).json()["hidden"] is True
    assert client.patch("/api/market/listings/nope/ops", json={}, headers=h).status_code == 404
    inst = client.get("/api/market/instance", headers=h).json()
    assert inst["payment_adapter"] == "mock" and inst["license_issuer"].startswith("pub-")
