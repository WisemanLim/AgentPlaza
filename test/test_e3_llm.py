"""Epic 3 — LLM 게이트웨이·모델 카탈로그·데이터 등급 (D1-01/03/05/06, NFR-L1~L5, NFR-S3).

mock 공급자로 '퍼블릭 흉내(local=false)'·'로컬(local=true)' 모델을 만들어 폴백·정책을 결정적으로 시험한다.
실제 Ollama·퍼블릭 호출은 impl 시나리오(실 스택)에서 확인한다.
"""
import asyncio
import json
import time

import pytest

from app import db as appdb
from app.core.config import settings
from app.llm.providers import ChatRequest, OpenAICompatProvider
from app.llm.router import Router, get_router
from app.models import LlmModel, LlmRoute
from helpers import auth, make_user

MODELS = [
    ("mock/echo-local", "echo", True), ("mock/echo-public", "echo", False),
    ("mock/fail-public", "fail", False), ("mock/slow-public", "slow", False), ("mock/fail-local", "fail", True),
]
ROUTES = {
    "plaza/t-local": ["mock/echo-local"],
    "plaza/t-fallback": ["mock/fail-public", "mock/echo-local"],
    "plaza/t-slow": ["mock/slow-public", "mock/echo-local"],
    "plaza/t-mixed": ["mock/echo-public", "mock/echo-local"],
    "plaza/t-public": ["mock/echo-public"],
    "plaza/t-dead": ["mock/fail-public", "mock/fail-local"],
}


@pytest.fixture
def llm(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_target_timeout", 0.3)
    monkeypatch.setattr(get_router().providers["mock"], "slow_seconds", 2.0)
    with appdb.SessionLocal() as s:
        for mid, model, local in MODELS:
            s.merge(LlmModel(id=mid, provider="mock", model_id=model, local=local, context=8192, tool_call=True,
                             vision=False, license="test", cost_in=0.001, cost_out=0.002))
        for alias, targets in ROUTES.items():
            s.merge(LlmRoute(alias=alias, targets=targets))
        s.commit()
    return client


def chat(client, token, alias, text="hi", data_class=None, **kw):
    headers = auth(token) | ({"X-Plaza-Data-Class": data_class} if data_class else {})
    return client.post("/v1/chat/completions", json={"model": alias, "messages": [{"role": "user", "content": text}], **kw},
                       headers=headers)


def test_e3_01_bootstrap_catalog_and_required_fields(client, sup_token):
    models = {m["id"]: m for m in client.get("/api/llm/models", headers=auth(sup_token)).json()}
    assert models["ollama/granite4.1:3b"]["local"] is True and models["ollama/granite4.1:3b"]["enabled"] is True
    assert "mock/echo" in models  # 비운영 환경 전용
    for m in models.values():  # NFR-L5 필수 필드
        assert {"context", "tool_call", "vision", "license", "local"} <= set(m)
    routes = {r["alias"] for r in client.get("/api/llm/routes", headers=auth(sup_token)).json()}
    assert {"plaza/chat", "plaza/fast", "plaza/local", "plaza/orchestrator"} <= routes
    bad = client.post("/api/llm/models", json={"provider": "x", "model_id": "y", "local": True}, headers=auth(sup_token))
    assert bad.status_code == 422


def test_e3_02_alias_routing_and_metering(llm, sup_token):
    res = chat(llm, sup_token, "plaza/t-local", "안녕", data_class="L3")
    assert res.status_code == 200
    assert res.json()["choices"][0]["message"]["content"] == "echo: 안녕"
    assert res.headers["x-plaza-model"] == "mock/echo-local" and res.headers["x-plaza-degraded"] == "false"
    usage = llm.get("/api/llm/usage", headers=auth(sup_token)).json()
    assert usage["by_alias"]["plaza/t-local"]["calls"] == 1 and usage["by_alias"]["plaza/t-local"]["tokens_out"] > 0


def test_e3_03_public_failure_falls_back_to_local(llm, sup_token):
    """NFR-L1: 퍼블릭 장애 → 30초 내 로컬 폴백 + 강등 표시."""
    t0 = time.monotonic()
    res = chat(llm, sup_token, "plaza/t-fallback", data_class="L0")
    assert res.status_code == 200 and time.monotonic() - t0 < settings.llm_fallback_budget
    assert res.headers["x-plaza-degraded"] == "true"
    assert res.headers["x-plaza-fallback-from"] == "mock/fail-public"
    assert res.headers["x-plaza-model"] == "mock/echo-local"


def test_e3_04_public_timeout_falls_back(llm, sup_token):
    t0 = time.monotonic()
    res = chat(llm, sup_token, "plaza/t-slow", data_class="L1")
    assert res.status_code == 200 and time.monotonic() - t0 < 1.5
    assert res.headers["x-plaza-fallback-from"] == "mock/slow-public"


def test_e3_05_confidential_never_leaves_local(llm, sup_token):
    """NFR-L3·US4: confidential(L3) 은 local 모델 외로 나가지 않는다. 등급 규칙이 폴백보다 우선."""
    res = chat(llm, sup_token, "plaza/t-mixed", data_class="confidential")
    assert res.status_code == 200 and res.headers["x-plaza-model"] == "mock/echo-local"
    denied = chat(llm, sup_token, "plaza/t-public", data_class="L3")
    assert denied.status_code == 403 and denied.json()["detail"]["error"] == "policy_denied"
    events = llm.get("/api/audit?action=llm.policy_denied", headers=auth(sup_token)).json()
    assert events and events[0]["detail"]["blocked"] == ["mock/echo-public"]


def test_e3_06_missing_header_defaults_to_L2(llm, sup_token):
    assert chat(llm, sup_token, "plaza/t-public").status_code == 403  # 헤더 없음 = L2 → 퍼블릭 불가
    assert chat(llm, sup_token, "plaza/t-public", data_class="L0").status_code == 200
    assert chat(llm, sup_token, "plaza/t-public", data_class="bogus").status_code == 422


def test_e3_07_all_targets_failed_503(llm, sup_token):
    res = chat(llm, sup_token, "plaza/t-dead", data_class="L0")
    assert res.status_code == 503 and res.json()["detail"]["error"] == "all_targets_failed"
    assert chat(llm, sup_token, "plaza/nope").status_code == 404


def _sse(res) -> tuple[str, list[dict]]:
    frames = [line[6:] for line in res.text.splitlines() if line.startswith("data: ")]
    assert frames[-1] == "[DONE]"
    chunks = [json.loads(f) for f in frames[:-1]]
    return "".join(c["choices"][0]["delta"].get("content", "") for c in chunks), chunks


def test_e3_08_streaming_and_stream_fallback(llm, sup_token):
    res = chat(llm, sup_token, "plaza/t-local", "스트리밍 시험", stream=True, data_class="L3")
    assert res.status_code == 200 and res.headers["content-type"].startswith("text/event-stream")
    text, chunks = _sse(res)
    assert text == "echo: 스트리밍 시험" and chunks[-1]["choices"][0]["finish_reason"] == "stop"
    fb = chat(llm, sup_token, "plaza/t-fallback", "x", stream=True, data_class="L0")
    assert fb.headers["x-plaza-fallback-from"] == "mock/fail-public" and _sse(fb)[0] == "echo: x"
    calls = llm.get("/api/llm/usage", headers=auth(sup_token)).json()["by_alias"]
    assert calls["plaza/t-local"]["calls"] == 1  # 스트림 종료 후 계량


def test_e3_09_api_key_as_bearer(llm, sup_token):
    key = llm.post("/api/api-keys", json={"name": "openwebui"}, headers=auth(sup_token)).json()["key"]
    res = llm.post("/v1/chat/completions", json={"model": "plaza/t-local", "messages": [{"role": "user", "content": "k"}]},
                   headers={"Authorization": f"Bearer {key}", "X-Plaza-Data-Class": "L3"})
    assert res.status_code == 200
    assert llm.get("/v1/models", headers={"Authorization": f"Bearer {key}"}).json()["object"] == "list"


def test_e3_10_license_gate(llm, sup_token):
    body = {"provider": "ollama", "model_id": "llama3.2:3b", "local": True, "context": 131072, "tool_call": True,
            "vision": False, "license": "Llama-3.2-Community", "commercial_use": "conditional", "enabled": False}
    assert llm.post("/api/llm/models", json=body, headers=auth(sup_token)).status_code == 201
    path = "/api/llm/models/ollama/llama3.2:3b"
    assert llm.patch(path, json={"enabled": True}, headers=auth(sup_token)).status_code == 409
    assert llm.patch(path, json={"enabled": True, "acknowledge_license": True}, headers=auth(sup_token)).status_code == 200
    assert llm.patch(path, json={"commercial_use": "prohibited"}, headers=auth(sup_token)).status_code == 409


def test_e3_11_route_admin_only_and_validated(llm, sup_token):
    put = lambda alias, targets, tok: llm.put(f"/api/llm/routes/{alias}", json={"targets": targets},  # noqa: E731
                                              headers=auth(tok))
    assert put("plaza/new", ["mock/echo-local"], sup_token).status_code == 200
    assert put("plaza/new", ["nope/model"], sup_token).status_code == 422
    assert put("custom/x", ["mock/echo-local"], sup_token).status_code == 422
    _, user_tok = make_user(llm, sup_token, "llmuser@example.test")
    assert put("plaza/new", ["mock/echo-local"], user_tok).status_code == 403
    assert chat(llm, user_tok, "plaza/new", data_class="L3").status_code == 200  # 사용자는 호출 가능


def test_e3_12_gateway_overhead_p95_under_50ms(llm):
    """NFR-L4: 게이트웨이 자체 오버헤드(mock 공급자 지연 0) p95 ≤ 50ms."""
    r = Router(get_router().providers)
    req = ChatRequest(messages=[{"role": "user", "content": "ping"}])
    samples = []
    with appdb.SessionLocal() as s:
        for _ in range(60):
            t0 = time.perf_counter()
            asyncio.run(r.complete(s, "plaza/t-local", req, level="L3"))
            samples.append((time.perf_counter() - t0) * 1000)
    p95 = sorted(samples)[int(len(samples) * 0.95) - 1]
    assert p95 < 50, f"p95={p95:.1f}ms"


def test_e3_13_no_public_keys_local_only_works(llm, sup_token):
    """NFR-L2·NFR-S3: 키 0개면 퍼블릭 공급자 미등록, 로컬만으로 동작. 키는 게이트웨이 프로세스에만 있다."""
    names = {p["name"] for p in llm.get("/api/llm/providers", headers=auth(sup_token)).json()}
    assert not names & {"openai", "anthropic", "gemini", "openrouter"}
    assert {"mock", "ollama"} <= names
    assert chat(llm, sup_token, "plaza/t-local", data_class="L3").status_code == 200
    assert isinstance(get_router().providers["ollama"], OpenAICompatProvider)
