"""plaza CLI (P12) — init · validate · test · pack · keygen · publish · sbom-check · export · convert-v1 · market-build ·
verify-coverage.

컨테이너에서: make plaza ARGS="init board --template app --out agents/board"
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from app.agentspec import generator as gen
from app.agentspec.coverage import verify
from app.agentspec.validate import from_v1_meta, validate_text


def _read(src: str) -> dict[str, bytes]:
    p = Path(src)
    if p.is_dir():
        return {f.relative_to(p).as_posix(): f.read_bytes() for f in sorted(p.rglob("*"))
                if f.is_file() and "__pycache__" not in f.parts}
    return gen.read_zip(p.read_bytes())


def _write_dir(files: dict[str, bytes], out: Path) -> None:
    for rel, data in files.items():
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)


def _strict(src: Path) -> list[str]:
    """선언 vs 실제(coherence): backend/main.py 를 별 프로세스에서 import 해 핸들러 집합을 비교한다."""
    code = ("import os,sys; sys.path.insert(0,'backend'); os.environ['AGENT_MANIFEST']='agent.yaml';"
            "import importlib.util as u; s=u.spec_from_file_location('m','backend/main.py'); m=u.module_from_spec(s);"
            "s.loader.exec_module(m)")
    r = subprocess.run([sys.executable, "-c", code], cwd=src, capture_output=True, text=True, timeout=60)
    return [] if r.returncode == 0 else [f"strict: {r.stderr.strip().splitlines()[-1] if r.stderr else 'import failed'}"]


def cmd_init(a) -> int:
    files = gen.scaffold(a.id, a.name or a.id.replace("-", " ").title(), a.template, description=a.description,
                         federation_url=a.url)
    out = Path(a.out or a.id)
    if out.exists() and any(out.iterdir()):
        print(f"FAIL: {out} 비어 있지 않음 / not empty", file=sys.stderr)
        return 1
    _write_dir(files, out)
    print(f"created {out} ({len(files)} files, type={a.template})")
    return 0


def cmd_validate(a) -> int:
    files = _read(a.src)
    if "agent.yaml" not in files:
        print("FAIL: agent.yaml 없음", file=sys.stderr)
        return 1
    m, errs = validate_text(files["agent.yaml"].decode())
    if m and m["spec"]["type"] != "federation":
        errs += [f"missing: {p}" for p in ("compose.yaml", "backend/main.py", "backend/Dockerfile") if p not in files]
    if not errs and a.strict and Path(a.src).is_dir() and m["spec"]["type"] != "federation":
        errs += _strict(Path(a.src))
    for e in errs:
        print(f"ERROR {e}")
    print("OK" if not errs else f"FAIL ({len(errs)})")
    return 0 if not errs else 1


def cmd_test(a) -> int:
    """D4-05: 구조·문법·SQL·런타임 계약(REST·MCP·A2A)·시나리오(evals/*.yaml). --report 디렉터리에 result.md·result.json."""
    from app.agentspec import localtest
    rep = localtest.run(Path(a.src))
    for c in rep["checks"]:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['check']} {'' if c['ok'] else c['detail']}")
    for e in rep["evals"]:
        print(f"{'PASS' if e['ok'] else 'FAIL'} eval:{e['id']} {', '.join(e['fails'])}")
    if a.report:
        out = Path(a.report)
        out.mkdir(parents=True, exist_ok=True)
        (out / "result.md").write_text(localtest.markdown(rep), encoding="utf-8")
        (out / "result.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK" if rep["ok"] else "FAIL")
    return 0 if rep["ok"] else 1


def cmd_pack(a) -> int:
    files = _read(a.src)
    m = gen.manifest_of(files)
    out = Path(a.out or f"{m['metadata']['id']}-{m['metadata']['version']}.zip")
    out.write_bytes(gen.pack(files))
    print(f"packed {out}")
    return 0


def cmd_keygen(a) -> int:
    """퍼블리셔 서명 키(Ed25519). 비밀키는 0600, 공개키는 콘솔 '신뢰 키' 또는 퍼블리셔 등록에 쓴다."""
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from app.supplychain.trust import kid_of
    out = Path(a.out)
    key_path, pub_path = out.with_suffix(".key"), out.with_suffix(".pub")
    if key_path.exists():
        print(f"FAIL: {key_path} 이미 있음 / exists", file=sys.stderr)
        return 1
    k = Ed25519PrivateKey.generate()
    out.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(k.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()))
    key_path.chmod(0o600)
    pub = k.public_key().public_bytes(ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()
    pub_path.write_text(pub)
    print(f"key {key_path} (0600) · pub {pub_path} · kid {kid_of(pub)}")
    return 0


def cmd_publish(a) -> int:
    """make publish (D4-06): zip · checksums.txt · sbom.json(syft) · signature.sig(cosign, checksums.txt 서명)."""
    from app.supplychain.publish import publish
    data, kid, n = publish(_read(a.src), Path(a.key).read_bytes())
    m = gen.manifest_of(gen.read_zip(data))
    out = Path(a.out or f"{m['metadata']['id']}-{m['metadata']['version']}.zip")
    out.write_bytes(data)
    print(f"published {out} (kid {kid}, sbom {n} components)")
    if a.registry:  # 마켓 게시(D6-06): POST {registry}/api/market/releases — 토큰은 환경 변수 PLAZA_TOKEN
        import os

        import httpx
        if a.dry_run:
            print(f"dry-run: {a.registry}/api/market/releases publisher={a.publisher}")
            return 0
        listing = Path(a.listing).read_text() if a.listing else "{}"
        res = httpx.post(f"{a.registry.rstrip('/')}/api/market/releases", timeout=600,
                         headers={"Authorization": f"Bearer {os.environ.get('PLAZA_TOKEN', '')}"},
                         files={"file": (out.name, data, "application/zip")},
                         data={"publisher": a.publisher, "listing": listing})
        body = res.json()
        if res.status_code != 201:
            print(f"FAIL {res.status_code}: {json.dumps(body.get('detail'), ensure_ascii=False)[:500]}")
            return 1
        print(f"release {body['id']} {body['listing_id']}@{body['version']} status={body['status']}")
    return 0


def cmd_sbom_check(a) -> int:
    """NFR-C1: 경로(기본 플랫폼 venv)의 SBOM 라이선스를 등급으로 집계. fail-on 등급 이상이 있으면 실패."""
    from app.supplychain import licenses, tools
    from app.supplychain.licenses import GRADES
    comps = licenses.sbom_licenses(tools.syft_sbom(Path(a.path)))
    by = {g: [] for g in GRADES}
    for c in comps:
        if c["grade"]:
            by[c["grade"]].append(f"{c['name']}@{c['version']} ({c['license']})")
    bad = [x for g in GRADES[GRADES.index(a.fail_on):] for x in by[g]]
    print(json.dumps({"components": len(comps), "unknown": sum(1 for c in comps if not c["grade"]),
                      "grades": {g: len(v) for g, v in by.items()}, "flagged": bad}, ensure_ascii=False, indent=2))
    return 1 if bad else 0


def cmd_export(a) -> int:
    files = _read(a.src)
    if a.derive:
        from app.supplychain.licenses import grade
        lic = gen.manifest_of(files)["metadata"].get("license")
        if grade(lic) == "G4":
            print(f"FAIL: {lic} = G4 — 파생(포크) 금지, 연계(M2)만 (PRD 9.7)", file=sys.stderr)
            return 1
        files = gen.derive(files, a.derive)
    if a.standalone:
        files = gen.standalone_bundle(files)
    m = gen.manifest_of(files)
    out = Path(a.out or f"{m['metadata']['id']}-{m['metadata']['version']}{'-standalone' if a.standalone else ''}.zip")
    out.write_bytes(gen.pack(files))
    print(f"exported {out}")
    return 0


def cmd_convert(a) -> int:
    import yaml
    print(yaml.safe_dump(from_v1_meta(json.loads(Path(a.meta).read_text())), sort_keys=False, allow_unicode=True))
    return 0


def cmd_coverage(a) -> int:
    report = verify(Path(a.root))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def cmd_market_build(a) -> int:
    from app.market import seed
    cat = seed.build(Path(a.out), key=Path(a.key).read_bytes() if a.key else None)
    print(f"catalog {a.out}/catalog.json ({len(cat['listings'])} listings)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="plaza")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init")
    s.add_argument("id")
    s.add_argument("--template", choices=gen.TYPES, default="service")
    s.add_argument("--name")
    s.add_argument("--description", default="")
    s.add_argument("--url", help="federation 유형의 원격 Card/MCP URL")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_init)
    s = sub.add_parser("validate")
    s.add_argument("src")
    s.add_argument("--strict", action="store_true")
    s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("test")
    s.add_argument("src")
    s.add_argument("--report", help="result.md·result.json 을 쓸 디렉터리(예: test/impl/<Nth>)")
    s.set_defaults(fn=cmd_test)
    s = sub.add_parser("pack")
    s.add_argument("src")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_pack)
    s = sub.add_parser("keygen")
    s.add_argument("--out", required=True, help="경로 접두어 — <out>.key · <out>.pub")
    s.set_defaults(fn=cmd_keygen)
    s = sub.add_parser("publish")
    s.add_argument("src")
    s.add_argument("--key", required=True, help="Ed25519 비밀키(PEM, plaza keygen)")
    s.add_argument("--out")
    s.add_argument("--registry", help="마켓 주소(예: http://127.0.0.1:8090) — 주면 게시까지(PLAZA_TOKEN)")
    s.add_argument("--publisher", default="local", help="퍼블리셔 id(서명 키가 이 퍼블리셔에 등록돼 있어야 함)")
    s.add_argument("--listing", help="카탈로그 정보 JSON 파일(name·description·tags·categories·pricing)")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_publish)
    s = sub.add_parser("sbom-check")
    s.add_argument("path", nargs="?", default="/opt/venv")
    s.add_argument("--fail-on", default="G4", choices=["G3", "G4", "G5"])
    s.set_defaults(fn=cmd_sbom_check)
    s = sub.add_parser("export")
    s.add_argument("src")
    s.add_argument("--derive", metavar="NEW_ID")
    s.add_argument("--standalone", action="store_true")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_export)
    s = sub.add_parser("convert-v1")
    s.add_argument("meta")
    s.set_defaults(fn=cmd_convert)
    s = sub.add_parser("market-build")
    s.add_argument("--out", default="market")
    s.add_argument("--key", help="산출물 서명 키(Ed25519 PEM). 주면 리스팅에 signature.keyId 를 기록")
    s.set_defaults(fn=cmd_market_build)
    s = sub.add_parser("verify-coverage")
    s.add_argument("--root", default=".")
    s.set_defaults(fn=cmd_coverage)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
