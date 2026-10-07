"""프로토콜 표면 (D7-01 MCP · D7-03 A2A) — agent.yaml 하나에서 생성한다(DP4, 손으로 쓴 Card 금지).

- MCP: 공식 python-sdk(mcp 2.x) 저수준 Server + stateless JSON StreamableHTTP. 요청마다 매니저를 만들어 같은
  코루틴 안에서 run→handle 하므로 lifespan 이 필요 없다. 2026-07-28(server/discover)·2025-11-25(initialize) 모두 응답.
- A2A: 공식 a2a-sdk(1.x, 프로토콜 1.0) 카드 라우트 + JSON-RPC(SendMessage·GetTask…). 메시지는 텍스트 또는
  Data Part({"capability", "args"}) 로 capability 에 매핑한다.
플랫폼 게이트웨이도 build_card·resolve_call 을 그대로 재사용한다.
"""
import json
import os
from collections.abc import Awaitable, Callable
from pathlib import Path

import jsonschema
import mcp.types as mtypes
from a2a.client.card_resolver import parse_agent_card
from a2a.helpers import get_data_parts, new_data_part, new_task_from_user_message, new_text_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.request_handlers.response_helpers import agent_card_to_dict
from a2a.server.routes import add_a2a_routes_to_fastapi, create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (AgentCapabilities, AgentCard, AgentInterface, AgentProvider, AgentSkill, APIKeySecurityScheme,
                       SecurityRequirement, SecurityScheme, StringList)
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.routing import Route

from agentplaza_sdk.agent import Agent, CapabilityError

CARD_PATH = "/.well-known/agent-card.json"


def _text(v) -> str:
    return " ".join(v.values()) if isinstance(v, dict) else str(v or "")


# ---------------- 공통: 카드·매핑 ----------------

def build_card(manifest: dict, rpc_url: str) -> AgentCard:
    meta, spec = manifest["metadata"], manifest["spec"]
    skills = [AgentSkill(id=c["verb"], name=c["verb"], description=_text(c.get("description")) or c["verb"],
                         tags=[c["domain"], spec["type"]] + (["approval-required"] if c.get("humanApprovalRequired") else []))
              for c in spec.get("capabilities", [])]
    return AgentCard(
        name=meta.get("name", meta["id"]), description=_text(meta.get("description")) or meta["id"],
        version=meta["version"],
        provider=AgentProvider(organization=meta.get("publisher", {}).get("id", "local"), url=meta.get("publisher", {}).get("url", "")),
        supported_interfaces=[AgentInterface(url=rpc_url, protocol_binding=TransportProtocol.JSONRPC,
                                             protocol_version=PROTOCOL_VERSION_CURRENT)],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain", "application/json"], default_output_modes=["application/json", "text/plain"],
        skills=skills,
        security_schemes={"apiKey": SecurityScheme(api_key_security_scheme=APIKeySecurityScheme(name="x-api-key",
                                                                                               location="header"))},
        security_requirements=[SecurityRequirement(schemes={"apiKey": StringList(list=[])})])


def card_json(card: AgentCard) -> dict:
    return agent_card_to_dict(card)


def load_card(data: dict) -> AgentCard:
    return parse_agent_card(data)


def _fill(cap: dict, text: str) -> dict:
    schema = cap.get("inputSchema", {})
    for k in schema.get("required", []):
        if schema.get("properties", {}).get(k, {}).get("type", "string") == "string":
            return {k: text}
    return {"text": text}


def resolve_call(capabilities: list[dict], text: str, data: list[dict] | None = None,
                 skill: str | None = None) -> tuple[str, dict]:
    """A2A 메시지 → (verb, args). Data Part {"capability","args"} > JSON 텍스트 > skill 힌트 > 단일 capability."""
    caps = {c["verb"]: c for c in capabilities}
    obj = next((d for d in (data or []) if isinstance(d, dict)), None)
    if obj is None and text.strip().startswith("{"):
        try:
            obj = json.loads(text)
        except ValueError:
            obj = None
    if isinstance(obj, dict) and obj.get("capability"):
        verb, args = obj["capability"], obj.get("args") or {}
    elif skill in caps:
        verb, args = skill, obj if isinstance(obj, dict) else _fill(caps[skill], text)
    elif len(caps) == 1:
        verb = next(iter(caps))
        args = obj if isinstance(obj, dict) else _fill(caps[verb], text)
    else:
        raise CapabilityError(f"capability 지정 필요 / specify one of {sorted(caps)} via data part "
                              '{"capability": ..., "args": {...}}')
    if verb not in caps:
        raise CapabilityError(f"unknown capability: {verb}", status=404)
    return verb, args


# ---------------- MCP ----------------

ToolsFn = Callable[[object], Awaitable[list[dict]]]
CallFn = Callable[[object, str, dict], Awaitable[dict]]


def mcp_server(name: str, version: str, list_tools: ToolsFn, call_tool: CallFn) -> Server:
    """list_tools(request) → [{"name","description","inputSchema"}], call_tool(request, name, args) → dict."""

    async def on_list_tools(ctx, params):
        tools = await list_tools(ctx.request)
        return mtypes.ListToolsResult(tools=[mtypes.Tool(name=t["name"], description=t.get("description", ""),
                                                         input_schema=t.get("inputSchema") or {"type": "object"})
                                             for t in tools])

    async def on_call_tool(ctx, params: mtypes.CallToolRequestParams):
        tools = {t["name"]: t for t in await list_tools(ctx.request)}
        tool, args = tools.get(params.name), params.arguments or {}
        if tool is None:
            return mtypes.CallToolResult(content=[mtypes.TextContent(text=f"unknown tool: {params.name}")], is_error=True)
        try:  # 저수준 Server 는 인자 검증을 하지 않는다 — 직접 검증
            jsonschema.validate(args, tool.get("inputSchema") or {"type": "object"})
            result = await call_tool(ctx.request, params.name, args)
        except jsonschema.ValidationError as exc:
            return mtypes.CallToolResult(content=[mtypes.TextContent(text=f"invalid arguments: {exc.message}")],
                                         is_error=True)
        except CapabilityError as exc:
            return mtypes.CallToolResult(content=[mtypes.TextContent(text=str(exc))], is_error=True)
        structured = result if isinstance(result, dict) else {"result": result}
        return mtypes.CallToolResult(content=[mtypes.TextContent(text=json.dumps(structured, ensure_ascii=False, default=str))],
                                     structured_content=structured)

    return Server(name, version=version, on_list_tools=on_list_tools, on_call_tool=on_call_tool)


class MCPEndpoint:
    """ASGI 엔드포인트. guard(scope) 가 응답(거부)을 돌려주면 그대로 보낸다."""

    def __init__(self, server: Server, guard=None):
        self.server, self.guard = server, guard

    async def __call__(self, scope, receive, send):
        if self.guard is not None:
            denied = await self.guard(scope)
            if denied is not None:
                return await denied(scope, receive, send)
        mgr = StreamableHTTPSessionManager(self.server, stateless=True, json_response=True)
        async with mgr.run():
            await mgr.handle_request(scope, receive, send)


# ---------------- A2A ----------------

class CapabilityExecutor(AgentExecutor):
    """A2A 메시지를 capability 호출로 바꿔 실행한다. invoke(verb, args, headers) → dict."""

    def __init__(self, capabilities: list[dict], invoke: Callable[[str, dict, dict], Awaitable[object]]):
        self.capabilities, self.invoke = capabilities, invoke

    async def execute(self, context: RequestContext, event_queue):
        task = context.current_task or new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.start_work()
        headers = (context.call_context.state or {}).get("headers", {}) if context.call_context else {}
        try:
            verb, args = resolve_call(self.capabilities, context.get_user_input() or "",
                                      get_data_parts(list(context.message.parts)),
                                      skill=(dict(context.message.metadata) or {}).get("skill"))
            result = await self.invoke(verb, args, headers)
        except CapabilityError as exc:
            return await updater.failed(new_text_message(str(exc), task_id=task.id, context_id=task.context_id))
        payload = result if isinstance(result, dict) else {"result": result}
        await updater.add_artifact([new_data_part(payload), new_text_part(json.dumps(payload, ensure_ascii=False, default=str))],
                                   name=verb)
        await updater.complete(new_text_message(f"{verb} done", task_id=task.id, context_id=task.context_id))

    async def cancel(self, context: RequestContext, event_queue):
        await TaskUpdater(event_queue, context.task_id, context.context_id).cancel()


def a2a_routes(app, card: AgentCard, executor: AgentExecutor, *, prefix: str = "", rpc_path: str = "/a2a") -> None:
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore(), agent_card=card)
    add_a2a_routes_to_fastapi(app, agent_card_routes=create_agent_card_routes(card, card_url=prefix + CARD_PATH),
                              jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url=prefix + rpc_path))


# ---------------- 에이전트 앱에 붙이기 ----------------

def _card_for(agent: Agent) -> AgentCard:
    """플랫폼이 서명해 넣은 카드(a2a/agent-card.json)가 있으면 그대로, 없으면 manifest 에서 생성(미서명, M1)."""
    f = Path(os.environ.get("AGENT_CARD_FILE", agent.base_dir / "a2a" / "agent-card.json"))
    if f.is_file():
        return load_card(json.loads(f.read_text(encoding="utf-8")))
    base = os.environ.get("AGENT_PUBLIC_URL", f"http://127.0.0.1:{os.environ.get('PORT', '8001')}").rstrip("/")
    return build_card(agent.manifest, base + "/a2a")


def mount(app, agent: Agent) -> None:
    def tools() -> list[dict]:
        return [{"name": c["verb"], "description": _text(c.get("description")), "inputSchema": c.get("inputSchema", {})}
                for c in agent.capabilities]

    async def list_tools(_request) -> list[dict]:
        return tools()

    async def call_tool(request, name: str, args: dict):
        caller = {k.removeprefix("x-plaza-"): v for k, v in request.headers.items() if k.startswith("x-plaza-")}
        return await agent.invoke(name, args, agent.context(caller))

    app.router.routes.append(Route("/mcp", endpoint=MCPEndpoint(mcp_server(agent.id, agent.version, list_tools, call_tool))))

    async def invoke(verb: str, args: dict, headers: dict):
        caller = {k.removeprefix("x-plaza-"): v for k, v in headers.items() if k.lower().startswith("x-plaza-")}
        return await agent.invoke(verb, args, agent.context(caller))

    a2a_routes(app, _card_for(agent), CapabilityExecutor(agent.capabilities, invoke))
