"""플랫폼 서명 키 (D7-03 Agent Card JWS). Ed25519 — 최초 사용 시 생성해 data 볼륨에 0600 으로 보관한다.

공개키는 /.well-known/jwks.json 으로 게시한다(인증 없이 공개 가능한 유일한 키 정보).
"""
import base64
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.core.config import settings


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _key_path() -> Path:
    return Path(settings.data_dir) / "keys" / "platform-ed25519.pem"


@lru_cache
def _load(path: str) -> Ed25519PrivateKey:
    """여러 워커가 동시에 처음 기동해도 키는 하나: 임시 파일에 완성한 뒤 os.link 로 원자적으로 게시한다
    (이미 있으면 링크가 실패하고 기존 키를 쓴다 — 반쯤 쓰인 파일을 읽지 않는다)."""
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        pem = Ed25519PrivateKey.generate().private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                          serialization.NoEncryption())
        tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(pem)
        try:
            os.link(tmp, p)
        except FileExistsError:
            pass  # 다른 워커가 먼저 게시함
        finally:
            tmp.unlink(missing_ok=True)
    return serialization.load_pem_private_key(p.read_bytes(), password=None)


def private_key() -> Ed25519PrivateKey:
    return _load(str(_key_path()))


def public_raw(key: Ed25519PublicKey | None = None) -> bytes:
    pub = key or private_key().public_key()
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def kid() -> str:
    return "plaza-" + hashlib.sha256(public_raw()).hexdigest()[:16]


def jwks() -> dict:
    return {"keys": [{"kty": "OKP", "crv": "Ed25519", "alg": "EdDSA", "use": "sig", "kid": kid(),
                      "x": b64url(public_raw())}]}


def canonical(obj: dict) -> bytes:
    """RFC 8785(JCS) 근사: 키 정렬·공백 없음·UTF-8. 카드에는 부동소수가 없어 숫자 직렬화 차이는 없다."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
