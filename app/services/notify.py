"""알림 (D10-07, UI B03): 알림 센터 + 외부 발송(Slack·Telegram·메일).

- emit(): 알림을 남긴다. 같은 dedup 키(종류+대상)는 억제 시간 안에 다시 만들지 않는다.
- audience = admins(admin 이상) | all | user:<actor>. 읽음은 사람마다(notification_reads).
- dispatch(): 아직 발송하지 않은 알림을 채널별 최소 심각도에 맞춰 보낸다(상태 루프가 주기적으로 호출).
  Slack = Incoming Webhook URL, Telegram = Bot API sendMessage, 메일 = SMTP. 비밀값(웹훅 URL·봇 토큰·SMTP 암호)은 시크릿 저장소.
"""
import asyncio
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.models import ROLE_RANK, Notification, NotificationRead
from app.services import secrets as secret_store
from app.services import sysconfig

KEY = "notify.channels"
SEVERITY = {"info": 0, "warn": 1, "error": 2}
DEFAULT = {"slack": {"enabled": False, "min_severity": "warn"},
           "telegram": {"enabled": False, "min_severity": "warn", "chat_id": ""},
           "email": {"enabled": False, "min_severity": "error", "host": "", "port": 587, "tls": "starttls",
                     "from": "", "to": [], "username": ""}}
SECRET = {"slack": "SLACK_WEBHOOK_URL", "telegram": "TELEGRAM_BOT_TOKEN", "email": "SMTP_PASSWORD"}
TRANSPORTS: dict[str, httpx.AsyncBaseTransport] = {}  # 시험용: 기준 URL → 가짜 서버


class NotifyError(ValueError):
    pass


# ---- 알림 센터 ----

def emit(db: Session, kind: str, severity: str, title: str, body: str = "", *, resource: str | None = None,
         audience: str = "admins", dedup_minutes: int = 30, commit: bool = True) -> Notification | None:
    key = f"{kind}:{resource or ''}:{audience}"
    since = utcnow() - timedelta(minutes=dedup_minutes)
    if dedup_minutes and db.execute(select(Notification.id).where(Notification.dedup_key == key,
                                                                  Notification.created_at >= since)).first():
        return None
    n = Notification(kind=kind, severity=severity if severity in SEVERITY else "info", title=title[:200], body=body,
                     resource=resource, audience=audience, dedup_key=key)
    db.add(n)
    if commit:
        db.commit()
    else:
        db.flush()
    return n


def _visible(actor: str, role: str):
    aud = ["all", f"user:{actor}"] + (["admins"] if ROLE_RANK.get(role, 0) >= ROLE_RANK["admin"] else [])
    return Notification.audience.in_(aud)


def listing(db: Session, actor: str, role: str, *, unread: bool = False, limit: int = 100) -> list[dict]:
    read = select(NotificationRead.notification_id).where(NotificationRead.reader == actor)
    q = select(Notification).where(_visible(actor, role)).order_by(Notification.created_at.desc(),
                                                                   Notification.id.desc()).limit(limit)
    if unread:
        q = q.where(Notification.id.not_in(read))
    done = set(db.execute(read).scalars())
    return [{"id": n.id, "kind": n.kind, "severity": n.severity, "title": n.title, "body": n.body,
             "resource": n.resource, "created_at": n.created_at, "read": n.id in done,
             "deliveries": n.deliveries} for n in db.execute(q).scalars()]


def unread_count(db: Session, actor: str, role: str) -> int:
    read = select(NotificationRead.notification_id).where(NotificationRead.reader == actor)
    return db.scalar(select(func.count()).select_from(Notification)
                     .where(_visible(actor, role), Notification.id.not_in(read))) or 0


def mark_read(db: Session, actor: str, role: str, ids: list[int] | None) -> int:
    q = select(Notification.id).where(_visible(actor, role))
    if ids:
        q = q.where(Notification.id.in_(ids))
    done = set(db.execute(select(NotificationRead.notification_id).where(NotificationRead.reader == actor)).scalars())
    new = [i for i in db.execute(q).scalars() if i not in done]
    db.add_all([NotificationRead(notification_id=i, reader=actor) for i in new])
    db.commit()
    return len(new)


# ---- 발송 채널 ----

def channels(db: Session) -> dict:
    cur = sysconfig.blob(db, KEY)
    out = {k: {**v, **cur.get(k, {})} for k, v in DEFAULT.items()}
    have = secret_store.names(db, "notify")
    for k, name in SECRET.items():
        out[k]["has_secret"] = name in have
    return out


def set_channel(db: Session, name: str, cfg: dict, secret: str | None, actor: str) -> dict:
    if name not in DEFAULT:
        raise NotifyError(f"채널 ∈ {list(DEFAULT)}")
    allowed = set(DEFAULT[name]) - {"has_secret"}
    bad = [k for k in cfg if k not in allowed]
    if bad:
        raise NotifyError(f"알 수 없는 설정: {bad}")
    if cfg.get("min_severity", "info") not in SEVERITY:
        raise NotifyError("min_severity ∈ info | warn | error")
    if name == "email" and cfg.get("tls", "starttls") not in ("starttls", "ssl", "none"):
        raise NotifyError("tls ∈ starttls | ssl | none")
    cur = sysconfig.blob(db, KEY)
    cur[name] = {**cur.get(name, {}), **cfg}
    sysconfig.put_blob(db, KEY, cur)
    if secret:
        if name == "slack" and not secret.startswith(("https://", "http://")):
            raise NotifyError("Slack Incoming Webhook URL 이어야 함")
        secret_store.put(db, "notify", SECRET[name], secret, actor)
    return channels(db)[name]


def _client(base: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=10, transport=TRANSPORTS.get(base.rstrip("/")))


def _text(n: Notification) -> str:
    mark = {"info": "ℹ️", "warn": "⚠️", "error": "🚨"}.get(n.severity, "")
    return f"{mark} [AgentPlaza] {n.title}" + (f"\n{n.body}" if n.body else "")


async def _slack(db: Session, n: Notification) -> str:
    url = secret_store.get(db, "notify", SECRET["slack"])
    if not url:
        return "no webhook"
    base = "/".join(url.split("/")[:3])
    async with _client(base) as c:
        r = await c.post(url, json={"text": _text(n)})
    return "ok" if r.status_code < 300 else f"HTTP {r.status_code}"


async def _telegram(db: Session, n: Notification, chat_id: str) -> str:
    token = secret_store.get(db, "notify", SECRET["telegram"])
    if not token or not chat_id:
        return "no token/chat_id"
    base = settings.telegram_api_base.rstrip("/")
    async with _client(base) as c:
        r = await c.post(f"{base}/bot{token}/sendMessage", json={"chat_id": chat_id, "text": _text(n)[:4000]})
    return "ok" if r.status_code < 300 and r.json().get("ok", True) else f"HTTP {r.status_code}"


def _email(db: Session, n: Notification, cfg: dict) -> str:
    if not cfg.get("host") or not cfg.get("from") or not cfg.get("to"):
        return "no host/from/to"
    msg = EmailMessage()
    msg["Subject"] = f"[AgentPlaza] {n.title}"
    msg["From"], msg["To"] = cfg["from"], ", ".join(cfg["to"])
    msg.set_content(_text(n))
    tls = cfg.get("tls", "starttls")
    cls = smtplib.SMTP_SSL if tls == "ssl" else smtplib.SMTP
    with cls(cfg["host"], int(cfg.get("port") or 587), timeout=10) as s:
        if tls == "starttls":
            s.starttls(context=ssl.create_default_context())
        pw = secret_store.get(db, "notify", SECRET["email"])
        if cfg.get("username") and pw:
            s.login(cfg["username"], pw)
        s.send_message(msg)
    return "ok"


async def send(db: Session, n: Notification, only: str | None = None) -> dict:
    cfg = channels(db)
    out = {}
    for name in ("slack", "telegram", "email"):
        c = cfg[name]
        if only and name != only:
            continue
        below = SEVERITY[n.severity] < SEVERITY[c["min_severity"]] and n.kind != "usage_report"  # 리포트는 심각도 무관
        if not only and (not c["enabled"] or below):
            continue
        try:
            if name == "slack":
                out[name] = await _slack(db, n)
            elif name == "telegram":
                out[name] = await _telegram(db, n, c.get("chat_id", ""))
            else:
                out[name] = await asyncio.to_thread(_email, db, n, c)
        except (httpx.HTTPError, OSError, smtplib.SMTPException) as exc:
            out[name] = f"error: {type(exc).__name__}"
    return out


async def dispatch(db: Session, limit: int = 50) -> int:
    """미발송 알림(관리자·전체 대상)을 채널로 보낸다. 사용자 개인 알림은 콘솔에만."""
    rows = list(db.execute(select(Notification).where(Notification.deliveries.is_(None),
                                                      or_(Notification.audience == "admins", Notification.audience == "all"))
                           .order_by(Notification.id).limit(limit)).scalars())
    for n in rows:
        n.deliveries = await send(db, n)
        db.commit()
    return len(rows)
