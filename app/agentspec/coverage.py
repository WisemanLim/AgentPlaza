"""verify-coverage (PRD 10.8 의 P0 적용판): P0 FR ↔ 구현 계획표 Epic ↔ 시험 코드 추적이 끊기지 않았는지 검사.

- PRD §3.1 핵심 기능 표의 '관련 FR' 열 = P0 집합(43)
- 계획표의 모든 P0 FR 이 Epic 에 배정됐는지
- DONE Epic 의 FR 이 test/test_*.py 에 1회 이상 언급됐는지(시험 docstring 의 'D9-01/02' 같은 표기 포함)
- 템플릿 9유형 디렉터리/정의가 모두 있는지
"""
import re
from pathlib import Path

from app.agentspec.generator import TEMPLATES, TYPE_DEFS, TYPES

FR = re.compile(r"D(\d+)-(\d{2})((?:[~/]\d{2})*)")


def expand(text: str) -> set[str]:
    """'D2-01~04' → D2-01..D2-04, 'D9-01/02/07' → D9-01, D9-02, D9-07."""
    out: set[str] = set()
    for dom, first, rest in FR.findall(text):
        nums = [int(first)]
        for sep, n in re.findall(r"([~/])(\d{2})", rest):
            if sep == "~":
                nums += list(range(nums[-1] + 1, int(n) + 1))
            else:
                nums.append(int(n))
        out |= {f"D{dom}-{n:02d}" for n in nums}
    return out


def _section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def prd_p0(prd: Path) -> set[str]:
    table = _section(prd.read_text(encoding="utf-8"), "### 3.1", "- **P1")
    return expand(table)


def plan_epics(plan: Path) -> list[dict]:
    rows = []
    for line in plan.read_text(encoding="utf-8").splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 7 and re.fullmatch(r"\d+", cols[0]):
            rows.append({"epic": int(cols[0]), "name": cols[1], "frs": expand(cols[2]), "status": cols[-1]})
    return rows


def tested_frs(test_dir: Path) -> set[str]:
    found: set[str] = set()
    for f in test_dir.glob("test_*.py"):
        found |= expand(f.read_text(encoding="utf-8"))
    return found


def _doc(root: Path, name: str) -> Path:
    """문서는 루트 또는 .docs/ 어느 쪽에 있어도 된다(루트 우선)."""
    return root / name if (root / name).is_file() else root / ".docs" / name


def verify(root: Path) -> dict:
    p0 = prd_p0(_doc(root, "PRD.md"))
    epics = plan_epics(_doc(root, "IMPLEMENT_PLAN.md"))
    planned = set().union(*(e["frs"] for e in epics)) if epics else set()
    tested = tested_frs(root / "test")
    done = [e for e in epics if e["status"] == "DONE"]
    untested = sorted({fr for e in done for fr in e["frs"]} - tested)
    missing_types = [t for t in TYPES if t not in TYPE_DEFS or (t != "federation" and not (TEMPLATES / t).is_dir())]
    problems = []
    if len(p0) != 43:
        problems.append(f"PRD P0 FR 수 {len(p0)} ≠ 43")
    if p0 - planned:
        problems.append(f"계획표 미배정 P0 FR: {sorted(p0 - planned)}")
    if untested:
        problems.append(f"DONE Epic 인데 시험 언급 없는 FR: {untested}")
    if missing_types:
        problems.append(f"템플릿 누락 유형: {missing_types}")
    return {"ok": not problems, "p0": len(p0), "planned": len(planned & p0),
            "done_epics": [e["epic"] for e in done], "tested_p0": len(tested & p0), "problems": problems}
