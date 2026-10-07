"""Agent Card(JWS 서명)·MCP server.json 생성 (D7-03, NFR-P3). 원천은 agent.yaml 하나(DP4).

서명은 a2a-sdk 내장 서명기(RFC 8785 정규화 + 분리형 JWS, EdDSA)로 하고, 키는 플랫폼 Ed25519(keys.py).
"""
from functools import lru_cache

from a2a.types import AgentCard
from a2a.utils.signing import create_agent_card_signer, create_signature_verifier
from agentplaza_sdk.protocols import build_card, card_json
from cryptography.hazmat.primitives import serialization

from app.core.config import settings
from app.protocols import keys


def rpc_url(agent_id: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/a/{agent_id}/a2a"


def jku() -> str:
    return f"{settings.public_base_url.rstrip('/')}/.well-known/jwks.json"


def _pems() -> tuple[bytes, bytes]:
    sk = keys.private_key()
    return (sk.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
            sk.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))


def sign(card: AgentCard) -> AgentCard:
    private_pem, _ = _pems()
    signer = create_agent_card_signer(signing_key=private_pem,
                                      protected_header={"alg": "EdDSA", "kid": keys.kid(), "typ": "JOSE", "jku": jku()})
    return signer(card)


@lru_cache
def _verifier_for(kid: str, public_pem: bytes):
    return create_signature_verifier(key_provider=lambda k, _jku: public_pem if k == kid else b"", algorithms=["EdDSA"])


def verify(card: AgentCard) -> None:
    """플랫폼 키로 서명된 카드만 통과(InvalidSignaturesError / NoSignatureError)."""
    _, public_pem = _pems()
    _verifier_for(keys.kid(), public_pem)(card)


def signed_card(manifest: dict, url: str | None = None) -> AgentCard:
    return sign(build_card(manifest, url or rpc_url(manifest["metadata"]["id"])))


def signed_card_json(manifest: dict, url: str | None = None) -> dict:
    return card_json(signed_card(manifest, url))


def server_json(manifest: dict, url: str | None = None) -> dict:
    """MCP registry 의 server.json 형식(remotes: streamable-http). 인증 헤더는 x-api-key."""
    meta = manifest["metadata"]
    url = url or f"{settings.public_base_url.rstrip('/')}/mcp/{meta['id']}"
    desc = meta.get("description")
    return {
        "name": f"io.agentplaza/{meta['id']}",
        "description": (" ".join(desc.values()) if isinstance(desc, dict) else str(desc or meta["id"]))[:100],
        "version": meta["version"],
        "remotes": [{"type": "streamable-http", "url": url,
                     "headers": [{"name": "x-api-key", "description": "AgentPlaza API key", "isRequired": True,
                                  "isSecret": True}]}],
    }
