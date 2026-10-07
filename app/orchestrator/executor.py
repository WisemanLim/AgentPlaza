"""도구 호출 실행기 (D2-04): 내부 REST(agent /api/invoke) — 원격 A2A·MCP 는 REMOTE 등록부로 확장(Epic 8).
결과는 {ok, result|error, latency_ms} 로 정규화한다(v1 _format_api_result 승계)."""
import time
from collections.abc import Awaitable, Callable

import httpx

from app.core.config import settings
from app.observability import SpanKind, Status, StatusCode, inject, tracer
from app.services.registry import agent_key

# 시험·로컬 통합용: endpoint → httpx 전송(예: ASGITransport). 운영은 비어 있음(실 네트워크).
TRANSPORTS: dict[str, httpx.AsyncBaseTransport] = {}
# 같은 용도의 ASGI 앱(공식 MCP 클라이언트는 httpx2 전송이 필요하므로 앱을 함께 둔다)
APPS: dict[str, object] = {}


def register_app(base_url: str, app) -> None:
    TRANSPORTS[base_url] = httpx.ASGITransport(app=app)
    APPS[base_url] = app


def clear_apps() -> None:
    TRANSPORTS.clear()
    APPS.clear()


# source 별 원격 호출기: (cap, args, headers) -> result. Epic 8 에서 "link" 를 등록한다.
REMOTE: dict[str, Callable[[dict, dict, dict], Awaitable[dict]]] = {}


async def call(cap: dict, args: dict, *, principal: str, task_id: str, approval_id: str | None = None,
               session_id: str | None = None) -> dict:
    with tracer().start_as_current_span(f"execute_tool {cap['agent']}.{cap['verb']}", kind=SpanKind.CLIENT) as span:
        span.set_attributes({"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": cap["verb"],
                             "gen_ai.agent.id": cap["agent"], "plaza.capability": f"{cap['agent']}.{cap['verb']}",
                             "plaza.task_id": task_id, "plaza.source": cap.get("source", "")})
        if session_id:
            span.set_attribute("plaza.session_id", session_id)
        out = await _call(cap, args, principal=principal, task_id=task_id, approval_id=approval_id)
        span.set_attribute("plaza.latency_ms", out.get("latency_ms", 0))
        if not out["ok"]:
            span.set_status(Status(StatusCode.ERROR, str(out.get("error"))[:200]))
        return out


async def _call(cap: dict, args: dict, *, principal: str, task_id: str, approval_id: str | None = None) -> dict:
    started = time.monotonic()
    headers = {"x-api-key": agent_key(cap["agent"]), "x-plaza-user": principal, "x-plaza-task": task_id}
    if approval_id:
        headers["x-plaza-approval-id"] = approval_id
    inject(headers)  # W3C traceparent 전파
    try:
        if cap["source"] in REMOTE:
            result = await REMOTE[cap["source"]](cap, args, headers)
            return {"ok": True, "result": result, "latency_ms": int((time.monotonic() - started) * 1000)}
        if not cap.get("endpoint"):
            return {"ok": False, "error": "agent has no endpoint", "latency_ms": 0}
        async with httpx.AsyncClient(base_url=cap["endpoint"], transport=TRANSPORTS.get(cap["endpoint"]),
                                     timeout=settings.agent_call_timeout) as c:
            res = await c.post(f"/api/invoke/{cap['verb']}", json=args, headers=headers)
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:  # 요청이 나가지 않음 — 항상 재시도 가능
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "transient": "connect",
                "latency_ms": int((time.monotonic() - started) * 1000)}
    except (httpx.HTTPError, RuntimeError) as exc:  # 나갔을 수 있음 — 멱등 capability 만 재시도
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "transient": "timeout",
                "latency_ms": int((time.monotonic() - started) * 1000)}
    latency = int((time.monotonic() - started) * 1000)
    try:
        body = res.json()
    except ValueError:
        body = {"detail": res.text[:500]}
    if res.status_code >= 400:
        out = {"ok": False, "status": res.status_code, "error": body.get("detail", body), "latency_ms": latency}
        if res.status_code in (502, 503, 504):
            out["transient"] = "status"
        return out
    return {"ok": True, "result": body.get("result", body), "latency_ms": latency}
