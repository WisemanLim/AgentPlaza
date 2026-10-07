"""비밀번호 해시·JWT·API 키 (D9-01·D9-03). 외부 의존 최소화: pbkdf2(stdlib) + PyJWT."""
import base64
import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt

from app.core.config import settings
from app.db import utcnow

JWT_ALG = "HS256"
API_KEY_PREFIX = "ap_sk_"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    n = settings.password_hash_iterations
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, n)
    return f"pbkdf2_sha256${n}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, salt, dk = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(n))
    return hmac.compare_digest(calc, base64.b64decode(dk))


def create_token(sub: str, role: str, typ: str = "user", scopes: dict | None = None,
                 ttl_minutes: int | None = None, audience: str | None = None) -> str:
    now = utcnow()
    claims = {"sub": sub, "role": role, "typ": typ, "iat": now,
              "exp": now + timedelta(minutes=ttl_minutes or settings.jwt_ttl_minutes)}
    if scopes is not None:
        claims["scopes"] = scopes
    if audience:
        claims["aud"] = audience
    return jwt.encode(claims, settings.jwt_secret, algorithm=JWT_ALG)


def decode_token(token: str, audience: str | None = None) -> dict:
    """서비스 토큰은 aud=agent:{id} 를 가질 수 있다. audience 미지정이면 aud 검사를 생략한다."""
    opts = {} if audience else {"verify_aud": False}
    return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALG], audience=audience, options=opts)


def new_api_key() -> tuple[str, str, str]:
    """(원문 키, 표시용 prefix, sha256 해시). 원문은 생성 응답에서 1회만 노출한다."""
    raw = API_KEY_PREFIX + secrets.token_urlsafe(32)
    return raw, raw[: len(API_KEY_PREFIX) + 6], hash_api_key(raw)


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def temp_password() -> str:
    return secrets.token_urlsafe(12)
