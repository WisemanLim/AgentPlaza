"""LLM 카탈로그·라우팅·사용량 API (D1-05·D1-06, UI J01·J02·J04·J05) + OpenAI 호환 /v1 (게이트웨이 단일 엔드포인트)."""
import json
import time
import uuid
from collections import defaultdict
from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin, require_supervisor, require_user
from app.db import get_db, utcnow
from app.llm import budget
from app.llm.providers import BifrostProvider, ChatRequest
from app.llm.router import (AllTargetsFailed, Caller, NoRoute, PolicyDenied, aliases, get_router,
                            parse_data_class)
from app.models import LlmModel, LlmRoute, LlmUsage
from app.services import audit

router = APIRouter(prefix="/api/llm", tags=["llm"], dependencies=[Depends(require_user)])
v1 = APIRouter(prefix="/v1", tags=["openai-compat"], dependencies=[Depends(require_user)])


class ModelIn(BaseModel):
    """NFR-L5: context·tool_call·vision·license·local 은 필수."""
    provider: str
    model_id: str
    local: bool
    context: int = Field(gt=0)
    tool_call: bool
    vision: bool
    license: str = Field(min_length=1)
    commercial_use: str = Field(default="allowed", pattern="^(allowed|conditional|prohibited)$")
    cost_in: float = 0.0
    cost_out: float = 0.0
    enabled: bool = True
    kind: str = Field(default="chat", pattern="^(chat|embedding)$")


class ModelPatch(BaseModel):
    enabled: bool | None = None
    commercial_use: str | None = Field(default=None, pattern="^(allowed|conditional|prohibited)$")
    cost_in: float | None = None
    cost_out: float | None = None
    acknowledge_license: bool = False


class RouteIn(BaseModel):
    targets: list[str] = Field(min_length=1)
    description: str | None = None


def model_out(m: LlmModel) -> dict:
    return {c: getattr(m, c) for c in ("id", "provider", "model_id", "local", "context", "tool_call", "vision",
                                       "license", "commercial_use", "cost_in", "cost_out", "enabled", "kind")}


def _license_gate(commercial_use: str, enabled: bool, ack: bool) -> None:
    if enabled and commercial_use == "prohibited":
        raise HTTPException(status.HTTP_409_CONFLICT, "상업 이용 금지 모델은 활성화 불가 / prohibited")
    if enabled and commercial_use == "conditional" and not ack:
        raise HTTPException(status.HTTP_409_CONFLICT, "조건부 라이선스 — acknowledge_license=true 필요")


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    return [model_out(m) for m in db.execute(select(LlmModel).order_by(LlmModel.id)).scalars()]


@router.post("/models", status_code=201)
def add_model(body: ModelIn, ack: bool = False, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    mid = f"{body.provider}/{body.model_id}"
    if db.get(LlmModel, mid):
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 존재 / exists")
    _license_gate(body.commercial_use, body.enabled, ack)
    m = LlmModel(id=mid, **body.model_dump())
    db.add(m)
    audit.record(db, actor=p.actor, actor_type=p.type, action="llm.model_added", resource=f"model:{mid}")
    return model_out(m)


@router.patch("/models/{model_id:path}")
def patch_model(model_id: str, body: ModelPatch, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    m = db.get(LlmModel, model_id)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "모델 없음 / not found")
    cu = body.commercial_use or m.commercial_use
    enabled = m.enabled if body.enabled is None else body.enabled
    _license_gate(cu, enabled, body.acknowledge_license)
    for k, v in body.model_dump(exclude_none=True, exclude={"acknowledge_license"}).items():
        setattr(m, k, v)
    audit.record(db, actor=p.actor, actor_type=p.type, action="llm.model_updated", resource=f"model:{model_id}",
                 detail=body.model_dump(exclude_none=True))
    return model_out(m)


class ServerIn(BaseModel):
    base_url: str = Field(pattern=r"^https?://", max_length=500)
    local: bool = True  # 내부망 서버(vLLM·llama-server 등) = 로컬. CLI 브리지처럼 외부로 나가면 false
    api_key: str | None = Field(default=None, max_length=4000)


@router.get("/servers", dependencies=[Depends(require_admin)])
def list_servers(db: Session = Depends(get_db)):
    from app.llm import servers
    return [{"name": n, **cfg} for n, cfg in sorted(servers.all_servers(db).items())]


@router.put("/servers/{name}")
def put_server(name: str, body: ServerIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """OpenAI 호환 서버 등록(D1-02). 모델은 /servers/{name}/models 로 확인하고 /models 로 카탈로그에 올린다."""
    from app.llm import servers
    try:
        out = servers.put(db, name, body.base_url, body.local, body.api_key, p.actor)
    except servers.ServerError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    servers.sync(db, get_router().providers)
    audit.record(db, actor=p.actor, actor_type=p.type, action="llm.server_put", resource=f"server:{name}",
                 detail={"base_url": body.base_url, "local": body.local})
    return out


@router.delete("/servers/{name}")
def delete_server(name: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    from app.llm import servers
    try:
        servers.remove(db, name)
    except servers.ServerError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    servers.sync(db, get_router().providers)
    for m in db.execute(select(LlmModel).where(LlmModel.provider == name)).scalars():
        m.enabled = False  # 서버가 없어진 모델은 끈다(라우팅 제외)
    audit.record(db, actor=p.actor, actor_type=p.type, action="llm.server_deleted", resource=f"server:{name}")
    return {"deleted": name}


@router.get("/servers/{name}/models", dependencies=[Depends(require_admin)])
async def server_models(name: str, db: Session = Depends(get_db)):
    from app.llm import servers
    servers.sync(db, get_router().providers)
    prov = get_router().providers.get(name)
    if prov is None or not getattr(prov, "registered", False):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "서버 없음 / not found")
    try:
        return {"server": name, "models": await servers.models(prov)}
    except servers.ServerError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from None


@router.get("/routes")
def list_routes(db: Session = Depends(get_db)):
    return [{"alias": r.alias, "targets": r.targets, "description": r.description} for r in aliases(db)]


@router.put("/routes/{alias:path}")
def put_route(alias: str, body: RouteIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    if not alias.startswith("plaza/"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "별칭은 plaza/ 로 시작 / alias must start with plaza/")
    missing = [t for t in body.targets if db.get(LlmModel, t) is None]
    if missing:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"카탈로그에 없는 모델: {missing}")
    r = db.get(LlmRoute, alias) or LlmRoute(alias=alias)
    r.targets, r.description = body.targets, body.description
    db.add(r)
    audit.record(db, actor=p.actor, actor_type=p.type, action="llm.route_set", resource=f"alias:{alias}",
                 detail={"targets": body.targets})
    return {"alias": alias, "targets": r.targets, "description": r.description}


@router.get("/providers")
async def providers():
    out = []
    provs = get_router().providers
    gw = next((p.gateway for p in provs.values() if isinstance(p, BifrostProvider)), None)
    if gw is not None:  # Bifrost(PRD Q1) — 공급자 호출 엔진. 장애 시 로컬 Ollama 는 직접 호출로 폴백
        item = {"name": "bifrost", "configured": True, "via": "gateway", "reachable": False,
                "fallbacks": sum(getattr(p, "fallbacks", 0) for p in provs.values())}
        try:
            async with httpx.AsyncClient(timeout=3, transport=gw.TRANSPORTS.get(gw.base_url)) as c:
                item["reachable"] = (await c.get(gw.base_url.removesuffix("/v1") + "/health")).status_code == 200
        except httpx.HTTPError:
            pass
        out.append(item)
    for name, prov in provs.items():
        item = {"name": name, "configured": True, "reachable": None, "via": getattr(prov, "via", "direct")}
        if name == "ollama":
            base = (prov.direct if isinstance(prov, BifrostProvider) else prov).base_url
            try:
                async with httpx.AsyncClient(timeout=3) as c:
                    res = await c.get(base.removesuffix("/v1") + "/api/tags")
                item["reachable"] = res.status_code == 200
                item["models"] = [m["name"] for m in res.json().get("models", [])] if res.status_code == 200 else []
            except httpx.HTTPError:
                item["reachable"] = False
        out.append(item)
    return out


class BudgetIn(BaseModel):
    monthly: float = Field(ge=0)
    ratio: float = Field(default=0.8, ge=0.5, le=1.0)


@router.get("/budget", dependencies=[Depends(require_admin)])
def get_budget(db: Session = Depends(get_db)):
    """월 예산·이번 달 사용·로컬 강제 여부(J05)."""
    return budget.status(db)


@router.put("/budget")
def put_budget(body: BudgetIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    budget.set_config(db, monthly=body.monthly, ratio=body.ratio)
    audit.record(db, actor=p.actor, actor_type=p.type, action="llm.budget_set", detail=body.model_dump())
    return budget.status(db)


@router.get("/usage")
def usage(days: int = 7, db: Session = Depends(get_db)):
    since = utcnow() - timedelta(days=days)
    agg: dict = defaultdict(lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0, "fallbacks": 0,
                                     "errors": 0})
    local_calls = total = 0
    for u in db.execute(select(LlmUsage).where(LlmUsage.ts >= since)).scalars():
        a = agg[u.alias]
        a["calls"] += 1
        a["tokens_in"] += u.tokens_in
        a["tokens_out"] += u.tokens_out
        a["cost"] += u.cost
        a["fallbacks"] += bool(u.fallback_from)
        a["errors"] += u.outcome != "ok"
        total += 1
        local_calls += u.model.startswith(("ollama/", "mock/"))
    return {"days": days, "by_alias": dict(agg), "local_ratio": (local_calls / total) if total else None}


# ---------- OpenAI 호환 게이트웨이 ----------

class ChatIn(BaseModel):
    model: str = "plaza/chat"
    messages: list[dict] = Field(min_length=1)
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[dict] | None = None
    tool_choice: str | dict | None = None
    response_format: dict | None = None


def _caller(p: Principal) -> Caller:
    return Caller(principal=p.actor, agent_id=p.scopes.get("agent") if p.type == "service" else None)


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, PolicyDenied):
        return HTTPException(status.HTTP_403_FORBIDDEN, {"error": "policy_denied", "level": exc.level, "reason": exc.reason,
                                                         "blocked": exc.blocked, "message": str(exc)})
    if isinstance(exc, NoRoute):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, {"error": "all_targets_failed", "detail": str(exc)})


AGENT = "agent/"


@v1.get("/models")
def v1_models(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    """별칭 + 에이전트를 모델로(D7-05): Open WebUI·LibreChat 이 agent/<id> 를 골라 쓴다."""
    from app.services import registry
    agents = sorted({c["agent"] for c in registry.routable(db, viewer=(p.actor, p.role))} | {"orchestrator"})
    return {"object": "list", "data": [{"id": r.alias, "object": "model", "owned_by": "agentplaza"} for r in aliases(db)]
            + [{"id": f"{AGENT}{a}", "object": "model", "owned_by": "agentplaza-agent"} for a in agents
               if p.can_access_agent(a)]}


def _text(content) -> str:
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    return str(content or "")


async def _agent_completion(body: "ChatIn", p: Principal, db: Session, level: str):
    """agent/<id> 모델 = 그 에이전트로 범위를 좁힌 Orchestrator 실행. 답변 텍스트를 OpenAI 응답·스트림으로 돌려준다."""
    import asyncio

    from app.orchestrator import service as orchestrator
    from app.services import registry
    aid = body.model[len(AGENT):]
    if not p.can_access_agent(aid):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "키 범위 밖 에이전트 / agent out of key scope")
    if aid != "orchestrator" and not registry.routable(db, aid, viewer=(p.actor, p.role)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown model: {body.model}")
    users = [m for m in body.messages if m.get("role") == "user"]
    if not users:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "user 메시지 필요 / user message required")
    message = _text(users[-1].get("content"))
    history = [{"role": m["role"], "content": _text(m.get("content"))} for m in body.messages[:-1]
               if m.get("role") in ("user", "assistant")][-20:]
    rid, created = f"chatcmpl-{uuid.uuid4().hex[:24]}", int(time.time())
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(ev: dict) -> None:
        await queue.put(ev)

    async def run(session: Session) -> dict:
        try:
            return await orchestrator.start(session, principal=p.actor, role=p.role, message=message, history=history,
                                            agent_scope=None if aid == "orchestrator" else aid, emit=emit, data_class=level)
        finally:
            await queue.put(None)

    def note(ev: dict) -> str | None:
        if ev.get("type") == "CUSTOM" and ev.get("name") == "approval_required":
            v = ev["value"]
            return f"\n⚠ 승인 필요 / approval required: {v['agent']}.{v['capability']} (approval {v['approval_id']})\n"
        return None

    headers = {"x-plaza-agent": aid, "x-plaza-data-class": level}
    if not body.stream:
        result = await run(db)
        text = result.get("answer") or ""
        if result.get("pending"):
            text += note({"type": "CUSTOM", "name": "approval_required", "value": result["pending"]}) or ""
        return JSONResponse({"id": rid, "object": "chat.completion", "created": created, "model": body.model,
                             "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                                          "finish_reason": "stop"}],
                             "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                             "plaza": {"task_id": result["task_id"], "state": result["state"]}}, headers=headers)

    async def sse():
        from app.db import SessionLocal
        own = SessionLocal()  # 스트림은 요청 의존성(세션)보다 오래 산다
        task = asyncio.create_task(run(own))

        def frame(delta: dict, finish: str | None = None) -> str:
            return "data: " + json.dumps({"id": rid, "object": "chat.completion.chunk", "created": created,
                                          "model": body.model, "choices": [{"index": 0, "delta": delta,
                                                                            "finish_reason": finish}]},
                                         ensure_ascii=False) + "\n\n"
        yield frame({"role": "assistant"})
        while (ev := await queue.get()) is not None:
            if ev.get("type") == "TEXT_MESSAGE_CONTENT":
                yield frame({"content": ev["delta"]})
            elif (n := note(ev)) is not None:
                yield frame({"content": n})
        await task
        own.close()
        yield frame({}, "stop")
        yield "data: [DONE]\n\n"
    return StreamingResponse(sse(), media_type="text/event-stream", headers=headers)


@v1.post("/chat/completions")
async def chat_completions(body: ChatIn, p: Principal = Depends(require_user), db: Session = Depends(get_db),
                           x_plaza_data_class: str | None = Header(default=None)):
    try:
        level = parse_data_class(x_plaza_data_class)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    if body.model.startswith(AGENT):
        return await _agent_completion(body, p, db, level)
    req = ChatRequest(**body.model_dump(include={"messages", "temperature", "max_tokens", "tools", "tool_choice",
                                                  "response_format"}))
    rid, created = f"chatcmpl-{uuid.uuid4().hex[:24]}", int(time.time())
    r = get_router()
    try:
        if body.stream:
            meta, chunks = await r.stream(db, body.model, req, level=level, caller=_caller(p))
        else:
            res, meta = await r.complete(db, body.model, req, level=level, caller=_caller(p))
    except (PolicyDenied, NoRoute, AllTargetsFailed) as exc:
        raise _error(exc) from None

    if not body.stream:
        msg: dict = {"role": "assistant", "content": res.content}
        if res.tool_calls:
            msg["tool_calls"] = res.tool_calls
        return JSONResponse({"id": rid, "object": "chat.completion", "created": created, "model": body.model,
                             "choices": [{"index": 0, "message": msg, "finish_reason": res.finish_reason}],
                             "usage": {**res.usage, "total_tokens": sum(res.usage.values())}},
                            headers=meta.headers())

    async def sse():
        def frame(delta: dict, finish: str | None = None) -> str:
            return "data: " + json.dumps({"id": rid, "object": "chat.completion.chunk", "created": created,
                                          "model": body.model, "choices": [{"index": 0, "delta": delta,
                                                                            "finish_reason": finish}]},
                                         ensure_ascii=False) + "\n\n"
        yield frame({"role": "assistant"})
        async for c in chunks:
            if c.get("delta"):
                yield frame({"content": c["delta"]})
            if c.get("tool_calls"):
                yield frame({"tool_calls": c["tool_calls"]})
        yield frame({}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream", headers=meta.headers())


class EmbedIn(BaseModel):
    model: str = "plaza/embed"
    input: str | list[str]


@v1.post("/embeddings")
async def embeddings(body: EmbedIn, p: Principal = Depends(require_user), db: Session = Depends(get_db),
                     x_plaza_data_class: str | None = Header(default=None)):
    """OpenAI 호환 임베딩(D1-07). 등급 규칙·폴백·계량은 채팅과 같다."""
    try:
        level = parse_data_class(x_plaza_data_class)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    inputs = [body.input] if isinstance(body.input, str) else body.input
    if not inputs or len(inputs) > 256:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "input 1~256개 / 1..256 inputs")
    try:
        vecs, meta = await get_router().embed(db, body.model, inputs, level=level, caller=_caller(p))
    except (PolicyDenied, NoRoute, AllTargetsFailed) as exc:
        raise _error(exc) from None
    return JSONResponse({"object": "list", "model": body.model,
                         "data": [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vecs)],
                         "usage": {"prompt_tokens": sum(len(t) // 4 + 1 for t in inputs), "total_tokens": 0}},
                        headers=meta.headers())


class RerankIn(BaseModel):
    query: str = Field(min_length=1)
    documents: list[str] = Field(min_length=1, max_length=200)
    top_n: int | None = Field(default=None, ge=1)
    return_documents: bool = False


@v1.post("/rerank")
async def rerank(body: RerankIn, p: Principal = Depends(require_user), db: Session = Depends(get_db),
                 x_plaza_data_class: str | None = Header(default=None)):
    """내부 규격 재정렬(D1-07): TEI 교차 인코더(설정 시) 또는 임베딩 코사인."""
    try:
        level = parse_data_class(x_plaza_data_class)
        results, by = await get_router().rerank(db, body.query, body.documents, top_n=body.top_n, level=level,
                                                caller=_caller(p))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    except (PolicyDenied, NoRoute, AllTargetsFailed) as exc:
        raise _error(exc) from None
    if body.return_documents:
        results = [{**r, "document": body.documents[r["index"]]} for r in results]
    return {"model": by, "results": results}
