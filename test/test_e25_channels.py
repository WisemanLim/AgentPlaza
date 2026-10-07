"""Epic 25 — 채널·임베드 (D3-07, UI C07): 웹 위젯 · Slack · Telegram · 카카오 i 오픈빌더 → AI Assistant.

Slack·Telegram·카카오 콜백은 가짜 ASGI 서버, LLM 은 mock/echo. 서명·토큰이 틀리면 401.
"""
import hashlib
import hmac
import json
import time

import httpx
import pytest
from fastapi import FastAPI, Request

from app import db as appdb
from app.core.config import settings
from app.llm.providers import ChatResult, MockProvider
from app.models import ChannelThread, ChatSession, LlmRoute, Message
from app.orchestrator import executor
from app.services import channels as chans
from app.services import registry
from helpers import auth, load_template_app, make_user


@pytest.fixture
def world(client, monkeypatch):
    """LLM = mock/echo, 메신저 API 가짜 서버(보낸 것을 box 에)."""
    with appdb.SessionLocal() as s:
        for alias in ("plaza/chat", "plaza/orchestrator"):
            s.merge(LlmRoute(alias=alias, targets=["mock/echo"]))
        s.commit()
    box: list = []
    api = FastAPI()

    @api.post("/api/chat.postMessage")
    async def slack(request: Request):
        box.append(("slack", request.headers.get("authorization"), await request.json()))
        return {"ok": True}

    @api.post("/bot{token}/sendMessage")
    async def tg(token: str, request: Request):
        box.append(("telegram", token, await request.json()))
        return {"ok": True}

    @api.post("/v1/skills/callback/{cid}")
    async def kakao_cb(cid: str, request: Request):
        box.append(("kakao-callback", cid, await request.json()))
        return {"status": "SUCCESS"}

    for base in ("https://slack.test", "https://tg.test", "https://bot-api.kakao.com"):
        monkeypatch.setitem(chans.TRANSPORTS, base, httpx.ASGITransport(app=api))
    monkeypatch.setattr(settings, "slack_api_base", "https://slack.test/api")
    monkeypatch.setattr(settings, "telegram_api_base", "https://tg.test")
    return box


def create(client, token, cid, kind, config=None):
    r = client.post("/api/channels", json={"id": cid, "kind": kind, "name": cid.title(), "config": config or {}},
                    headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def slack_post(client, cid, payload, secret="slack-signing", ts=None, extra=None):
    body = json.dumps(payload).encode()
    t = str(ts or int(time.time()))
    sig = "v0=" + hmac.new(secret.encode(), f"v0:{t}:".encode() + body, hashlib.sha256).hexdigest()
    return client.post(f"/api/channels/{cid}/slack/events", content=body,
                       headers={"x-slack-request-timestamp": t, "x-slack-signature": sig,
                                "content-type": "application/json", **(extra or {})})


def test_e25_01_channel_admin_secrets_rbac(client, sup_token, world):
    h = auth(sup_token)
    _, user = make_user(client, sup_token, "c25@example.test")
    assert client.get("/api/channels", headers=auth(user)).status_code == 403
    tg = create(client, sup_token, "tg-help", "telegram")
    assert set(tg["generated"]) == {"WEBHOOK_SECRET"} and tg["secrets"] == {"BOT_TOKEN": False, "WEBHOOK_SECRET": True}
    assert tg["endpoint"].endswith("/api/channels/tg-help/telegram/webhook")
    assert client.patch("/api/channels/tg-help", json={"secrets": {"WEBHOOK_SECRET": "x"}}, headers=h).status_code == 422
    r = client.patch("/api/channels/tg-help", json={"secrets": {"BOT_TOKEN": "123:abc"}}, headers=h).json()
    assert r["secrets"]["BOT_TOKEN"] is True and "123:abc" not in json.dumps(client.get("/api/channels", headers=h).json())
    assert client.post("/api/channels", json={"id": "w", "kind": "web", "name": "W", "config": {}}, headers=h).status_code == 422
    assert client.post("/api/channels", json={"id": "web1", "kind": "web", "name": "W",
                                              "config": {"allowed_origins": ["javascript:alert(1)"]}}, headers=h).status_code == 422
    assert create(client, sup_token, "web1", "web", {"allowed_origins": ["https://shop.example"]})["embed"].startswith("<script")
    new = client.post("/api/channels/tg-help/rotate", headers=h).json()["generated"]["WEBHOOK_SECRET"]
    assert new != tg["generated"]["WEBHOOK_SECRET"]
    assert client.delete("/api/channels/tg-help", headers=h).json() == {"deleted": "tg-help"}


def test_e25_02_slack_events_signature_thread_session(client, sup_token, world):
    h = auth(sup_token)
    create(client, sup_token, "slk", "slack")
    client.patch("/api/channels/slk", json={"secrets": {"SIGNING_SECRET": "slack-signing", "BOT_TOKEN": "xoxb-1"}}, headers=h)
    assert slack_post(client, "slk", {"type": "url_verification", "challenge": "abc"}).json() == {"challenge": "abc"}
    assert slack_post(client, "slk", {"type": "url_verification", "challenge": "abc"}, secret="wrong").status_code == 401
    assert slack_post(client, "slk", {"type": "url_verification"}, ts=int(time.time()) - 3600).status_code == 401
    ev = {"type": "event_callback", "event": {"type": "app_mention", "text": "<@U0BOT> 안녕 슬랙", "channel": "C1", "ts": "111.1"}}
    assert slack_post(client, "slk", ev).json() == {"ok": True}
    who, authz, body = world[0]
    assert who == "slack" and authz == "Bearer xoxb-1" and body["thread_ts"] == "111.1" and body["text"] == "echo: 안녕 슬랙"
    reply = {"type": "event_callback", "event": {"type": "message", "text": "두번째", "channel": "C1", "ts": "112.2",
                                                 "thread_ts": "111.1"}}
    slack_post(client, "slk", reply)
    assert slack_post(client, "slk", reply, extra={"x-slack-retry-num": "1"}).json()["retry"] is True
    slack_post(client, "slk", {"type": "event_callback", "event": {"type": "message", "text": "봇", "channel": "C1",
                                                                     "ts": "113", "bot_id": "B1"}})
    assert len(world) == 2  # 재전송·봇 메시지는 무시
    with appdb.SessionLocal() as s:
        t = s.query(ChannelThread).one()
        assert t.external_id == "C1:111.1" and s.get(ChatSession, t.session_id).owner == "channel:slk:C1:111.1"
        assert s.query(Message).filter(Message.session_id == t.session_id).count() == 4  # 같은 스레드 = 같은 세션
    assert client.get("/api/audit?action=channel.rejected", headers=h).json()


def test_e25_03_telegram_secret_token(client, sup_token, world):
    h = auth(sup_token)
    secret = create(client, sup_token, "tg", "telegram")["generated"]["WEBHOOK_SECRET"]
    client.patch("/api/channels/tg", json={"secrets": {"BOT_TOKEN": "123:abc"}}, headers=h)
    upd = {"update_id": 1, "message": {"message_id": 7, "chat": {"id": 42}, "from": {"id": 9}, "text": "텔레그램 질문"}}
    assert client.post("/api/channels/tg/telegram/webhook", json=upd,
                       headers={"x-telegram-bot-api-secret-token": "nope"}).status_code == 401
    assert client.post("/api/channels/tg/telegram/webhook", json=upd,
                       headers={"x-telegram-bot-api-secret-token": secret}).json() == {"ok": True}
    assert world == [("telegram", "123:abc", {"chat_id": 42, "text": "echo: 텔레그램 질문",
                                               "reply_parameters": {"message_id": 7}})]
    client.patch("/api/channels/tg", json={"enabled": False}, headers=h)
    assert client.post("/api/channels/tg/telegram/webhook", json=upd,
                       headers={"x-telegram-bot-api-secret-token": secret}).status_code == 401


def test_e25_04_kakao_skill_sync_callback_and_ssrf(client, sup_token, world):
    token = create(client, sup_token, "kk", "kakao")["generated"]["SKILL_TOKEN"]
    hdr = {"x-plaza-channel-token": token}

    def req(text, callback=None):
        return {"userRequest": {"utterance": text, "user": {"id": "kuser1"}, **({"callbackUrl": callback} if callback else {})}}
    assert client.post("/api/channels/kk/kakao/skill", json=req("hi"), headers={"x-plaza-channel-token": "x"}).status_code == 401
    sync = client.post("/api/channels/kk/kakao/skill", json=req("카카오 질문"), headers=hdr).json()
    assert sync == {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "echo: 카카오 질문"}}]}}
    cb = client.post("/api/channels/kk/kakao/skill", json=req("콜백 질문", "https://bot-api.kakao.com/v1/skills/callback/abc"),
                     headers=hdr).json()
    assert cb["useCallback"] is True
    assert world[-1] == ("kakao-callback", "abc", {"version": "2.0", "template": {"outputs": [
        {"simpleText": {"text": "echo: 콜백 질문"}}]}})
    evil = client.post("/api/channels/kk/kakao/skill", json=req("외부", "https://evil.example/steal"), headers=hdr).json()
    assert "template" in evil and len([b for b in world if b[0] == "kakao-callback"]) == 1  # 카카오 도메인만 콜백


def test_e25_05_web_widget_csp_session_chat(client, sup_token, world):
    h = auth(sup_token)
    create(client, sup_token, "site", "web", {"allowed_origins": ["https://shop.example"], "greeting": "<b>안녕</b>"})
    client.patch("/api/channels/site", json={"name": 'Shop "help" </script>'}, headers=h)
    js = client.get("/widget/site.js").text
    assert 'base = "http://gw.test"' in js and 'title = "Shop \\"help\\" </script>"' in js  # JS 문자열로 이스케이프
    page = client.get("/widget/site")
    assert "frame-ancestors https://shop.example" in page.headers["content-security-policy"]
    assert "&lt;b&gt;안녕&lt;/b&gt;" in page.text and "script-src 'self'" in page.headers["content-security-policy"]
    assert client.get("/widget/site/app.js").status_code == 200
    s1 = client.post("/api/widget/site/session", json={}).json()
    assert s1["visitor"].startswith("v-")
    assert client.post("/api/widget/site/chat", json={"message": "x"}).status_code == 401
    res = client.post("/api/widget/site/chat", json={"message": "위젯 질문"}, headers={"authorization": f"Bearer {s1['token']}"})
    events = [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith("data: ")]
    assert "".join(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT") == "echo: 위젯 질문"
    again = client.post("/api/widget/site/session", json={"visitor": s1["visitor"]}).json()
    assert again["visitor"] == s1["visitor"]  # 같은 방문자 = 같은 대화
    assert client.get("/api/sessions", headers={"authorization": f"Bearer {s1['token']}"}).status_code == 401  # 플랫폼 주체 아님
    create(client, sup_token, "other", "web", {"allowed_origins": []})
    assert "frame-ancestors 'none'" in client.get("/widget/other").headers["content-security-policy"]
    assert client.post("/api/widget/other/chat", json={"message": "x"},
                       headers={"authorization": f"Bearer {s1['token']}"}).status_code == 401  # 다른 위젯의 토큰
    client.patch("/api/channels/site", json={"enabled": False}, headers=h)
    assert client.get("/widget/site.js").status_code == 404


def test_e25_06_approval_needed_points_to_console(client, sup_token, world, tmp_path, monkeypatch):
    """승인 필요 작업은 채널에서 처리하지 않고 콘솔 승인함으로 안내한다."""
    with appdb.SessionLocal() as s:
        app, manifest = load_template_app(tmp_path, "hitl", "ops", monkeypatch, registry.agent_key("ops"))
        executor.register_app("http://ops.test", app)
        registry.register(s, manifest, endpoint="http://ops.test", status="healthy")
    plan = {"steps": [{"id": "s1", "agent": "ops", "capability": "execute_action", "args": {"action": "deploy"}}]}
    default = MockProvider.responder
    monkeypatch.setattr(MockProvider, "responder", staticmethod(
        lambda model, req: ChatResult(content=json.dumps(plan), model=model)
        if req.messages[0]["content"].startswith("You are the AgentPlaza orchestrator") else default(model, req)))
    try:
        token = create(client, sup_token, "kk2", "kakao", {"agent_scope": "ops"})["generated"]["SKILL_TOKEN"]
        r = client.post("/api/channels/kk2/kakao/skill", json={"userRequest": {"utterance": "배포해줘", "user": {"id": "u"}}},
                        headers={"x-plaza-channel-token": token}).json()
        assert chans.APPROVAL_NOTE.strip() in r["template"]["outputs"][0]["simpleText"]["text"]
        approvals = client.get("/api/approvals", headers=auth(sup_token)).json()
        assert approvals and approvals[0]["requester"] == "channel:kk2:kakao:u"
    finally:
        executor.clear_apps()


def test_e25_07_channel_counts_as_one_seat(client, sup_token, world):
    """유료 에이전트 좌석: 채널은 방문자·사용자 수와 관계없이 좌석 하나(공개 위젯이 좌석을 소진하지 않게)."""
    from app.market import licensing
    from app.models import Agent
    with appdb.SessionLocal() as s:
        s.merge(Agent(id="paid-a", name="Paid", type="service", version="1.0.0", status="healthy", manifest={}))
        s.commit()
        licensing.register(s, licensing.issue(s, listing="paid-a", publisher="p", versions="*", seats=2), "paid-a", "t")
        assert licensing.check_use(s, "paid-a", "channel:site:v-1", claim=True) is None
        assert licensing.check_use(s, "paid-a", "channel:site:v-2", claim=True) is None  # 같은 좌석
        assert licensing.check_use(s, "paid-a", "alice@example.test", claim=True) is None  # 남은 좌석 1
        assert "좌석 초과" in licensing.check_use(s, "paid-a", "bob@example.test", claim=True)
