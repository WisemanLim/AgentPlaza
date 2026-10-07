"""wise-agentplaza — FastAPI entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import db
from app.api import (agents, api_keys, audit, auth, channels, chat, commerce, console, governance, knowledge, llm, market,
                     obs, ops, orchestrator, orgs, personal, status, trust, users)
from app.core.config import settings
from app.governance.ratelimit import RateLimitMiddleware
from app.protocols import gateway, link  # noqa: F401 — link 은 원격 호출기(REMOTE['link'])를 등록한다


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.services.secrets import install_log_filter
    install_log_filter()  # 로그 마스킹(D9-04)
    if settings.auto_migrate:
        db.migrate()
    from app.llm import catalog
    from app.llm.router import get_router
    from app.services import registry
    with db.SessionLocal() as s:
        catalog.bootstrap(s, get_router().providers)
        catalog.ensure_defaults(s)
        registry.bootstrap_builtins(s)
        from app.assistant.chat import purge_expired
        purge_expired(s)
    import asyncio

    from app.runtime.driver import RuntimeFailure, get_runtime
    rt = get_runtime()
    if hasattr(rt, "reconcile"):  # api 재생성 직후 에이전트 네트워크 재연결(runtime 도 10초 주기로 수행)
        async def _reconcile():
            try:
                await rt.reconcile()
            except RuntimeFailure:
                pass
        reconcile_task = asyncio.create_task(_reconcile())  # noqa: F841 — 기동을 막지 않는다

    async def _recovery_loop():  # 크래시 복구(D2-07): 멈춘 작업을 체크포인트에서 재개
        from app.orchestrator.service import recover_stale
        while True:
            try:
                await recover_stale()
            except Exception:  # noqa: BLE001 — 복구 루프는 죽지 않는다
                logging.getLogger("app").exception("task recovery failed")
            await asyncio.sleep(30)
    recovery = asyncio.create_task(_recovery_loop())

    async def _market_loop():  # D6-07: 원격 레지스트리 동기화 + 업데이트 알림·자동 갱신
        from app.market import remote, updates
        while True:
            await asyncio.sleep(settings.market_sync_interval)
            try:
                with db.SessionLocal() as s:
                    await remote.sync_due(s)
                    await updates.auto_update(s)
            except Exception:  # noqa: BLE001 — 루프는 죽지 않는다
                logging.getLogger("app").exception("market sync failed")
    market_loop = asyncio.create_task(_market_loop()) if settings.market_sync_interval > 0 else None

    async def _status_loop():  # D10-07: 상태 변화 감시 → 알림 · 채널 발송 · 주간 리포트
        from app.services import notify
        from app.services import status as health
        while True:
            await asyncio.sleep(settings.status_check_interval)
            try:
                with db.SessionLocal() as s:
                    await health.check(s)
                    if health.weekly_due(s):
                        health.send_report(s)
                    await notify.dispatch(s)
            except Exception:  # noqa: BLE001 — 루프는 죽지 않는다
                logging.getLogger("app").exception("status check failed")
    status_loop = asyncio.create_task(_status_loop()) if settings.status_check_interval > 0 else None
    yield
    recovery.cancel()
    for t in (market_loop, status_loop):
        if t:
            t.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan,
              docs_url="/docs" if settings.app_env != "prod" else None, redoc_url=None,
              openapi_url="/openapi.json" if settings.app_env != "prod" else None)
gateway.mount_orchestrator_a2a(app)  # 정적 /a/orchestrator/… 를 동적 /a/{agent}/… 보다 먼저
for r in (auth.router, users.router, api_keys.router, audit.router, agents.router, llm.router, llm.v1,
          orchestrator.router, chat.router, market.router, commerce.router, commerce.licenses, commerce.registry, commerce.hooks,
          console.router, trust.router, governance.router, ops.router, knowledge.router, personal.router, obs.router,
          orgs.router, status.router, channels.router, channels.widget,
          gateway.router):
    app.include_router(r)
app.router.routes.append(gateway.MCP_ROUTE)
app.add_middleware(RateLimitMiddleware)  # 게이트웨이 레이트리밋(D7-07)


@app.middleware("http")
async def a2a_auth(request: Request, call_next):
    """Orchestrator A2A JSON-RPC 는 인증 필수(카드만 공개, NFR-S5). SDK 라우트에는 의존성이 없어 여기서 막는다."""
    if request.url.path == "/a/orchestrator/a2a" and gateway._principal_from(
            {k.lower(): v for k, v in request.headers.items()}) is None:
        return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "unauthorized"}},
                            status_code=401)
    return await call_next(request)


@app.get("/health")
def health():
    try:
        db.ping()
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001 — 헬스 응답에 원인 노출(시크릿 제외)
        db_status = f"error: {type(exc).__name__}"
    body = {"status": "ok" if db_status == "ok" else "degraded",
            "env": settings.app_env, "db": {"engine": settings.db_engine, "status": db_status}}
    return JSONResponse(body, status_code=200 if db_status == "ok" else 503)
