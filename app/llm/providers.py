"""LLM 공급자 어댑터 (D1-01 Ollama · D1-03 퍼블릭 · mock). 모두 OpenAI chat 형식의 입출력으로 정규화한다."""
import asyncio
import json
import os
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field

import httpx


class ProviderError(Exception):
    """공급자 장애(연결·타임아웃·5xx). 라우터는 이 예외에서 다음 대상으로 폴백한다."""


class ProviderUnreachable(ProviderError):
    """연결 자체가 안 됨(게이트웨이 다운 등). Bifrost 경유 공급자는 이때 직접 호출로 넘어간다."""


def _transport_error(name: str, exc: httpx.HTTPError) -> ProviderError:
    cls = ProviderUnreachable if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)) else ProviderError
    return cls(f"{name}: {type(exc).__name__}")


@dataclass
class ChatRequest:
    messages: list[dict]
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[dict] | None = None
    tool_choice: str | dict | None = None
    response_format: dict | None = None

    def openai_body(self, model: str, stream: bool) -> dict:
        body: dict = {"model": model, "messages": self.messages, "stream": stream}
        for k in ("temperature", "max_tokens", "tools", "tool_choice", "response_format"):
            if getattr(self, k) is not None:
                body[k] = getattr(self, k)
        if stream:
            body["stream_options"] = {"include_usage": True}
        return body


@dataclass
class ChatResult:
    content: str
    model: str
    finish_reason: str = "stop"
    tool_calls: list[dict] | None = None
    usage: dict = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0})


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class OpenAICompatProvider:
    """Ollama(/v1)·OpenAI·Gemini(OpenAI 호환)·OpenRouter·vLLM·LiteLLM·Bifrost 공용."""

    TRANSPORTS: dict = {}  # 시험용: base_url → httpx 전송(ASGI 앱). 운영은 비어 있음

    def __init__(self, name: str, base_url: str, api_key: str = "", timeout: float = 30.0):
        self.name, self.base_url, self.api_key, self.timeout = name, base_url.rstrip("/"), api_key, timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout, transport=self.TRANSPORTS.get(self.base_url))

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def complete(self, model: str, req: ChatRequest) -> ChatResult:
        try:
            async with self._client() as c:
                res = await c.post(f"{self.base_url}/chat/completions", json=req.openai_body(model, False),
                                   headers=self._headers())
        except httpx.HTTPError as exc:
            raise _transport_error(self.name, exc) from exc
        if res.status_code >= 500 or res.status_code in (408, 429):
            raise ProviderError(f"{self.name}: HTTP {res.status_code}")
        if res.status_code >= 400:
            raise ProviderError(f"{self.name}: HTTP {res.status_code} {res.text[:200]}")
        data = res.json()
        msg = data["choices"][0]["message"]
        return ChatResult(content=msg.get("content") or "", model=model, tool_calls=msg.get("tool_calls"),
                          finish_reason=data["choices"][0].get("finish_reason") or "stop",
                          usage={k: data.get("usage", {}).get(k, 0) for k in ("prompt_tokens", "completion_tokens")})

    async def embed(self, model: str, inputs: list[str]) -> tuple[list[list[float]], dict]:
        """OpenAI 호환 /embeddings (Ollama·vLLM·TEI 공용)."""
        try:
            async with self._client() as c:
                res = await c.post(f"{self.base_url}/embeddings", json={"model": model, "input": inputs},
                                   headers=self._headers())
        except httpx.HTTPError as exc:
            raise _transport_error(self.name, exc) from exc
        if res.status_code >= 400:
            raise ProviderError(f"{self.name}: HTTP {res.status_code} {res.text[:200]}")
        data = res.json()
        vecs = [d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"])]
        return vecs, {"prompt_tokens": data.get("usage", {}).get("prompt_tokens", estimate_tokens(" ".join(inputs)))}

    async def stream(self, model: str, req: ChatRequest) -> AsyncIterator[dict]:
        try:
            async with self._client() as c, c.stream(
                    "POST", f"{self.base_url}/chat/completions", json=req.openai_body(model, True),
                    headers=self._headers()) as res:
                if res.status_code >= 400:
                    raise ProviderError(f"{self.name}: HTTP {res.status_code}")
                async for line in res.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    if chunk.get("usage"):
                        yield {"usage": {k: chunk["usage"].get(k, 0) for k in ("prompt_tokens", "completion_tokens")}}
                    for ch in chunk.get("choices", []):
                        delta = ch.get("delta", {})
                        if delta.get("content"):
                            yield {"delta": delta["content"]}
                        if delta.get("tool_calls"):
                            yield {"tool_calls": delta["tool_calls"]}
        except httpx.HTTPError as exc:
            raise _transport_error(self.name, exc) from exc


class AnthropicProvider:
    """Anthropic Messages API ↔ OpenAI chat 형식 변환."""

    name = "anthropic"

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com", timeout: float = 30.0):
        self.api_key, self.base_url, self.timeout = api_key, base_url.rstrip("/"), timeout

    def _body(self, model: str, req: ChatRequest, stream: bool) -> dict:
        system = "\n".join(m["content"] for m in req.messages if m["role"] == "system")
        msgs = [{"role": m["role"], "content": m["content"]} for m in req.messages if m["role"] in ("user", "assistant")]
        body: dict = {"model": model, "messages": msgs, "max_tokens": req.max_tokens or 1024, "stream": stream}
        if system:
            body["system"] = system
        if req.temperature is not None:
            body["temperature"] = req.temperature
        if req.tools:
            body["tools"] = [{"name": t["function"]["name"], "description": t["function"].get("description", ""),
                              "input_schema": t["function"].get("parameters", {"type": "object"})} for t in req.tools]
        return body

    def _headers(self) -> dict:
        return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

    async def complete(self, model: str, req: ChatRequest) -> ChatResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                res = await c.post(f"{self.base_url}/v1/messages", json=self._body(model, req, False),
                                   headers=self._headers())
        except httpx.HTTPError as exc:
            raise ProviderError(f"anthropic: {type(exc).__name__}") from exc
        if res.status_code >= 400:
            raise ProviderError(f"anthropic: HTTP {res.status_code}")
        data = res.json()
        text = "".join(b.get("text", "") for b in data["content"] if b["type"] == "text")
        calls = [{"id": b["id"], "type": "function", "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}
                 for b in data["content"] if b["type"] == "tool_use"] or None
        u = data.get("usage", {})
        return ChatResult(content=text, model=model, tool_calls=calls,
                          finish_reason="tool_calls" if calls else "stop",
                          usage={"prompt_tokens": u.get("input_tokens", 0), "completion_tokens": u.get("output_tokens", 0)})

    async def stream(self, model: str, req: ChatRequest) -> AsyncIterator[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c, c.stream(
                    "POST", f"{self.base_url}/v1/messages", json=self._body(model, req, True),
                    headers=self._headers()) as res:
                if res.status_code >= 400:
                    raise ProviderError(f"anthropic: HTTP {res.status_code}")
                async for line in res.aiter_lines():
                    if line.startswith("data:"):
                        ev = json.loads(line[5:])
                        if ev.get("type") == "content_block_delta" and ev["delta"].get("type") == "text_delta":
                            yield {"delta": ev["delta"]["text"]}
                        elif ev.get("type") == "message_delta" and ev.get("usage"):
                            yield {"usage": {"prompt_tokens": 0, "completion_tokens": ev["usage"].get("output_tokens", 0)}}
        except httpx.HTTPError as exc:
            raise ProviderError(f"anthropic: {type(exc).__name__}") from exc


Responder = Callable[[str, ChatRequest], ChatResult]


def _default_responder(model: str, req: ChatRequest) -> ChatResult:
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    if isinstance(last, list):
        last = " ".join(p.get("text", "") for p in last if isinstance(p, dict))
    content = json.dumps({"echo": last}, ensure_ascii=False) if req.response_format else f"echo: {last}"
    return ChatResult(content=content, model=model,
                      usage={"prompt_tokens": estimate_tokens(json.dumps(req.messages)), "completion_tokens": estimate_tokens(content)})


def hash_embedding(text: str, dims: int = 256) -> list[float]:
    """결정적 시험용 임베딩: 단어·문자 바이그램 해시 가방(같은 단어가 겹치면 가깝다), L2 정규화."""
    import hashlib
    import math
    import re as _re
    vec = [0.0] * dims
    low = text.lower()
    tokens = _re.findall(r"\w+", low) + [low[i:i + 2] for i in range(len(low) - 1) if not low[i:i + 2].isspace()]
    for tok in tokens:
        h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "big")
        vec[h % dims] += 1.0 if (h >> 32) & 1 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class MockProvider:
    """결정적 시험용 공급자. model_id: echo | fail(항상 장애) | slow(타임아웃 유발) | embed(해시 임베딩).
    시험은 responder 를 바꿔 낄 수 있다."""

    name = "mock"
    responder: Responder = staticmethod(_default_responder)

    def __init__(self, slow_seconds: float = 5.0):
        self.slow_seconds = slow_seconds

    async def complete(self, model: str, req: ChatRequest) -> ChatResult:
        if model == "fail":
            raise ProviderError("mock: injected failure")
        if model == "slow":
            await asyncio.sleep(self.slow_seconds)
        return MockProvider.responder(model, req)

    async def embed(self, model: str, inputs: list[str]) -> tuple[list[list[float]], dict]:
        if model == "fail":
            raise ProviderError("mock: injected failure")
        return [hash_embedding(t) for t in inputs], {"prompt_tokens": estimate_tokens(" ".join(inputs))}

    async def stream(self, model: str, req: ChatRequest) -> AsyncIterator[dict]:
        res = await self.complete(model, req)
        for i in range(0, len(res.content), 8):
            yield {"delta": res.content[i:i + 8]}
        if res.tool_calls:
            yield {"tool_calls": res.tool_calls}
        yield {"usage": res.usage}


class BifrostProvider:
    """Bifrost(Apache-2.0, PRD Q1) 경유 공급자: 모델 = '<공급자>/<모델>' 로 Bifrost 의 OpenAI 호환 /v1 을 부른다.
    퍼블릭 키는 Bifrost 서비스에만 있다. Bifrost 에 닿지 않으면 direct(로컬 Ollama)로 바로 부르고,
    direct 가 없는 퍼블릭 공급자는 오류 → 라우터가 별칭의 다음 대상(로컬)으로 폴백한다(NFR-L1)."""

    def __init__(self, name: str, gateway: OpenAICompatProvider, direct: object | None = None):
        self.name, self.gateway, self.direct = name, gateway, direct
        self.via = "bifrost"
        self.fallbacks = 0

    def _route(self, model: str) -> str:
        return f"{self.name}/{model}"

    async def complete(self, model: str, req: ChatRequest) -> ChatResult:
        try:
            res = await self.gateway.complete(self._route(model), req)
        except ProviderUnreachable:
            if self.direct is None:
                raise
            self.fallbacks += 1
            return await self.direct.complete(model, req)
        res.model = model
        return res

    async def embed(self, model: str, inputs: list[str]) -> tuple[list[list[float]], dict]:
        try:
            return await self.gateway.embed(self._route(model), inputs)
        except ProviderUnreachable:
            if self.direct is None:
                raise
            self.fallbacks += 1
            return await self.direct.embed(model, inputs)

    async def stream(self, model: str, req: ChatRequest) -> AsyncIterator[dict]:
        try:
            async for ch in self.gateway.stream(self._route(model), req):
                yield ch
        except ProviderUnreachable:  # 연결 단계 실패 = 아직 아무것도 보내지 않음 → 직접 호출로 다시
            if self.direct is None:
                raise
            self.fallbacks += 1
            async for ch in self.direct.stream(model, req):
                yield ch


PUBLIC_VIA_BIFROST = ("openai", "anthropic", "gemini", "openrouter")


def build_providers(timeout: float, slow_seconds: float) -> dict[str, object]:
    """키가 있는 퍼블릭 공급자만 등록한다(NFR-L2: 키 0개여도 로컬로 전 기능).
    BIFROST_URL 이 있으면 공급자 호출은 모두 Bifrost 경유이고 퍼블릭 키는 Bifrost 만 가진다(api 에는 없음, NFR-S3)."""
    env = os.environ
    if env.get("BIFROST_URL"):
        gw = OpenAICompatProvider("bifrost", env["BIFROST_URL"].rstrip("/") + "/v1", timeout=timeout)
        direct = OpenAICompatProvider("ollama", env.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434") + "/v1",
                                      timeout=timeout)
        providers: dict[str, object] = {"mock": MockProvider(slow_seconds), "ollama": BifrostProvider("ollama", gw, direct)}
        providers.update({p: BifrostProvider(p, gw) for p in PUBLIC_VIA_BIFROST})
        return providers
    providers = {
        "mock": MockProvider(slow_seconds),
        "ollama": OpenAICompatProvider("ollama", env.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434") + "/v1",
                                       timeout=timeout),
    }
    if env.get("OPENAI_API_KEY"):
        providers["openai"] = OpenAICompatProvider("openai", env.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                                                   env["OPENAI_API_KEY"], timeout)
    if env.get("ANTHROPIC_API_KEY"):
        providers["anthropic"] = AnthropicProvider(env["ANTHROPIC_API_KEY"], timeout=timeout)
    if env.get("GEMINI_API_KEY"):
        providers["gemini"] = OpenAICompatProvider(
            "gemini", "https://generativelanguage.googleapis.com/v1beta/openai", env["GEMINI_API_KEY"], timeout)
    if env.get("OPENROUTER_API_KEY"):
        providers["openrouter"] = OpenAICompatProvider("openrouter", "https://openrouter.ai/api/v1",
                                                       env["OPENROUTER_API_KEY"], timeout)
    if env.get("UPSTREAM_GATEWAY_URL"):  # 그 밖의 OpenAI 호환 업스트림(LiteLLM 은 쓰지 않는다 — PRD Q1)
        providers["upstream"] = OpenAICompatProvider("upstream", env["UPSTREAM_GATEWAY_URL"],
                                                     env.get("UPSTREAM_GATEWAY_KEY", ""), timeout)
    return providers
