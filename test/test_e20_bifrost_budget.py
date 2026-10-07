"""Epic 20 — LLM 게이트웨이 Bifrost 전환·월 예산 기반 로컬 강제 (D1-01·D1-03·D1-05·D1-06, PRD Q1·Q15, UI J05).

Bifrost 는 가짜 ASGI 앱(OpenAI 호환 /v1, 모델 '<공급자>/<모델>')으로 흉내 낸다. 실제 Bifrost 는 test/impl 라이브 시나리오.
"""
import asyncio
import importlib.util
import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app import db as appdb
from app.llm import budget
from app.llm.providers import BifrostProvider, ChatRequest, OpenAICompatProvider, ProviderError, build_providers
from app.llm.router import Router
from app.models import LlmModel, LlmRoute, LlmUsage
from helpers import auth, make_user

ROOT = Path(__file__).resolve().parents[1]


def fake_openai(name: str, seen: list):
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        body = await request.json()
        seen.append((name, body["model"]))
        text = f"{name}:{body['model']}"
        if body.get("stream"):
            async def gen():
                yield "data: " + json.dumps({"choices": [{"delta": {"content": text}}]}) + "\n\n"
                yield "data: " + json.dumps({"choices": [], "usage": {"prompt_tokens": 3, "completion_tokens": 2}}) + "\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(gen(), media_type="text/event-stream")
        return {"choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2}}

    @app.post("/v1/embeddings")
    async def embed(request: Request):
        body = await request.json()
        seen.append((name, body["model"]))
        return {"data": [{"index": i, "embedding": [1.0, 0.0]} for i, _ in enumerate(body["input"])],
                "usage": {"prompt_tokens": 1}}

    @app.get("/health")
    def health():
        return JSONResponse({"status": "ok"})
    return app


@pytest.fixture
def bifrost(monkeypatch):
    seen: list = []
    monkeypatch.setenv("BIFROST_URL", "http://bifrost.test")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-be-used")
    monkeypatch.setitem(OpenAICompatProvider.TRANSPORTS, "http://bifrost.test/v1",
                        httpx.ASGITransport(app=fake_openai("bifrost", seen)))
    monkeypatch.setitem(OpenAICompatProvider.TRANSPORTS, "http://ollama.test/v1",
                        httpx.ASGITransport(app=fake_openai("ollama-direct", seen)))
    yield seen


def test_e20_01_providers_route_through_bifrost(bifrost):
    """공급자 호출 = Bifrost(모델 '<공급자>/<모델>'), 퍼블릭 공급자는 api 쪽 키 없이 Bifrost 경유로만."""
    provs = build_providers(5.0, 0.1)
    assert isinstance(provs["ollama"], BifrostProvider) and isinstance(provs["openai"], BifrostProvider)
    assert provs["openai"].direct is None and provs["openai"].gateway.api_key == ""
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    res = asyncio.run(provs["ollama"].complete("granite4.1:3b", req))
    assert res.content == "bifrost:ollama/granite4.1:3b" and res.model == "granite4.1:3b"

    async def stream():
        return [c async for c in provs["anthropic"].stream("claude-x", req)]
    chunks = asyncio.run(stream())
    assert chunks[0] == {"delta": "bifrost:anthropic/claude-x"} and chunks[-1]["usage"]["completion_tokens"] == 2
    vecs, _ = asyncio.run(provs["ollama"].embed("bge-m3", ["a", "b"]))
    assert len(vecs) == 2 and ("bifrost", "ollama/bge-m3") in bifrost


def test_e20_02_bifrost_down_direct_ollama_fallback(bifrost, monkeypatch):
    """Bifrost 에 닿지 않으면 로컬 Ollama 는 직접 호출, 퍼블릭은 오류(→ 라우터 별칭 폴백)."""
    monkeypatch.delitem(OpenAICompatProvider.TRANSPORTS, "http://bifrost.test/v1")
    monkeypatch.setenv("BIFROST_URL", "http://127.0.0.1:9")  # 닫힌 포트 = 연결 거부
    provs = build_providers(2.0, 0.1)
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    assert asyncio.run(provs["ollama"].complete("granite4.1:3b", req)).content == "ollama-direct:granite4.1:3b"
    assert provs["ollama"].fallbacks == 1
    with pytest.raises(ProviderError):
        asyncio.run(provs["openai"].complete("gpt-x", req))


def test_e20_03_router_public_failure_falls_back_to_local(bifrost):
    """Bifrost 가 퍼블릭 키 없이 400 을 주면 별칭의 다음 대상(로컬)으로 — 기존 폴백 규칙 유지."""
    provs = build_providers(5.0, 0.1)
    no_key = FastAPI()

    @no_key.post("/v1/chat/completions")
    async def fail(request: Request):
        body = await request.json()
        if body["model"].startswith("openai/"):
            return JSONResponse({"error": {"message": "no keys found that support model"}}, status_code=400)
        return {"choices": [{"message": {"content": "local ok"}, "finish_reason": "stop"}], "usage": {}}
    provs["openai"].gateway.TRANSPORTS["http://bifrost.test/v1"] = httpx.ASGITransport(app=no_key)
    with appdb.SessionLocal() as s:
        s.merge(LlmModel(id="openai/gpt-x", provider="openai", model_id="gpt-x", local=False, context=8192,
                         tool_call=True, vision=False, license="Proprietary"))
        s.merge(LlmModel(id="ollama/granite4.1:3b", provider="ollama", model_id="granite4.1:3b", local=True,
                         context=8192, tool_call=True, vision=False, license="Apache-2.0"))
        s.merge(LlmRoute(alias="t/pub", targets=["openai/gpt-x", "ollama/granite4.1:3b"]))
        s.commit()
        res, meta = asyncio.run(Router(provs).complete(s, "t/pub", ChatRequest(messages=[{"role": "user", "content": "x"}]),
                                                       level="L1"))
    assert res.content == "local ok" and meta.model == "ollama/granite4.1:3b" and meta.fallback_from == "openai/gpt-x"


@pytest.fixture
def priced(client):
    budget.invalidate()
    with appdb.SessionLocal() as s:
        s.merge(LlmModel(id="mock/pub", provider="mock", model_id="echo", local=False, context=8192, tool_call=True,
                         vision=False, license="test", cost_in=1.0, cost_out=1.0))
        s.merge(LlmRoute(alias="plaza/chat", targets=["mock/pub", "mock/echo"]))
        s.merge(LlmRoute(alias="t/pubonly", targets=["mock/pub"]))
        s.commit()
    yield client
    budget.invalidate()


def chat(client, token, model="plaza/chat"):
    return client.post("/v1/chat/completions", json={"model": model, "messages": [{"role": "user", "content": "hi"}]},
                       headers=auth(token) | {"X-Plaza-Data-Class": "L1"})


def test_e20_04_budget_forces_local_at_ratio(priced, sup_token):
    h = auth(sup_token)
    assert chat(priced, sup_token).headers["x-plaza-model"] == "mock/pub"  # 예산 없음 = 퍼블릭 1순위
    st = priced.put("/api/llm/budget", json={"monthly": 1.0, "ratio": 0.8}, headers=h).json()
    assert st["forced"] is False and st["spent"] > 0
    with appdb.SessionLocal() as s:
        s.add(LlmUsage(alias="plaza/chat", model="mock/pub", data_class="L1", tokens_in=0, tokens_out=0, cost=0.85))
        s.commit()
    budget.invalidate()
    res = chat(priced, sup_token)
    assert res.headers["x-plaza-model"] == "mock/echo" and res.headers["x-plaza-budget"] == "local-forced"
    chat(priced, sup_token)
    assert len(priced.get("/api/audit?action=llm.budget_local_forced", headers=h).json()) == 1  # 달마다 한 번
    st = priced.get("/api/llm/budget", headers=h).json()
    assert st["forced"] is True and st["used"] >= 0.85 and st["month"]
    denied = chat(priced, sup_token, "t/pubonly")
    assert denied.status_code == 403 and denied.json()["detail"]["reason"] == "budget"
    priced.put("/api/llm/budget", json={"monthly": 0, "ratio": 0.8}, headers=h)  # 0 = 끔
    assert chat(priced, sup_token).headers["x-plaza-model"] == "mock/pub"


def test_e20_05_budget_rbac_and_validation(priced, sup_token):
    _, admin = make_user(priced, sup_token, "budget-admin@example.test", role="admin")
    _, user = make_user(priced, sup_token, "budget-user@example.test")
    assert priced.get("/api/llm/budget", headers=auth(admin)).status_code == 200
    assert priced.get("/api/llm/budget", headers=auth(user)).status_code == 403
    assert priced.put("/api/llm/budget", json={"monthly": 5}, headers=auth(admin)).status_code == 403
    assert priced.put("/api/llm/budget", json={"monthly": 5, "ratio": 0.3}, headers=auth(sup_token)).status_code == 422
    assert priced.put("/api/llm/budget", json={"monthly": -1}, headers=auth(sup_token)).status_code == 422


def test_e20_06_litellm_not_used_and_compose_isolation():
    """LiteLLM 미사용(Q1) · 퍼블릭 키는 bifrost 서비스에만(api 는 비워 덮어씀) · Bifrost 버전 고정·포트 미공개."""
    assert importlib.util.find_spec("litellm") is None
    assert "litellm" not in (ROOT / "pyproject.toml").read_text().lower()
    import yaml
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    api, bf = compose["services"]["api"], compose["services"]["bifrost"]
    assert all(api["environment"][k] == "" for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"))
    assert bf["image"].startswith("maximhq/bifrost:v") and "ports" not in bf
    assert bf["read_only"] is True and bf["cap_drop"] == ["ALL"]
    cfg = json.loads((ROOT / "ops" / "bifrost" / "config.json").read_text())
    assert cfg["providers"]["openai"]["keys"][0]["value"] == "env.OPENAI_API_KEY"  # 키 원문은 파일에 없다
