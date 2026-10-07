"""모델 카탈로그 기본값(최초 기동 시 1회). 관리자가 바꾼 값은 덮어쓰지 않는다.

라이선스 판정: conditional(조건부) 모델은 기본 비활성(D1-06, PRD R9). 로컬 기본 모델은 Apache-2.0 계열.
"""
import os

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import LlmModel, LlmRoute

# Ollama 태그 → (라이선스, 상업 이용, 컨텍스트, 도구호출, 비전). 모르는 모델은 conditional(비활성)로 둔다.
KNOWN_LOCAL = {
    "granite4.1": ("Apache-2.0", "allowed", 131072, True, False),
    "qwen3": ("Apache-2.0", "allowed", 40960, True, False),
    "mistral": ("Apache-2.0", "allowed", 32768, True, False),
    "llama3.2": ("Llama-3.2-Community", "conditional", 131072, True, False),
    "gemma4": ("Gemma", "conditional", 131072, True, True),
    "qwen2.5vl": ("Apache-2.0", "allowed", 32768, False, True),
    "bge-m3": ("MIT", "allowed", 8192, False, False),
    "nomic-embed-text": ("Apache-2.0", "allowed", 8192, False, False),
}
EMBED_FAMILIES = ("bge-m3", "nomic-embed-text")
KNOWN_PUBLIC = {"anthropic": ("Proprietary", 200000, True, True), "openai": ("Proprietary", 128000, True, True),
                "gemini": ("Proprietary", 1000000, True, True), "openrouter": ("Mixed", 128000, True, False)}


def _local_model(tag: str) -> LlmModel:
    lic, cu, ctx, tools, vision = KNOWN_LOCAL.get(tag.split(":")[0], ("unknown", "conditional", 8192, False, False))
    return LlmModel(id=f"ollama/{tag}", provider="ollama", model_id=tag, local=True, context=ctx, tool_call=tools,
                    vision=vision, license=lic, commercial_use=cu, enabled=cu == "allowed",
                    kind="embedding" if tag.split(":")[0] in EMBED_FAMILIES else "chat")


def ensure_defaults(db: Session) -> list[str]:
    """임베딩·비전 기본값(D1-07·D3-04)을 없을 때만 더한다 — 기존 설치의 업그레이드 경로. 관리자 변경은 덮어쓰지 않는다."""
    embed = os.environ.get("LLM_LOCAL_EMBED_MODEL", "bge-m3")
    vision = os.environ.get("LLM_LOCAL_VISION_MODEL", "qwen2.5vl:7b")
    added = []
    models = [_local_model(embed), _local_model(vision)]
    if settings.app_env != "prod":
        models += [LlmModel(id="mock/embed", provider="mock", model_id="embed", local=True, context=8192, tool_call=False,
                            vision=False, license="internal-test", kind="embedding"),
                   LlmModel(id="mock/vision", provider="mock", model_id="echo", local=True, context=8192, tool_call=False,
                            vision=True, license="internal-test")]
    for m in models:
        if db.get(LlmModel, m.id) is None:
            db.add(m)
            added.append(m.id)
    fallback = settings.app_env != "prod"
    routes = {"plaza/embed": ([f"ollama/{embed}"] + (["mock/embed"] if fallback else []), "임베딩(RAG·메모리) — 로컬"),
              "plaza/vision": ([f"ollama/{vision}"] + (["mock/vision"] if fallback else []), "이미지 이해 — 로컬 비전")}
    for alias, (targets, desc) in routes.items():
        if db.get(LlmRoute, alias) is None:
            db.add(LlmRoute(alias=alias, targets=targets, description=desc))
            added.append(alias)
    db.commit()
    return added


def bootstrap(db: Session, providers: dict) -> bool:
    """카탈로그가 비어 있을 때만 기본 모델·별칭을 넣는다. 반환: 새로 넣었는지."""
    if db.scalar(select(func.count()).select_from(LlmModel)):
        return False
    chat = os.environ.get("LLM_LOCAL_CHAT_MODEL", "granite4.1:3b")
    reasoning = os.environ.get("LLM_LOCAL_REASONING_MODEL", "qwen3:8b")
    models = [_local_model(t) for t in dict.fromkeys([chat, reasoning])]
    public = []
    for ref in filter(None, os.environ.get("PUBLIC_MODELS", "").split(",")):
        provider, model_id = ref.strip().split("/", 1)
        if provider in providers and provider in KNOWN_PUBLIC:
            lic, ctx, tools, vision = KNOWN_PUBLIC[provider]
            public.append(LlmModel(id=f"{provider}/{model_id}", provider=provider, model_id=model_id, local=False,
                                   context=ctx, tool_call=tools, vision=vision, license=lic))
    mock = []
    if settings.app_env != "prod":  # 개발·시험 전용 결정적 모델(운영 카탈로그에는 넣지 않음)
        mock = [LlmModel(id="mock/echo", provider="mock", model_id="echo", local=True, context=8192, tool_call=True,
                         vision=False, license="internal-test")]
    db.add_all(models + public + mock)
    local_chat, local_reason = f"ollama/{chat}", f"ollama/{reasoning}"
    pub = [m.id for m in public]
    fallback = [m.id for m in mock]
    db.add_all([
        LlmRoute(alias="plaza/chat", targets=pub + [local_chat] + fallback, description="대화 기본. 퍼블릭 1순위 + 로컬 폴백"),
        LlmRoute(alias="plaza/fast", targets=[local_chat] + fallback, description="저지연 로컬"),
        LlmRoute(alias="plaza/local", targets=[local_chat, local_reason] + fallback, description="로컬 전용"),
        LlmRoute(alias="plaza/orchestrator", targets=[local_reason, local_chat] + pub + fallback,
                 description="Orchestrator — 구조화 출력"),
    ])
    db.commit()
    return True
