"""에이전트 API — 스캐폴드·템플릿(D4-01·D4-02) · 카탈로그(D5-06) · 등록 파이프라인(D5-01·D5-05) · 내보내기(D4-07)."""
import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agentspec import generator as gen
from app.core.config import settings
from app.core.deps import Principal, require_admin, require_user
from app.db import get_db
from app.models import Agent, AgentScope, AgentVersion, Capability, Install
from app.registry import pipeline
from app.runtime.driver import RuntimeFailure, get_runtime
from app.services import audit, orgs

router = APIRouter(prefix="/api/agents", tags=["agents"], dependencies=[Depends(require_user)])


class ScaffoldIn(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,40}$")
    name: str = Field(min_length=1, max_length=80)
    type: str = "service"
    description: str = ""
    llm_alias: str = Field(default="plaza/chat", pattern=r"^plaza/[a-z0-9._/-]+$")
    federation_url: str | None = None


def agent_out(a: Agent, caps: list[Capability]) -> dict:
    ui = a.manifest.get("spec", {}).get("ui", {})
    return {"id": a.id, "name": a.name, "type": a.type, "version": a.version, "status": a.status,
            "is_active": a.is_active, "builtin": a.builtin, "source": a.source, "trust": a.trust,
            "runtime_mode": a.runtime_mode, "has_frontend": bool(ui.get("hasFrontend")),
            "nav_visible": bool(a.is_active and ui.get("hasFrontend") and ui.get("navVisible", True)),
            "capabilities": [{"verb": c.verb, "domain": c.domain, "description": c.description,
                              "approval": c.human_approval_required} for c in caps]}


@router.get("")
def list_agents(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    """카탈로그: 내장·설치·원격 에이전트와 상태·버전 (D10-01, UI D01). 일반 사용자에게는 배치 범위(PRD Q7) 밖 에이전트를 빼고,
    관리자에게는 전부 보이되 자기에게 범위 밖이면 네비에서 뺀다."""
    caps: dict[str, list[Capability]] = {}
    for c in db.execute(select(Capability).order_by(Capability.id)).scalars():
        caps.setdefault(c.agent_id, []).append(c)
    hidden = orgs.hidden_agents(db, p.actor, p.role)
    scopes = {s.agent_id: orgs.scope_out(s) for s in db.execute(select(AgentScope)).scalars()}
    out = []
    for a in db.execute(select(Agent).order_by(Agent.builtin.desc(), Agent.id)).scalars():
        if a.id in hidden and p.role == "user":
            continue
        item = agent_out(a, caps.get(a.id, []))
        item["deploy_scope"] = scopes.get(a.id)
        if a.id in hidden:
            item["nav_visible"] = False
        out.append(item)
    return out


@router.get("/templates")
def templates():
    return [{"type": t, "capabilities": [c["verb"] for c in gen.TYPE_DEFS[t]["capabilities"]],
             "hasFrontend": bool(gen.TYPE_DEFS[t].get("ui")), "hasBackend": gen.TYPE_DEFS[t].get("backend", True)}
            for t in gen.TYPES]


@router.post("/scaffold")
def scaffold(body: ScaffoldIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    if body.type not in gen.TYPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"type ∈ {gen.TYPES}")
    try:
        files = gen.scaffold(body.id, body.name, body.type, description=body.description,
                             llm_alias=body.llm_alias, federation_url=body.federation_url)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    data = gen.pack(files)
    audit.record(db, actor=p.actor, actor_type=p.type, action="agent.scaffolded", agent_id=body.id,
                 detail={"type": body.type, "sha256": hashlib.sha256(data).hexdigest()})
    return Response(data, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{body.id}-0.1.0.zip"'})


# ---------- 등록 파이프라인·카탈로그 관리 (D5-01·D5-05·D5-06·D5-07·D4-07) ----------

def _builtin_guard(a: Agent | None, agent_id: str) -> Agent:
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"에이전트 없음 / not found: {agent_id}")
    if a.builtin:
        raise HTTPException(status.HTTP_409_CONFLICT, "내장 에이전트는 변경·삭제 불가 / builtin agent")
    return a


@router.post("/upload", status_code=202)
async def upload(background: BackgroundTasks, files: list[UploadFile] = File(...), env: str = Form("{}"),
                 force: bool = Form(False), p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """단일·다중 zip 업로드(경로 B 직접 설치). 파일마다 8단계 작업 ID 를 돌려준다."""
    try:
        env_map = json.loads(env or "{}")
        assert isinstance(env_map, dict)
    except (ValueError, AssertionError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "env 는 JSON 객체 / env must be a JSON object") from None
    limit = settings.upload_max_mb * 1024 * 1024
    out = []
    for f in files:
        data = await f.read(limit + 1)
        if len(data) > limit:
            out.append({"filename": f.filename, "error": f"크기 초과 > {settings.upload_max_mb}MB"})
            continue
        inst = pipeline.new_install(db, source="zip", source_ref=f.filename or "upload.zip", created_by=p.actor,
                                    env=env_map)
        background.add_task(pipeline.run, inst.id, data, force=force, env=env_map)
        out.append({"filename": f.filename, "install_id": inst.id})
    return out


class LinkIn(BaseModel):
    kind: str = Field(pattern="^(a2a|mcp|openapi)$")
    url: str = Field(pattern=r"^https?://", max_length=500)
    base_url: str | None = Field(default=None, pattern=r"^https?://", max_length=500)  # openapi: servers 대신 쓸 주소
    id: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9-]{1,40}$")
    auth_header: str | None = Field(default=None, max_length=100)
    auth_value: str | None = Field(default=None, max_length=2000)


@router.post("/link", status_code=201)
async def link_remote(body: LinkIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """경로 C — 원격 A2A Card / MCP 서버 등록(코드 미설치). 계약 시험 통과 후 카탈로그·라우팅에 편입."""
    from app.protocols import link
    try:
        a = await link.link(db, kind=body.kind, url=body.url, agent_id=body.id, header=body.auth_header,
                            value=body.auth_value, actor=p.actor, base_url=body.base_url)
    except link.LinkError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    caps = list(db.execute(select(Capability).where(Capability.agent_id == a.id)).scalars())
    return {**agent_out(a, caps), "federation": {k: v for k, v in a.manifest["spec"]["federation"].items() if k != "names"}}


@router.post("/{agent_id}/revalidate")
async def revalidate(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """원격 에이전트 재검증: 도구·스킬 목록 해시(pin)가 바뀌면 비활성화(rug-pull 방어)."""
    from app.protocols import link
    a = db.get(Agent, agent_id)
    if a is None or a.source != "link":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "원격 연동 에이전트 아님 / not a linked agent")
    return await link.revalidate(db, agent_id, p.actor)


class InstallUrlIn(BaseModel):
    url: str = Field(pattern=r"^https?://", max_length=500)
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    env: dict[str, str] = Field(default_factory=dict)
    force: bool = False


class InstallGitIn(BaseModel):
    url: str = Field(max_length=500)
    path: str = Field(default="", max_length=200)
    ref: str | None = Field(default=None, max_length=100)
    env: dict[str, str] = Field(default_factory=dict)
    force: bool = False


async def _start(background: BackgroundTasks, db: Session, p: Principal, source: str, ref: str, data: bytes,
                 env: dict, force: bool) -> dict:
    inst = pipeline.new_install(db, source=source, source_ref=ref, created_by=p.actor)
    background.add_task(pipeline.run, inst.id, data, force=force, env=env)
    return {"install_id": inst.id}


@router.post("/install-url", status_code=202)
async def install_url(body: InstallUrlIn, background: BackgroundTasks, p: Principal = Depends(require_admin),
                      db: Session = Depends(get_db)):
    """경로 B: zip URL 직접 설치(D6-03). sha256 을 주면 대조한다."""
    from app.registry import fetch
    try:
        data = await fetch.zip_url(body.url)
    except fetch.FetchError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    if body.sha256 and hashlib.sha256(data).hexdigest() != body.sha256:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "sha256 불일치 / digest mismatch")
    return await _start(background, db, p, "url", body.url, data, body.env, body.force)


@router.post("/install-git", status_code=202)
async def install_git(body: InstallGitIn, background: BackgroundTasks, p: Principal = Depends(require_admin),
                      db: Session = Depends(get_db)):
    """경로 B: Git URL(subdir·ref) 직접 설치(D6-03)."""
    import asyncio

    from app.registry import fetch
    try:
        data = await asyncio.to_thread(fetch.git_subdir, body.url, body.path, body.ref)
    except fetch.FetchError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    ref = f"{body.url}#{body.path}@{body.ref or 'HEAD'}"
    return await _start(background, db, p, "git", ref, data, body.env, body.force)


@router.get("/installs")
def list_installs(limit: int = 50, db: Session = Depends(get_db)):
    q = select(Install).order_by(Install.created_at.desc()).limit(min(limit, 200))
    return [pipeline.install_out(i) for i in db.execute(q).scalars()]


@router.get("/installs/{install_id}")
def install_status(install_id: str, db: Session = Depends(get_db)):
    i = db.get(Install, install_id)
    if i is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "작업 없음 / not found")
    return pipeline.install_out(i)


@router.get("/{agent_id}")
def get_agent(agent_id: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    a = db.get(Agent, agent_id)
    if a is None or (p.role == "user" and not orgs.visible(db, p.actor, p.role, agent_id)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "에이전트 없음 / not found")
    caps = list(db.execute(select(Capability).where(Capability.agent_id == a.id)).scalars())
    versions = [{"version": v.version, "current": v.current, "sha256": v.sha256, "installed_at": v.installed_at,
                 "signature": "unverified" if v.signature_ok is None else ("verified" if v.signature_ok else "invalid"),
                 "signer": v.signer, "license_grade": v.license_grade, "vulns": v.vulns, "sbom": bool(v.sbom_ref)}
                for v in db.execute(select(AgentVersion).where(AgentVersion.agent_id == a.id)
                                    .order_by(AgentVersion.installed_at.desc())).scalars()]
    return {**agent_out(a, caps), "manifest": a.manifest, "versions": versions, "endpoint": a.endpoint,
            "deploy_scope": orgs.scope_out(db.get(AgentScope, a.id))}


@router.get("/{agent_id}/install-status")
def agent_install_status(agent_id: str, db: Session = Depends(get_db)):
    i = db.execute(select(Install).where(Install.agent_id == agent_id).order_by(Install.created_at.desc())).scalars().first()
    if i is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "설치 이력 없음 / no install")
    return pipeline.install_out(i)


class AgentPatch(BaseModel):
    is_active: bool | None = None


@router.patch("/{agent_id}")
def patch_agent(agent_id: str, body: AgentPatch, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    a = _builtin_guard(db.get(Agent, agent_id), agent_id)
    if body.is_active is not None:
        a.is_active = body.is_active
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.updated",
                 detail=body.model_dump(exclude_none=True))
    return agent_out(a, list(db.execute(select(Capability).where(Capability.agent_id == a.id)).scalars()))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    _builtin_guard(db.get(Agent, agent_id), agent_id)
    result = await pipeline.uninstall(db, agent_id)
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.deleted", detail=result)
    return result


def _current(db: Session, agent_id: str) -> AgentVersion:
    v = db.execute(select(AgentVersion).where(AgentVersion.agent_id == agent_id, AgentVersion.current.is_(True))).scalar_one_or_none()
    if v is None or not Path(v.artifact).is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "설치 산출물 없음 / no artifact")
    return v


def _current_files(db: Session, agent_id: str) -> dict[str, bytes]:
    return gen.read_zip(Path(_current(db, agent_id).artifact).read_bytes())


@router.get("/{agent_id}/sbom")
def agent_sbom(agent_id: str, db: Session = Depends(get_db)):
    """현재 버전 SBOM(CycloneDX JSON, 등록 3단계 syft 생성)."""
    v = _current(db, agent_id)
    if not v.sbom_ref or not Path(v.sbom_ref).is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SBOM 없음 / no SBOM")
    return Response(Path(v.sbom_ref).read_bytes(), media_type="application/vnd.cyclonedx+json")


class DeriveIn(BaseModel):
    new_id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,40}$")
    name: str | None = None


class RestoreIn(BaseModel):
    backup: str = Field(pattern=r"^\d{8}T\d{6}Z$")


def _installed(db: Session, agent_id: str) -> Agent:
    a = _builtin_guard(db.get(Agent, agent_id), agent_id)
    if a.source == "link":
        raise HTTPException(status.HTTP_409_CONFLICT, "원격 연동 에이전트는 볼륨이 없음 / linked agent has no volumes")
    return a


@router.post("/{agent_id}/backup")
async def backup_agent(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """볼륨 백업(D8-06): runtime 이 일시정지 스냅숏을 tar.gz 로 남긴다."""
    _installed(db, agent_id)
    try:
        out = await get_runtime().backup(agent_id)
    except RuntimeFailure as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.backup", detail={"backup": out["backup"]})
    return out


@router.get("/{agent_id}/backups")
async def list_backups(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    _installed(db, agent_id)
    try:
        return await get_runtime().backups(agent_id)
    except RuntimeFailure as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None


@router.post("/{agent_id}/restore")
async def restore_agent(agent_id: str, body: RestoreIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    _installed(db, agent_id)
    try:
        out = await get_runtime().restore(agent_id, body.backup)
    except RuntimeFailure as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND if "not found" in str(exc) else status.HTTP_409_CONFLICT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.restored", detail={"backup": body.backup})
    return out


@router.post("/{agent_id}/rotate-key")
async def rotate_key(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """게이트웨이 키 회전(D9-04). 사용자 시크릿 회전은 PUT /api/secrets/agent:{id}/{NAME}."""
    _builtin_guard(db.get(Agent, agent_id), agent_id)
    try:
        out = await pipeline.rotate_gateway_key(db, agent_id)
    except RuntimeFailure as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.key_rotated", detail=out)
    return out


@router.post("/{agent_id}/export")
def export_derived(agent_id: str, body: DeriveIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """파생 export(D4-07, v1 F26): 출처(provenance) 자동 기록. G4 라이선스는 포크 금지(PRD 9.7)."""
    if _current(db, agent_id).license_grade == "G4":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "G4 라이선스 — 파생(포크) 금지, 연계(M2)만 / derive forbidden")
    files = gen.derive(_current_files(db, agent_id), body.new_id, body.name)
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.exported",
                 detail={"derived": body.new_id})
    return Response(gen.pack(files), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{body.new_id}-0.1.0.zip"'})


@router.post("/{agent_id}/export-standalone")
def export_standalone(agent_id: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """M1 독립 번들(D4-07, v1 F27): docker compose --profile standalone up 으로 단독 구동."""
    files = gen.standalone_bundle(_current_files(db, agent_id))
    m = gen.manifest_of(files)
    ver = m["metadata"]["version"]
    # M1 기본 주소(PORT=8001)로 서명한 카드와 server.json 을 함께 넣는다(PRD 7.4 생성물)
    from app.protocols import card as cards
    files["a2a/agent-card.json"] = json.dumps(cards.signed_card_json(m, "http://127.0.0.1:8001/a2a"), ensure_ascii=False,
                                              indent=2).encode()
    files["mcp/server.json"] = json.dumps(cards.server_json(m, "http://127.0.0.1:8001/mcp"), ensure_ascii=False,
                                          indent=2).encode()
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="agent.exported",
                 detail={"standalone": True})
    return Response(gen.pack(files), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{agent_id}-{ver}-standalone.zip"'})


class RollbackIn(BaseModel):
    version: str


@router.post("/{agent_id}/rollback", status_code=202)
async def rollback(agent_id: str, body: RollbackIn, background: BackgroundTasks,
                   p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    _builtin_guard(db.get(Agent, agent_id), agent_id)
    v = db.execute(select(AgentVersion).where(AgentVersion.agent_id == agent_id,
                                              AgentVersion.version == body.version)).scalar_one_or_none()
    if v is None or not Path(v.artifact).is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "해당 버전 산출물 없음 / version not found")
    inst = pipeline.new_install(db, source="zip", source_ref=f"rollback:{body.version}", created_by=p.actor,
                                env=_last_env(db, agent_id))
    background.add_task(pipeline.run, inst.id, Path(v.artifact).read_bytes(), force=True, env=_last_env(db, agent_id))
    return {"install_id": inst.id}


def _last_env(db: Session, agent_id: str) -> dict:
    i = db.execute(select(Install).where(Install.agent_id == agent_id, Install.status == "succeeded")
                   .order_by(Install.created_at.desc())).scalars().first()
    return dict(i.env) if i else {}


@router.get("/{agent_id}/ui")
def ui_mount(agent_id: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    """프론트 통합(D5-07): 콘솔이 iframe 으로 마운트할 정보. 네비 노출 규칙 = is_active && hasFrontend && 배치 범위 안."""
    a = db.get(Agent, agent_id)
    if a is None or not orgs.visible(db, p.actor, p.role, agent_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "에이전트 없음 / not found")
    ui = a.manifest.get("spec", {}).get("ui", {})
    has_front = bool(ui.get("hasFrontend"))
    return {"agent_id": a.id, "mount": ui.get("mount", "none") if has_front else "chat",
            "src": f"{settings.public_apps_url.rstrip('/')}/a/{a.id}/ui/" if has_front else None,
            "origin": settings.public_apps_url.rstrip("/"),
            "fallback_chat": f"/a/{a.id}/chat",  # 화면 없는 에이전트 = 스코프 채팅(NFR-U5)
            "nav_visible": bool(a.is_active and has_front and ui.get("navVisible", True)),
            "sandbox": "allow-scripts allow-forms allow-same-origin",
            "postMessage": {"version": 1, "types": ["ready", "auth", "context", "resize", "navigate", "notify",
                                                    "modal", "telemetry", "error"]}}
