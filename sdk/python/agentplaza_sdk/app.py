"""create_app(agent): REST 표면 + 헬스. 프로토콜 표면(MCP·A2A)은 protocols 모듈이 같은 앱에 붙인다."""
import hmac
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from agentplaza_sdk.agent import Agent, CapabilityError

PUBLIC_PATHS = {"/health", "/.well-known/agent-card.json"}


def caller_from(request: Request) -> dict:
    """게이트웨이가 인증 후 넘긴 호출자 정보. 에이전트는 정책을 모른다(D7-07)."""
    return {k.removeprefix("x-plaza-"): v for k, v in request.headers.items() if k.startswith("x-plaza-")}


def create_app(agent: Agent) -> FastAPI:
    errors = agent.coherence()
    if errors:
        raise RuntimeError(f"agent.yaml 과 핸들러 불일치 / incoherent agent: {errors}")

    app = FastAPI(title=agent.name, version=agent.version, docs_url=None, redoc_url=None,
                  openapi_url="/api/openapi.json")
    app.state.agent = agent
    api_key = os.environ.get("AGENT_API_KEY", "")

    @app.middleware("http")
    async def require_key(request: Request, call_next):
        # AGENT_API_KEY 가 있으면 /health·agent-card 외 전부 x-api-key 필요(M1 단독 구동 시 보호, NFR-S5).
        if api_key and request.url.path not in PUBLIC_PATHS:
            if not hmac.compare_digest(request.headers.get("x-api-key", ""), api_key):
                return JSONResponse({"detail": "invalid api key"}, status_code=401)
        return await call_next(request)

    @app.get("/health")
    def health():
        return {"status": "ok", "agent": agent.id, "version": agent.version}

    @app.get("/api/capabilities")
    def capabilities():
        return agent.capabilities

    @app.post("/api/invoke/{verb}")
    async def invoke(verb: str, request: Request):
        try:
            payload = await request.json() if await request.body() else {}
        except ValueError:
            raise HTTPException(400, "JSON body required") from None
        try:
            result = await agent.invoke(verb, payload, agent.context(caller_from(request)))
        except CapabilityError as exc:
            raise HTTPException(exc.status, str(exc)) from None
        return {"result": result}

    try:  # 프로토콜 의존성(mcp·a2a-sdk)이 없는 구형 이미지는 REST 만 노출한다
        from agentplaza_sdk import protocols
    except ImportError:
        return app
    protocols.mount(app, agent)
    return app
