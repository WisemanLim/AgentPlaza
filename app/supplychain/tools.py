"""cosign·syft·trivy 실행 래퍼. 바이너리는 이미지에 포함(Dockerfile), 모두 오프라인으로 돈다.

- cosign: 신뢰 키(Ed25519 SPKI PEM)로 checksums.txt 의 서명을 검증한다. 투명성 로그(Rekor)는 폐쇄망 전제라 쓰지 않는다.
- syft: 패키지 디렉터리 SBOM(CycloneDX JSON).
- trivy: 오프라인 취약점 DB(볼륨, `make trivy-db`)로 파일시스템 스캔. DB 가 없으면 'unscanned'.
"""
import json
import os
import secrets
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


class ToolError(Exception):
    pass


def _run(args: list[str], *, env: dict | None = None, timeout: float | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout or settings.supply_chain_timeout,
                              env={**os.environ, **(env or {})})
    except FileNotFoundError:
        raise ToolError(f"{args[0]} 없음 — 이미지 재빌드 필요 / binary missing") from None
    except subprocess.TimeoutExpired:
        raise ToolError(f"{args[0]} 시간 초과 / timeout") from None


def cosign_verify(blob: bytes, signature: bytes, public_pem: str) -> bool:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "blob").write_bytes(blob)
        (p / "blob.sig").write_bytes(signature)
        (p / "key.pub").write_text(public_pem)
        r = _run(["cosign", "verify-blob", "--key", str(p / "key.pub"), "--signature", str(p / "blob.sig"),
                  "--insecure-ignore-tlog=true", "--use-signed-timestamps=false", str(p / "blob")], timeout=60)
    return r.returncode == 0


def cosign_sign(blob: bytes, private_pem: bytes) -> bytes:
    """Ed25519 PKCS8 PEM 으로 서명(plaza publish). cosign 키 형식으로 임시 가져와 서명하고 바로 지운다."""
    password = secrets.token_urlsafe(24)
    env = {"COSIGN_PASSWORD": password}
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "key.pem").write_bytes(private_pem)
        (p / "key.pem").chmod(0o600)
        (p / "blob").write_bytes(blob)
        r = _run(["cosign", "import-key-pair", "--key", str(p / "key.pem"), "--output-key-prefix", str(p / "imp"), "-y"],
                 env=env, timeout=60)
        if r.returncode != 0:
            raise ToolError(f"cosign import-key-pair 실패: {r.stderr.strip()[-300:]}")
        r = _run(["cosign", "sign-blob", "--key", str(p / "imp.key"), "--tlog-upload=false", "--use-signing-config=false",
                  "--new-bundle-format=false", "--output-signature", str(p / "blob.sig"), "-y", str(p / "blob")],
                 env=env, timeout=60)
        if r.returncode != 0:
            raise ToolError(f"cosign sign-blob 실패: {r.stderr.strip()[-300:]}")
        return (p / "blob.sig").read_bytes()


def syft_sbom(directory: Path) -> dict:
    r = _run(["syft", "scan", f"dir:{directory}", "-o", "cyclonedx-json", "-q"],
             env={"SYFT_CHECK_FOR_APP_UPDATE": "false"})
    if r.returncode != 0:
        raise ToolError(f"syft 실패: {r.stderr.strip()[-300:]}")
    return json.loads(r.stdout)


def trivy_db_ready() -> bool:
    return (Path(settings.trivy_cache_dir) / "db" / "trivy.db").is_file()


def trivy_scan(directory: Path) -> dict:
    """{status: scanned|unscanned, critical, high, medium, low, findings[:20]}"""
    empty = {s.lower(): 0 for s in SEVERITIES}
    if not trivy_db_ready():
        return {"status": "unscanned", **empty, "findings": [], "reason": "취약점 DB 없음 — make trivy-db"}
    r = _run(["trivy", "fs", "--cache-dir", settings.trivy_cache_dir, "--skip-db-update", "--skip-java-db-update",
              "--offline-scan", "--scanners", "vuln", "--format", "json", "-q", str(directory)])
    if r.returncode != 0:
        raise ToolError(f"trivy 실패: {r.stderr.strip()[-300:]}")
    counts, findings = dict(empty), []
    for res in json.loads(r.stdout or "{}").get("Results") or []:
        for v in res.get("Vulnerabilities") or []:
            sev = v.get("Severity", "UNKNOWN")
            if sev in SEVERITIES:
                counts[sev.lower()] += 1
            findings.append({"target": res.get("Target"), "pkg": v.get("PkgName"), "version": v.get("InstalledVersion"),
                             "id": v.get("VulnerabilityID"), "severity": sev, "fixed": v.get("FixedVersion")})
    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: order.get(f["severity"], 9))
    return {"status": "scanned", **counts, "findings": findings[:20]}
