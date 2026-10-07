"""월 예산 기반 로컬 강제 (UI J05, PRD Q15): 이번 달 LLM 사용 비용이 월 예산의 기준 비율(기본 80%)에 닿으면
퍼블릭(비로컬) 대상은 계획에서 빼고 로컬 모델만 쓴다. 로컬 대상이 없으면 정책 거부(403)로 끝낸다.

비용 = llm_usage.cost(모델 카탈로그의 1천 토큰당 단가로 계량, USD). 달 경계는 UTC. 집계는 30초 캐시.
처음 강제되는 순간 달마다 한 번 원장(llm.budget_local_forced)에 남긴다.
"""
import time
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import LlmUsage
from app.services import audit, sysconfig

KEY, STATE_KEY = "llm.budget", "llm.budget_state"
DEFAULT = {"monthly": 0.0, "ratio": 0.8, "currency": "USD"}
TTL = 30.0
_cache: dict = {"at": 0.0, "month": None, "spent": 0.0}


class BudgetError(ValueError):
    pass


def config(db: Session) -> dict:
    return {**DEFAULT, **sysconfig.blob(db, KEY)}


def set_config(db: Session, *, monthly: float, ratio: float) -> dict:
    if monthly < 0 or not 0.5 <= ratio <= 1.0:
        raise BudgetError("monthly ≥ 0, 0.5 ≤ ratio ≤ 1.0")
    sysconfig.put_blob(db, KEY, {**config(db), "monthly": float(monthly), "ratio": float(ratio)})
    invalidate()
    return config(db)


def invalidate() -> None:
    _cache.update(at=0.0, month=None)


def _month(now: datetime) -> tuple[str, datetime]:
    return now.strftime("%Y-%m"), now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def spent(db: Session) -> float:
    label, start = _month(utcnow())
    if _cache["month"] == label and time.monotonic() - _cache["at"] < TTL:
        return _cache["spent"]
    total = db.scalar(select(func.coalesce(func.sum(LlmUsage.cost), 0.0)).where(LlmUsage.ts >= start)) or 0.0
    _cache.update(at=time.monotonic(), month=label, spent=float(total))
    return float(total)


def forced(db: Session) -> bool:
    c = config(db)
    return c["monthly"] > 0 and spent(db) >= c["ratio"] * c["monthly"]


def note_forced(db: Session) -> None:
    label, _ = _month(utcnow())
    if sysconfig.blob(db, STATE_KEY).get("month") == label:
        return
    sysconfig.put_blob(db, STATE_KEY, {"month": label, "forced_at": utcnow().isoformat()})
    c = config(db)
    audit.record(db, actor="system", actor_type="system", action="llm.budget_local_forced", resource=f"month:{label}",
                 detail={"spent": round(spent(db), 4), "monthly": c["monthly"], "ratio": c["ratio"]})
    from app.services import notify
    notify.emit(db, "budget_forced", "warn", f"월 예산 {int(c['ratio'] * 100)}% 도달 — 로컬 모델로 강제",
                f"{label} 사용 {round(spent(db), 4)} / {c['monthly']} {c['currency']}", resource=f"month:{label}")


def status(db: Session) -> dict:
    c = config(db)
    s = spent(db)
    return {**c, "month": _month(utcnow())[0], "spent": round(s, 6),
            "used": round(s / c["monthly"], 4) if c["monthly"] else None, "forced": forced(db)}
