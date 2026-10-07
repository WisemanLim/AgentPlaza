"""Epic 1 — 플랫폼 기반: 셋업·인증·RBAC·API 키·감사 원장·무인증 경로 (D9-01/02/03/07, D10-06, NFR-S5)."""
import re

from fastapi.routing import APIRoute
from sqlalchemy import inspect, text

from app import db as appdb
from app.main import app
from helpers import SUPERVISOR, auth, make_user


def test_e1_01_schema_tables():
    tables = set(inspect(appdb.engine).get_table_names())
    assert {"users", "api_keys", "audit_events", "settings", "alembic_version"} <= tables


def test_e1_02_setup_once(client):
    assert client.get("/api/setup/status").json() == {"initialized": False}
    res = client.post("/api/setup/admin", json=SUPERVISOR)
    assert res.status_code == 201
    assert res.json()["user"]["role"] == "supervisor"
    assert client.get("/api/setup/status").json() == {"initialized": True}
    again = client.post("/api/setup/admin", json={"email": "x@example.test", "password": "another-pass-1"})
    assert again.status_code == 409


def test_e1_03_login_and_generic_error(client, sup_token):
    ok = client.post("/api/auth/login", json=SUPERVISOR)
    assert ok.status_code == 200 and ok.json()["token_type"] == "bearer"
    wrong_pw = client.post("/api/auth/login", json={**SUPERVISOR, "password": "wrong-password"})
    no_user = client.post("/api/auth/login", json={"email": "nobody@example.test", "password": "wrong-password"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json()["detail"] == no_user.json()["detail"]  # 아이디/비번 구분 안 함
    me = client.get("/api/auth/me", headers=auth(ok.json()["access_token"]))
    assert me.json()["email"] == SUPERVISOR["email"]


def test_e1_04_lockout_after_5_failures(client, sup_token):
    for _ in range(5):
        assert client.post("/api/auth/login", json={**SUPERVISOR, "password": "bad-password"}).status_code == 401
    locked = client.post("/api/auth/login", json=SUPERVISOR)
    assert locked.status_code == 423


def test_e1_05_rbac_lower_roles_only(client, sup_token):
    _, admin_tok = make_user(client, sup_token, "admin@example.test", "admin")
    _, user_tok = make_user(client, sup_token, "user@example.test", "user")
    assert client.get("/api/users", headers=auth(user_tok)).status_code == 403
    assert client.get("/api/users", headers=auth(admin_tok)).status_code == 200
    # admin 은 user 만 생성 가능, admin·supervisor 생성은 403
    assert client.post("/api/users", json={"email": "a2@example.test", "role": "admin"},
                       headers=auth(admin_tok)).status_code == 403
    assert client.post("/api/users", json={"email": "u2@example.test", "role": "user"},
                       headers=auth(admin_tok)).status_code == 201
    sup_id = client.get("/api/auth/me", headers=auth(sup_token)).json()["id"]
    assert client.patch(f"/api/users/{sup_id}", json={"is_active": False},
                        headers=auth(admin_tok)).status_code == 403


def test_e1_06_temp_password_and_change(client, sup_token):
    body, tok = make_user(client, sup_token, "temp@example.test")
    assert body["must_change_password"] is True
    assert "temporary_password" not in client.get("/api/users", headers=auth(sup_token)).text
    res = client.post("/api/auth/password", json={"current_password": body["temporary_password"],
                                                   "new_password": "brand-new-pass-1"}, headers=auth(tok))
    assert res.status_code == 200
    assert client.post("/api/auth/login", json={"email": "temp@example.test",
                                                "password": "brand-new-pass-1"}).status_code == 200


def test_e1_07_deactivated_user_rejected(client, sup_token):
    body, tok = make_user(client, sup_token, "gone@example.test")
    client.patch(f"/api/users/{body['id']}", json={"is_active": False}, headers=auth(sup_token))
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 401


def test_e1_08_api_key_lifecycle(client, sup_token):
    res = client.post("/api/api-keys", json={"name": "cursor", "agents": ["board"]}, headers=auth(sup_token))
    assert res.status_code == 201
    raw = res.json()["key"]
    assert raw.startswith("ap_sk_")
    assert raw not in client.get("/api/api-keys", headers=auth(sup_token)).text  # 원문 1회 노출
    me = client.get("/api/auth/me", headers={"x-api-key": raw}).json()
    assert me["type"] == "service" and me["scopes"] == {"agents": ["board"]}
    tok = client.post("/api/auth/token?agent=board", headers={"x-api-key": raw})
    assert tok.status_code == 200
    assert client.get("/api/auth/me", headers=auth(tok.json()["access_token"])).json()["type"] == "service"
    assert client.post("/api/auth/token?agent=other", headers={"x-api-key": raw}).status_code == 403
    client.delete(f"/api/api-keys/{res.json()['id']}", headers=auth(sup_token))
    assert client.get("/api/auth/me", headers={"x-api-key": raw}).status_code == 401


def test_e1_09_audit_chain_and_tamper_detection(client, sup_token):
    make_user(client, sup_token, "audited@example.test")
    events = client.get("/api/audit", headers=auth(sup_token)).json()
    actions = {e["action"] for e in events}
    assert {"setup.admin_created", "user.created", "auth.login"} <= actions
    assert all(re.fullmatch(r"[0-9a-f]{64}", e["hash"]) for e in events)
    assert client.get("/api/audit/verify", headers=auth(sup_token)).json()["ok"] is True
    with appdb.engine.begin() as conn:  # SQLite 는 트리거가 없으므로 직접 변조해 탐지 여부를 본다
        conn.execute(text("UPDATE audit_events SET actor='mallory' WHERE id = (SELECT MIN(id) FROM audit_events)"))
    verdict = client.get("/api/audit/verify", headers=auth(sup_token)).json()
    assert verdict["ok"] is False and verdict["broken_at"] is not None


PUBLIC = {("GET", "/health"), ("GET", "/api/setup/status"), ("POST", "/api/setup/admin"),
          ("POST", "/api/auth/login"), ("POST", "/api/auth/token"), ("POST", "/api/auth/logout"),
          # Agent Card 는 공개(NFR-S5), JWKS 는 카드 서명 검증용 공개키
          ("GET", "/a/{agent_id}/.well-known/agent-card.json"), ("GET", "/a/orchestrator/.well-known/agent-card.json"),
          ("GET", "/.well-known/jwks.json"),
          # D3-07 웹 위젯: 외부 사이트에 넣는 공개 채널(허용 오리진만 iframe — CSP frame-ancestors, 대화는 위젯 세션 토큰)
          ("GET", "/widget/{cid}.js"), ("GET", "/widget/{cid}"), ("GET", "/widget/{cid}/app.js"),
          ("POST", "/api/widget/{cid}/session"), ("POST", "/api/widget/{cid}/chat")}


def test_e1_10_unauthenticated_routes_are_allowlisted(client):
    """NFR-S5: 허용목록 밖의 모든 API 는 자격증명 없이 401."""
    leaks = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = re.sub(r"\{[^}]+\}", "1", route.path)
        for method in route.methods - {"HEAD", "OPTIONS"}:
            if (method, route.path) in PUBLIC:
                continue
            status = client.request(method, path).status_code
            if status != 401:
                leaks.append((method, route.path, status))
    assert leaks == []
