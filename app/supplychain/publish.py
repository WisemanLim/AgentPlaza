"""서명 패키징 (D4-06, `plaza publish`): zip · checksums.txt · sbom.json(syft) · signature.sig(cosign).

서명 대상은 checksums.txt 이고, 그 안에 sbom.json 을 포함한 모든 파일의 sha256 이 있다.
agent.yaml metadata.publisher.keyId 에 서명 키 kid 를 기록한다(설치 3단계가 검증 키를 고르는 근거).
"""
import json
import tempfile
from pathlib import Path

import yaml
from cryptography.hazmat.primitives import serialization as ser

from app.agentspec import generator as gen
from app.supplychain import tools
from app.supplychain.trust import kid_of

META = ("checksums.txt", "signature.sig", "sbom.json")


def public_pem_of(private_pem: bytes) -> str:
    return ser.load_pem_private_key(private_pem, password=None).public_key().public_bytes(
        ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()


def publish(files: dict[str, bytes], private_pem: bytes) -> tuple[bytes, str, int]:
    """→ (zip, kid, SBOM 컴포넌트 수)"""
    files = {p: b for p, b in files.items() if p not in META}
    kid = kid_of(public_pem_of(private_pem))
    m = gen.manifest_of(files)
    if (m["metadata"].get("publisher") or {}).get("keyId") != kid:
        m["metadata"]["publisher"] = {**(m["metadata"].get("publisher") or {"id": "local"}), "keyId": kid}
        files["agent.yaml"] = yaml.safe_dump(m, sort_keys=False, allow_unicode=True).encode()
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            dst = Path(d) / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(body)
        sbom = tools.syft_sbom(Path(d))
    files["sbom.json"] = json.dumps(sbom, ensure_ascii=False, indent=1).encode()
    sig = tools.cosign_sign(gen.checksums(files), private_pem)
    return gen.pack(files, extra={"signature.sig": sig}), kid, len(sbom.get("components") or [])
