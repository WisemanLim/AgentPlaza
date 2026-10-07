"""통합 게이트웨이 라우터 (D1-05·D1-06).

- 별칭 → 대상 목록(1순위 + 폴백). 첫 토큰 전 장애·타임아웃이면 다음 대상으로(NFR-L1, 전체 예산 30초).
- 데이터 등급(L0~L3): 헤더 없으면 L2. 등급별 허용 모델은 정책(D9-05 data.model_locality, 기본 L2 이상 local 만) —
  등급 규칙이 폴백보다 우선(PRD 13.1, NFR-L3). 퍼블릭 대상으로 나가는 메시지는 한국어 PII 를 마스킹한다(D9-06).
- 사용량 계량(llm_usage)과 정책 거부 감사 기록.
"""
import asyncio
import time

import httpx
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal
from app.llm.providers import ChatRequest, ChatResult, ProviderError, build_providers, estimate_tokens
from app.governance import guardrails
from app.governance import policy as gov
from app.llm import budget
from app.models import LlmModel, LlmRoute, LlmUsage
from app.observability import SpanKind, Status, StatusCode, clean, tracer
from app.services import audit

LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
CLASS_TO_LEVEL = {"public": "L0", "internal": "L1", "confidential": "L3"}
DEFAULT_LEVEL = "L2"


def parse_data_class(value: str | None) -> str:
    if not value:
        return DEFAULT_LEVEL
    v = value.strip()
    if v.upper() in LEVELS:
        return v.upper()
    if v.lower() in CLASS_TO_LEVEL:
        return CLASS_TO_LEVEL[v.lower()]
    raise ValueError(f"data class ∈ L0..L3 | {list(CLASS_TO_LEVEL)}")


class NoRoute(Exception):
    pass


class PolicyDenied(Exception):
    def __init__(self, level: str, blocked: list[str], reason: str = "data_class"):
        super().__init__(f"data class {level} 는 로컬 모델만 허용 — 허용 대상 없음 / no local target" if reason == "data_class"
                         else "월 예산 기준 도달 — 로컬 모델만 허용, 로컬 대상 없음 / budget: local only, no local target")
        self.level, self.blocked, self.reason = level, blocked, reason


class AllTargetsFailed(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class Caller:
    principal: str | None = None
    agent_id: str | None = None


@dataclass
class RouteMeta:
    alias: str
    level: str
    model: str = ""
    fallback_from: str | None = None
    blocked: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    budget_forced: bool = False

    @property
    def degraded(self) -> bool:
        return self.fallback_from is not None

    def headers(self) -> dict[str, str]:
        h = {"x-plaza-model": self.model, "x-plaza-data-class": self.level,
             "x-plaza-degraded": "true" if self.degraded else "false"}
        if self.fallback_from:
            h["x-plaza-fallback-from"] = self.fallback_from
        if self.budget_forced:
            h["x-plaza-budget"] = "local-forced"
        return h


class Router:
    def __init__(self, providers: dict | None = None):
        self.providers = providers if providers is not None else build_providers(
            settings.llm_target_timeout, settings.mock_slow_seconds)

    def plan(self, db: Session, alias: str, level: str, *, kind: str = "chat", vision: bool = False,
             meta: "RouteMeta | None" = None) -> tuple[list[LlmModel], list[str]]:
        from app.llm import servers
        servers.sync(db, self.providers)  # 등록된 OpenAI 호환 서버(D1-02)
        route = db.get(LlmRoute, alias)
        if route is None:
            raise NoRoute(f"unknown alias: {alias}")
        models = [m for m in (db.get(LlmModel, t) for t in route.targets)
                  if m is not None and m.enabled and m.provider in self.providers and (m.kind or "chat") == kind
                  and (m.vision or not vision)]
        if not models:
            raise NoRoute(f"{alias}: {'비전' if vision else kind} 대상 없음 / no {'vision' if vision else kind} target")
        local_only = gov.local_only(gov.get(db), level)
        allowed = [m for m in models if m.local or not local_only]
        blocked = [m.id for m in models if m not in allowed]
        if not allowed:
            raise PolicyDenied(level, blocked)
        if any(not m.local for m in allowed) and budget.forced(db):  # J05: 월 예산 기준 도달 → 로컬만
            blocked += [m.id for m in allowed if not m.local]
            allowed = [m for m in allowed if m.local]
            if meta is not None:
                meta.budget_forced = True
            budget.note_forced(db)
            if not allowed:
                raise PolicyDenied(level, blocked, reason="budget")
        return allowed, blocked

    def _meter(self, db: Session, meta: RouteMeta, caller: Caller, m: LlmModel | None, usage: dict,
               started: float, outcome: str = "ok") -> None:
        tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        cost = (tin * m.cost_in + tout * m.cost_out) / 1000 if m else 0.0
        db.add(LlmUsage(alias=meta.alias, model=meta.model or "-", agent_id=caller.agent_id, principal=caller.principal,
                        data_class=meta.level, tokens_in=tin, tokens_out=tout, cost=cost,
                        latency_ms=int((time.monotonic() - started) * 1000), fallback_from=meta.fallback_from,
                        outcome=outcome))
        db.commit()

    def _deny(self, db: Session, exc: PolicyDenied, alias: str, caller: Caller) -> None:
        audit.record(db, actor=caller.principal or "anonymous", actor_type="service" if caller.agent_id else "user",
                     agent_id=caller.agent_id, action="llm.policy_denied", resource=f"alias:{alias}",
                     outcome="denied", detail={"level": exc.level, "blocked": exc.blocked, "reason": exc.reason})

    async def complete(self, db: Session, alias: str, req: ChatRequest, *, level: str = DEFAULT_LEVEL,
                       caller: Caller | None = None) -> tuple[ChatResult, RouteMeta]:
        caller = caller or Caller()
        meta = RouteMeta(alias=alias, level=level)
        try:
            targets, meta.blocked = self.plan(db, alias, level, vision=has_images(req), meta=meta)
        except PolicyDenied as exc:
            self._deny(db, exc, alias, caller)
            raise
        started = time.monotonic()
        deadline = started + settings.llm_fallback_budget
        with tracer().start_as_current_span(f"chat {alias}", kind=SpanKind.CLIENT) as span:
            for m in targets:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    res = await asyncio.wait_for(self.providers[m.provider].complete(m.model_id, _outbound(db, m, req)),
                                                 timeout=min(settings.llm_target_timeout, remaining))
                except (ProviderError, TimeoutError) as exc:
                    meta.errors.append(f"{m.id}: {exc or 'timeout'}")
                    meta.fallback_from = meta.fallback_from or m.id
                    continue
                meta.model = m.id
                self._meter(db, meta, caller, m, res.usage, started)
                span.set_attributes(_genai(meta, caller, m, res.usage))
                return res, meta
            self._meter(db, meta, caller, None, {}, started, outcome="error")
            span.set_attributes(_genai(meta, caller, None, {}))
            span.set_status(Status(StatusCode.ERROR, "all targets failed"))
            raise AllTargetsFailed(meta.errors)

    async def stream(self, db: Session, alias: str, req: ChatRequest, *, level: str = DEFAULT_LEVEL,
                     caller: Caller | None = None) -> tuple[RouteMeta, AsyncIterator[dict]]:
        """첫 청크를 받은 대상으로 확정한 뒤 (meta, 나머지 스트림)을 돌려준다. 첫 청크 전 장애만 폴백한다."""
        caller = caller or Caller()
        meta = RouteMeta(alias=alias, level=level)
        try:
            targets, meta.blocked = self.plan(db, alias, level, vision=has_images(req), meta=meta)
        except PolicyDenied as exc:
            self._deny(db, exc, alias, caller)
            raise
        started = time.monotonic()
        deadline = started + settings.llm_fallback_budget
        for m in targets:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            gen = self.providers[m.provider].stream(m.model_id, _outbound(db, m, req)).__aiter__()
            try:
                first = await asyncio.wait_for(gen.__anext__(), timeout=min(settings.llm_target_timeout, remaining))
            except StopAsyncIteration:
                first = {"delta": ""}
            except (ProviderError, TimeoutError) as exc:
                meta.errors.append(f"{m.id}: {exc or 'timeout'}")
                meta.fallback_from = meta.fallback_from or m.id
                await gen.aclose()
                continue
            meta.model = m.id
            return meta, self._tail(db, meta, caller, m, first, gen, started, req)
        self._meter(db, meta, caller, None, {}, started, outcome="error")
        raise AllTargetsFailed(meta.errors)

    async def _tail(self, db, meta, caller, m, first, gen, started, req) -> AsyncIterator[dict]:
        usage: dict = {}
        text = []
        span = tracer().start_span(f"chat {meta.alias}", kind=SpanKind.CLIENT, attributes={"plaza.stream": True})
        try:
            chunk = first
            while True:
                if "usage" in chunk:
                    usage = chunk["usage"]
                else:
                    text.append(chunk.get("delta", ""))
                    yield chunk
                try:
                    chunk = await gen.__anext__()
                except StopAsyncIteration:
                    break
        finally:
            if not usage:  # 공급자가 usage 를 안 주면 추정치로 계량
                usage = {"prompt_tokens": estimate_tokens(str(req.messages)), "completion_tokens": estimate_tokens("".join(text))}
            # 스트림은 요청 의존성(세션)이 끝난 뒤에도 이어지므로 계량은 별도 세션으로 기록한다.
            with SessionLocal() as own:
                self._meter(own, meta, caller, m, usage, started)
            span.set_attributes(_genai(meta, caller, m, usage))
            span.end()


    async def embed(self, db: Session, alias: str, inputs: list[str], *, level: str = DEFAULT_LEVEL,
                    caller: Caller | None = None) -> tuple[list[list[float]], RouteMeta]:
        """임베딩(D1-07): 별칭·폴백·데이터 등급·계량은 채팅과 같다. 퍼블릭 대상이면 PII 마스킹 후 보낸다."""
        caller = caller or Caller()
        meta = RouteMeta(alias=alias, level=level)
        try:
            targets, meta.blocked = self.plan(db, alias, level, kind="embedding", meta=meta)
        except PolicyDenied as exc:
            self._deny(db, exc, alias, caller)
            raise
        started = time.monotonic()
        for m in targets:
            texts = inputs if m.local or not gov.get(db)["guardrails"]["pii_mask_public"] else \
                [guardrails.mask_pii(t)[0] for t in inputs]
            try:
                vecs, usage = await asyncio.wait_for(self.providers[m.provider].embed(m.model_id, texts),
                                                     timeout=settings.llm_target_timeout * 3)
            except (ProviderError, TimeoutError, AttributeError) as exc:
                meta.errors.append(f"{m.id}: {exc or 'timeout'}")
                meta.fallback_from = meta.fallback_from or m.id
                continue
            meta.model = m.id
            self._meter(db, meta, caller, m, {"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": 0},
                        started)
            return vecs, meta
        self._meter(db, meta, caller, None, {}, started, outcome="error")
        raise AllTargetsFailed(meta.errors)

    async def rerank(self, db: Session, query: str, documents: list[str], *, top_n: int | None = None,
                     level: str = DEFAULT_LEVEL, caller: Caller | None = None) -> tuple[list[dict], str]:
        """재정렬(D1-07, 내부 규격 POST /v1/rerank). TEI_RERANK_URL 이 있으면 교차 인코더, 없으면 임베딩 코사인."""
        if not documents:
            return [], "none"
        if settings.tei_rerank_url:
            try:
                async with httpx.AsyncClient(timeout=settings.llm_target_timeout) as c:
                    res = await c.post(f"{settings.tei_rerank_url.rstrip('/')}/rerank",
                                       json={"query": query, "texts": documents, "raw_scores": False})
                res.raise_for_status()
                scored = [{"index": r["index"], "relevance_score": float(r["score"])} for r in res.json()]
                return sorted(scored, key=lambda r: -r["relevance_score"])[:top_n or len(documents)], "tei"
            except (httpx.HTTPError, KeyError, ValueError):
                pass  # 교차 인코더 장애 → 임베딩 코사인으로 강등
        vecs, meta = await self.embed(db, "plaza/embed", [query, *documents], level=level, caller=caller)
        q = vecs[0]
        scored = [{"index": i, "relevance_score": cosine(q, v)} for i, v in enumerate(vecs[1:])]
        return sorted(scored, key=lambda r: -r["relevance_score"])[:top_n or len(documents)], meta.model


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return dot / (na * nb)


def has_images(req: ChatRequest) -> bool:
    return any(isinstance(m.get("content"), list) and any(isinstance(p, dict) and p.get("type") == "image_url"
                                                            for p in m["content"]) for m in req.messages)


def _outbound(db: Session, m: LlmModel, req: ChatRequest) -> ChatRequest:
    """퍼블릭(비로컬) 모델로 나가는 메시지는 PII 를 마스킹한다(정책 guardrails.pii_mask_public)."""
    if m.local or not gov.get(db)["guardrails"]["pii_mask_public"]:
        return req
    messages, found = guardrails.mask_messages(req.messages)
    if not found:
        return req
    from dataclasses import replace
    return replace(req, messages=messages)


def _genai(meta: RouteMeta, caller: Caller, m: LlmModel | None, usage: dict) -> dict:
    """OTel GenAI semconv(PRD 12.6) — 프롬프트 원문은 넣지 않는다."""
    return clean({"gen_ai.operation.name": "chat", "gen_ai.system": m.provider if m else None,
                  "gen_ai.request.model": meta.alias, "gen_ai.response.model": m.model_id if m else None,
                  "gen_ai.usage.input_tokens": usage.get("prompt_tokens"),
                  "gen_ai.usage.output_tokens": usage.get("completion_tokens"),
                  "gen_ai.agent.id": caller.agent_id, "plaza.model": meta.model or None, "plaza.data_class": meta.level,
                  "plaza.fallback_from": meta.fallback_from, "plaza.degraded": meta.degraded})


_router: Router | None = None


def get_router() -> Router:
    global _router
    if _router is None:
        _router = Router()
    return _router


def aliases(db: Session) -> list[LlmRoute]:
    return list(db.execute(select(LlmRoute).order_by(LlmRoute.alias)).scalars())
