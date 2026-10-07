"""퍼블리셔·게시·심사·릴리스 (D6-06).

게시 = zip(퍼블리셔 서명 키로 서명) + 카탈로그 정보 → 자동 검사(D5 게이트: 구조·서명·SBOM·취약점·라이선스·egress)
→ supervisor 는 즉시 릴리스, admin 은 심사 대기 → supervisor 승인(또는 사유와 함께 거부) → DB 리스팅(origin=release).
퍼블리셔 키 = trusted_keys.publisher_id. 키를 철회하면 그 키로 서명한 자산은 '미검증'으로 강등된다(배지는 신뢰 키 집합으로 계산).
"""
import asyncio
import hashlib
import re
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.market import catalog, payments
from app.models import MarketDownload, MarketListing, MarketRelease, Publisher, TrustedKey
from app.registry import gate
from app.registry.pipeline import data_path, semver
from app.services import audit
from app.supplychain import tools as sc_tools
from app.supplychain import trust as sc_trust

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
TAG = re.compile(r"^[a-z0-9-]{1,30}$")
MODELS = ("free", "subscription", "per_seat", "per_call")


class PublishError(ValueError):
    def __init__(self, msg: str, code: int = 422, gate: dict | None = None):
        super().__init__(msg)
        self.code, self.gate = code, gate


# ---- 퍼블리셔 ----

def ensure_publisher(db: Session, pid: str, actor: str, supervisor: bool) -> Publisher:
    """게시 권한: supervisor 는 모든 퍼블리셔, admin 은 구성원인 퍼블리셔만. 없으면 게시자 자신을 구성원으로 만든다."""
    p = db.get(Publisher, pid)
    if p is None:
        if not SLUG.match(pid):
            raise PublishError("퍼블리셔 id 는 소문자·숫자·하이픈 2~64자")
        p = Publisher(id=pid, name=pid, members=[actor], created_by=actor)
        db.add(p)
        db.commit()
        audit.record(db, actor=actor, actor_type="user", action="market.publisher.created", resource=pid)
    elif not supervisor and actor not in (p.members or []):
        raise PublishError(f"퍼블리셔 {pid} 의 구성원이 아님 / not a member", 403)
    return p


def publisher_out(db: Session, p: Publisher) -> dict:
    ids = {x["id"] for x in catalog.load(db) if (x.get("publisher") or {}).get("id") == p.id}
    keys = list(db.execute(select(TrustedKey).where(TrustedKey.publisher_id == p.id)).scalars())
    counts = {"download": 0, "install": 0, "update": 0}
    for kind in db.execute(select(MarketDownload.kind).where(MarketDownload.listing_id.in_(ids))).scalars():
        counts[kind] = counts.get(kind, 0) + 1
    pending = db.execute(select(MarketRelease.id).where(MarketRelease.publisher_id == p.id,
                                                        MarketRelease.status == "pending")).all()
    return {"id": p.id, "name": p.name, "url": p.url, "verified": p.verified, "members": p.members or [],
            "assets": sorted(ids), "downloads": counts["download"], "installs": counts["install"] + counts["update"],
            "pending": len(pending), "keys": [sc_trust.key_out(k) for k in keys],
            "active_keys": sum(1 for k in keys if k.revoked_at is None), "created_at": p.created_at}


def add_publisher_key(db: Session, p: Publisher, *, name: str, public_pem: str, rotate: bool, actor: str) -> dict:
    """서명 키 등록. rotate=True 면 새 키를 등록한 뒤 이 퍼블리셔의 기존 키를 철회한다(회전)."""
    old = [k for k in db.execute(select(TrustedKey).where(TrustedKey.publisher_id == p.id)).scalars()
           if k.revoked_at is None]
    k = sc_trust.add_key(db, name=name, public_pem=public_pem, created_by=actor, publisher_id=p.id)
    revoked = []
    if rotate:
        for o in old:
            sc_trust.revoke_key(db, o.kid)
            revoked.append(o.kid)
    audit.record(db, actor=actor, actor_type="user", action="market.publisher.key", resource=p.id,
                 detail={"kid": k.kid, "rotated_out": revoked})
    return {"kid": k.kid, "revoked": revoked}


# ---- 카탈로그 정보 ----

def check_info(info: dict) -> dict:
    tags = info.get("tags") or []
    if len(tags) > 10 or not all(isinstance(t, str) and TAG.match(t) for t in tags):
        raise PublishError("태그는 10개 이하, ^[a-z0-9-]{1,30}$")
    pr = payments.pricing_of(info)
    if pr.get("model", "free") not in MODELS:
        raise PublishError(f"가격 모델은 {MODELS}")
    if pr.get("model", "free") != "free":
        if not isinstance(pr.get("price"), int) or pr["price"] < 0 or not re.fullmatch(r"[A-Z]{3}", pr.get("currency", "")):
            raise PublishError("유료 가격 = {model, price(정수 ≥0), currency(ISO 4217)}")
    for k in ("name", "description"):
        if k in info and not isinstance(info[k], (str, dict)):
            raise PublishError(f"{k} 는 문자열 또는 {{ko, en}}")
    return info


def listing_of(m: dict, info: dict, pub: Publisher, signer: str | None) -> dict:
    """agent.yaml + 게시자가 넣은 카탈로그 정보 → catalog.json 리스팅 모양(정적 카탈로그와 같음)."""
    meta, spec = m["metadata"], m["spec"]
    env = spec.get("env", {})
    return {
        "id": meta["id"], "version": meta["version"], "type": spec["type"],
        "name": info.get("name") or meta.get("displayName") or meta["name"],
        "description": info.get("description") or meta.get("description") or "",
        "categories": info.get("categories") or meta.get("categories", []),
        "industry": spec.get("industry", "-"), "work": spec.get("work", "W19"), "domain": info.get("domain", "common"),
        "tags": info.get("tags") or meta.get("tags", []),
        "publisher": {"id": pub.id, "name": pub.name, "verified": pub.verified},
        "license": meta.get("license") or "NOASSERTION", "trust": "partner" if pub.verified else "community",
        "pricing": info.get("pricing") or "free",
        "capabilities": [c["verb"] for c in spec["capabilities"]],
        "approval": [c["verb"] for c in spec["capabilities"] if c.get("humanApprovalRequired")],
        "required_env": env.get("required", []),
        "permissions": {"egress": (spec.get("permissions") or {}).get("network", {}).get("egress", []),
                        "secretRefs": env.get("secretRefs", []), "docker": False,
                        "dataClassification": spec.get("governance", {}).get("dataClassification")},
        "hasFrontend": bool(spec.get("ui", {}).get("hasFrontend")), "compat": spec.get("compat", {}),
        **({"signature": {"keyId": signer, "format": "cosign-ed25519"}} if signer else {}),
    }


# ---- 자동 검사(D5 게이트) ----

async def review_gate(db: Session, data: bytes, publisher_id: str) -> tuple[dict | None, dict, list[str]]:
    """(manifest, 보고서, 오류). 오류가 하나라도 있으면 게시 불가. 업로드 코드는 실행하지 않는다(DP5)."""
    report: dict = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    g = gate.inspect(gate.extract(data))
    report["structure"] = {"ok": g.ok, "files": len(g.files), "warnings": g.warnings[:20]}
    if not g.ok:
        return None, report, g.errors[:20]
    m = g.manifest
    pol = sc_trust.policy(db)
    v3 = sc_trust.verify_signature(db, g.files, g.meta, m)
    scanned: dict = {"sbom": {}}
    if v3.status != "failed":
        try:
            v_scan, scanned = await asyncio.to_thread(sc_trust.scan, data_path("staging", f"rel-{uuid.uuid4().hex}"),
                                                      g.files)
            v3.merge(v_scan)
            sc_trust.gate_vulns(v3, scanned, pol)
        except sc_tools.ToolError as exc:
            v3.fail(f"공급망 도구 오류 / tool error: {exc}")
    report["supply_chain"] = {k: v3.detail.get(k) for k in ("checksums", "signature", "signer", "publisher", "sbom",
                                                             "vulns")}
    errors = [v3.error] if v3.status == "failed" else []
    if not errors and (v3.detail.get("signature") != "verified" or v3.detail.get("publisher") != publisher_id):
        errors.append(f"퍼블리셔 {publisher_id} 의 서명 키로 서명해야 게시 가능(D6-06) / must be signed by the publisher key")
    v4 = sc_trust.license_policy(m, scanned["sbom"], pol)
    report["license"] = {k: v4.detail.get(k) for k in ("license", "grade", "effective", "egress")}
    if v4.status == "failed":
        errors.append(v4.error)
    report["warnings"] = [*g.warnings, *v3.warnings, *v4.warnings][:30]
    report["evals"] = sorted(p for p in g.files if p.startswith("evals/"))
    return m, report, [e for e in errors if e]


# ---- 게시·심사 ----

def _owner(db: Session, listing_id: str) -> tuple[str | None, str | None]:
    """(퍼블리셔 id, origin) — 이미 이 id 를 쓰는 리스팅의 소유자."""
    x = catalog.get(listing_id, db)
    return ((x.get("publisher") or {}).get("id"), x.get("origin", "static")) if x else (None, None)


async def submit(db: Session, *, data: bytes, publisher_id: str, info: dict, actor: str, supervisor: bool,
                 overwrite: bool = False) -> MarketRelease:
    pub = ensure_publisher(db, publisher_id, actor, supervisor)
    check_info(info)
    if len(data) > settings.upload_max_mb * 1024 * 1024:
        raise PublishError(f"크기 초과 > {settings.upload_max_mb}MB")
    m, report, errors = await review_gate(db, data, pub.id)
    if m is None:
        raise PublishError("; ".join(errors), gate=report)
    lid, ver = m["metadata"]["id"], m["metadata"]["version"]
    owner, origin = _owner(db, lid)
    if owner is not None and (owner != pub.id or origin not in ("static", "release")):
        raise PublishError(f"id {lid} 는 다른 퍼블리셔·출처({owner}, {origin})가 사용 중", 409)
    cur = catalog.get(lid, db)
    if cur is not None and semver(ver) <= semver(cur["version"]):
        raise PublishError(f"버전은 게시된 {cur['version']} 보다 커야 함 / version must increase", 409)
    prev = db.execute(select(MarketRelease).where(MarketRelease.listing_id == lid,
                                                  MarketRelease.version == ver)).scalar_one_or_none()
    if prev is not None:
        if prev.status == "published" or not overwrite:
            raise PublishError(f"{lid}@{ver} 가 이미 있음({prev.status}) — 덮어쓰기는 미게시 건만", 409)
        _drop(db, prev)
    rel = MarketRelease(id=str(uuid.uuid4()), listing_id=lid, version=ver, publisher_id=pub.id, sha256=report["sha256"],
                        size=len(data), gate={**report, "errors": errors}, submitted_by=actor,
                        listing=listing_of(m, info, pub, report["supply_chain"].get("signer")))
    if errors:
        rel.status = "blocked"
        db.add(rel)
        db.commit()
        audit.record(db, actor=actor, actor_type="user", action="market.release.blocked", resource=f"{lid}@{ver}",
                     outcome="denied", detail={"errors": errors[:5]})
        raise PublishError("; ".join(errors), gate=rel.gate)
    path = data_path("market", "releases", f"{lid}-{ver}.zip")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    rel.artifact = str(path.relative_to(settings.data_dir))
    rel.status = "pending"
    db.add(rel)
    db.commit()
    audit.record(db, actor=actor, actor_type="user", action="market.release.submitted", resource=f"{lid}@{ver}",
                 detail={"publisher": pub.id})
    if supervisor:  # supervisor 게시 = 즉시 승인(UI E06 7)
        approve(db, rel, actor)
    return rel


def _drop(db: Session, rel: MarketRelease) -> None:
    if rel.artifact:
        (data_path(rel.artifact)).unlink(missing_ok=True)
    db.delete(rel)
    db.commit()


def approve(db: Session, rel: MarketRelease, actor: str) -> MarketRelease:
    if rel.status != "pending":
        raise PublishError(f"심사 대기 상태가 아님({rel.status})", 409)
    rel.status, rel.reviewed_by, rel.reviewed_at = "published", actor, utcnow()
    cur = catalog.get(rel.listing_id, db)
    if cur is None or semver(rel.version) > semver(cur["version"]):
        row = db.get(MarketListing, rel.listing_id) or MarketListing(id=rel.listing_id, origin="release")
        row.publisher_id, row.updated_at = rel.publisher_id, utcnow()
        row.data = {**rel.listing, "published_at": utcnow().isoformat(),
                    "source": {"type": "release", "path": rel.artifact, "sha256": rel.sha256}}
        db.add(row)
    db.commit()
    audit.record(db, actor=actor, actor_type="user", action="market.release.published",
                 resource=f"{rel.listing_id}@{rel.version}", detail={"publisher": rel.publisher_id,
                                                                     "notify": rel.submitted_by})
    return rel


def reject(db: Session, rel: MarketRelease, actor: str, reason: str) -> MarketRelease:
    if rel.status != "pending":
        raise PublishError(f"심사 대기 상태가 아님({rel.status})", 409)
    if len(reason.strip()) < 2:
        raise PublishError("거부 사유 필수 / reason required")
    rel.status, rel.reviewed_by, rel.reviewed_at, rel.reason = "rejected", actor, utcnow(), reason.strip()
    db.commit()
    audit.record(db, actor=actor, actor_type="user", action="market.release.rejected",
                 resource=f"{rel.listing_id}@{rel.version}", outcome="denied",
                 detail={"reason": rel.reason, "notify": rel.submitted_by})
    return rel


def release_out(rel: MarketRelease) -> dict:
    return {"id": rel.id, "listing_id": rel.listing_id, "version": rel.version, "publisher_id": rel.publisher_id,
            "status": rel.status, "sha256": rel.sha256, "size": rel.size, "gate": rel.gate, "listing": rel.listing,
            "submitted_by": rel.submitted_by, "reviewed_by": rel.reviewed_by, "reason": rel.reason,
            "created_at": rel.created_at, "reviewed_at": rel.reviewed_at}


def published_versions(db: Session, listing_id: str) -> list[MarketRelease]:
    return list(db.execute(select(MarketRelease).where(MarketRelease.listing_id == listing_id,
                                                       MarketRelease.status == "published")
                           .order_by(MarketRelease.created_at)).scalars())


def remove_listing(db: Session, listing_id: str) -> None:
    db.execute(delete(MarketListing).where(MarketListing.id == listing_id))
    db.commit()
