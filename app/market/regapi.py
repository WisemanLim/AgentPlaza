"""레지스트리 API (D6-07): 공식 MCP registry(/v0.1/servers, server.json 2025-12-11)와 같은 모양으로 이 마켓을 노출한다.

- servers[].server = server.json(name·description·version, 원격 리스팅은 remotes) · _meta 의 official 블록(status·시각·isLatest)
- _meta["io.agentplaza/listing"] = 리스팅 정보 + 산출물(url·sha256). 다른 AgentPlaza 가 이것으로 동기화·설치한다.
- 산출물 다운로드: 유료면 X-Plaza-License(이 마켓이 발급한, 그 버전을 덮는 토큰)가 있어야 한다(NFR-C4).
- 원격 레지스트리에서 받아 온 리스팅(origin=registry:*)은 다시 노출하지 않는다(순환 방지).
"""
import base64
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import utcnow
from app.market import catalog, licensing, payments, publishing
from app.models import MarketListing
from app.services import sysconfig

SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
OFFICIAL = "io.modelcontextprotocol.registry/official"
OURS = "io.agentplaza/listing"
EXPOSE_KEY = "market.registry"
KEEP = ("id", "type", "name", "description", "categories", "industry", "work", "domain", "tags", "publisher",
        "license", "trust", "pricing", "capabilities", "approval", "required_env", "permissions", "hasFrontend",
        "compat", "signature")


def exposed(db: Session) -> bool:
    return bool(sysconfig.blob(db, EXPOSE_KEY).get("public"))


def set_exposed(db: Session, public: bool) -> dict:
    return sysconfig.put_blob(db, EXPOSE_KEY, {"public": bool(public)})


def server_name(listing_id: str) -> str:
    return f"io.agentplaza/{listing_id}"


def _text(v) -> str:
    return (v.get("en") or v.get("ko") or "") if isinstance(v, dict) else str(v or "")


def _times(db: Session, x: dict) -> tuple[str, str]:
    row = db.get(MarketListing, x["id"])
    if row is not None:
        return _iso(row.created_at), _iso(row.updated_at)
    p = catalog.catalog_path()
    t = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat() if p.is_file() else utcnow().isoformat()
    return t, t


def _iso(t: datetime) -> str:
    return (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).isoformat()


def entry(db: Session, x: dict, base: str, *, latest: bool = True) -> dict:
    """base = 클라이언트가 이 레지스트리에 접속한 기준 URL(산출물 주소를 같은 호스트로 돌려준다)."""
    src = x["source"]
    server = {"$schema": SCHEMA, "name": server_name(x["id"]), "title": _text(x.get("name"))[:100],
              "description": (_text(x.get("description")) or x["id"])[:100], "version": x["version"]}
    ours = {k: x[k] for k in KEEP if k in x}
    if src["type"] in catalog.REMOTE_TYPES:
        if src["type"] == "remote-mcp":
            server["remotes"] = [{"type": "streamable-http", "url": src["url"]}]
        ours.update(source_type=src["type"], source={k: v for k, v in src.items() if k != "registry"})
    else:
        ours["artifact"] = {"url": f"{base.rstrip('/')}/registry/v0.1/artifacts/{x['id']}/{x['version']}.zip",
                            "sha256": src.get("sha256")}
    published, updated = _times(db, x)
    return {"server": server, "_meta": {OFFICIAL: {"status": "active", "publishedAt": published, "updatedAt": updated,
                                                   "isLatest": latest}, OURS: ours}}


def local_listings(db: Session) -> list[dict]:
    ops = sysconfig.blob(db, catalog.OPS_KEY)
    return [x for x in catalog.load(db) if not str(x.get("origin", "")).startswith("registry:")
            and x["source"]["type"] != "remote-a2a" and not ops.get(x["id"], {}).get("hidden")]


def servers(db: Session, base: str, *, cursor: str | None, limit: int, search: str | None,
            updated_since: str | None) -> dict:
    items = [entry(db, x, base) for x in local_listings(db)]
    if search:
        s = search.lower()
        items = [e for e in items if s in (e["server"]["name"] + e["server"]["title"] + e["server"]["description"]).lower()]
    if updated_since:
        since = datetime.fromisoformat(updated_since.replace("Z", "+00:00"))
        items = [e for e in items if datetime.fromisoformat(e["_meta"][OFFICIAL]["updatedAt"]) > since]
    start = int(base64.urlsafe_b64decode(cursor.encode()).decode()) if cursor else 0
    page = items[start:start + limit]
    nxt = start + limit
    return {"servers": page, "metadata": {"count": len(page),
                                          **({"nextCursor": base64.urlsafe_b64encode(str(nxt).encode()).decode()}
                                             if nxt < len(items) else {})}}


def versions(db: Session, name: str, base: str) -> list[dict]:
    lid = name.removeprefix("io.agentplaza/")
    x = next((y for y in local_listings(db) if y["id"] == lid), None)
    if x is None:
        return []
    older = [{**r.listing, "source": {"type": "release", "path": r.artifact, "sha256": r.sha256}}
             for r in publishing.published_versions(db, lid) if r.version != x["version"]]
    return [entry(db, y, base, latest=False) for y in older] + [entry(db, x, base)]


def artifact_of(db: Session, listing_id: str, version: str) -> tuple[dict, dict] | None:
    """(리스팅, 그 버전의 source) — 현재 버전이거나 게시된 이전 릴리스."""
    x = next((y for y in local_listings(db) if y["id"] == listing_id), None)
    if x is None or x["source"]["type"] in catalog.REMOTE_TYPES:
        return None
    if x["version"] == version:
        return x, x["source"]
    rel = next((r for r in publishing.published_versions(db, listing_id) if r.version == version), None)
    return (x, {"type": "release", "path": rel.artifact, "sha256": rel.sha256}) if rel else None


def license_ok(db: Session, x: dict, version: str, token: str | None) -> str | None:
    """유료 산출물 다운로드 판정(None = 허용). 호스트 바인딩은 구매자 쪽에서 검사하므로 여기서는 보지 않는다."""
    if not payments.is_paid(x):
        return None
    if not token:
        return "라이선스 토큰 필요(X-Plaza-License) / license required"
    try:
        _, checks = licensing.verify(db, token, listing=x["id"], version=version)
    except licensing.LicenseError as exc:
        return str(exc)
    bad = [c["check"] for c in checks if not c["ok"] and c["check"] != "host"]
    return f"라이선스 검증 실패: {bad}" if bad else None
