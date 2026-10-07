"""라이선스 등급 G1~G5 (PRD 9.7).

G1 허용(링크·내장 가능) · G2 파일 카피레프트(파일 단위 고지) · G3 프로세스 카피레프트(별 컨테이너, 링크 금지)
G4 네트워크·소스공개형(연계 M2 만 — 포크·내장·재판매 금지) · G5 확인 부족·비OSS(재확인 전 사용 금지)
SPDX 식: 'A OR B' 는 더 관대한 쪽, 'A AND B' 는 더 엄격한 쪽을 택한다.
"""
import re

GRADES = ("G1", "G2", "G3", "G4", "G5")
_TABLE = {
    "G1": ["Apache-2.0", "MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "ISC", "Zlib", "BSL-1.0", "CC0-1.0",
           "Unlicense", "PSF-2.0", "Python-2.0", "UPL-1.0", "X11", "CC-BY-4.0"],
    "G2": ["MPL-2.0", "MPL-1.1", "EPL-2.0", "EPL-1.0", "CDDL-1.0", "CDDL-1.1"],
    "G3": ["GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "LGPL-2.0"],
    "G4": ["AGPL-3.0", "SSPL-1.0", "BUSL-1.1", "Elastic-2.0", "PolyForm-Shield-1.0.0", "PolyForm-Noncommercial-1.0.0",
           "LicenseRef-Sustainable-Use", "LicenseRef-Open-WebUI", "LicenseRef-Dify"],
}
_INDEX = {lic.lower(): g for g, items in _TABLE.items() for lic in items}
# 사람이 쓴 이름(패키지 메타데이터)도 흔하다 — 접두어로 대충 맞춘다
_NAMES = [(r"affero|\bagpl", "G4"), (r"server side public|\bsspl", "G4"), (r"business source|\bbusl", "G4"),
          (r"lesser general public|gnu library|\blgpl", "G3"), (r"general public|\bgpl", "G3"),
          (r"mozilla public|\bmpl", "G2"), (r"eclipse public", "G2"),
          (r"\bapache", "G1"), (r"\bmit\b", "G1"), (r"\bbsd\b", "G1"), (r"\bisc\b", "G1"),
          (r"python software foundation|\bpsf\b", "G1"), (r"public domain", "G1"), (r"\bzlib\b", "G1"),
          (r"\bunlicense\b", "G1")]


def _one(lic: str) -> str:
    lic = lic.strip().strip("()")
    base = re.sub(r"(-only|-or-later|\+)$", "", lic, flags=re.I)
    if base.lower() in _INDEX:
        return _INDEX[base.lower()]
    low = lic.lower()
    if not low or low in ("none", "noassertion", "unknown", "proprietary") or low.startswith("licenseref-"):
        return "G5"
    for pat, g in _NAMES:
        if re.search(pat, low):
            return g
    return "G5"


def grade(expr: str | None) -> str:
    """SPDX 식 또는 이름 → G1~G5."""
    if not expr or not expr.strip():
        return "G5"
    expr = re.sub(r"\s+WITH\s+[\w.-]+", "", expr.strip(), flags=re.I)
    alts = re.split(r"\s+OR\s+", expr, flags=re.I)
    best = []
    for alt in alts:
        parts = re.split(r"\s+AND\s+", alt, flags=re.I)
        best.append(max((_one(p) for p in parts), key=GRADES.index))
    return min(best, key=GRADES.index)


def worst(grades) -> str | None:
    gs = [g for g in grades if g]
    return max(gs, key=GRADES.index) if gs else None


def sbom_licenses(sbom: dict) -> list[dict]:
    """CycloneDX 컴포넌트 → [{name, version, license|None, grade|None}] (라이선스 정보가 없으면 None)."""
    out = []
    for c in sbom.get("components") or []:
        lics = []
        for entry in c.get("licenses") or []:
            if "expression" in entry:
                lics.append(entry["expression"])
            lic = entry.get("license") or {}
            if lic.get("id") or lic.get("name"):
                lics.append(lic.get("id") or lic.get("name"))
        expr = " AND ".join(lics) if lics else None
        out.append({"name": c.get("name"), "version": c.get("version"), "license": expr,
                    "grade": grade(expr) if expr else None})
    return out
