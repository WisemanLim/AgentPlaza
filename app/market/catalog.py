"""마켓 카탈로그 (D6-01) — 정적 git+JSON 카탈로그(큐레이션) + DB 리스팅(승인된 게시·원격 레지스트리·오프라인 번들, D6-06·07).

catalog.json 리스팅의 source 는 다형 필드(PRD 10.5):
  {"type": "zip", "path": "artifacts/x.zip", "sha256": …} · {"type": "zip-url", "url": …, "sha256": …}
  {"type": "git-subdir", "url": …, "path": …, "ref": …} · {"type": "remote-a2a", "card_url": …} · {"type": "remote-mcp", "url": …}
  {"type": "release", "path": <data 디렉터리 기준>, "sha256": …}(이 인스턴스에 게시된 릴리스)
같은 id 면 DB 리스팅이 정적 리스팅을 대신한다(게시 단계에서 같은 퍼블리셔만 허용).
"""
import asyncio
import hashlib
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.models import Agent, MarketDownload, MarketListing, TrustedKey
from app.registry import fetch
from app.services import sysconfig

REMOTE_TYPES = ("remote-a2a", "remote-mcp")
OPS_KEY = "market.listing_ops"  # 운영 배지·숨김(UI E07): {id: {hidden, featured_until, validated_ref}}


class MarketError(Exception):
    pass


def catalog_path() -> Path:
    return Path(settings.market_catalog)


def load(db: Session | None = None) -> list[dict]:
    p = catalog_path()
    static = json.loads(p.read_text(encoding="utf-8")).get("listings", []) if p.is_file() else []
    if db is None:
        return static
    rows = {r.id: {**r.data, "origin": r.origin} for r in db.execute(select(MarketListing)).scalars()}
    return [rows.pop(x["id"], x) for x in static] + list(rows.values())


def get(listing_id: str, db: Session | None = None) -> dict | None:
    return next((x for x in load(db) if x["id"] == listing_id), None)


def _text(v) -> str:
    return " ".join(v.values()) if isinstance(v, dict) else str(v or "")


def search(db: Session, *, q: str | None = None, category: str | None = None, industry: str | None = None,
           work: str | None = None, domain: str | None = None, type_: str | None = None,
           trust: str | None = None) -> list[dict]:
    installed = {a.id: a for a in db.execute(select(Agent)).scalars()}
    trusted = trusted_kids(db)
    ops = sysconfig.blob(db, OPS_KEY)
    out = []
    for x in load(db):
        if ops.get(x["id"], {}).get("hidden"):
            continue
        hay = " ".join([x["id"], _text(x.get("name")), _text(x.get("description")), " ".join(x.get("tags", [])),
                        " ".join(x.get("capabilities", []))]).lower()
        if q and q.lower() not in hay:
            continue
        if category and category not in x.get("categories", []):
            continue
        if industry and x.get("industry") != industry:
            continue
        if work and work != x.get("work"):
            continue
        if domain and domain != x.get("domain"):
            continue
        if type_ and type_ != x.get("type"):
            continue
        if trust and trust != x.get("trust"):
            continue
        out.append(decorate(x, installed.get(x["id"]), trusted, db))
    return sorted(out, key=lambda x: not x.get("featured"))


def trusted_kids(db: Session) -> set[str]:
    return set(db.execute(select(TrustedKey.kid).where(TrustedKey.revoked_at.is_(None))).scalars())


def decorate(x: dict, agent: Agent | None, trusted: set[str] = frozenset(), db: Session | None = None) -> dict:
    """설치 상태·업데이트 여부·신뢰 배지를 붙인다(D6-01, UI E01 카드). db 를 주면 가격·라이선스·통계·운영 배지도."""
    from app.market import licensing, payments
    from app.registry.pipeline import semver
    inst = None
    if agent is not None:
        inst = {"version": agent.version, "status": agent.status,
                "update_available": x["source"]["type"] not in REMOTE_TYPES and semver(x["version"]) > semver(agent.version)}
    badges = [x.get("trust", "community")]
    # 서명 키가 신뢰 키면 '서명 검증'(실제 검증은 설치 3단계), 아니면 '미검증'(NFR-S2)
    signed = (x.get("signature") or {}).get("keyId") in trusted
    badges.append("signature:verified" if signed else "signature:unverified")
    if x.get("publisher", {}).get("verified"):
        badges.append("publisher:verified")
    out = {**x, "installed": inst, "badges": badges, "pricing": payments.pricing_of(x), "paid": payments.is_paid(x)}
    if db is not None:
        op = sysconfig.blob(db, OPS_KEY).get(x["id"], {})
        featured = bool(op.get("featured_until")) and op["featured_until"] >= utcnow().date().isoformat()
        badges += ["featured"] * featured + (["validated"] if op.get("validated_ref") else [])
        out.update(featured=featured, validated_ref=op.get("validated_ref"), hidden=bool(op.get("hidden")),
                   stats=stats(db, x["id"]),
                   licensed=bool(licensing.entitled(db, x["id"], x["version"])) if out["paid"] else None)
    return out


def stats(db: Session, listing_id: str) -> dict:
    rows = db.execute(select(MarketDownload.kind, func.count()).where(MarketDownload.listing_id == listing_id)
                      .group_by(MarketDownload.kind)).all()
    return {k: n for k, n in rows}


def count(db: Session, listing_id: str, version: str, kind: str, actor: str) -> None:
    db.add(MarketDownload(listing_id=listing_id, version=version, kind=kind, actor=actor))
    db.commit()


async def artifact(x: dict, headers: dict | None = None) -> bytes:
    """headers = 원격 레지스트리 인증·라이선스 토큰(유료 산출물, D6-05)."""
    src = x["source"]
    if src["type"] in ("zip", "release"):
        base = catalog_path().parent if src["type"] == "zip" else Path(settings.data_dir)
        p = (base / src["path"]).resolve()
        if not p.is_relative_to(base.resolve()):
            raise MarketError("artifact path escapes catalog")
        if not p.is_file():
            raise MarketError(f"산출물 없음 / artifact missing: {src['path']}")
        data = p.read_bytes()
    elif src["type"] == "zip-url":
        data = await fetch.zip_url(src["url"], headers=headers)
    elif src["type"] == "git-subdir":
        data = await asyncio.to_thread(fetch.git_subdir, src["url"], src.get("path", ""), src.get("ref"))
    else:
        raise MarketError(f"원격 연동 리스팅은 artifact 가 없음: {src['type']}")
    want = src.get("sha256")
    if want and hashlib.sha256(data).hexdigest() != want:
        raise MarketError("sha256 불일치 — 변조 또는 손상 / artifact digest mismatch")
    return data
