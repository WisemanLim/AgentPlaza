"""헬스 대시보드·알림 센터·알림 채널·사용량 리포트 API (D10-07, UI B03)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin, require_supervisor, require_user
from app.db import get_db
from app.models import Notification
from app.services import audit, notify
from app.services import status as health
from app.services import sysconfig

router = APIRouter(prefix="/api", tags=["status"], dependencies=[Depends(require_user)])


class ReadIn(BaseModel):
    ids: list[int] | None = None


class ChannelIn(BaseModel):
    config: dict = Field(default_factory=dict)
    secret: str | None = Field(default=None, max_length=2000)  # Slack 웹훅 URL · Telegram 봇 토큰 · SMTP 암호(쓰기 전용)


class ReportSettingsIn(BaseModel):
    weekly: bool


@router.get("/status")
async def get_status(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return await health.snapshot(db)


@router.post("/status/check")
async def check_now(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """지금 점검: 상태 변화 알림 + 미발송 알림 발송."""
    out = await health.check(db)
    out["dispatched"] = await notify.dispatch(db)
    return out


@router.get("/status/report")
def get_report(days: int = 7, _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return health.report(db, max(1, min(days, 90))) | {"settings": health.report_settings(db)}


@router.post("/status/report/send")
async def send_report(days: int = 7, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    n = health.send_report(db, max(1, min(days, 90)))
    sent = await notify.dispatch(db)
    audit.record(db, actor=p.actor, actor_type=p.type, action="status.report_sent", detail={"days": days})
    return {"notification": n.id if n else None, "dispatched": sent, "deliveries": db.get(Notification, n.id).deliveries if n else None}


@router.put("/status/report/settings")
def report_settings(body: ReportSettingsIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    sysconfig.put_blob(db, health.REPORT_KEY, {**health.report_settings(db), "weekly": body.weekly})
    return health.report_settings(db)


@router.get("/notifications")
def list_notifications(unread: bool = False, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    return notify.listing(db, p.actor, p.role, unread=unread)


@router.get("/notifications/unread-count")
def unread(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    return {"unread": notify.unread_count(db, p.actor, p.role)}


@router.post("/notifications/read")
def mark_read(body: ReadIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    return {"marked": notify.mark_read(db, p.actor, p.role, body.ids)}


@router.get("/notifications/channels")
def get_channels(_: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    return notify.channels(db)


@router.put("/notifications/channels/{name}")
def put_channel(name: str, body: ChannelIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        out = notify.set_channel(db, name, body.config, body.secret, p.actor)
    except notify.NotifyError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="notify.channel_set", resource=f"channel:{name}",
                 detail={"config": body.config, "secret_updated": bool(body.secret)})
    return out


@router.post("/notifications/channels/{name}/test")
async def test_channel(name: str, _: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    if name not in notify.DEFAULT:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "채널 없음 / unknown channel")
    probe = Notification(kind="test", severity="info", title="알림 채널 연결 시험 / test", body="AgentPlaza")
    return {"channel": name, "result": (await notify.send(db, probe, only=name)).get(name)}
