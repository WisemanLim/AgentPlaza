"""게이트웨이 레이트리밋 (D7-07): 분 단위 고정 창, 주체별(자격 증명 해시) 카운터.

- 대상: LLM(/v1)·MCP(/mcp)·A2A(/a/{id}/a2a)·Orchestrator·채팅 스트림 — 에이전트 코드는 정책을 모른다.
- 저장소: REDIS_URL(Valkey) 이 있으면 INCR+EXPIRE(워커·재기동 사이 공유), 없으면 프로세스 메모리.
- 한도: 정책 gateway.rate_per_minute {user, service, anonymous}. 초과 시 429 + Retry-After.
"""
import hashlib
import re
import time

import jwt
from starlette.responses import JSONResponse

from app.core.config import settings
from app.db import SessionLocal
from app.governance import policy

PATHS = re.compile(r"^(/v1/|/mcp/|/api/orchestrate$|/api/chat/stream$|/a/[a-z0-9-]+/a2a$)")


class MemoryCounter:
    def __init__(self):
        self.counts: dict[str, int] = {}

    async def incr(self, key: str, ttl: int) -> int:
        window = key.rsplit(":", 1)[-1]
        for k in [k for k in self.counts if not k.endswith(window)]:  # 지난 창 정리
            del self.counts[k]
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]


class RedisCounter:
    """Valkey 카운터. 연결 장애 시 요청을 막지 않고 프로세스 메모리로 대신 센다(가용성 우선)."""

    def __init__(self, url: str):
        import redis.asyncio as redis
        self.r = redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        self.fallback = MemoryCounter()

    async def incr(self, key: str, ttl: int) -> int:
        try:
            n = await self.r.incr(key)
            if n == 1:
                await self.r.expire(key, ttl)
            return n
        except Exception:  # noqa: BLE001 — redis 오류 종류가 다양하다
            return await self.fallback.incr(key, ttl)


_counter = None


def counter():
    global _counter
    if _counter is None:
        _counter = RedisCounter(settings.redis_url) if settings.redis_url else MemoryCounter()
    return _counter


def reset() -> None:
    global _counter
    _counter = None


def identify(headers: dict, client: str) -> tuple[str, str]:
    """(kind, bucket) — DB 를 읽지 않는다. 검증은 각 엔드포인트가 한다(여기는 한도만)."""
    cred = headers.get("x-api-key") or ""
    auth = headers.get("authorization") or ""
    if not cred and auth.lower().startswith("bearer "):
        cred = auth[7:].strip()
    if not cred:
        cookie = re.search(r"(?:^|;\s*)plaza_session=([^;]+)", headers.get("cookie", ""))
        cred = cookie.group(1) if cookie else ""
    if not cred:
        return "anonymous", f"ip:{client}"
    kind = "service"
    if not cred.startswith("ap_sk_"):
        try:
            kind = "service" if jwt.decode(cred, settings.jwt_secret, algorithms=["HS256"],
                                           options={"verify_aud": False}).get("typ") == "service" else "user"
        except jwt.PyJWTError:
            return "anonymous", f"ip:{client}"
    return kind, hashlib.sha256(cred.encode()).hexdigest()[:24]


class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not settings.rate_limit_enabled or not PATHS.match(scope["path"]):
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        kind, bucket = identify(headers, (scope.get("client") or ("?",))[0])
        limit = policy.cached(SessionLocal)["gateway"]["rate_per_minute"].get(kind, 60)
        window = int(time.time() // 60)
        n = await counter().incr(f"rl:{kind}:{bucket}:{window}", 70)
        if n > limit:
            retry = 60 - int(time.time()) % 60
            body = {"detail": f"요청 한도 초과 / rate limit exceeded ({limit}/min)"}
            if scope["path"].startswith("/mcp/") or scope["path"].endswith("/a2a"):
                body = {"jsonrpc": "2.0", "id": None, "error": {"code": -32029, "message": body["detail"]}}
            res = JSONResponse(body, status_code=429, headers={"Retry-After": str(retry), "X-RateLimit-Limit": str(limit),
                                                                "X-RateLimit-Remaining": "0"})
            return await res(scope, receive, send)

        async def send_with_headers(msg):
            if msg["type"] == "http.response.start":
                msg = {**msg, "headers": [*msg.get("headers", []), (b"x-ratelimit-limit", str(limit).encode()),
                                          (b"x-ratelimit-remaining", str(max(limit - n, 0)).encode())]}
            await send(msg)
        return await self.app(scope, receive, send_with_headers)
