"""OpenAI 호환 서버 등록 (D1-02): vLLM·SGLang·llama-server·LocalAI·TEI·CLI 브리지 등을 공급자로 붙인다.

설정(settings 'llm.servers')에 {name: {base_url, local}} 를 두고, API 키는 시크릿 저장소(global/LLM_SERVER_<NAME>_KEY)에.
라우터는 계획할 때마다 설정을 맞춰(sync) 워커가 여러 개여도 같은 공급자 집합을 쓴다.
"""
import re

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.llm.providers import OpenAICompatProvider
from app.services import secrets, sysconfig

KEY = "llm.servers"
NAME = re.compile(r"^[a-z][a-z0-9-]{1,30}$")
RESERVED = {"mock", "ollama", "openai", "anthropic", "gemini", "openrouter", "upstream", "agent", "plaza"}


class ServerError(ValueError):
    pass


def secret_name(name: str) -> str:
    return f"LLM_SERVER_{name.upper().replace('-', '_')}_KEY"


def all_servers(db: Session) -> dict:
    return sysconfig.blob(db, KEY)


def put(db: Session, name: str, base_url: str, local: bool, api_key: str | None, actor: str) -> dict:
    if not NAME.match(name) or name in RESERVED:
        raise ServerError(f"이름은 소문자·숫자·- 이고 예약어({sorted(RESERVED)}) 불가")
    if not re.match(r"^https?://", base_url):
        raise ServerError("base_url 은 http(s)://…/v1")
    data = all_servers(db)
    data[name] = {"base_url": base_url.rstrip("/"), "local": bool(local), "has_key": bool(api_key) or
                  bool(data.get(name, {}).get("has_key"))}
    if api_key:
        secrets.put(db, "global", secret_name(name), api_key, actor)
    sysconfig.put_blob(db, KEY, data)
    return {"name": name, **data[name]}


def remove(db: Session, name: str) -> None:
    data = all_servers(db)
    if name not in data:
        raise ServerError("서버 없음 / not found")
    data.pop(name)
    secrets.delete(db, "global", secret_name(name))
    sysconfig.put_blob(db, KEY, data)


def sync(db: Session, providers: dict) -> None:
    """설정과 라우터 공급자를 맞춘다(추가·주소 변경·삭제)."""
    data = all_servers(db)
    for name, cfg in data.items():
        cur = providers.get(name)
        key = secrets.get(db, "global", secret_name(name)) if cfg.get("has_key") else ""
        if not isinstance(cur, OpenAICompatProvider) or cur.base_url != cfg["base_url"] or cur.api_key != (key or ""):
            providers[name] = OpenAICompatProvider(name, cfg["base_url"], key or "", settings.llm_target_timeout)
    for name in [n for n, p in providers.items() if getattr(p, "registered", False) and n not in data]:
        providers.pop(name)
    for name in data:
        providers[name].registered = True


async def models(provider: OpenAICompatProvider) -> list[str]:
    """서버가 서빙 중인 모델 목록(GET {base}/models)."""
    try:
        async with httpx.AsyncClient(timeout=10, transport=OpenAICompatProvider.TRANSPORTS.get(provider.base_url)) as c:
            res = await c.get(f"{provider.base_url}/models", headers=provider._headers())
        res.raise_for_status()
        return sorted(m["id"] for m in res.json().get("data", []))
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise ServerError(f"모델 목록 조회 실패 / cannot list models: {type(exc).__name__}") from None
