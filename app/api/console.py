"""콘솔 API (D10-01, UI B02 대시보드·M04 런타임·L01 설정·L02 프로필) + 셋업 위저드 (D10-02, UI A02)."""
from datetime import timedelta

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin, require_supervisor, require_user
from app.db import get_db, utcnow
from app.llm import catalog as llm_catalog
from app.llm.router import get_router
from app.models import (ROLE_RANK, Agent, Approval, ChatSession, Install, LlmModel, LlmRoute, LlmUsage, User)
from app.runtime.driver import get_runtime
from app.services import audit, sysconfig

router = APIRouter(tags=["console"], dependencies=[Depends(require_user)])


# ---------- 대시보드 (B02: 상태 타일 6개, 30초 폴링) ----------

@router.get("/api/console/dashboard")
async def dashboard(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    agents = list(db.execute(select(Agent).where(Agent.builtin.is_(False))).scalars())
    since = utcnow() - timedelta(days=1)
    usage = list(db.execute(select(LlmUsage).where(LlmUsage.ts >= since)).scalars())
    pending = select(func.count()).select_from(Approval).where(Approval.status == "pending")
    if ROLE_RANK.get(p.role, 0) < ROLE_RANK["admin"]:
        pending = pending.where(Approval.requester == p.actor)
    installs = list(db.execute(select(Install).where(Install.created_at >= since)).scalars())
    rt = get_runtime()
    tiles = [
        {"id": "agents", "label": "에이전트", "value": sum(a.status == "healthy" and a.is_active for a in agents),
         "total": len(agents), "warn": sum(a.status in ("unhealthy", "failed") for a in agents),
         "linked": sum(a.source == "link" for a in agents)},
        {"id": "approvals", "label": "승인 대기", "value": db.scalar(pending)},
        {"id": "llm", "label": "LLM 호출(24h)", "value": len(usage), "fallbacks": sum(bool(u.fallback_from) for u in usage),
         "errors": sum(u.outcome != "ok" for u in usage),
         "local_ratio": (sum(u.model.startswith(("ollama/", "mock/")) for u in usage) / len(usage)) if usage else None},
        {"id": "installs", "label": "설치(24h)", "value": len(installs),
         "running": sum(i.status in ("queued", "running") for i in installs),
         "failed": sum(i.status in ("failed", "rolled_back") for i in installs)},
        {"id": "sessions", "label": "내 대화", "value": db.scalar(select(func.count()).select_from(ChatSession)
                                                                  .where(ChatSession.owner == p.actor))},
        {"id": "runtime", "label": "런타임", "value": rt.name, "ok": rt.name != "none"},
    ]
    return {"tiles": tiles, "refresh_seconds": 30, "generated_at": utcnow()}


@router.get("/api/agents/{agent_id}/runtime", dependencies=[Depends(require_admin)])
async def agent_runtime(agent_id: str, db: Session = Depends(get_db)):
    """M04: 컨테이너 상태·헬스(runtime 서비스 조회)."""
    a = db.get(Agent, agent_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "에이전트 없음 / not found")
    if a.builtin or a.source == "link":
        return {"agent_id": agent_id, "mode": "inprocess" if a.builtin else "remote", "containers": []}
    return {"agent_id": agent_id, "mode": "container", **await get_runtime().status(agent_id)}


# ---------- 시스템 설정 (L01) · 내 프로필 (L02) ----------

@router.get("/api/settings", dependencies=[Depends(require_admin)])
def get_settings(db: Session = Depends(get_db)):
    return sysconfig.effective(db)


@router.put("/api/settings")
def put_settings(body: dict, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        out = sysconfig.update(db, body)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="settings.updated", detail=body)
    return out


class ProfileIn(BaseModel):
    locale: str | None = Field(default=None, pattern="^(ko|en)$")
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")


@router.get("/api/me/profile")
def get_profile(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    if p.type != "user":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "사용자 계정 전용 / users only")
    u = db.get(User, int(p.id))
    prefs = sysconfig.blob(db, f"prefs:{u.id}")
    return {"email": u.email, "role": u.role, "locale": u.locale, "theme": prefs.get("theme", "system")}


@router.patch("/api/me/profile")
def patch_profile(body: ProfileIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    if p.type != "user":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "사용자 계정 전용 / users only")
    u = db.get(User, int(p.id))
    if body.locale:
        u.locale = body.locale
    prefs = sysconfig.blob(db, f"prefs:{u.id}")
    if body.theme:
        prefs["theme"] = body.theme
    sysconfig.put_blob(db, f"prefs:{u.id}", prefs)
    return get_profile(p, db)


# ---------- 셋업 위저드 (A02: 관리자 → LLM 연결 → 모델 pull → 기본 에이전트 → 완료) ----------

STEPS = ["admin", "llm", "models", "agents", "complete"]


def _setup(db: Session) -> dict:
    s = sysconfig.blob(db, "setup")
    s.setdefault("steps", {})
    s["steps"]["admin"] = {"done": True}  # 이 API 는 supervisor 생성 이후에만 호출 가능
    return s


def _save(db: Session, s: dict) -> dict:
    return sysconfig.put_blob(db, "setup", s)


def _ollama():
    return get_router().providers.get("ollama")


async def _ollama_tags() -> tuple[bool, list[str]]:
    prov = _ollama()
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            res = await c.get(prov.base_url.removesuffix("/v1") + "/api/tags")
        return res.status_code == 200, [m["name"] for m in res.json().get("models", [])]
    except (httpx.HTTPError, ValueError, AttributeError):
        return False, []


@router.get("/api/setup/progress", dependencies=[Depends(require_supervisor)])
def setup_progress(db: Session = Depends(get_db)):
    s = _setup(db)
    return {"steps": [{"id": k, **s["steps"].get(k, {"done": False})} for k in STEPS],
            "completed": bool(s["steps"].get("complete", {}).get("done"))}


@router.get("/api/setup/llm", dependencies=[Depends(require_supervisor)])
async def setup_llm_status():
    """Ollama 자동 감지 + 퍼블릭 키 보유 여부(키 값은 노출하지 않는다, NFR-S3)."""
    reachable, models = await _ollama_tags()
    public = {k: k in get_router().providers for k in ("openai", "anthropic", "gemini", "openrouter")}
    return {"ollama": {"reachable": reachable, "models": models,
                       "recommended": [m for m in models if m.split(":")[0] in llm_catalog.KNOWN_LOCAL]},
            "public": public,
            "hint": "퍼블릭 키는 게이트웨이 env(OPENAI_API_KEY 등)로 주입 — 화면에 입력·저장하지 않는다"}


class LlmChoice(BaseModel):
    chat_model: str = Field(min_length=1, max_length=100)
    reasoning_model: str | None = Field(default=None, max_length=100)
    acknowledge_license: bool = False


@router.post("/api/setup/llm")
async def setup_llm(body: LlmChoice, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    """선택한 로컬 모델로 기본 별칭을 구성한다. 설치되지 않은 모델은 비차단 경고(이후 pull 단계)."""
    reachable, models = await _ollama_tags()
    chosen = [body.chat_model] + ([body.reasoning_model] if body.reasoning_model else [])
    warnings = [f"Ollama 에 없음(다음 단계에서 pull): {m}" for m in chosen if m not in models] if reachable else \
        ["Ollama 에 연결할 수 없음 — 로컬 모델 없이 계속(비차단)"]
    for tag in chosen:
        mid = f"ollama/{tag}"
        m = db.get(LlmModel, mid) or llm_catalog._local_model(tag)
        if m.commercial_use == "conditional" and not body.acknowledge_license:
            raise HTTPException(status.HTTP_409_CONFLICT, f"조건부 라이선스 모델 — acknowledge_license 필요: {tag}")
        m.enabled = m.commercial_use != "prohibited"
        db.merge(m)
    chat, reason = f"ollama/{body.chat_model}", f"ollama/{body.reasoning_model or body.chat_model}"
    fallback = [x for x in ("mock/echo",) if db.get(LlmModel, x)]
    for alias, targets in {"plaza/chat": [chat], "plaza/fast": [chat], "plaza/local": [chat, reason],
                           "plaza/orchestrator": [reason, chat]}.items():
        r = db.get(LlmRoute, alias) or LlmRoute(alias=alias)
        public = [t for t in (r.targets or []) if not t.startswith(("ollama/", "mock/"))]
        r.targets = list(dict.fromkeys((public if alias == "plaza/chat" else []) + targets + fallback))
        db.merge(r)
    db.commit()
    s = _setup(db)
    s["steps"]["llm"] = {"done": True, "chat": body.chat_model, "reasoning": body.reasoning_model, "warnings": warnings}
    _save(db, s)
    audit.record(db, actor=p.actor, actor_type=p.type, action="setup.llm", detail={"models": chosen})
    return {"ok": True, "warnings": warnings}


class PullIn(BaseModel):
    model: str = Field(pattern=r"^[A-Za-z0-9._:/-]{1,100}$")


async def _pull(model: str) -> None:
    from app.db import SessionLocal
    prov = _ollama()
    status_ = {"model": model, "state": "pulling", "at": utcnow().isoformat()}
    try:
        async with httpx.AsyncClient(timeout=None) as c:
            res = await c.post(prov.base_url.removesuffix("/v1") + "/api/pull", json={"model": model, "stream": False})
        status_["state"] = "done" if res.status_code == 200 else f"error HTTP {res.status_code}"
    except httpx.HTTPError as exc:
        status_["state"] = f"error {type(exc).__name__}"
    with SessionLocal() as db:
        s = _setup(db)
        pulls = s["steps"].setdefault("models", {"done": False, "pulls": {}}).setdefault("pulls", {})
        pulls[model] = status_
        s["steps"]["models"]["done"] = all(v["state"] == "done" for v in pulls.values())
        _save(db, s)


@router.post("/api/setup/models/pull", status_code=202)
async def setup_pull(body: PullIn, background: BackgroundTasks, p: Principal = Depends(require_supervisor),
                     db: Session = Depends(get_db)):
    """모델 pull 은 오래 걸릴 수 있어 백그라운드로 — 진행은 /api/setup/progress 로(비차단)."""
    s = _setup(db)
    pulls = s["steps"].setdefault("models", {"done": False, "pulls": {}}).setdefault("pulls", {})
    pulls[body.model] = {"model": body.model, "state": "queued", "at": utcnow().isoformat()}
    _save(db, s)
    background.add_task(_pull, body.model)
    audit.record(db, actor=p.actor, actor_type=p.type, action="setup.model_pull", detail={"model": body.model})
    return {"queued": body.model}


class SkipIn(BaseModel):
    step: str = Field(pattern="^(llm|models|agents)$")


@router.post("/api/setup/skip", dependencies=[Depends(require_supervisor)])
def setup_skip(body: SkipIn, db: Session = Depends(get_db)):
    s = _setup(db)
    s["steps"][body.step] = {**s["steps"].get(body.step, {}), "done": True, "skipped": True}
    _save(db, s)
    return setup_progress(db)


class AgentsIn(BaseModel):
    listings: list[str] = Field(default_factory=list, max_length=20)


@router.post("/api/setup/agents", status_code=202)
async def setup_agents(body: AgentsIn, background: BackgroundTasks, p: Principal = Depends(require_supervisor),
                       db: Session = Depends(get_db)):
    """기본 에이전트 활성화: 내장 2종(Orchestrator·Assistant)은 항상 켜져 있고, 선택한 마켓 리스팅을 설치한다."""
    from app.market import catalog, payments
    from app.registry import pipeline
    started = []
    for lid in body.listings:
        x = catalog.get(lid)
        if x is None or x["source"]["type"] in catalog.REMOTE_TYPES or x.get("required_env") or payments.is_paid(x):
            started.append({"listing": lid, "error": "설치 불가(없음·원격·필수 env·유료)"})
            continue
        data = await catalog.artifact(x)
        inst = pipeline.new_install(db, source="market", source_ref=f"{lid}@{x['version']}", created_by=p.actor)
        background.add_task(pipeline.run, inst.id, data, trust=x.get("trust", "community"))
        started.append({"listing": lid, "install_id": inst.id})
    s = _setup(db)
    s["steps"]["agents"] = {"done": True, "installs": started}
    _save(db, s)
    return {"installs": started}


@router.post("/api/setup/complete")
def setup_complete(p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    s = _setup(db)
    todo = [k for k in ("llm", "models", "agents") if not s["steps"].get(k, {}).get("done")]
    if todo:
        raise HTTPException(status.HTTP_409_CONFLICT, f"미완료 단계(건너뛰기 가능): {todo}")
    s["steps"]["complete"] = {"done": True, "at": utcnow().isoformat()}
    _save(db, s)
    audit.record(db, actor=p.actor, actor_type=p.type, action="setup.completed")
    return setup_progress(db)

