"""대화 채널·임베드 (D3-07, UI C07): 웹 위젯 · Slack · Telegram · 카카오 i 오픈빌더 → AI Assistant.

- 채널 주체 = "channel:<채널>:<외부 대화>"(역할 user). 외부 대화(슬랙 스레드·텔레그램 채팅·카카오 사용자·위젯 방문자)마다
  플랫폼 세션 하나(channel_threads). 배치 범위가 있는 에이전트는 채널 주체에게 보이지 않는다(조직 구성원이 아님).
- 인증: Slack = 서명(v0, HMAC-SHA256, 5분) · Telegram = X-Telegram-Bot-Api-Secret-Token · 카카오 = X-Plaza-Channel-Token
  · 웹 위젯 = CSP frame-ancestors(허용 오리진) + 위젯 세션 토큰(aud=widget:<id>, 2시간). 틀리면 401.
- 승인 필요 작업은 채널에서 승인할 수 없다 — 콘솔 승인함 안내를 덧붙인다.
"""
import hashlib
import hmac
import json
import re
import secrets
import time
import uuid
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal, utcnow
from app.models import Channel, ChannelThread
from app.services import secrets as secret_store

KINDS = ("web", "slack", "telegram", "kakao")
ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
SECRETS = {"web": (), "slack": ("SIGNING_SECRET", "BOT_TOKEN"), "telegram": ("BOT_TOKEN", "WEBHOOK_SECRET"),
           "kakao": ("SKILL_TOKEN",)}
GENERATED = {"telegram": "WEBHOOK_SECRET", "kakao": "SKILL_TOKEN"}  # 플랫폼이 만들어 1회 보여 준다
APPROVAL_NOTE = "\n\n(승인이 필요한 작업입니다 — 콘솔 승인함에서 처리해 주세요 / approval required in the console)"
TRANSPORTS: dict[str, httpx.AsyncBaseTransport] = {}  # 시험용: 기준 URL → 가짜 서버


class ChannelError(ValueError):
    def __init__(self, msg: str, code: int = 422):
        super().__init__(msg)
        self.code = code


def scope(ch: Channel) -> str:
    return f"channel:{ch.id}"


def secret(db: Session, ch: Channel, name: str) -> str | None:
    return secret_store.get(db, scope(ch), name)


def _check_config(kind: str, cfg: dict) -> dict:
    allowed = {"agent_scope", "data_class", "allowed_origins", "greeting"}
    bad = [k for k in cfg if k not in allowed]
    if bad:
        raise ChannelError(f"알 수 없는 설정: {bad}")
    if cfg.get("data_class", "L2") not in ("L0", "L1", "L2", "L3"):
        raise ChannelError("data_class ∈ L0..L3")
    origins = cfg.get("allowed_origins", [])
    if kind == "web":
        if not isinstance(origins, list) or not all(re.fullmatch(r"https?://[A-Za-z0-9.\-]+(:\d+)?", o) for o in origins):
            raise ChannelError("allowed_origins = ['https://example.com', …] (스킴+호스트[+포트])")
    return cfg


def create(db: Session, *, cid: str, kind: str, name: str, config: dict, actor: str) -> tuple[Channel, dict]:
    if not ID.match(cid):
        raise ChannelError("id 는 소문자·숫자·하이픈 2~40자")
    if kind not in KINDS:
        raise ChannelError(f"kind ∈ {KINDS}")
    if db.get(Channel, cid) is not None:
        raise ChannelError("이미 있는 채널 / duplicate", 409)
    ch = Channel(id=cid, kind=kind, name=name, config=_check_config(kind, config), created_by=actor)
    db.add(ch)
    db.commit()
    return ch, rotate(db, ch, actor)


def rotate(db: Session, ch: Channel, actor: str) -> dict:
    """플랫폼이 만드는 비밀값(텔레그램 웹훅 비밀·카카오 스킬 토큰)을 새로 만든다 — 응답에서 1회만 보여 준다."""
    name = GENERATED.get(ch.kind)
    if not name:
        return {}
    value = secrets.token_urlsafe(24)
    secret_store.put(db, scope(ch), name, value, actor)
    return {name: value}


def update(db: Session, ch: Channel, *, name: str | None, enabled: bool | None, config: dict | None,
           values: dict | None, actor: str) -> Channel:
    if name is not None:
        ch.name = name
    if enabled is not None:
        ch.enabled = enabled
    if config is not None:
        ch.config = _check_config(ch.kind, {**(ch.config or {}), **config})
    for k, v in (values or {}).items():
        if k not in SECRETS[ch.kind] or k in GENERATED.values():
            raise ChannelError(f"{ch.kind} 채널이 받는 비밀값: {[s for s in SECRETS[ch.kind] if s not in GENERATED.values()]}")
        if v:
            secret_store.put(db, scope(ch), k, v, actor, commit=False)
    db.commit()
    return ch


def out(db: Session, ch: Channel) -> dict:
    base = settings.public_base_url.rstrip("/")
    have = secret_store.names(db, scope(ch))
    endpoint = {"slack": f"{base}/api/channels/{ch.id}/slack/events",
                "telegram": f"{base}/api/channels/{ch.id}/telegram/webhook",
                "kakao": f"{base}/api/channels/{ch.id}/kakao/skill"}.get(ch.kind)
    return {"id": ch.id, "kind": ch.kind, "name": ch.name, "enabled": ch.enabled, "config": ch.config,
            "secrets": {k: k in have for k in SECRETS[ch.kind]}, "endpoint": endpoint,
            "embed": f'<script src="{base}/widget/{ch.id}.js" async></script>' if ch.kind == "web" else None,
            "threads": len(list(db.execute(select(ChannelThread.id).where(ChannelThread.channel_id == ch.id)))),
            "created_by": ch.created_by, "created_at": ch.created_at}


# ---- 서명·토큰 검증 ----

def verify_slack(signing_secret: str | None, headers: dict, body: bytes) -> bool:
    ts, sig = headers.get("x-slack-request-timestamp", ""), headers.get("x-slack-signature", "")
    if not signing_secret or not ts.isdigit() or abs(time.time() - int(ts)) > 300:
        return False
    want = "v0=" + hmac.new(signing_secret.encode(), f"v0:{ts}:".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, sig)


def same(expected: str | None, got: str | None) -> bool:
    return bool(expected) and bool(got) and hmac.compare_digest(expected, got)


# ---- 대화 ----

def thread(db: Session, ch: Channel, external_id: str) -> ChannelThread:
    t = db.execute(select(ChannelThread).where(ChannelThread.channel_id == ch.id,
                                               ChannelThread.external_id == external_id)).scalar_one_or_none()
    if t is None:
        t = ChannelThread(channel_id=ch.id, external_id=external_id)
        db.add(t)
        db.commit()
    return t


def principal_of(ch: Channel, external_id: str) -> str:
    return f"channel:{ch.id}:{external_id}"[:255]


async def stream(ch: Channel, external_id: str, text: str):
    """채널 대화 한 턴의 SSE 프레임(웹 위젯은 그대로 흘리고, 메신저는 answer() 로 모은다)."""
    from app.assistant import chat
    with SessionLocal() as db:
        t = thread(db, ch, external_id)
        session_id = t.session_id
    async for frame in chat.run(principal=principal_of(ch, external_id), role="user", message=text, session_id=session_id,
                                agent_scope=(ch.config or {}).get("agent_scope"),
                                data_class=(ch.config or {}).get("data_class", "L2")):
        for line in frame.splitlines():
            if line.startswith("data: "):
                ev = json.loads(line[6:])
                if ev.get("type") == "CUSTOM" and ev.get("name") == "session":
                    with SessionLocal() as db:
                        t = thread(db, ch, external_id)
                        t.session_id, t.updated_at = ev["value"]["id"], utcnow()
                        db.commit()
        yield frame


async def answer(ch: Channel, external_id: str, text: str) -> str:
    parts, approval, error = [], False, None
    async for frame in stream(ch, external_id, text):
        for line in frame.splitlines():
            if not line.startswith("data: "):
                continue
            ev = json.loads(line[6:])
            if ev["type"] == "TEXT_MESSAGE_CONTENT":
                parts.append(ev["delta"])
            elif ev["type"] == "CUSTOM" and ev.get("name") == "approval_required":
                approval = True
            elif ev["type"] == "RUN_ERROR":
                error = ev.get("message")
    reply = "".join(parts).strip() or (f"응답을 만들지 못했습니다 / no answer ({error})" if error else "…")
    return reply + (APPROVAL_NOTE if approval else "")


# ---- 메신저 발송 ----

def _client(url: str) -> httpx.AsyncClient:
    u = urlparse(url)
    return httpx.AsyncClient(timeout=15, transport=TRANSPORTS.get(f"{u.scheme}://{u.netloc}"))


async def slack_reply(db: Session, ch: Channel, channel: str, thread_ts: str, text: str) -> int:
    base = settings.slack_api_base.rstrip("/")
    async with _client(base) as c:
        r = await c.post(f"{base}/chat.postMessage", headers={"Authorization": f"Bearer {secret(db, ch, 'BOT_TOKEN')}"},
                         json={"channel": channel, "text": text[:3900], "thread_ts": thread_ts})
    return r.status_code


async def telegram_reply(db: Session, ch: Channel, chat_id: int | str, reply_to: int | None, text: str) -> int:
    base = settings.telegram_api_base.rstrip("/")
    async with _client(base) as c:
        r = await c.post(f"{base}/bot{secret(db, ch, 'BOT_TOKEN')}/sendMessage",
                         json={"chat_id": chat_id, "text": text[:4000],
                               **({"reply_parameters": {"message_id": reply_to}} if reply_to else {})})
    return r.status_code


def kakao_template(text: str) -> dict:
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": text[:1000]}}]}}


def kakao_callback_ok(url: str) -> bool:
    """콜백 주소는 카카오 도메인(https)만 — 요청에 담긴 URL 로 임의 호출하지 않는다(SSRF)."""
    u = urlparse(url)
    return u.scheme == "https" and bool(u.hostname) and (u.hostname == "kakao.com" or u.hostname.endswith(".kakao.com"))


async def kakao_reply(url: str, text: str) -> int:
    async with _client(url) as c:
        r = await c.post(url, json=kakao_template(text))
    return r.status_code


def visitor_id() -> str:
    return "v-" + uuid.uuid4().hex[:20]
