"""게이트웨이 별칭만 아는 LLM 클라이언트(DP3). M1 에서는 LLM_BASE_URL 로 Ollama 에 직결할 수 있다."""
import os

import httpx


class LLMClient:
    def __init__(self, alias: str = "plaza/chat", base_url: str | None = None, api_key: str | None = None,
                 timeout: float = 60.0):
        self.alias = os.environ.get("LLM_ALIAS", alias)
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.base_url)

    async def chat(self, messages: list[dict], **kwargs) -> str:
        if not self.available:
            raise RuntimeError("LLM_BASE_URL 미설정 / not configured")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        # 에이전트의 데이터 등급(governance.dataClassification)을 게이트웨이에 알린다 — 없으면 게이트웨이가 L2 로 본다.
        if os.environ.get("AGENT_DATA_CLASS"):
            headers["X-Plaza-Data-Class"] = os.environ["AGENT_DATA_CLASS"]
        body = {"model": self.alias, "messages": messages, "stream": False, **kwargs}
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            res = await c.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
