"""프로토콜 게이트웨이 (D7-01·D7-03): 모든 에이전트를 같은 표면으로 노출한다. 에이전트 코드는 정책을 모른다(D7-07).

- MCP  /mcp/{agent}                     tools = capability 인덱스. x-api-key·Bearer 인증, 키 범위·활성 검사.
  내장 orchestrator 는 orchestrate 도구를 노출한다(PRD 4.2 "MCP tool orchestrate").
- A2A  /a/{agent}/.well-known/agent-card.json  플랫폼 서명 카드(공개, NFR-S5)
       /a/{agent}/a2a                   인증 후 에이전트 컨테이너의 /a2a 로 프록시(키 주입)
       /a/orchestrator/…                Orchestrator 를 A2A Task 로 호출(a2a-sdk 서버)
승인 필요 capability 는 MCP·A2A 로 직접 실행할 수 없다(DP8 — UI·API 우회 방지).
게이트웨이 정책(D7-07): Mcp-Method·Mcp-Name 헤더로 툴 단위 RBAC 를 본문 해석 전에 판정하고, 본문 기준으로 한 번 더 판정한다.
"""
import json
import uuid

import httpx
from agentplaza_sdk.agent import CapabilityError
from agentplaza_sdk.protocols import CapabilityExecutor, MCPEndpoint, a2a_routes, build_card, mcp_server
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy.orm import Session
from starlette.routing import Route

from app.core.deps import Principal, current_principal
from app.db import SessionLocal, get_db
from app.governance import policy as gov
from app.llm.router import parse_data_class
from app.market import licensing
from app.models import Agent
from app.orchestrator import executor
from app.orchestrator import service as orchestrator
from app.protocols import card as cards
from app.protocols import keys
from app.services import audit, orgs, registry

router = APIRouter(tags=["protocols"])
ORCH_TOOLS = [{"name": "orchestrate", "description": "AgentPlaza Orchestrator — 요청을 설치된 에이전트로 계획·실행",
               "inputSchema": {"type": "object", "required": ["message"],
                               "properties": {"message": {"type": "string"}, "agent_scope": {"type": "string"}}}}]


def _rpc_error(code: int, http: int, message: str) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": code, "message": message}}, status_code=http)


def _principal_from(headers: dict) -> Principal | None:
    with SessionLocal() as db:
        try:
            return current_principal(authorization=headers.get("authorization"), x_api_key=headers.get("x-api-key"), db=db)
        except HTTPException:
            return None


def _agent_accessible(agent_id: str, p: Principal) -> tuple[Agent | None, str | None]:
    with SessionLocal() as db:
        a = db.get(Agent, agent_id)
        if a is None or (a.builtin and agent_id != "orchestrator"):
            return None, "unknown agent"
        if not a.is_active or a.status not in ("healthy", "registered"):
            return None, "agent inactive"
        if not p.can_access_agent(agent_id):
            return None, "agent out of key scope"
        if not orgs.visible(db, p.actor, p.role, agent_id):  # 조직·그룹 배치 범위(PRD Q7)
            return None, "agent out of deploy scope"
        db.expunge(a)
        return a, None


async def _guard(scope) -> JSONResponse | None:
    headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
    p = _principal_from(headers)
    if p is None:
        return _rpc_error(-32001, 401, "unauthorized")
    agent_id = scope["path_params"]["agent"]
    agent, why = _agent_accessible(agent_id, p)
    if agent is None:
        return _rpc_error(-32601 if why == "unknown agent" else -32003, 404 if why == "unknown agent" else 403, why)
    level = _level_of(headers)
    if level is None:
        return _rpc_error(-32602, 422, "X-Plaza-Data-Class ∈ L0..L3")
    if headers.get("mcp-method") == "tools/call" and headers.get("mcp-name") and agent_id != "orchestrator":
        denied = _tool_denied(agent_id, headers["mcp-name"], p, level, "mcp-header")
        if denied:
            return _rpc_error(-32003, 403, denied)
    scope.setdefault("state", {})["plaza_principal"] = p
    scope["state"]["plaza_level"] = level
    return None


def _level_of(headers: dict) -> str | None:
    try:
        return parse_data_class(headers.get("x-plaza-data-class"))
    except ValueError:
        return None


def _tool_denied(agent_id: str, verb: str, p: Principal, level: str, channel: str) -> str | None:
    """정책 판정(허용목록·툴 RBAC·등급) — 거부면 사유를 원장에 남기고 돌려준다."""
    cap = _cap_index(agent_id).get(verb)
    if cap is None:
        return None  # 없는 도구는 MCP 서버가 not found 로 답한다
    with SessionLocal() as db:
        why = gov.tool_decision(gov.get(db), cap, role=p.role, level=level)
        if why:
            audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="gateway.tool_denied",
                         resource=f"{agent_id}.{verb}", outcome="denied", detail={"reason": why, "channel": channel})
    return why


def _cap_index(agent_id: str) -> dict[str, dict]:
    with SessionLocal() as db:
        return {c["verb"]: c for c in registry.routable(db, agent_id)}


async def _list_tools(request) -> list[dict]:
    agent_id = request.path_params["agent"]
    if agent_id == "orchestrator":
        return ORCH_TOOLS
    state = request.scope.get("state", {})
    p, level = state.get("plaza_principal"), state.get("plaza_level", "L2")
    with SessionLocal() as db:
        pol = gov.get(db)
    return [{"name": v, "description": c["description"], "inputSchema": c["input_schema"]}
            for v, c in _cap_index(agent_id).items()
            if p is None or gov.tool_decision(pol, c, role=p.role, level=level) is None]  # 툴 RBAC: 못 쓰는 도구는 숨긴다


async def invoke_capability(agent_id: str, verb: str, args: dict, p: Principal, channel: str, level: str = "L2") -> dict:
    cap = _cap_index(agent_id).get(verb)
    if cap is None:
        raise CapabilityError(f"unknown capability: {verb}", status=404)
    denied = _tool_denied(agent_id, verb, p, level, channel)
    if denied:
        raise CapabilityError(f"정책 거부 / denied by policy: {denied}", 403)
    with SessionLocal() as db:
        why = licensing.check_use(db, agent_id, p.actor, claim=True)
        if why:  # 유료 에이전트: 라이선스·좌석(D6-05)
            audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="license.denied",
                         resource=f"{agent_id}.{verb}", outcome="denied", detail={"reason": why, "channel": channel})
            raise CapabilityError(f"라이선스 / license: {why}", 402)
        if cap["approval"]:
            audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="tool.approval_bypass_blocked",
                         resource=f"{agent_id}.{verb}", outcome="denied", args=args, detail={"channel": channel})
            raise CapabilityError("휴먼 승인 필요 — /api/orchestrate 또는 콘솔에서 요청 / human approval required", 403)
        out = await executor.call(cap, args, principal=p.actor, task_id=f"{channel}:{uuid.uuid4().hex[:12]}")
        audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="tool.call",
                     resource=f"{agent_id}.{verb}", outcome="ok" if out["ok"] else "error", args=args,
                     result=out.get("result", out.get("error")), detail={"channel": channel})
    if not out["ok"]:
        raise CapabilityError(json.dumps(out.get("error"), ensure_ascii=False, default=str), out.get("status", 400))
    return out["result"] if isinstance(out["result"], dict) else {"result": out["result"]}


async def _orchestrate(message: str, agent_scope: str | None, p: Principal, level: str = "L2") -> dict:
    with SessionLocal() as db:
        r = await orchestrator.start(db, principal=p.actor, role=p.role, message=message, agent_scope=agent_scope,
                                     data_class=level)
    return {k: r.get(k) for k in ("task_id", "state", "answer", "pending")}


async def _call_tool(request, name: str, args: dict):
    p: Principal = request.scope["state"]["plaza_principal"]
    agent_id = request.path_params["agent"]
    level = request.scope["state"].get("plaza_level", "L2")
    if agent_id == "orchestrator":
        return await _orchestrate(args["message"], args.get("agent_scope"), p, level)
    return await invoke_capability(agent_id, name, args, p, "mcp", level)


MCP_ROUTE = Route("/mcp/{agent}", endpoint=MCPEndpoint(mcp_server("agentplaza", "0.1.0", _list_tools, _call_tool),
                                                       guard=_guard))


# ---------- A2A ----------

ORCH_MANIFEST = {"metadata": {"id": "orchestrator", "name": "AgentPlaza Orchestrator", "version": "0.1.0",
                              "description": "설치된 에이전트로 요청을 계획·라우팅·실행 / plan and route requests"},
                 "spec": {"type": "service", "capabilities": [
                     {"verb": "orchestrate", "domain": "platform.orchestration", "description": "자연어 요청 실행",
                      "inputSchema": ORCH_TOOLS[0]["inputSchema"]}]}}


def mount_orchestrator_a2a(app) -> None:
    """Orchestrator 를 A2A Task 로 노출(PRD 4.2). 카드는 플랫폼 서명."""

    async def invoke(verb: str, args: dict, headers: dict):
        p = _principal_from({k.lower(): v for k, v in headers.items()})
        if p is None:
            raise CapabilityError("unauthorized", 401)
        return await _orchestrate(args.get("message") or "", args.get("agent_scope"), p)

    card = cards.sign(build_card(ORCH_MANIFEST, cards.rpc_url("orchestrator")))
    a2a_routes(app, card, CapabilityExecutor(ORCH_MANIFEST["spec"]["capabilities"], invoke),
               prefix="/a/orchestrator", rpc_path="/a2a")


@router.get("/.well-known/jwks.json")
def jwks():
    return keys.jwks()


@router.get("/a/{agent_id}/.well-known/agent-card.json")
def agent_card(agent_id: str, db: Session = Depends(get_db)):
    """공개(NFR-S5 허용목록). 카탈로그의 agent.yaml 에서 생성·서명한다 — 손으로 쓴 Card 금지(DP4)."""
    a = db.get(Agent, agent_id)
    if a is None or a.builtin or a.source == "link" or not a.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent card not found")
    return JSONResponse(cards.signed_card_json(a.manifest), headers={"Cache-Control": "max-age=60"})


@router.get("/a/{agent_id}/mcp/server.json", dependencies=[Depends(current_principal)])
def server_json(agent_id: str, db: Session = Depends(get_db)):
    a = db.get(Agent, agent_id)
    if a is None or a.builtin or a.source == "link":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    return cards.server_json(a.manifest)


@router.post("/a/{agent_id}/a2a")
async def a2a_proxy(agent_id: str, request: Request):
    """인증·범위 검사 후 에이전트 컨테이너의 A2A JSON-RPC 로 프록시. 승인 필요 capability 는 에이전트가 403 으로 거부."""
    headers = {k.lower(): v for k, v in request.headers.items()}
    p = _principal_from(headers)
    if p is None:
        return _rpc_error(-32001, 401, "unauthorized")
    agent, why = _agent_accessible(agent_id, p)
    if agent is None or agent.builtin or agent.source == "link" or not agent.endpoint:
        return _rpc_error(-32601, 404, why or "agent has no A2A endpoint")
    fwd = {k: v for k, v in headers.items() if k in ("content-type", "accept", "a2a-version")}
    fwd.update({"x-api-key": registry.agent_key(agent_id), "x-plaza-user": p.actor})
    body = await request.body()
    client = httpx.AsyncClient(base_url=agent.endpoint, transport=executor.TRANSPORTS.get(agent.endpoint), timeout=120)
    req = client.build_request("POST", "/a2a", content=body, headers=fwd)
    upstream = await client.send(req, stream=True)
    with SessionLocal() as db:
        audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="a2a.request",
                     resource=f"a2a:{agent_id}", args=body.decode("utf-8", "replace"), outcome="ok" if upstream.status_code < 400 else "error")
    ctype = upstream.headers.get("content-type", "application/json")
    if ctype.startswith("text/event-stream"):
        async def relay():
            try:
                async for chunk in upstream.aiter_raw():
                    yield chunk
            finally:
                await upstream.aclose()
                await client.aclose()
        return StreamingResponse(relay(), status_code=upstream.status_code, media_type="text/event-stream")
    data = await upstream.aread()
    await upstream.aclose()
    await client.aclose()
    return Response(data, status_code=upstream.status_code, media_type=ctype)
