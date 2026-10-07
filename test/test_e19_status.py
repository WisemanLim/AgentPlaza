"""Epic 19 — 알림·상태 (D10-07, UI B03): 헬스 대시보드·상태 변화 알림·알림 센터·Slack/Telegram/메일 발송·사용량 리포트.

Slack·Telegram 은 가짜 ASGI 서버, 메일은 smtplib.SMTP 를 가짜로 바꿔 시험한다. 실 메일은 mailpit 오버레이로 라이브 시험.
"""
import asyncio
import io
import zipfile
from datetime import timedelta

import httpx
import pytest
from fastapi import FastAPI, Request

from app import db as appdb
from app.core.config import settings
from app.db import utcnow
from app.models import Agent, License
from app.orchestrator import executor
from app.services import notify, registry
from app.services import status as health
from helpers import auth, load_template_app, make_user


@pytest.fixture
def outbox(monkeypatch):
    """Slack 웹훅·Telegram Bot API 가짜 서버 + SMTP 가짜."""
    box: list = []
    app = FastAPI()

    @app.post("/services/T000/B000/XXX")
    async def slack(request: Request):
        box.append(("slack", (await request.json())["text"]))
        return {"ok": True}

    @app.post("/bot{token}/sendMessage")
    async def telegram(token: str, request: Request):
        body = await request.json()
        box.append(("telegram", token, body["chat_id"], body["text"]))
        return {"ok": True, "result": {"message_id": 1}}

    for base in ("https://hooks.slack.test", "https://tg.test"):
        monkeypatch.setitem(notify.TRANSPORTS, base, httpx.ASGITransport(app=app))
    monkeypatch.setattr(settings, "telegram_api_base", "https://tg.test")

    class FakeSMTP:
        def __init__(self, host, port, timeout=10):
            box.append(("smtp-connect", host, port))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context=None):
            box.append(("starttls",))

        def login(self, user, pw):
            box.append(("login", user))

        def send_message(self, msg):
            box.append(("email", msg["To"], msg["Subject"]))
    monkeypatch.setattr(notify.smtplib, "SMTP", FakeSMTP)
    return box


def run(coro):
    return asyncio.run(coro)


def test_e19_01_center_dedup_audience_read(client, sup_token):
    _, user = make_user(client, sup_token, "u19@example.test")
    with appdb.SessionLocal() as s:
        assert notify.emit(s, "x", "warn", "관리자 알림", resource="r1") is not None
        assert notify.emit(s, "x", "warn", "관리자 알림", resource="r1") is None  # 억제 시간 안 중복
        notify.emit(s, "y", "info", "개인 알림", audience="user:u19@example.test")
        notify.emit(s, "z", "info", "전체 공지", audience="all")
    h, hu = auth(sup_token), auth(user)
    assert [n["title"] for n in client.get("/api/notifications", headers=h).json()] == ["전체 공지", "관리자 알림"]
    assert [n["title"] for n in client.get("/api/notifications", headers=hu).json()] == ["전체 공지", "개인 알림"]
    assert client.get("/api/notifications/unread-count", headers=hu).json() == {"unread": 2}
    first = client.get("/api/notifications", headers=hu).json()[0]["id"]
    assert client.post("/api/notifications/read", json={"ids": [first]}, headers=hu).json() == {"marked": 1}
    assert client.get("/api/notifications/unread-count", headers=hu).json() == {"unread": 1}
    assert client.get("/api/notifications/unread-count", headers=h).json() == {"unread": 2}  # 읽음은 사람마다
    client.post("/api/notifications/read", json={}, headers=h)
    assert client.get("/api/notifications?unread=true", headers=h).json() == []
    assert client.get("/api/status", headers=hu).status_code == 403
    assert client.get("/api/notifications/channels", headers=hu).status_code == 403


def test_e19_02_status_transitions_and_agent_routing(client, sup_token, tmp_path, monkeypatch):
    """에이전트 /health 실패 → 장애 알림 + unhealthy(라우팅 제외) → 복구 알림 + healthy. 처음 보는 대상은 기록만."""
    app, manifest = load_template_app(tmp_path, "service", "svc19", monkeypatch, registry.agent_key("svc19"))
    executor.register_app("http://svc19.test", app)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")  # 결정적: 호스트 Ollama 대신 가짜
    executor.TRANSPORTS["http://ollama.test"] = httpx.MockTransport(lambda req: httpx.Response(200, json={"models": []}))
    try:
        with appdb.SessionLocal() as s:
            registry.register(s, manifest, endpoint="http://svc19.test", status="healthy")
            snap = run(health.snapshot(s))
            assert snap["components"]["db"]["ok"] and snap["agents"]["svc19"]["ok"]
            assert run(health.check(s))["changes"] == []  # 첫 기록
        executor.TRANSPORTS["http://svc19.test"] = httpx.MockTransport(lambda req: httpx.Response(503))  # 백엔드 장애
        with appdb.SessionLocal() as s:
            assert run(health.check(s))["changes"] == [("agents", "svc19", False)]
            assert s.get(Agent, "svc19").status == "unhealthy" and not registry.routable(s, "svc19")
        executor.TRANSPORTS["http://svc19.test"] = httpx.ASGITransport(app=app)
        with appdb.SessionLocal() as s:
            assert run(health.check(s))["changes"] == [("agents", "svc19", True)]
            assert s.get(Agent, "svc19").status == "healthy"
        kinds = [n["kind"] for n in client.get("/api/notifications", headers=auth(sup_token)).json()]
        assert kinds[:2] == ["agents_up", "agents_down"]
        assert client.get("/api/status", headers=auth(sup_token)).json()["agents"]["svc19"]["ok"] is True
    finally:
        executor.clear_apps()


def test_e19_03_channels_dispatch_by_severity(client, sup_token, outbox):
    h = auth(sup_token)
    r = client.put("/api/notifications/channels/slack", json={"config": {"enabled": True, "min_severity": "warn"},
                                                                "secret": "https://hooks.slack.test/services/T000/B000/XXX"}, headers=h)
    assert r.status_code == 200 and r.json()["has_secret"] is True
    client.put("/api/notifications/channels/telegram", json={"config": {"enabled": True, "min_severity": "error", "chat_id": "-100"},
                                                              "secret": "123:ABC"}, headers=h)
    client.put("/api/notifications/channels/email", json={"config": {"enabled": True, "min_severity": "warn", "host": "smtp.test",
                                                                       "port": 587, "from": "plaza@example.test", "to": ["ops@example.test"],
                                                                       "username": "plaza"}, "secret": "smtp-pass"}, headers=h)
    assert client.put("/api/notifications/channels/slack", json={"config": {}, "secret": "not-a-url"}, headers=h).status_code == 422
    assert client.put("/api/notifications/channels/email", json={"config": {"tls": "bogus"}}, headers=h).status_code == 422
    chans = client.get("/api/notifications/channels", headers=h).json()
    assert "123:ABC" not in str(chans) and "smtp-pass" not in str(chans) and chans["email"]["has_secret"] is True
    with appdb.SessionLocal() as s:
        notify.emit(s, "a", "info", "정보")
        notify.emit(s, "b", "warn", "경고")
        notify.emit(s, "c", "error", "오류", body="상세")
        assert run(notify.dispatch(s)) == 3 and run(notify.dispatch(s)) == 0  # 한 번만
    slack = [b[1] for b in outbox if b[0] == "slack"]
    tg = [b for b in outbox if b[0] == "telegram"]
    mail = [b for b in outbox if b[0] == "email"]
    assert len(slack) == 2 and "⚠️ [AgentPlaza] 경고" in slack[0] and "🚨 [AgentPlaza] 오류\n상세" in slack[1]
    assert tg == [("telegram", "123:ABC", "-100", "🚨 [AgentPlaza] 오류\n상세")]
    assert [m[2] for m in mail] == ["[AgentPlaza] 경고", "[AgentPlaza] 오류"] and ("login", "plaza") in outbox
    items = client.get("/api/notifications", headers=h).json()
    assert next(i for i in items if i["kind"] == "c")["deliveries"] == {"slack": "ok", "telegram": "ok", "email": "ok"}
    assert next(i for i in items if i["kind"] == "a")["deliveries"] == {}
    t = client.post("/api/notifications/channels/telegram/test", headers=h).json()
    assert t == {"channel": "telegram", "result": "ok"}


def test_e19_04_hooks_install_failure_budget_license(client, sup_token):
    h = auth(sup_token)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("README.md", "no manifest")
    client.post("/api/agents/upload", files=[("files", ("bad.zip", buf.getvalue(), "application/zip"))],
                data={"env": "{}", "force": "false"}, headers=h)
    with appdb.SessionLocal() as s:
        from app.llm import budget
        budget.note_forced(s)
        s.add(License(id="lic-exp", listing_id="paid-x", token="t", payload={}, issuer="pub-x", seats=1,
                      expires_at=utcnow() + timedelta(days=5), status="active", registered_by="t"))
        s.add(License(id="lic-far", listing_id="paid-y", token="t", payload={}, issuer="pub-x", seats=1,
                      expires_at=utcnow() + timedelta(days=60), status="active", registered_by="t"))
        s.commit()
        assert health.expiring(s) == 1 and health.expiring(s) == 0  # 하루 1회
    kinds = {n["kind"]: n for n in client.get("/api/notifications", headers=h).json()}
    assert kinds["install_failed"]["severity"] == "error" and kinds["budget_forced"]["severity"] == "warn"
    assert "paid-x" in kinds["license_expiring"]["title"]


def test_e19_05_usage_report_and_weekly(client, sup_token, outbox):
    h = auth(sup_token)
    client.put("/api/notifications/channels/slack", json={"config": {"enabled": True, "min_severity": "error"},
                                                            "secret": "https://hooks.slack.test/services/T000/B000/XXX"}, headers=h)
    r = client.get("/api/status/report?days=7", headers=h).json()
    assert r["days"] == 7 and "llm" in r and r["markdown"].startswith("# AgentPlaza 사용량 리포트") and r["settings"]["weekly"] is False
    sent = client.post("/api/status/report/send?days=7", headers=h).json()
    assert sent["deliveries"] == {"slack": "ok"}  # 리포트는 최소 심각도와 무관하게 발송
    assert "사용량 리포트" in [b for b in outbox if b[0] == "slack"][0][1]
    assert client.put("/api/status/report/settings", json={"weekly": True}, headers=h).json()["weekly"] is True
    with appdb.SessionLocal() as s:
        assert health.weekly_due(s) is False  # 방금 보냄
    _, admin = make_user(client, sup_token, "a19@example.test", role="admin")
    assert client.post("/api/status/report/send", headers=auth(admin)).status_code == 403
