"""등록 8단계 (PRD 10.4): 업로드·수집 → 구조 검증 → 서명·SBOM·취약점 → 라이선스·정책 → 빌드 → 등록 → 기동·헬스 → 노출.

3단계(D5-03): checksums 무결성·cosign 서명(신뢰 키)·SBOM(syft)·취약점(trivy). 서명 없음 = '미검증' 경고(NFR-S2).
4단계(D5-04): 라이선스 등급 G1~G5·선언 egress vs 조직 정책. 단계 상태는 ok | warn | failed.
실패 시: 새 설치는 흔적 제거, 업그레이드는 이전 버전으로 복구한다.
"""
import asyncio
import hashlib
import json
import shutil
import uuid
from pathlib import Path

import httpx
import yaml
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.agentspec import generator as gen
from app.core.config import settings
from app.core.security import new_api_key
from app.db import SessionLocal, utcnow
from app.models import Agent, AgentVersion, ApiKey, Install
from app.orchestrator import executor
from app.registry import gate
from app.runtime.driver import RuntimeFailure, get_runtime
from app.services import audit, registry
from app.services import secrets as secret_store
from app.supplychain import tools as sc_tools
from app.supplychain import trust as sc_trust

STEPS = ["업로드·수집", "구조 검증", "서명·SBOM·취약점", "라이선스·정책", "빌드", "등록", "기동·헬스", "노출"]
# 설치 후 훅(예: Epic 8 Agent Card·server.json 생성). (db, agent, workdir) -> None
POST_REGISTER: list = []
CONTRACT_CHECKS: list = []  # (endpoint, manifest) -> list[str] 오류 — 기본으로 protocol_contract 를 넣는다(아래)


async def protocol_contract(endpoint: str, manifest: dict) -> list[str]:
    """NFR-P3: 에이전트가 실제로 노출하는 MCP tools/list·A2A 카드 skills 가 agent.yaml 과 같아야 한다."""
    from app.protocols import card as cards
    from app.protocols import link
    declared = {c["verb"] for c in manifest["spec"]["capabilities"]}
    headers = {"x-api-key": registry.agent_key(manifest["metadata"]["id"])}
    errs = []
    for mode, ver in (("discover", "2026-07-28"), ("initialize", "2025-11-25")):  # NFR-P1: 두 핸드셰이크 모두(Q8)
        try:
            tools = {t["name"] for t in await link.mcp_tools(f"{endpoint}/mcp", headers, mode=mode)}
            if tools != declared:
                errs.append(f"MCP {ver} tools 불일치 declared={sorted(declared)} served={sorted(tools)}")
        except Exception as exc:  # noqa: BLE001
            errs.append(f"MCP {ver}({mode}) 계약 시험 실패: {type(exc).__name__}")
    try:
        _, card, _ = await link.fetch_card(endpoint, headers)
        if {s.id for s in card.skills} != declared:
            errs.append("Agent Card skills 불일치")
        cards.verify(card)
    except Exception as exc:  # noqa: BLE001
        errs.append(f"Agent Card 계약 시험 실패: {type(exc).__name__}: {exc}")
    return errs


def data_path(*parts: str) -> Path:
    return Path(settings.data_dir).joinpath(*parts)


def network_for(agent_id: str) -> str:
    """에이전트 전용 네트워크(runtime 이 만들고 api·traefik 만 연결, NFR-I4)."""
    return f"{settings.plaza_project}-net-{agent_id}"


def _prune(aid: str) -> None:
    """실패·롤백 후 비어 버린 installed/{id} 상위 디렉터리를 남기지 않는다."""
    parent = data_path("installed", aid)
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def endpoint_for(agent_id: str) -> str:
    return f"http://{agent_id}-be:{gen.AGENT_PORT}"


def semver(v: str) -> tuple:
    core = v.split("+")[0].split("-")[0]
    return tuple(int(x) for x in core.split("."))


def new_install(db: Session, *, source: str, source_ref: str, created_by: str, env: dict | None = None) -> Install:
    """env 값은 여기 저장하지 않는다 — run(env=…) 으로 메모리로만 넘기고, 2단계에서 비밀 아닌 선언 키만 Install.env 에,
    secretRefs 는 암호화 저장소(D9-04)에 넣는다."""
    inst = Install(id=str(uuid.uuid4()), source=source, source_ref=source_ref[:500], created_by=created_by, env={},
                   steps=[{"n": i + 1, "name": n, "status": "pending"} for i, n in enumerate(STEPS)], warnings=[])
    db.add(inst)
    db.commit()
    return inst


def _mark(db: Session, inst: Install, n: int, status: str, detail: str | dict = "") -> None:
    steps = [dict(s) for s in inst.steps]
    steps[n - 1].update(status=status, detail=detail, at=utcnow().isoformat())
    inst.steps, inst.step = steps, n
    db.commit()


def _fail(db: Session, inst: Install, n: int, msg: str, status: str = "failed") -> None:
    _mark(db, inst, n, "failed", msg)
    inst.status, inst.error = status, msg
    audit.record(db, actor=inst.created_by, actor_type="user", agent_id=inst.agent_id, action="agent.install_failed",
                 resource=f"install:{inst.id}", outcome="error", detail={"step": n, "error": msg[:500]})
    from app.services import notify
    notify.emit(db, "install_failed", "error", f"설치 실패: {inst.agent_id or inst.source_ref} ({n}단계)", msg[:500],
                resource=f"install:{inst.id}", dedup_minutes=0)


async def wait_healthy(endpoint: str, timeout: float) -> bool:
    deadline = asyncio.get_running_loop().time() + timeout
    async with httpx.AsyncClient(base_url=endpoint, transport=executor.TRANSPORTS.get(endpoint), timeout=5) as c:
        while asyncio.get_running_loop().time() < deadline:
            try:
                if (await c.get("/health")).status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
    return False


async def wait_routed(agent_id: str, timeout: float = 30.0) -> bool:
    """8단계 노출 확인: 게이트웨이(Traefik)가 /a/{id}/health 를 실제로 이 에이전트로 보낼 때까지 기다린다.
    컨테이너가 healthy 여도 Traefik 이 라우터를 반영하기 전 1~2초 동안 요청이 다른 라우터로 빠질 수 있다."""
    if not settings.gateway_internal_url:
        return True
    from app.core.security import create_token
    token = create_token("pipeline", "admin", typ="service", scopes={"agents": [agent_id]}, ttl_minutes=2)
    deadline = asyncio.get_running_loop().time() + timeout
    async with httpx.AsyncClient(base_url=settings.gateway_internal_url, timeout=5) as c:
        while asyncio.get_running_loop().time() < deadline:
            try:
                res = await c.get(f"/a/{agent_id}/health", headers={"authorization": f"Bearer {token}"})
                if res.status_code == 200 and res.headers.get("content-type", "").startswith("application/json") \
                        and res.json().get("agent") == agent_id:
                    return True
            except (httpx.HTTPError, ValueError):
                pass
            await asyncio.sleep(0.5)
    return False


async def contract(endpoint: str, manifest: dict) -> list[str]:
    """선언 vs 런타임(DP4·NFR-P3): 노출 capability 가 agent.yaml 과 같아야 한다."""
    headers = {"x-api-key": registry.agent_key(manifest["metadata"]["id"])}
    async with httpx.AsyncClient(base_url=endpoint, transport=executor.TRANSPORTS.get(endpoint), timeout=10) as c:
        res = await c.get("/api/capabilities", headers=headers)
    if res.status_code != 200:
        return [f"/api/capabilities HTTP {res.status_code}"]
    declared = {c["verb"] for c in manifest["spec"]["capabilities"]}
    served = {c["verb"] for c in res.json()}
    errs = [] if declared == served else [f"capability 불일치 declared={sorted(declared)} served={sorted(served)}"]
    for check in CONTRACT_CHECKS:
        errs += await check(endpoint, manifest)
    return errs


def _agent_gateway_key(db: Session, agent_id: str) -> str:
    """에이전트가 게이트웨이(/v1)를 부를 키. 이전 키는 폐기하고 새로 발급한다. 원문은 workdir/.env 에만."""
    for k in db.execute(select(ApiKey).where(ApiKey.name == f"agent:{agent_id}", ApiKey.revoked_at.is_(None))).scalars():
        k.revoked_at = utcnow()
    raw, prefix, h = new_api_key()
    db.add(ApiKey(name=f"agent:{agent_id}", key_prefix=prefix, key_hash=h, role="user",
                  scopes={"agents": [agent_id], "agent": agent_id}, owner_id=0))
    db.flush()
    return raw


def _write_workdir(workdir: Path, files: dict[str, bytes], manifest: dict, env: dict, gw_key: str) -> None:
    if workdir.exists():
        shutil.rmtree(workdir)
    for rel, body in files.items():
        dst = workdir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(body)
    doc = gen.compose_for(manifest, federated=True, network=network_for(manifest["metadata"]["id"]))
    (workdir / "compose.plaza.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    declared = set(manifest["spec"].get("env", {}).get("required", []) + manifest["spec"].get("env", {}).get("optional", []))
    lines = {"AGENT_API_KEY": registry.agent_key(manifest["metadata"]["id"]), "LLM_BASE_URL": settings.agent_gateway_url,
             "LLM_API_KEY": gw_key, "PLAZA_REGISTRY": "local", "PLAZA_PROJECT": settings.plaza_project,
             "CONSOLE_ORIGIN": settings.public_base_url.rstrip("/"),
             "PLAZA_API_URL": settings.platform_internal_url,  # 시크릿 pull(D9-04) — 값은 파일에 쓰지 않는다
             **{k: str(v) for k, v in env.items() if k in declared}}  # 선언된 키만 주입(임의 env 차단)
    (workdir / ".env").write_text("".join(f"{k}={v}\n" for k, v in lines.items()))
    (workdir / ".env").chmod(0o600)
    # 생성물(PRD 7.4, 수정 금지): 플랫폼 서명 Agent Card · MCP server.json — 이미지에 함께 들어간다
    from app.protocols import card as cards
    (workdir / "a2a").mkdir(exist_ok=True)
    (workdir / "a2a" / "agent-card.json").write_text(json.dumps(cards.signed_card_json(manifest), ensure_ascii=False, indent=2))
    (workdir / "mcp").mkdir(exist_ok=True)
    (workdir / "mcp" / "server.json").write_text(json.dumps(cards.server_json(manifest), ensure_ascii=False, indent=2))


async def run(install_id: str, data: bytes, *, force: bool = False, trust: str = "community",
              env: dict | None = None) -> None:
    env = {k: str(v) for k, v in (env or {}).items()}
    with SessionLocal() as db:
        inst = db.get(Install, install_id)
        inst.status = "running"
        rt = get_runtime()
        # 1 업로드·수집
        digest = hashlib.sha256(data).hexdigest()
        _mark(db, inst, 1, "ok", {"bytes": len(data), "sha256": digest})
        # 2 구조 검증
        g = gate.inspect(gate.extract(data))
        inst.warnings = g.warnings
        if not g.ok:
            return _fail(db, inst, 2, "; ".join(g.errors[:20]))
        m = g.manifest
        aid, ver = m["metadata"]["id"], m["metadata"]["version"]
        inst.agent_id, inst.version = aid, ver
        prev = db.get(Agent, aid)
        if prev is not None and prev.builtin:
            return _fail(db, inst, 2, f"예약된 내장 id: {aid}")
        if prev is not None and prev.source == "link":
            return _fail(db, inst, 2, f"원격 연동 에이전트와 id 충돌: {aid}")
        if prev is not None and not force and semver(ver) <= semver(prev.version):
            return _fail(db, inst, 2, f"버전은 현재({prev.version})보다 커야 함 — force 로 재설치 / version must increase")
        if m["spec"].get("runtime", {}).get("mode") == "inprocess":
            return _fail(db, inst, 2, "in-process 모드는 서명된 신뢰 퍼블리셔 전용(D5-03, P1 미구현) — container 사용 (NFR-I2)")
        if m["spec"]["type"] == "federation":
            return _fail(db, inst, 2, "federation 유형은 원격 연동(경로 C, /api/agents/link)으로 등록")
        spec_env = m["spec"].get("env", {})
        secret_refs = spec_env.get("secretRefs", [])
        declared = set(spec_env.get("required", []) + spec_env.get("optional", [])) - set(secret_refs)
        inst.env = {k: v for k, v in env.items() if k in declared}  # 비밀 아닌 선언 키만 남긴다
        missing = [k for k in spec_env.get("required", []) if not inst.env.get(k) and k not in secret_refs]
        if missing:
            return _fail(db, inst, 2, f"required_env 누락: {missing}")
        have = secret_store.names(db, f"agent:{aid}")
        missing = [k for k in secret_refs if not env.get(k) and k not in have]
        if missing:
            return _fail(db, inst, 2, f"secretRefs 값 누락: {missing}")
        new_secrets = {k: env[k] for k in secret_refs if env.get(k)}
        _mark(db, inst, 2, "ok", {"warnings": len(g.warnings), "files": len(g.files)})
        # 3 서명·SBOM·취약점 (D5-03, NFR-S2)
        pol = sc_trust.policy(db)
        v3 = sc_trust.verify_signature(db, g.files, g.meta, m)
        scanned: dict = {"sbom": {}}
        if v3.status != "failed":
            try:
                v_scan, scanned = await asyncio.to_thread(sc_trust.scan, data_path("staging", inst.id), g.files)
            except sc_tools.ToolError as exc:
                return _fail(db, inst, 3, f"공급망 도구 오류 / tool error: {exc}")
            v3.merge(v_scan)
            sc_trust.gate_vulns(v3, scanned, pol)
        if v3.status != "failed" and pol["require_signature"] and v3.detail.get("signature") != "verified":
            v3.fail("정책: 서명 검증된 패키지만 설치 / policy requires a verified signature")
        if v3.status == "failed":
            return _fail(db, inst, 3, v3.error)
        inst.warnings = [*inst.warnings, *v3.warnings]
        _mark(db, inst, 3, v3.status, v3.detail)
        # 4 라이선스·정책 (D5-04)
        v4 = sc_trust.license_policy(m, scanned["sbom"], pol)
        if v4.status == "failed":
            return _fail(db, inst, 4, v4.error)
        inst.warnings = [*inst.warnings, *v4.warnings]
        _mark(db, inst, 4, v4.status, v4.detail)
        # 5 빌드
        workdir = data_path("installed", aid, ver)
        gw_key = _agent_gateway_key(db, aid)
        _write_workdir(workdir, g.files, m, inst.env, gw_key)
        try:
            await rt.build(aid, workdir)
        except RuntimeFailure as exc:
            shutil.rmtree(workdir, ignore_errors=True)
            _prune(aid)
            db.rollback()
            return _fail(db, inst, 5, f"빌드 실패: {exc}")
        backup = None
        if prev is not None and prev.source != "link" and hasattr(rt, "backup"):  # NFR-O4: 업그레이드 전 백업
            try:
                backup = (await rt.backup(aid))["backup"]
            except RuntimeFailure as exc:
                shutil.rmtree(workdir, ignore_errors=True)
                db.rollback()
                return _fail(db, inst, 5, f"업그레이드 전 백업 실패 — 중단 / pre-upgrade backup failed: {exc}")
        _mark(db, inst, 5, "ok", {"workdir": str(workdir), "image_tag": f"{aid}:{ver}", "pre_upgrade_backup": backup})
        # 6 등록
        prev_manifest = dict(prev.manifest) if prev else None
        prev_version = prev.version if prev else None
        artifact = data_path("artifacts", aid, f"{ver}.zip")
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(data)
        agent = registry.register(db, m, endpoint=endpoint_for(aid), source=inst.source, trust=trust,
                                  status="registered", commit=False)
        db.execute(update(AgentVersion).where(AgentVersion.agent_id == aid).values(current=False))
        row = db.execute(select(AgentVersion).where(AgentVersion.agent_id == aid, AgentVersion.version == ver)).scalar_one_or_none()
        row = row or AgentVersion(agent_id=aid, version=ver, installed_by=inst.created_by)
        row.sha256, row.artifact, row.current, row.installed_at = digest, str(artifact), True, utcnow()
        sbom_path = artifact.with_suffix(".sbom.json")
        sbom_path.write_text(json.dumps(scanned["sbom"], ensure_ascii=False))
        row.signature_ok = True if v3.detail.get("signature") == "verified" else None
        row.signer, row.sbom_ref = v3.detail.get("signer"), str(sbom_path)
        row.license_grade = v4.detail["effective"]
        row.vulns = v3.detail.get("vulns")
        db.add(row)
        for k, v in new_secrets.items():  # 암호문만 저장(D9-04). 에이전트는 기동 후 pull 한다
            secret_store.put(db, f"agent:{aid}", k, v, inst.created_by, commit=False)
        db.commit()
        for hook in POST_REGISTER:
            hook(db, agent, workdir)
        _mark(db, inst, 6, "ok", {"version": ver, "upgrade_from": prev_version})
        # 7 기동·헬스·계약 시험
        error = None
        try:
            await _up(rt, aid, workdir, m, trust)
            if not await wait_healthy(endpoint_for(aid), settings.health_timeout_seconds):
                error = "헬스 체크 시간 초과 / health timeout"
            else:
                errs = await contract(endpoint_for(aid), m)
                error = "; ".join(errs) if errs else None
        except RuntimeFailure as exc:
            error = f"기동 실패: {exc}"
        if error:
            await _rollback(db, rt, aid, workdir, prev_manifest, prev_version, backup)
            return _fail(db, inst, 7, error, status="rolled_back")
        _mark(db, inst, 7, "ok", "healthy")
        # 8 노출: 카탈로그 상태 healthy → 라우팅·콘솔 네비·Assistant 도구·MCP/A2A 게이트웨이에 반영
        if not await wait_routed(aid):
            inst.warnings = [*inst.warnings, "게이트웨이 라우트 반영 지연 — 잠시 후 /a/{id}/… 사용 가능"]
        agent.status = "healthy"
        inst.status = "succeeded"
        _mark(db, inst, 8, "ok", {"nav": bool(m["spec"].get("ui", {}).get("hasFrontend")),
                                 "routes": [f"/a/{aid}/api", f"/mcp/{aid}"]})
        audit.record(db, actor=inst.created_by, actor_type="user", agent_id=aid, action="agent.installed",
                     resource=f"install:{inst.id}",
                     detail={"version": ver, "source": inst.source, "source_ref": inst.source_ref, "sha256": digest,
                             "license": m["metadata"].get("license"), "license_grade": v4.detail["effective"],
                             "signature": v3.detail.get("signature"), "signer": v3.detail.get("signer"),
                             "vulns": v3.detail.get("vulns", {}).get("status")})  # NFR-C2 출처·라이선스 증적
        write_include(db)


async def _up(rt, aid: str, workdir: Path, manifest: dict, trust: str) -> None:
    if rt.name == "remote":
        await rt.up(aid, workdir, egress=gen.has_egress(manifest), trust=trust)
    else:
        await rt.up(aid, workdir)


async def _rollback(db: Session, rt, aid: str, workdir: Path, prev_manifest: dict | None, prev_version: str | None,
                    backup: str | None = None) -> None:
    try:
        await rt.down(aid, workdir, volumes=prev_manifest is None)
    except RuntimeFailure:
        pass
    shutil.rmtree(workdir, ignore_errors=True)
    if prev_manifest is None:
        remove_catalog(db, aid)
        secret_store.delete(db, f"agent:{aid}")
        shutil.rmtree(data_path("artifacts", aid), ignore_errors=True)
        _prune(aid)
        return
    prev_dir = data_path("installed", aid, prev_version)
    failed = workdir.name  # 실패한 새 버전은 이력·산출물에 남기지 않는다(다시 롤백 대상으로 보이지 않게)
    if failed != prev_version:
        for v in db.execute(select(AgentVersion).where(AgentVersion.agent_id == aid, AgentVersion.version == failed)).scalars():
            db.delete(v)
        for f in (data_path("artifacts", aid, f"{failed}.zip"), data_path("artifacts", aid, f"{failed}.sbom.json")):
            f.unlink(missing_ok=True)
    registry.register(db, prev_manifest, endpoint=endpoint_for(aid), source=db.get(Agent, aid).source,
                      status="healthy", commit=False)
    db.execute(update(AgentVersion).where(AgentVersion.agent_id == aid).values(current=False))
    db.execute(update(AgentVersion).where(AgentVersion.agent_id == aid, AgentVersion.version == prev_version)
               .values(current=True))
    db.commit()
    try:
        if backup:  # 새 버전이 데이터를 바꿨을 수 있다 — 업그레이드 전 스냅숏으로 되돌린 뒤 이전 태그로 기동(NFR-O4)
            await rt.restore(aid, backup)
        await _up(rt, aid, prev_dir, prev_manifest, db.get(Agent, aid).trust)
    except RuntimeFailure:
        db.get(Agent, aid).status = "unhealthy"
        db.commit()


async def rotate_gateway_key(db: Session, aid: str) -> dict:
    """에이전트 게이트웨이 키 회전(D9-04): 새 키 발급·이전 키 폐기 → workdir/.env 갱신 → 컨테이너 재생성."""
    a = db.get(Agent, aid)
    current = db.execute(select(AgentVersion).where(AgentVersion.agent_id == aid, AgentVersion.current.is_(True))).scalar_one_or_none()
    if a is None or current is None:
        raise RuntimeFailure("설치 에이전트 아님 / not an installed agent")
    workdir = data_path("installed", aid, current.version)
    env_file = workdir / ".env"
    lines = [ln for ln in env_file.read_text().splitlines() if not ln.startswith("LLM_API_KEY=")]
    key = _agent_gateway_key(db, aid)
    env_file.write_text("\n".join([*lines, f"LLM_API_KEY={key}"]) + "\n")
    env_file.chmod(0o600)
    db.commit()
    await _up(get_runtime(), aid, workdir, a.manifest, a.trust)
    return {"agent": aid, "rotated": "LLM_API_KEY"}


def remove_catalog(db: Session, aid: str) -> None:
    a = db.get(Agent, aid)
    if a is not None:
        db.delete(a)  # capabilities 는 FK CASCADE
    for v in db.execute(select(AgentVersion).where(AgentVersion.agent_id == aid)).scalars():
        db.delete(v)
    for k in db.execute(select(ApiKey).where(ApiKey.name == f"agent:{aid}", ApiKey.revoked_at.is_(None))).scalars():
        k.revoked_at = utcnow()
    db.commit()


async def uninstall(db: Session, aid: str) -> dict:
    """삭제(NFR-I6): 컨테이너·볼륨·라우트·카탈로그·MCP/A2A 노출·설치 파일을 모두 제거."""
    rt = get_runtime()
    started = asyncio.get_running_loop().time()
    a = db.get(Agent, aid)
    current = db.execute(select(AgentVersion).where(AgentVersion.agent_id == aid, AgentVersion.current.is_(True))).scalar_one_or_none()
    workdir = data_path("installed", aid, current.version) if current else None
    if a is not None and a.source != "link":
        await rt.down(aid, workdir, volumes=True)
    if a is not None and a.source == "link":
        from app.protocols.link import save_secret
        save_secret(aid, None, None)  # 원격 인증 값 파기
    secret_store.delete(db, f"agent:{aid}")
    remove_catalog(db, aid)
    shutil.rmtree(data_path("installed", aid), ignore_errors=True)
    shutil.rmtree(data_path("artifacts", aid), ignore_errors=True)
    write_include(db)
    return {"deleted": aid, "seconds": round(asyncio.get_running_loop().time() - started, 2)}


def write_include(db: Session) -> Path:
    """루트 compose include 목록(D8-02, PRD 10.3): 설치된 현재 버전을 M2 로 함께 기동할 때 쓴다."""
    rows = db.execute(select(AgentVersion).where(AgentVersion.current.is_(True)).order_by(AgentVersion.agent_id)).scalars()
    entries = [{"path": f"{v.agent_id}/{v.version}/compose.plaza.yaml", "project_directory": f"{v.agent_id}/{v.version}",
                "env_file": f"{v.agent_id}/{v.version}/.env"} for v in rows]
    out = data_path("installed", "plaza.include.yaml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# 자동 생성 — 플랫폼 루트 compose 에 include 하면 설치 에이전트를 M2 로 함께 기동한다\n"
                   + yaml.safe_dump({"include": entries}, sort_keys=False))
    return out


def install_out(i: Install) -> dict:
    return {"id": i.id, "agent_id": i.agent_id, "version": i.version, "source": i.source, "source_ref": i.source_ref,
            "status": i.status, "step": i.step, "steps": i.steps, "warnings": i.warnings, "error": i.error,
            "created_at": i.created_at, "updated_at": i.updated_at}


CONTRACT_CHECKS.append(protocol_contract)
