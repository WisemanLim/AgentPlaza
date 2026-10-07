"""라이선스·엔타이틀먼트 (D6-05, NFR-C4): Ed25519 서명 토큰을 오프라인으로 검증하고 대상·버전 범위·좌석·기간·호스트를 지킨다.

토큰 = "apl1." + base64url(본문 JSON) + "." + base64url(Ed25519 서명(본문 바이트))
본문 = {v, lid, iss(발급 키 kid), listing, publisher, versions(범위: * · ^1.0.0 · >=1.0.0 <2.0.0), seats, iat, exp(없으면 무기한),
        host(없으면 어디서나 = 이 인스턴스 id 바인딩), sub(구매자)}
발급 키 = 이 인스턴스가 마켓 서버로서 쓰는 키(비밀키는 시크릿 저장소 암호문). 검증 키 = 자기 발급 키 + 등록한 외부 발급자 공개키.
유료 에이전트 = 라이선스가 한 번이라도 등록된 리스팅. 유효한 라이선스가 없거나 좌석이 차면 계획·도구 호출에서 막는다.
"""
import base64
import json
import re
import uuid
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization as ser
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import Agent, License, LicenseSeat
from app.services import secrets as secret_store
from app.services import sysconfig
from app.supplychain import trust

PREFIX = "apl1"
ISSUERS_KEY = "market.license_issuers"
INSTANCE_KEY = "platform.instance"
SECRET_SCOPE, SECRET_NAME = "market", "LICENSE_SIGNING_KEY"
VER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


class LicenseError(ValueError):
    def __init__(self, msg: str, checks: list[dict] | None = None):
        super().__init__(msg)
        self.checks = checks or []


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def instance_id(db: Session) -> str:
    """호스트 바인딩 기준(설치 인스턴스 id). 처음 쓸 때 만든다."""
    cur = sysconfig.blob(db, INSTANCE_KEY)
    if not cur.get("id"):
        cur = sysconfig.put_blob(db, INSTANCE_KEY, {**cur, "id": "inst-" + uuid.uuid4().hex[:16]})
    return cur["id"]


# ---- 발급 키·발급자 ----

def _issuer_private(db: Session) -> Ed25519PrivateKey:
    pem = secret_store.get(db, SECRET_SCOPE, SECRET_NAME)
    if pem is None:
        k = Ed25519PrivateKey.generate()
        pem = k.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()).decode()
        secret_store.put(db, SECRET_SCOPE, SECRET_NAME, pem, "system")
    return ser.load_pem_private_key(pem.encode(), None)


def issuer_public_pem(db: Session) -> str:
    pub = _issuer_private(db).public_key()
    return pub.public_bytes(ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()


def issuer_kid(db: Session) -> str:
    return trust.kid_of(issuer_public_pem(db))


def issuers(db: Session) -> dict[str, dict]:
    own = issuer_public_pem(db)
    return {**sysconfig.blob(db, ISSUERS_KEY), trust.kid_of(own): {"name": "this instance", "public_pem": own, "own": True}}


def add_issuer(db: Session, name: str, public_pem: str) -> str:
    kid = trust.kid_of(public_pem)
    cur = sysconfig.blob(db, ISSUERS_KEY)
    cur[kid] = {"name": name, "public_pem": public_pem.strip() + "\n"}
    sysconfig.put_blob(db, ISSUERS_KEY, cur)
    return kid


def remove_issuer(db: Session, kid: str) -> bool:
    cur = sysconfig.blob(db, ISSUERS_KEY)
    if cur.pop(kid, None) is None:
        return False
    sysconfig.put_blob(db, ISSUERS_KEY, cur)
    return True


# ---- 버전 범위 ----

def _ver(v: str) -> tuple[int, int, int]:
    m = VER.match(v.strip())
    if not m:
        raise LicenseError(f"버전 형식 오류: {v}")
    return int(m[1]), int(m[2]), int(m[3])


def in_range(version: str, rng: str | None) -> bool:
    if not rng or rng.strip() == "*":
        return True
    v = _ver(version)
    for part in rng.split():
        if part.startswith("^"):
            b = _ver(part[1:])
            upper = (b[0] + 1, 0, 0) if b[0] > 0 else (0, b[1] + 1, 0)
            if not b <= v < upper:
                return False
            continue
        op = next((o for o in (">=", "<=", ">", "<", "=") if part.startswith(o)), "=")
        b = _ver(part.removeprefix(op))
        if not {">=": v >= b, "<=": v <= b, ">": v > b, "<": v < b, "=": v == b}[op]:
            return False
    return True


# ---- 발급·검증 ----

def issue(db: Session, *, listing: str, publisher: str, versions: str, seats: int, days: int | None = None,
          host: str | None = None, sub: str = "") -> str:
    now = int(utcnow().timestamp())
    body = {"v": 1, "lid": "lic-" + uuid.uuid4().hex[:20], "iss": issuer_kid(db), "listing": listing,
            "publisher": publisher, "versions": versions, "seats": seats, "iat": now,
            "exp": now + days * 86400 if days else None, "host": host, "sub": sub}
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode()
    return f"{PREFIX}.{_b64(raw)}.{_b64(_issuer_private(db).sign(raw))}"


def verify(db: Session, token: str, *, listing: str | None = None, version: str | None = None) -> tuple[dict, list[dict]]:
    """오프라인 검증 → (본문, 체크리스트). 서명·형식 오류는 LicenseError, 나머지는 체크리스트의 ok=False."""
    try:
        prefix, b, s = token.strip().split(".")
        raw, sig = _unb64(b), _unb64(s)
        body = json.loads(raw)
        if prefix != PREFIX or not isinstance(body, dict):
            raise ValueError
    except ValueError:
        raise LicenseError("형식 오류 — apl1.<본문>.<서명> / malformed token") from None
    iss = issuers(db).get(body.get("iss"))
    if iss is None:
        raise LicenseError(f"알 수 없는 발급자 / unknown issuer: {body.get('iss')}")
    try:
        ser.load_pem_public_key(iss["public_pem"].encode()).verify(sig, raw)
    except InvalidSignature:
        raise LicenseError("서명 불일치 — 변조 / signature invalid") from None
    now = utcnow().timestamp()
    try:
        ver_ok = version is None or in_range(version, body.get("versions"))
    except LicenseError:
        ver_ok = False
    checks = [
        {"check": "signature", "ok": True, "detail": f"{body['iss']} ({iss['name']})"},
        {"check": "target", "ok": listing is None or body.get("listing") == listing, "detail": body.get("listing")},
        {"check": "versions", "ok": ver_ok, "detail": body.get("versions") or "*"},
        {"check": "seats", "ok": int(body.get("seats") or 0) >= 1, "detail": body.get("seats")},
        {"check": "expiry", "ok": body.get("exp") is None or body["exp"] > now,
         "detail": _iso(body.get("exp")) or "perpetual"},
        {"check": "host", "ok": not body.get("host") or body["host"] == instance_id(db), "detail": body.get("host") or "*"},
    ]
    return body, checks


def _iso(ts) -> str | None:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None


def register(db: Session, token: str, listing: str, actor: str, *, commit: bool = True) -> License:
    body, checks = verify(db, token, listing=listing)
    bad = [c["check"] for c in checks if not c["ok"]]
    if bad:
        raise LicenseError(f"라이선스 검증 실패 / license check failed: {bad}", checks)
    lic = db.get(License, body["lid"]) or License(id=body["lid"], registered_by=actor)
    lic.listing_id, lic.token, lic.payload, lic.issuer = listing, token.strip(), body, body["iss"]
    lic.seats = int(body["seats"])
    lic.expires_at = datetime.fromtimestamp(body["exp"], timezone.utc) if body.get("exp") else None
    lic.status = "active"
    db.add(lic)
    if commit:
        db.commit()
    return lic


def out(db: Session, lic: License) -> dict:
    used = db.scalar(select(func.count()).select_from(LicenseSeat).where(LicenseSeat.license_id == lic.id))
    holders = list(db.execute(select(LicenseSeat.holder).where(LicenseSeat.license_id == lic.id)).scalars())
    return {"id": lic.id, "listing_id": lic.listing_id, "issuer": lic.issuer, "versions": lic.payload.get("versions"),
            "seats": lic.seats, "seats_used": used, "holders": holders, "expires_at": lic.expires_at,
            "host": lic.payload.get("host"), "status": lic.status, "valid": _valid(db, lic),
            "registered_by": lic.registered_by, "created_at": lic.created_at}


# ---- 엔타이틀먼트 ----

def _valid(db: Session, lic: License, version: str | None = None) -> bool:
    if lic.status != "active":
        return False
    if lic.expires_at is not None and _aware(lic.expires_at) <= utcnow():
        return False
    host = lic.payload.get("host")
    if host and host != instance_id(db):
        return False
    try:
        return version is None or in_range(version, lic.payload.get("versions"))
    except LicenseError:
        return False


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def licensed_listings(db: Session) -> set[str]:
    return set(db.execute(select(License.listing_id).distinct()).scalars())


def entitled(db: Session, listing_id: str, version: str) -> list[License]:
    rows = db.execute(select(License).where(License.listing_id == listing_id).order_by(License.created_at)).scalars()
    return [lic for lic in rows if _valid(db, lic, version)]


def check_use(db: Session, agent_id: str, holder: str, *, claim: bool, required: set[str] | None = None) -> str | None:
    """유료 에이전트 사용 판정(None = 허용). claim=True 면 남은 좌석을 이 사용자에게 배정한다."""
    if agent_id not in (required if required is not None else licensed_listings(db)):
        return None
    if holder.startswith("channel:"):  # 채널(D3-07) = 좌석 하나 — 위젯 방문자·메신저 사용자마다 좌석을 쓰지 않는다
        holder = ":".join(holder.split(":")[:2])
    a = db.get(Agent, agent_id)
    valid = entitled(db, agent_id, a.version if a else "0.0.0")
    if not valid:
        return "유효한 라이선스 없음(만료·철회·버전 범위 밖) / no valid license"
    ids = [lic.id for lic in valid]
    if db.execute(select(LicenseSeat.id).where(LicenseSeat.license_id.in_(ids), LicenseSeat.holder == holder)).first():
        return None
    for lic in valid:
        used = db.scalar(select(func.count()).select_from(LicenseSeat).where(LicenseSeat.license_id == lic.id))
        if used < lic.seats:
            if claim:
                db.add(LicenseSeat(license_id=lic.id, holder=holder))
                db.commit()
            return None
    return f"좌석 초과({sum(lic.seats for lic in valid)}석 사용 중) / no free seat"
