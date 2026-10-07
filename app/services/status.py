"""헬스·상태 (D10-07): 플랫폼 구성요소·에이전트·LLM 공급자 상태를 모으고, 바뀌면 알림을 남긴다.

- snapshot(): 지금 상태(DB·Valkey·Bifrost·runtime·게이트웨이 + 설치 에이전트 /health + Ollama).
- check(): 직전 상태(sysconfig status.last)와 비교 → 장애·복구 알림, 에이전트 상태(healthy/unhealthy) 갱신(라우팅 반영),
  라이선스 만료 임박(14일) 알림(하루 1회). 상태 루프가 주기적으로 부른다.
- report(): 기간 사용량 리포트(LLM 호출·토큰·비용·폴백·로컬 비율·도구 호출 상위·설치·오류) + 마크다운.
"""
import asyncio
import os
import time
from collections import Counter
from datetime import timedelta

import httpx
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.models import Agent, AuditEvent, Install, License, LlmUsage, Notification
from app.orchestrator import executor
from app.services import notify, sysconfig

LAST_KEY = "status.last"
EXPIRY_DAYS = 14


async def _probe(url: str, headers: dict | None = None, timeout: float = 3.0) -> tuple[bool, str]:
    base = "/".join(url.split("/")[:3])
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout, transport=executor.TRANSPORTS.get(base)) as c:
            r = await c.get(url, headers=headers or {})
        return r.status_code < 400, f"HTTP {r.status_code} · {int((time.monotonic() - t0) * 1000)}ms"
    except httpx.HTTPError as exc:
        return False, type(exc).__name__


def _db_ok(db: Session) -> tuple[bool, str]:
    try:
        db.execute(text("SELECT 1"))
        return True, settings.db_engine
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


def _redis_ok() -> tuple[bool, str] | None:
    if not settings.redis_url:
        return None
    try:
        import redis
        redis.Redis.from_url(settings.redis_url, socket_timeout=2).ping()
        return True, "ping"
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


async def snapshot(db: Session) -> dict:
    comps: dict[str, dict] = {}
    ok, why = _db_ok(db)
    comps["db"] = {"ok": ok, "detail": why}
    if (r := await asyncio.to_thread(_redis_ok)) is not None:
        comps["valkey"] = {"ok": r[0], "detail": r[1]}
    if os.environ.get("BIFROST_URL"):
        ok, why = await _probe(os.environ["BIFROST_URL"].rstrip("/") + "/health")
        comps["bifrost"] = {"ok": ok, "detail": why}
    if settings.runtime_driver == "remote" and settings.runtime_url:
        ok, why = await _probe(settings.runtime_url.rstrip("/") + "/health")
        comps["runtime"] = {"ok": ok, "detail": why}
    if settings.gateway_internal_url:
        ok, why = await _probe(settings.gateway_internal_url.rstrip("/") + "/health")
        comps["gateway"] = {"ok": ok, "detail": why}
    ollama = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ok, why = await _probe(ollama.rstrip("/") + "/api/tags")
    llm = {"ollama": {"ok": ok, "detail": why}}
    agents = {}
    from app.services.registry import agent_key
    for a in db.execute(select(Agent).where(Agent.builtin.is_(False), Agent.is_active.is_(True))).scalars():
        if a.source == "link" or not a.endpoint:
            agents[a.id] = {"ok": a.status in ("healthy", "registered"), "detail": f"status {a.status}", "name": a.name,
                            "version": a.version, "probe": False}
            continue
        ok, why = await _probe(a.endpoint.rstrip("/") + "/health", {"x-api-key": agent_key(a.id)})
        agents[a.id] = {"ok": ok, "detail": why, "name": a.name, "version": a.version, "probe": True}
    return {"at": utcnow().isoformat(), "components": comps, "llm": llm, "agents": agents,
            "ok": all(c["ok"] for c in comps.values()) and all(v["ok"] for v in agents.values())}


async def check(db: Session) -> dict:
    """상태 변화를 알림으로. 처음 보는 대상은 기록만 한다(기동 직후 알림 폭주 방지)."""
    snap = await snapshot(db)
    last = sysconfig.blob(db, LAST_KEY)
    changes = []
    for group, label in (("components", "구성요소"), ("llm", "LLM 공급자"), ("agents", "에이전트")):
        prev = last.get(group, {})
        for name, cur in snap[group].items():
            if name not in prev or prev[name] == cur["ok"]:
                continue
            changes.append((group, name, cur["ok"]))
            sev, verb = ("info", "복구") if cur["ok"] else ("error", "장애")
            notify.emit(db, f"{group}_{'up' if cur['ok'] else 'down'}", sev, f"{label} {name} {verb}",
                        cur["detail"], resource=f"{group}:{name}", dedup_minutes=5)
            if group == "agents":  # 라우팅 반영: 장애 에이전트는 계획 후보에서 빠진다
                a = db.get(Agent, name)
                if a is not None and cur.get("probe"):
                    a.status = "healthy" if cur["ok"] else "unhealthy"
                    db.commit()
    sysconfig.put_blob(db, LAST_KEY, {g: {k: v["ok"] for k, v in snap[g].items()} for g in ("components", "llm", "agents")})
    expiring(db)
    return {"changes": changes, "ok": snap["ok"]}


def expiring(db: Session) -> int:
    soon = utcnow() + timedelta(days=EXPIRY_DAYS)
    n = 0
    for lic in db.execute(select(License).where(License.status == "active", License.expires_at.is_not(None))).scalars():
        exp = lic.expires_at if lic.expires_at.tzinfo else lic.expires_at.replace(tzinfo=utcnow().tzinfo)
        if utcnow() < exp <= soon:
            n += bool(notify.emit(db, "license_expiring", "warn", f"라이선스 만료 임박: {lic.listing_id}",
                                  f"{lic.id} · 만료 {exp.date().isoformat()} · 좌석 {lic.seats}",
                                  resource=f"license:{lic.id}", dedup_minutes=24 * 60))
    return n


def report(db: Session, days: int = 7) -> dict:
    since = utcnow() - timedelta(days=days)
    usage = list(db.execute(select(LlmUsage).where(LlmUsage.ts >= since)).scalars())
    calls = len(usage)
    local = sum(1 for u in usage if u.model.startswith(("ollama/", "mock/")))
    tools = Counter(e.resource for e in db.execute(select(AuditEvent).where(AuditEvent.action == "tool.call",
                                                                             AuditEvent.ts >= since)).scalars())
    installs = Counter(i.status for i in db.execute(select(Install).where(Install.created_at >= since)).scalars())
    alerts = Counter(n.severity for n in db.execute(select(Notification).where(Notification.created_at >= since)).scalars())
    out = {"days": days, "since": since.isoformat(), "llm": {
        "calls": calls, "tokens": sum(u.tokens_in + u.tokens_out for u in usage), "cost": round(sum(u.cost for u in usage), 4),
        "fallbacks": sum(1 for u in usage if u.fallback_from), "errors": sum(1 for u in usage if u.outcome != "ok"),
        "local_ratio": round(local / calls, 3) if calls else None},
        "top_tools": tools.most_common(5), "installs": dict(installs), "alerts": dict(alerts),
        "agents": db.scalar(select(func.count()).select_from(Agent).where(Agent.builtin.is_(False))) or 0}
    llm = out["llm"]
    lines = [f"# AgentPlaza 사용량 리포트 — 최근 {days}일", "",
             f"- LLM 호출 {llm['calls']} · 토큰 {llm['tokens']} · 비용 ${llm['cost']} · 폴백 {llm['fallbacks']} · 오류 {llm['errors']}"
             + (f" · 로컬 비율 {round(llm['local_ratio'] * 100)}%" if llm["local_ratio"] is not None else ""),
             f"- 설치 에이전트 {out['agents']} · 설치 시도 {sum(installs.values())} ({', '.join(f'{k} {v}' for k, v in installs.items()) or '—'})",
             f"- 알림 {sum(alerts.values())} ({', '.join(f'{k} {v}' for k, v in alerts.items()) or '—'})",
             "- 도구 호출 상위: " + (", ".join(f"{r} {n}" for r, n in out["top_tools"]) or "—")]
    out["markdown"] = "\n".join(lines)
    return out


REPORT_KEY = "notify.report"


def report_settings(db: Session) -> dict:
    return {"weekly": False, "last_sent": None, **sysconfig.blob(db, REPORT_KEY)}


def send_report(db: Session, days: int = 7) -> Notification | None:
    r = report(db, days)
    n = notify.emit(db, "usage_report", "info", f"사용량 리포트 — 최근 {days}일", r["markdown"], resource=f"report:{days}d",
                    dedup_minutes=0)
    sysconfig.put_blob(db, REPORT_KEY, {**report_settings(db), "last_sent": utcnow().isoformat()})
    return n


def weekly_due(db: Session) -> bool:
    cfg = report_settings(db)
    if not cfg["weekly"]:
        return False
    from datetime import datetime
    return not cfg["last_sent"] or utcnow() - datetime.fromisoformat(cfg["last_sent"]) >= timedelta(days=7)
