"""{{AGENT_NAME}} — tool-proxy 유형: 외부 REST API 1개를 capability 로 감싼다. 대상은 TOOL_BASE_URL(egress 허용목록)."""
import os
from urllib.parse import urljoin, urlparse

import httpx

from agentplaza_sdk import Agent, CapabilityError, create_app

agent = Agent.from_manifest("agent.yaml")
ALLOWED_METHODS = {"GET", "POST"}


@agent.capability("call")
async def call(payload: dict, ctx):
    base = os.environ.get("TOOL_BASE_URL", "")
    if not base:
        raise CapabilityError("TOOL_BASE_URL not configured", status=503)
    method = payload.get("method", "GET").upper()
    if method not in ALLOWED_METHODS:
        raise CapabilityError(f"method not allowed: {method}")
    url = urljoin(base.rstrip("/") + "/", payload.get("path", "").lstrip("/"))
    if urlparse(url).netloc != urlparse(base).netloc:  # 경로 조작으로 다른 호스트로 새지 않게
        raise CapabilityError("path escapes TOOL_BASE_URL host")
    async with httpx.AsyncClient(timeout=float(os.environ.get("TOOL_TIMEOUT", "15"))) as c:
        res = await c.request(method, url, params=payload.get("query"), json=payload.get("json"))
    ctype = res.headers.get("content-type", "")
    return {"status": res.status_code, "body": res.json() if "json" in ctype else res.text[:10_000]}


app = create_app(agent)
