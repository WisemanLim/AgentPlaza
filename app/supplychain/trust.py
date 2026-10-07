"""신뢰 키·공급망 정책·등록 3·4단계 판정 (D5-03, D5-04, NFR-S2, NFR-C2).

3단계: checksums 무결성 → cosign 서명(신뢰 키) → SBOM(syft) 생성·비교 → 취약점(trivy)
4단계: 라이선스 등급(G1~G5) → 선언 권한(egress) vs 조직 정책
OPA/Rego 대신 정책을 데이터(settings 'policy.supply_chain')로 두고 내장 평가기로 판정한다(가정, 계획표 참조).
"""
import fnmatch
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import TrustedKey
from app.services import sysconfig
from app.supplychain import licenses, tools

POLICY_KEY = "policy.supply_chain"
DEFAULT_POLICY = {
    "require_signature": False,     # True 면 미검증 패키지 설치 거부
    "block_severity": "CRITICAL",   # 이 등급 이상 취약점이 있으면 거부(NFR-S2). 비우면 차단 안 함
    "block_unscanned": False,       # True 면 취약점 DB 없이 설치 거부
    "license_block_grades": ["G5"],
    "license_allow": [],            # G5 라도 허용할 SPDX/LicenseRef(예: 상용 라이선스 + 엔타이틀먼트, Epic 18)
    "egress_allow": ["*"],          # 선언 egress 호스트 허용 패턴(fnmatch)
}
SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
META_FILES = ("checksums.txt", "signature.sig")


class TrustError(ValueError):
    pass


@dataclass
class Verdict:
    status: str = "ok"  # ok | warn | failed
    detail: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        if self.status == "ok":
            self.status = "warn"

    def fail(self, msg: str) -> "Verdict":
        self.status, self.error = "failed", msg
        return self

    def merge(self, other: "Verdict") -> "Verdict":
        self.detail.update(other.detail)
        for w in other.warnings:
            self.warn(w)
        if other.status == "failed":
            self.fail(other.error)
        return self


# ---- 신뢰 키 ----

def kid_of(public_pem: str) -> str:
    key = serialization.load_pem_public_key(public_pem.encode())
    if not isinstance(key, Ed25519PublicKey):
        raise TrustError("Ed25519 공개키(PEM)만 지원 / only Ed25519 SPKI PEM")
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return "pub-" + hashlib.sha256(raw).hexdigest()[:16]


def add_key(db: Session, *, name: str, public_pem: str, created_by: str, publisher_id: str | None = None) -> TrustedKey:
    try:
        kid = kid_of(public_pem)
    except (ValueError, TypeError) as exc:
        raise TrustError(f"공개키 해석 실패 / invalid key: {exc}") from None
    if db.get(TrustedKey, kid) is not None:
        raise TrustError(f"이미 등록된 키 / duplicate: {kid}")
    k = TrustedKey(kid=kid, name=name, public_pem=public_pem.strip() + "\n", created_by=created_by, publisher_id=publisher_id)
    db.add(k)
    db.commit()
    return k


def revoke_key(db: Session, kid: str) -> TrustedKey:
    k = db.get(TrustedKey, kid)
    if k is None:
        raise TrustError("키 없음 / not found")
    k.revoked_at = k.revoked_at or utcnow()
    db.commit()
    return k


def key_out(k: TrustedKey) -> dict:
    return {"kid": k.kid, "name": k.name, "publisher_id": k.publisher_id, "public_pem": k.public_pem,
            "created_by": k.created_by, "created_at": k.created_at, "revoked_at": k.revoked_at}


def is_trusted(db: Session, kid: str | None) -> bool:
    k = db.get(TrustedKey, kid) if kid else None
    return k is not None and k.revoked_at is None


# ---- 정책 ----

def policy(db: Session) -> dict:
    return {**DEFAULT_POLICY, **sysconfig.blob(db, POLICY_KEY)}


def set_policy(db: Session, changes: dict) -> dict:
    bad = [k for k in changes if k not in DEFAULT_POLICY]
    if bad:
        raise TrustError(f"알 수 없는 정책 키 / unknown: {bad}")
    p = {**policy(db), **changes}
    if p["block_severity"] not in ("", *SEVERITY_ORDER):
        raise TrustError("block_severity 는 '', LOW, MEDIUM, HIGH, CRITICAL")
    if not set(p["license_block_grades"]) <= set(licenses.GRADES):
        raise TrustError("license_block_grades 는 G1~G5")
    for k in ("require_signature", "block_unscanned"):
        if not isinstance(p[k], bool):
            raise TrustError(f"{k} 는 bool")
    for k in ("license_allow", "egress_allow"):
        if not isinstance(p[k], list) or not all(isinstance(x, str) for x in p[k]):
            raise TrustError(f"{k} 는 문자열 목록")
    sysconfig.put_blob(db, POLICY_KEY, p)
    return p


# ---- 3단계: 무결성·서명·SBOM·취약점 ----

def _checksum_map(text: bytes) -> dict[str, str]:
    out = {}
    for line in text.decode("utf-8", "replace").splitlines():
        if line.strip():
            digest, _, path = line.strip().partition("  ")
            out[path.strip()] = digest.strip()
    return out


def verify_signature(db: Session, files: dict[str, bytes], meta: dict[str, bytes], manifest: dict) -> Verdict:
    v = Verdict()
    checks, sig = meta.get("checksums.txt"), meta.get("signature.sig")
    if checks is None:
        if sig is not None:
            return v.fail("signature.sig 는 checksums.txt 와 함께 있어야 함")
        v.detail.update(checksums="absent", signature="unverified")
        v.warn("서명 미검증(서명 없음) / unsigned package")
        return v
    listed = _checksum_map(checks)
    actual = {p: hashlib.sha256(b).hexdigest() for p, b in files.items()}
    if listed != actual:
        bad = sorted({p for p in set(listed) | set(actual) if listed.get(p) != actual.get(p)})
        return v.fail(f"checksums 불일치 — 변조 또는 손상 / integrity failure: {bad[:5]}")
    v.detail["checksums"] = "ok"
    if sig is None:
        v.detail["signature"] = "unverified"
        v.warn("서명 미검증(signature.sig 없음) / unsigned package")
        return v
    want = (manifest["metadata"].get("publisher") or {}).get("keyId")
    rows = list(db.execute(select(TrustedKey)).scalars())
    candidates = [k for k in rows if k.kid == want] if want else rows
    for k in candidates:
        if tools.cosign_verify(checks, sig, k.public_pem):
            if k.revoked_at is not None:
                return v.fail(f"철회된 키로 서명됨 / signed with revoked key: {k.kid}")
            v.detail.update(signature="verified", signer=k.kid, publisher=k.publisher_id)
            return v
    if want and candidates:
        return v.fail(f"서명 불일치 — 변조 의심 / signature does not verify with {want}")
    v.detail["signature"] = "unverified"
    v.warn(f"서명 미검증(신뢰 키 아님: {want or '키 미지정'}) / unknown signing key")
    return v


def _components(sbom: dict) -> set[tuple]:
    return {(c.get("name"), c.get("version")) for c in sbom.get("components") or []}


def scan(staging: Path, files: dict[str, bytes]) -> tuple[Verdict, dict]:
    """SBOM 생성·비교 + 취약점 스캔. staging 에는 패키지 파일만(메타 파일·선언 SBOM 제외) 쓴다.
    돌려주는 dict = 취약점 요약 + 'sbom'(생성한 CycloneDX). SBOM 파일 저장은 6단계(등록)에서 한다."""
    v = Verdict()
    shutil.rmtree(staging, ignore_errors=True)
    for rel, body in files.items():
        if rel == "sbom.json":
            continue
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(body)
    try:
        sbom = tools.syft_sbom(staging)
        vulns = tools.trivy_scan(staging)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    v.detail["sbom"] = {"components": len(sbom.get("components") or [])}
    if "sbom.json" in files:
        try:
            declared = json.loads(files["sbom.json"])
        except ValueError:
            declared = {}
        diff = _components(declared) ^ _components(sbom)
        v.detail["sbom"]["declared_match"] = not diff
        if diff:
            v.warn(f"SBOM 불일치(선언 vs 생성) {len(diff)}건 / SBOM drift")
    v.detail["vulns"] = {k: vulns[k] for k in ("status", "critical", "high", "medium", "low")}
    v.detail["findings"] = vulns["findings"][:5]
    if vulns["status"] == "unscanned":
        v.warn(f"취약점 스캔 생략 — {vulns.get('reason')}")
    return v, {**vulns, "sbom": sbom}


def gate_vulns(v: Verdict, vulns: dict, pol: dict) -> None:
    if vulns["status"] == "unscanned" and pol["block_unscanned"]:
        v.fail("정책: 취약점 스캔 없이 설치 불가 / policy requires vulnerability scan")
        return
    if vulns["status"] != "scanned":
        return
    sev = pol["block_severity"]
    blocking = SEVERITY_ORDER[SEVERITY_ORDER.index(sev):] if sev else []
    hits = sum(vulns[s.lower()] for s in blocking)
    if hits:
        top = [f"{f['pkg']}@{f['version']} {f['id']}" for f in vulns["findings"] if f["severity"] in blocking][:3]
        v.fail(f"{sev} 이상 취약점 {hits}건 — 설치 거부(NFR-S2): {', '.join(top)}")
        return
    for s in ("CRITICAL", "HIGH"):
        if vulns[s.lower()]:
            v.warn(f"{s} 취약점 {vulns[s.lower()]}건")


# ---- 4단계: 라이선스·정책 ----

def license_policy(manifest: dict, sbom: dict, pol: dict) -> Verdict:
    v = Verdict()
    lic = manifest["metadata"].get("license") or "NOASSERTION"
    own = licenses.grade(lic)
    deps = licenses.sbom_licenses(sbom)
    dep_grade = licenses.worst(d["grade"] for d in deps)
    effective = licenses.worst([own, dep_grade if dep_grade in ("G3", "G4") else None])
    v.detail.update(license=lic, grade=own, effective=effective,
                    dependencies={"total": len(deps), "unknown": sum(1 for d in deps if d["grade"] is None),
                                  "worst": dep_grade})
    if own in pol["license_block_grades"] and lic not in pol["license_allow"]:
        return v.fail(f"라이선스 {lic} = {own} — 정책상 설치 불가(PRD 9.7) / license blocked")
    if effective == "G4":
        v.warn("G4 라이선스 — 격리 컨테이너 전용, 파생·내장·재판매 금지")
    elif effective == "G3":
        v.warn("G3 라이선스 — 별 컨테이너 전용(링크 금지)")
    egress = (manifest["spec"].get("permissions") or {}).get("network", {}).get("egress") or []
    denied = [h for h in egress if not any(fnmatch.fnmatch(h, pat) for pat in pol["egress_allow"])]
    v.detail["egress"] = {"declared": egress, "denied": denied}
    if denied:
        return v.fail(f"정책 위반 egress: {denied} — 허용 {pol['egress_allow']}")
    return v
