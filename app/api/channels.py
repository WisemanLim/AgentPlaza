"""대화 채널·임베드 API (D3-07, UI C07).

관리(admin 이상): /api/channels CRUD · 비밀값(쓰기 전용) · 생성 비밀값 재발급.
외부(서명·토큰 인증, 틀리면 401): /api/channels/{id}/slack/events · /telegram/webhook · /kakao/skill
웹 위젯(공개 — 허용 오리진만 iframe 으로 띄움): /widget/{id}.js · /widget/{id} · /widget/{id}/app.js · /api/widget/{id}/session · /chat
"""
import asyncio
import html
import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Principal, require_admin
from app.core.security import create_token, decode_token
from app.db import SessionLocal, get_db
from app.models import Channel, ChannelThread
from app.services import audit
from app.services import channels as chans
from app.services import secrets as secret_store

router = APIRouter(prefix="/api/channels", tags=["channels"])
widget = APIRouter(tags=["channels"])
ASSETS = Path(__file__).resolve().parents[1] / "widget"
WIDGET_TTL = 120  # 분


class ChannelIn(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,39}$")
    kind: str = Field(pattern="^(web|slack|telegram|kakao)$")
    name: str = Field(min_length=1, max_length=120)
    config: dict = Field(default_factory=dict)


class ChannelPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None
    config: dict | None = None
    secrets: dict[str, str] | None = None  # 쓰기 전용(BOT_TOKEN·SIGNING_SECRET)


def _get(db: Session, cid: str) -> Channel:
    ch = db.get(Channel, cid)
    if ch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "채널 없음 / not found")
    return ch


def _err(exc: chans.ChannelError) -> HTTPException:
    return HTTPException(exc.code, str(exc))


# ---- 관리 ----

@router.get("")
def list_channels(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return [chans.out(db, c) for c in db.query(Channel).order_by(Channel.id)]


@router.post("", status_code=201)
def create_channel(body: ChannelIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        ch, generated = chans.create(db, cid=body.id, kind=body.kind, name=body.name, config=body.config, actor=p.actor)
    except chans.ChannelError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="channel.created", resource=f"channel:{ch.id}",
                 detail={"kind": ch.kind})
    return chans.out(db, ch) | {"generated": generated}  # 생성 비밀값은 이 응답에서 1회만


@router.patch("/{cid}")
def patch_channel(cid: str, body: ChannelPatch, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    ch = _get(db, cid)
    try:
        chans.update(db, ch, name=body.name, enabled=body.enabled, config=body.config, values=body.secrets, actor=p.actor)
    except chans.ChannelError as exc:
        raise _err(exc) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="channel.updated", resource=f"channel:{cid}",
                 detail={"enabled": ch.enabled, "secrets": sorted((body.secrets or {}).keys())})
    return chans.out(db, ch)


@router.post("/{cid}/rotate")
def rotate_channel(cid: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    ch = _get(db, cid)
    generated = chans.rotate(db, ch, p.actor)
    audit.record(db, actor=p.actor, actor_type=p.type, action="channel.rotated", resource=f"channel:{cid}")
    return {"generated": generated}


@router.delete("/{cid}")
def delete_channel(cid: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    ch = _get(db, cid)
    db.execute(delete(ChannelThread).where(ChannelThread.channel_id == cid))
    secret_store.delete(db, chans.scope(ch), commit=False)
    db.delete(ch)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="channel.deleted", resource=f"channel:{cid}")
    return {"deleted": cid}


# ---- 메신저 웹훅(서명·토큰 인증) ----

def _open(db: Session, cid: str, kind: str) -> Channel:
    ch = db.get(Channel, cid)
    if ch is None or ch.kind != kind or not ch.enabled:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "채널 인증 실패 / unauthorized")
    return ch


def _deny(db: Session, ch: Channel, why: str) -> HTTPException:
    audit.record(db, actor=f"channel:{ch.id}", actor_type="service", action="channel.rejected", outcome="denied",
                 resource=f"channel:{ch.id}", detail={"reason": why})
    return HTTPException(status.HTTP_401_UNAUTHORIZED, "채널 인증 실패 / unauthorized")


async def _slack_turn(cid: str, ext: str, text: str, channel: str, thread_ts: str) -> None:
    with SessionLocal() as db:
        ch = db.get(Channel, cid)
    reply = await chans.answer(ch, ext, text)
    with SessionLocal() as db:
        await chans.slack_reply(db, ch, channel, thread_ts, reply)


@router.post("/{cid}/slack/events")
async def slack_events(cid: str, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    ch = _open(db, cid, "slack")
    body = await request.body()
    if not chans.verify_slack(chans.secret(db, ch, "SIGNING_SECRET"), {k.lower(): v for k, v in request.headers.items()}, body):
        raise _deny(db, ch, "slack signature")
    ev = json.loads(body)
    if ev.get("type") == "url_verification":
        return {"challenge": ev.get("challenge")}
    if request.headers.get("x-slack-retry-num"):  # Slack 재전송 — 이미 처리 중
        return {"ok": True, "retry": True}
    e = ev.get("event") or {}
    if ev.get("type") == "event_callback" and e.get("type") in ("app_mention", "message") and e.get("text") \
            and not e.get("bot_id") and not e.get("subtype"):
        text = e["text"].split(">", 1)[1].strip() if e["text"].startswith("<@") and ">" in e["text"] else e["text"]
        root = e.get("thread_ts") or e["ts"]
        background.add_task(_slack_turn, cid, f"{e.get('channel')}:{root}", text, e.get("channel"), root)
    return {"ok": True}


async def _telegram_turn(cid: str, chat_id, message_id, text: str) -> None:
    with SessionLocal() as db:
        ch = db.get(Channel, cid)
    reply = await chans.answer(ch, f"tg:{chat_id}", text)
    with SessionLocal() as db:
        await chans.telegram_reply(db, ch, chat_id, message_id, reply)


@router.post("/{cid}/telegram/webhook")
async def telegram_webhook(cid: str, request: Request, background: BackgroundTasks, db: Session = Depends(get_db),
                           x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    ch = _open(db, cid, "telegram")
    if not chans.same(chans.secret(db, ch, "WEBHOOK_SECRET"), x_telegram_bot_api_secret_token):
        raise _deny(db, ch, "telegram secret token")
    upd = await request.json()
    msg = upd.get("message") or upd.get("edited_message") or {}
    if msg.get("text"):
        background.add_task(_telegram_turn, cid, msg["chat"]["id"], msg.get("message_id"), msg["text"])
    return {"ok": True}


async def _kakao_turn(cid: str, ext: str, text: str, callback: str) -> None:
    with SessionLocal() as db:
        ch = db.get(Channel, cid)
    await chans.kakao_reply(callback, await chans.answer(ch, ext, text))


@router.post("/{cid}/kakao/skill")
async def kakao_skill(cid: str, request: Request, background: BackgroundTasks, db: Session = Depends(get_db),
                      x_plaza_channel_token: str | None = Header(default=None)):
    """카카오 i 오픈빌더 스킬 서버. 콜백(useCallback)이 켜진 블록이면 바로 '처리 중' 을 돌려주고 답은 콜백으로."""
    ch = _open(db, cid, "kakao")
    if not chans.same(chans.secret(db, ch, "SKILL_TOKEN"), x_plaza_channel_token):
        raise _deny(db, ch, "kakao skill token")
    req = (await request.json()).get("userRequest") or {}
    text, user = req.get("utterance", "").strip(), (req.get("user") or {}).get("id", "anonymous")
    if not text:
        return chans.kakao_template("무엇을 도와드릴까요?")
    callback = req.get("callbackUrl")
    if callback and chans.kakao_callback_ok(callback):
        background.add_task(_kakao_turn, cid, f"kakao:{user}", text, callback)
        return {"version": "2.0", "useCallback": True, "data": {"text": "답변을 준비하고 있어요…"}}
    try:  # 콜백 없는 블록: 카카오 제한(5초) 안에 답한다
        return chans.kakao_template(await asyncio.wait_for(chans.answer(ch, f"kakao:{user}", text), timeout=4.5))
    except TimeoutError:
        return chans.kakao_template("답변이 길어지고 있어요. 잠시 후 다시 물어봐 주세요.")


# ---- 웹 위젯(공개) ----

def _web(db: Session, cid: str) -> Channel:
    ch = db.get(Channel, cid)
    if ch is None or ch.kind != "web" or not ch.enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "위젯 없음 / not found")
    return ch


def _fill(name: str, ch: Channel, *, js: bool) -> str:
    title = ch.name
    greeting = (ch.config or {}).get("greeting") or "안녕하세요! 무엇을 도와드릴까요?"
    enc = (lambda v: json.dumps(v, ensure_ascii=False)[1:-1]) if js else html.escape  # noqa: E731
    return ((ASSETS / name).read_text(encoding="utf-8").replace("__BASE__", enc(settings.public_base_url.rstrip("/")))
            .replace("__ID__", ch.id).replace("__TITLE__", enc(title)).replace("__GREETING__", enc(greeting)))


@widget.get("/widget/{cid}.js")
def widget_loader(cid: str, db: Session = Depends(get_db)):
    return Response(_fill("loader.js", _web(db, cid), js=True), media_type="application/javascript",
                    headers={"Cache-Control": "no-cache"})


@widget.get("/widget/{cid}")
def widget_page(cid: str, db: Session = Depends(get_db)):
    ch = _web(db, cid)
    origins = " ".join((ch.config or {}).get("allowed_origins") or []) or "'none'"
    csp = ("default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; "
           f"img-src 'self' data:; frame-ancestors {origins}")
    return Response(_fill("page.html", ch, js=False), media_type="text/html",
                    headers={"Content-Security-Policy": csp, "Cache-Control": "no-cache"})


@widget.get("/widget/{cid}/app.js")
def widget_app(cid: str, db: Session = Depends(get_db)):
    return Response(_fill("app.js", _web(db, cid), js=True), media_type="application/javascript",
                    headers={"Cache-Control": "no-cache"})


class SessionIn(BaseModel):
    visitor: str | None = Field(default=None, pattern=r"^v-[0-9a-f]{20}$")


class WidgetChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@widget.post("/api/widget/{cid}/session")
def widget_session(cid: str, body: SessionIn, db: Session = Depends(get_db)):
    """방문자 세션 토큰(aud=widget:<id>). 방문자 id 를 다시 주면 같은 대화를 잇는다."""
    from app.db import utcnow
    ch = _web(db, cid)
    visitor = body.visitor or chans.visitor_id()
    token = create_token(visitor, "user", typ="widget", ttl_minutes=WIDGET_TTL, audience=f"widget:{ch.id}")
    return {"token": token, "visitor": visitor, "exp": int(utcnow().timestamp()) + WIDGET_TTL * 60}


@widget.post("/api/widget/{cid}/chat")
async def widget_chat(cid: str, body: WidgetChatIn, authorization: str | None = Header(default=None),
                      db: Session = Depends(get_db)):
    ch = _web(db, cid)
    try:
        claims = decode_token((authorization or "").removeprefix("Bearer ").strip(), audience=f"widget:{ch.id}")
    except Exception:  # noqa: BLE001 — 만료·서명·대상 오류 모두 401
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "위젯 세션 필요 / widget session required") from None
    if claims.get("typ") != "widget":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "위젯 세션 필요 / widget session required")
    return StreamingResponse(chans.stream(ch, claims["sub"], body.message), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
