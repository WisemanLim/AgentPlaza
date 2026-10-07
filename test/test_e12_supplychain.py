"""Epic 12 — 공급망 신뢰 게이트 (D4-06 패키징·서명, D5-03 서명·SBOM·취약점, D5-04 라이선스·정책, NFR-S2·C1·C2).

cosign·syft 는 실제 바이너리(이미지 포함)로 돌린다. trivy 는 시험 컨테이너에 취약점 DB 가 없어 결과를 주입하고,
실제 DB 스캔은 test/impl/12th 라이브 시나리오에서 확인한다.
"""
import io
import json
import subprocess
import sys
import zipfile

import pytest
import yaml
from cryptography.hazmat.primitives import serialization as ser
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.agentspec import generator as gen
from app.supplychain import licenses, tools
from app.supplychain.publish import publish
from helpers import auth, make_user
from test_e6_registry import install, rt, serve  # noqa: F401 — rt 는 픽스처

GW_CHECK = {"status": "scanned", "critical": 0, "high": 0, "medium": 0, "low": 0, "findings": []}


def keypair():
    k = Ed25519PrivateKey.generate()
    priv = k.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption())
    pub = k.public_key().public_bytes(ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()
    return priv, pub


def files_for(agent_id, type_="app", license_=None, egress=None):
    files = gen.scaffold(agent_id, agent_id.title(), type_)
    if license_ or egress is not None:
        m = gen.manifest_of(files)
        if license_:
            m["metadata"]["license"] = license_
        if egress is not None:
            m["spec"].setdefault("permissions", {}).setdefault("network", {})["egress"] = egress
        files["agent.yaml"] = yaml.safe_dump(m, sort_keys=False, allow_unicode=True).encode()
    return files


def raw_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p, b in files.items():
            z.writestr(p, b)
    return buf.getvalue()


def trust_key(client, token, pub, name="pub-a"):
    res = client.post("/api/trust/keys", json={"name": name, "public_key": pub}, headers=auth(token))
    assert res.status_code == 201, res.text
    return res.json()["kid"]


def test_e12_01_publish_package_layout():
    """D4-06: publish = checksums.txt · sbom.json(syft) · signature.sig(cosign) + agent.yaml keyId."""
    priv, pub = keypair()
    data, kid, n = publish(files_for("pub-board"), priv)
    z = gen.read_zip(data)
    assert {"checksums.txt", "signature.sig", "sbom.json", "agent.yaml"} <= set(z)
    assert gen.manifest_of(z)["metadata"]["publisher"]["keyId"] == kid and kid.startswith("pub-")
    listed = {line.split("  ", 1)[1] for line in z["checksums.txt"].decode().splitlines()}
    assert "sbom.json" in listed and "signature.sig" not in listed and "checksums.txt" not in listed
    assert json.loads(z["sbom.json"])["bomFormat"] == "CycloneDX" and n == len(json.loads(z["sbom.json"]).get("components", []))
    assert tools.cosign_verify(z["checksums.txt"], z["signature.sig"], pub)
    _, other = keypair()
    assert not tools.cosign_verify(z["checksums.txt"], z["signature.sig"], other)


def test_e12_02_signed_install_verified_badge(client, sup_token, rt, tmp_path, monkeypatch):
    """D5-03·NFR-S2: 신뢰 키로 서명 = verified, 버전 기록·마켓 배지."""
    priv, pub = keypair()
    kid = trust_key(client, sup_token, pub)
    serve(tmp_path, monkeypatch, "signed-app")
    st = install(client, sup_token, publish(files_for("signed-app"), priv)[0])
    assert st["status"] == "succeeded", st
    s3 = st["steps"][2]
    assert s3["status"] == "warn" and s3["detail"]["signature"] == "verified" and s3["detail"]["signer"] == kid
    assert s3["detail"]["sbom"]["declared_match"] is True and s3["detail"]["vulns"]["status"] == "unscanned"
    v = client.get("/api/agents/signed-app", headers=auth(sup_token)).json()["versions"][0]
    assert v["signature"] == "verified" and v["signer"] == kid and v["license_grade"] == "G1" and v["sbom"] is True
    sbom = client.get("/api/agents/signed-app/sbom", headers=auth(sup_token))
    assert sbom.status_code == 200 and sbom.json()["bomFormat"] == "CycloneDX"


def test_e12_03_tampered_and_revoked_rejected(client, sup_token, rt, tmp_path, monkeypatch):
    """NFR-S2: 파일 변조 → checksums 불일치, checksums 재계산 → 서명 불일치, 철회 키 → 거부."""
    priv, pub = keypair()
    kid = trust_key(client, sup_token, pub)
    z = gen.read_zip(publish(files_for("tamper"), priv)[0])
    z["backend/main.py"] += b"\n# injected\n"
    st = install(client, sup_token, raw_zip(z))
    assert st["status"] == "failed" and st["step"] == 3 and "checksums 불일치" in st["error"]
    body = {p: b for p, b in z.items() if p not in ("checksums.txt", "signature.sig")}
    z["checksums.txt"] = gen.checksums(body)
    st = install(client, sup_token, raw_zip(z))
    assert st["status"] == "failed" and "서명 불일치" in st["error"]
    good = publish(files_for("tamper"), priv)[0]
    assert client.delete(f"/api/trust/keys/{kid}", headers=auth(sup_token)).json()["revoked_at"]
    st = install(client, sup_token, good)
    assert st["status"] == "failed" and "철회된 키" in st["error"]
    assert client.get("/api/agents/tamper", headers=auth(sup_token)).status_code == 404


def test_e12_04_unknown_key_and_require_signature(client, sup_token, rt, tmp_path, monkeypatch):
    priv, _ = keypair()
    serve(tmp_path, monkeypatch, "unknown-key")
    signed_by_stranger = publish(files_for("unknown-key"), priv)[0]
    st = install(client, sup_token, signed_by_stranger)
    assert st["status"] == "succeeded" and st["steps"][2]["detail"]["signature"] == "unverified"
    assert any("신뢰 키 아님" in w for w in st["warnings"])
    res = client.put("/api/trust/policy", json={"require_signature": True}, headers=auth(sup_token))
    assert res.status_code == 200 and res.json()["require_signature"] is True
    st = install(client, sup_token, signed_by_stranger, force=True)
    assert st["status"] == "failed" and st["step"] == 3 and "서명 검증된 패키지만" in st["error"]


def test_e12_05_vulnerability_gate(client, sup_token, rt, tmp_path, monkeypatch):
    """NFR-S2: Critical 취약점 = 설치 거부, High = 경고. 차단 등급은 정책으로."""
    finding = {"target": "backend/requirements.txt", "pkg": "PyYAML", "version": "5.3", "id": "CVE-2020-14343",
               "severity": "CRITICAL", "fixed": "5.4"}
    monkeypatch.setattr(tools, "trivy_scan", lambda d: {**GW_CHECK, "critical": 1, "findings": [finding]})
    serve(tmp_path, monkeypatch, "vuln-app")
    st = install(client, sup_token, gen.pack(files_for("vuln-app")))
    assert st["status"] == "failed" and st["step"] == 3 and "CVE-2020-14343" in st["error"]
    monkeypatch.setattr(tools, "trivy_scan", lambda d: {**GW_CHECK, "high": 2,
                                                        "findings": [{**finding, "severity": "HIGH"}]})
    st = install(client, sup_token, gen.pack(files_for("vuln-app")))
    assert st["status"] == "succeeded" and any("HIGH" in w for w in st["warnings"])
    assert client.get("/api/agents/vuln-app", headers=auth(sup_token)).json()["versions"][0]["vulns"]["high"] == 2
    client.put("/api/trust/policy", json={"block_severity": "HIGH"}, headers=auth(sup_token))
    st = install(client, sup_token, gen.pack(files_for("vuln-app")), force=True)
    assert st["status"] == "rolled_back" or st["status"] == "failed"
    assert st["step"] == 3 and "HIGH 이상" in st["error"]


def test_e12_06_license_grades_and_g4_isolation(client, sup_token, rt, tmp_path, monkeypatch):
    """D5-04: G5 차단(허용목록 예외), G4 = 격리 표시 + 파생 금지."""
    st = install(client, sup_token, gen.pack(files_for("closed", license_="LicenseRef-Proprietary")))
    assert st["status"] == "failed" and st["step"] == 4 and "G5" in st["error"]
    client.put("/api/trust/policy", json={"license_allow": ["LicenseRef-Proprietary"]}, headers=auth(sup_token))
    serve(tmp_path, monkeypatch, "closed")
    assert install(client, sup_token, gen.pack(files_for("closed", license_="LicenseRef-Proprietary")))["status"] == "succeeded"
    serve(tmp_path, monkeypatch, "copyleft")
    st = install(client, sup_token, gen.pack(files_for("copyleft", license_="AGPL-3.0-only")))
    assert st["status"] == "succeeded" and st["steps"][3]["status"] == "warn"
    assert st["steps"][3]["detail"]["effective"] == "G4" and any("G4" in w for w in st["warnings"])
    res = client.post("/api/agents/copyleft/export", json={"new_id": "copyleft-fork"}, headers=auth(sup_token))
    assert res.status_code == 403 and "G4" in res.json()["detail"]


def test_e12_07_egress_policy(client, sup_token, rt, tmp_path, monkeypatch):
    """D5-04: 선언 egress 를 조직 허용 패턴과 대조."""
    client.put("/api/trust/policy", json={"egress_allow": ["*.corp.internal"]}, headers=auth(sup_token))
    st = install(client, sup_token, gen.pack(files_for("egress-app", type_="service", egress=["api.example.com"])))
    assert st["status"] == "failed" and st["step"] == 4 and "api.example.com" in st["error"]
    serve(tmp_path, monkeypatch, "egress-app", type_="service")
    st = install(client, sup_token, gen.pack(files_for("egress-app", type_="service", egress=["erp.corp.internal"])))
    assert st["status"] == "succeeded" and st["steps"][3]["detail"]["egress"]["denied"] == []


def test_e12_08_trust_api_rbac_and_validation(client, sup_token):
    _, user_token = make_user(client, sup_token, "u12@example.test")
    _, pub = keypair()
    assert client.get("/api/trust/keys", headers=auth(user_token)).status_code == 403
    assert client.post("/api/trust/keys", json={"name": "x", "public_key": "-----BEGIN PUBLIC KEY-----\nAAAA\n" * 2},
                       headers=auth(sup_token)).status_code == 422
    trust_key(client, sup_token, pub)
    assert client.post("/api/trust/keys", json={"name": "dup", "public_key": pub}, headers=auth(sup_token)).status_code == 422
    assert client.put("/api/trust/policy", json={"block_severity": "SEVERE"}, headers=auth(sup_token)).status_code == 422
    assert client.put("/api/trust/policy", json={"nope": 1}, headers=auth(sup_token)).status_code == 422
    actions = {e["action"] for e in client.get("/api/audit", headers=auth(sup_token)).json()}
    assert {"trust.key_added"} <= actions


def test_e12_09_market_badge_follows_trusted_key(client, sup_token, tmp_path, monkeypatch):
    from app.core.config import settings
    from app.market import seed
    priv, pub = keypair()
    seed.build(tmp_path / "mk", key=priv)
    monkeypatch.setattr(settings, "market_catalog", str(tmp_path / "mk" / "catalog.json"))
    listing = client.get("/api/market/listings/board", headers=auth(sup_token)).json()
    assert "signature:unverified" in listing["badges"] and listing["signature"]["keyId"].startswith("pub-")
    trust_key(client, sup_token, pub)
    listing = client.get("/api/market/listings/board", headers=auth(sup_token)).json()
    assert "signature:verified" in listing["badges"]


def test_e12_10_provenance_recorded(client, sup_token, rt, tmp_path, monkeypatch):
    """NFR-C2: 설치 증적에 출처·라이선스·서명 상태가 남는다."""
    serve(tmp_path, monkeypatch, "prov")
    assert install(client, sup_token, gen.pack(files_for("prov")))["status"] == "succeeded"
    ev = next(e for e in client.get("/api/audit?action=agent.installed", headers=auth(sup_token)).json())
    assert {"license": "MIT", "license_grade": "G1", "signature": "unverified", "source": "zip"}.items() <= ev["detail"].items()


@pytest.mark.parametrize("expr,grade", [
    ("MIT", "G1"), ("Apache-2.0 OR GPL-3.0-only", "G1"), ("Apache-2.0 AND AGPL-3.0-or-later", "G4"),
    ("GPL-2.0-or-later", "G3"), ("MPL-2.0", "G2"), ("NOASSERTION", "G5"), ("LicenseRef-Commercial", "G5"),
    ("GNU Affero General Public License v3", "G4"), ("BSD License", "G1"), ("GPL-2.0 WITH Classpath-exception-2.0", "G3"),
    ("", "G5"), ("Limited Use License", "G5")])
def test_e12_11_license_grade_table(expr, grade):
    assert licenses.grade(expr) == grade


def test_e12_12_platform_image_has_no_g4(tmp_path):
    """NFR-C1: 플랫폼 의존성(venv) SBOM 에 G4(AGPL·SSPL·BUSL 등) 컴포넌트가 없다."""
    r = subprocess.run([sys.executable, "-m", "plaza", "sbom-check", sys.prefix, "--fail-on", "G4"],
                       capture_output=True, text=True, timeout=300)
    report = json.loads(r.stdout)
    assert r.returncode == 0, report["flagged"]
    assert report["components"] > 50 and report["grades"]["G4"] == 0


def test_e12_13_cli_derive_refuses_g4(tmp_path):
    src = tmp_path / "agpl.zip"
    src.write_bytes(gen.pack(files_for("agpl-x", license_="AGPL-3.0-only")))
    r = subprocess.run([sys.executable, "-m", "plaza", "export", str(src), "--derive", "agpl-y", "--out",
                        str(tmp_path / "y.zip")], capture_output=True, text=True, timeout=60)
    assert r.returncode == 1 and "G4" in r.stderr
