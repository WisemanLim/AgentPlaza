"""원격 레지스트리 연결·동기화 + 오프라인 번들 (D6-07, UI E13).

- 레지스트리 = MCP registry API(/v0.1/servers) 서버. 다른 AgentPlaza 마켓(io.agentplaza/listing 메타 포함)은 패키지 리스팅으로,
  일반 MCP 서버(공식 레지스트리 미러 등)는 remotes(streamable-http)가 있으면 경로 C(remote-mcp) 리스팅으로 편입한다.
- 증분 동기화(updated_since) · 같은 버전의 체크섬이 바뀌면 거부 · 다른 출처와 id 가 겹치면 건너뜀(overwrite 로 덮어쓰기)
- 인증 토큰은 시크릿 저장소(scope=registry:<이름>), 원격 마켓의 라이선스 발급 공개키는 발급자 목록에 등록(오프라인 검증)
- 번들 = tar.gz(catalog.json + artifacts/*.zip + SHA256SUMS). 가져올 때 모든 파일 체크섬·리스팅 sha256 을 검증한다.
"""
import hashlib
import io
import json
import re
import tarfile
from datetime import datetime
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.market import catalog, licensing, payments
from app.models import MarketListing
from app.orchestrator import executor
from app.registry.pipeline import data_path
from app.services import secrets as secret_store
from app.services import sysconfig

REGS_KEY = "market.registries"
OURS = "io.agentplaza/listing"
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
MAX_PAGES = 50
BUNDLE_MAX = 512 * 1024 * 1024


class RemoteError(ValueError):
    pass


# ---- 레지스트리 설정 ----

def registries(db: Session) -> dict:
    return sysconfig.blob(db, REGS_KEY)


def _save(db: Session, regs: dict) -> None:
    sysconfig.put_blob(db, REGS_KEY, regs)


def put_registry(db: Session, name: str, *, url: str, token: str | None, license_key: str | None, interval: int,
                 actor: str) -> dict:
    if not NAME.match(name):
        raise RemoteError("이름은 소문자·숫자·하이픈 2~40자")
    u = urlparse(url)
    if u.scheme != "https" and not (u.scheme == "http" and settings.app_env != "prod"):
        raise RemoteError("레지스트리 URL 은 https 만(로컬 개발은 http 허용) / https only")
    regs = registries(db)
    cfg = {**regs.get(name, {}), "url": url.rstrip("/"), "interval_minutes": max(0, int(interval))}
    if token:
        secret_store.put(db, f"registry:{name}", "TOKEN", token, actor)
    if license_key:
        cfg["license_issuer"] = licensing.add_issuer(db, f"registry:{name}", license_key)
    regs[name] = cfg
    _save(db, regs)
    return cfg


def delete_registry(db: Session, name: str) -> int:
    regs = registries(db)
    cfg = regs.pop(name, None)
    if cfg is None:
        raise RemoteError("레지스트리 없음 / not found")
    _save(db, regs)
    secret_store.delete(db, f"registry:{name}")
    if cfg.get("license_issuer"):
        licensing.remove_issuer(db, cfg["license_issuer"])
    rows = list(db.execute(select(MarketListing).where(MarketListing.origin == f"registry:{name}")).scalars())
    for r in rows:
        db.delete(r)
    db.commit()
    return len(rows)


def _headers(db: Session, name: str) -> dict:
    token = secret_store.get(db, f"registry:{name}", "TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def headers_for(db: Session, x: dict, version: str) -> dict:
    """원격 산출물 다운로드 헤더: 레지스트리 인증 + 유료면 이 버전을 덮는 라이선스 토큰."""
    reg = (x.get("source") or {}).get("registry")
    h = _headers(db, reg) if reg else {}
    if reg and payments.is_paid(x):
        lic = licensing.entitled(db, x["id"], version)
        if lic:
            h["X-Plaza-License"] = lic[0].token
    return h


async def _fetch(db: Session, name: str, cfg: dict, params: dict) -> dict:
    base = cfg["url"]
    origin = f"{urlparse(base).scheme}://{urlparse(base).netloc}"
    try:
        async with httpx.AsyncClient(transport=executor.TRANSPORTS.get(origin), timeout=30) as c:
            res = await c.get(f"{base}/v0.1/servers", params=params, headers=_headers(db, name))
    except httpx.HTTPError as exc:
        raise RemoteError(f"연결 실패: {type(exc).__name__}") from None
    if res.status_code in (401, 403):
        raise RemoteError("auth_failed")
    if res.status_code != 200:
        raise RemoteError(f"HTTP {res.status_code}")
    return res.json()


async def test(db: Session, name: str) -> dict:
    regs = registries(db)
    cfg = regs[name]
    try:
        await _fetch(db, name, cfg, {"limit": 1})
        cfg.update(status="ok", error=None)
    except RemoteError as exc:
        cfg.update(status="auth_failed" if str(exc) == "auth_failed" else "error", error=str(exc))
    regs[name] = cfg
    _save(db, regs)
    return cfg


def _slug(server_name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", server_name.lower()).strip("-")[:64]


def _listing_of(name: str, entry: dict) -> tuple[dict | None, str | None]:
    server, meta = entry.get("server") or {}, (entry.get("_meta") or {})
    ours = meta.get(OURS)
    if ours:
        art = ours.get("artifact") or {}
        if ours.get("source_type") in catalog.REMOTE_TYPES:
            return {**ours, "version": server.get("version"), "source": ours["source"]}, None
        if not art.get("url") or not re.fullmatch(r"[0-9a-f]{64}", art.get("sha256") or ""):
            return None, "체크섬 없는 산출물 — 거부 / missing sha256"
        x = {k: v for k, v in ours.items() if k not in ("artifact", "source_type")}
        return {**x, "version": server.get("version", x.get("version")),
                "source": {"type": "zip-url", "url": art["url"], "sha256": art["sha256"], "registry": name}}, None
    remotes = [r for r in server.get("remotes") or [] if r.get("type") == "streamable-http" and r.get("url")]
    if not remotes:
        return None, "로컬 실행 패키지(npm·pypi·oci)만 있는 서버는 미지원 / package-only server"
    title = server.get("title") or server.get("name", "")
    return {"id": _slug(server.get("name", "")), "version": server.get("version", "0.0.0"), "type": "federation",
            "name": title, "description": server.get("description", ""), "categories": [], "industry": "-",
            "work": "W19", "domain": "common", "tags": ["mcp"],
            "publisher": {"id": f"registry:{name}", "name": name, "verified": False}, "license": "NOASSERTION",
            "trust": "external", "pricing": "free", "capabilities": [], "approval": [], "required_env": [],
            "permissions": {"egress": []}, "source": {"type": "remote-mcp", "url": remotes[0]["url"],
                                                      "registry": name}}, None


async def sync(db: Session, name: str, *, overwrite: bool = False, full: bool = False) -> dict:
    regs = registries(db)
    if name not in regs:
        raise RemoteError("레지스트리 없음 / not found")
    cfg = regs[name]
    started = utcnow().isoformat()
    params: dict = {"limit": 100}
    if cfg.get("last_sync") and not full:
        params["updated_since"] = cfg["last_sync"]
    report = {"added": [], "updated": [], "skipped": []}
    origin = f"registry:{name}"
    try:
        for _ in range(MAX_PAGES):
            page = await _fetch(db, name, cfg, params)
            for entry in page.get("servers") or []:
                x, why = _listing_of(name, entry)
                if x is None or not x.get("id"):
                    report["skipped"].append({"id": (entry.get("server") or {}).get("name"), "reason": why})
                    continue
                cur = catalog.get(x["id"], db)
                if cur is not None and cur.get("origin") != origin and not overwrite:
                    report["skipped"].append({"id": x["id"], "reason": f"id 충돌({cur.get('origin', 'static')}) — 덮어쓰기 확인 필요"})
                    continue
                if cur is not None and cur.get("origin") == origin and cur["version"] == x["version"] \
                        and cur["source"].get("sha256") != x["source"].get("sha256"):
                    report["skipped"].append({"id": x["id"], "reason": "같은 버전의 체크섬 변경 — 거부 / digest changed"})
                    continue
                row = db.get(MarketListing, x["id"]) or MarketListing(id=x["id"])
                report["updated" if row.origin else "added"].append(x["id"])
                row.origin, row.publisher_id, row.data, row.updated_at = origin, x["publisher"]["id"], x, utcnow()
                db.add(row)
            db.commit()
            cursor = (page.get("metadata") or {}).get("nextCursor")
            if not cursor:
                break
            params["cursor"] = cursor
        cfg.update(status="ok", error=None, last_sync=started,
                   count=len(list(db.execute(select(MarketListing.id).where(MarketListing.origin == origin)))))
    except RemoteError as exc:
        cfg.update(status="auth_failed" if str(exc) == "auth_failed" else "error", error=str(exc))
    regs[name] = cfg
    _save(db, regs)
    return {**report, "status": cfg["status"], "error": cfg.get("error")}


async def sync_due(db: Session) -> list[dict]:
    out = []
    now = utcnow()
    for name, cfg in registries(db).items():
        last = cfg.get("last_sync")
        every = int(cfg.get("interval_minutes") or 0)
        if every and (not last or (now - datetime.fromisoformat(last)).total_seconds() >= every * 60):
            out.append({"registry": name, **await sync(db, name)})
    return out


# ---- 오프라인 번들 ----

def export_bundle(db: Session, ids: list[str] | None = None) -> bytes:
    files: dict[str, bytes] = {}
    listings = []
    for x in catalog.load(db):
        if ids and x["id"] not in ids:
            continue
        src = x["source"]
        if src["type"] in ("zip", "release"):
            name = f"artifacts/{x['id']}-{x['version']}.zip"
            path = (catalog.catalog_path().parent if src["type"] == "zip" else data_path()) / src["path"]
            files[name] = path.read_bytes()
            x = {**x, "source": {"type": "bundle", "path": name, "sha256": hashlib.sha256(files[name]).hexdigest()}}
        elif src["type"] not in catalog.REMOTE_TYPES:
            continue  # 원격 zip·git 산출물은 번들에 넣지 않는다(폐쇄망에서 받을 수 없음)
        listings.append({k: v for k, v in x.items() if k != "origin"})
    files["catalog.json"] = json.dumps({"schema": "agentplaza/bundle/v1", "exported_at": utcnow().isoformat(),
                                        "listings": listings}, ensure_ascii=False, indent=2).encode()
    sums = "".join(f"{hashlib.sha256(b).hexdigest()}  {p}\n" for p, b in sorted(files.items())).encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for p, b in sorted({**files, "SHA256SUMS": sums}.items()):
            info = tarfile.TarInfo(p)
            info.size, info.mtime, info.mode = len(b), 0, 0o644
            tar.addfile(info, io.BytesIO(b))
    return buf.getvalue()


def import_bundle(db: Session, data: bytes, *, overwrite: bool = False) -> dict:
    if len(data) > BUNDLE_MAX:
        raise RemoteError("번들 크기 초과")
    files: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for m in tar.getmembers():
                if not m.isfile() or m.name.startswith("/") or ".." in m.name.split("/"):
                    raise RemoteError(f"허용되지 않는 항목: {m.name}")
                files[m.name] = tar.extractfile(m).read()
    except (tarfile.TarError, OSError) as exc:
        raise RemoteError(f"번들 해석 실패: {exc}") from None
    sums = files.pop("SHA256SUMS", None)
    if sums is None:
        raise RemoteError("SHA256SUMS 없음 — 체크섬 검증 필수")
    listed = {}
    for line in sums.decode().splitlines():
        digest, _, path = line.partition("  ")
        listed[path.strip()] = digest.strip()
    actual = {p: hashlib.sha256(b).hexdigest() for p, b in files.items()}
    if listed != actual:
        bad = sorted(p for p in set(listed) | set(actual) if listed.get(p) != actual.get(p))
        raise RemoteError(f"체크섬 불일치 — 변조 또는 손상: {bad[:5]}")
    try:
        listings = json.loads(files["catalog.json"])["listings"]
    except (KeyError, ValueError):
        raise RemoteError("catalog.json 없음 또는 형식 오류") from None
    report = {"added": [], "updated": [], "skipped": []}
    for x in listings:
        src = x.get("source") or {}
        cur = catalog.get(x["id"], db)
        if cur is not None and cur.get("origin") != "bundle" and not overwrite:
            report["skipped"].append({"id": x["id"], "reason": f"id 충돌({cur.get('origin', 'static')})"})
            continue
        if src.get("type") == "bundle":
            body = files.get(src["path"])
            if body is None or hashlib.sha256(body).hexdigest() != src.get("sha256"):
                report["skipped"].append({"id": x["id"], "reason": "산출물 체크섬 불일치"})
                continue
            rel = f"market/bundle/{x['id']}-{x['version']}.zip"
            data_path(rel).parent.mkdir(parents=True, exist_ok=True)
            data_path(rel).write_bytes(body)
            x = {**x, "source": {"type": "release", "path": rel, "sha256": src["sha256"]}}
        row = db.get(MarketListing, x["id"]) or MarketListing(id=x["id"])
        report["updated" if row.origin else "added"].append(x["id"])
        row.origin, row.publisher_id, row.data, row.updated_at = "bundle", (x.get("publisher") or {}).get("id"), x, utcnow()
        db.add(row)
    db.commit()
    return report
