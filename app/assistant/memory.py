"""메모리·개인화 (D3-05): 맞춤지침(instruction) + 장기 기억(fact). 본인 것만 쓰고, 언제든 지운다(삭제권, NFR-C3).

- 대화에서 "기억해: …" / "remember: …" 로 저장(LLM 없이 규칙). "잊어줘: …" / "forget: …" 는 일치 항목 삭제.
- 개인정보 최소화: 주민·외국인등록번호·카드·여권·계좌 형식은 저장 전에 마스킹한다.
- 프롬프트 주입: 지침 전부 + 질문과 가까운 기억 상위 8개(기억이 8개 이하면 전부)를 시스템 메시지로.
"""
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.governance import guardrails
from app.models import Memory
from app.services import sysconfig

REMEMBER = re.compile(r"^\s*(?:기억해\s*줘?|기억해|remember(?: that)?)\s*[:：]?\s*(.+)$", re.I | re.S)
FORGET = re.compile(r"^\s*(?:잊어\s*줘?|잊어|forget(?: that)?)\s*[:：]?\s*(.+)$", re.I | re.S)
SENSITIVE = {"rrn", "card", "passport", "account", "driver_license"}
MAX_FACTS = 200


def _minimize(text: str) -> str:
    masked = text
    for kind, pat in guardrails.PII:
        if kind in SENSITIVE:
            masked = pat.sub(f"[{kind.upper()}]", masked)
    return masked.strip()[:1000]


def enabled(db: Session, owner: str) -> bool:
    return sysconfig.blob(db, f"profile:{owner}").get("memory_enabled", True)


def items(db: Session, owner: str, kind: str | None = None) -> list[Memory]:
    q = select(Memory).where(Memory.owner == owner).order_by(Memory.created_at)
    if kind:
        q = q.where(Memory.kind == kind)
    return list(db.execute(q).scalars())


def add(db: Session, owner: str, kind: str, content: str, source: str = "manual") -> Memory:
    if kind not in ("instruction", "fact"):
        raise ValueError("kind ∈ instruction|fact")
    if kind == "fact" and len(items(db, owner, "fact")) >= MAX_FACTS:
        raise ValueError(f"기억은 최대 {MAX_FACTS}개 / too many memories")
    m = Memory(owner=owner, kind=kind, content=_minimize(content), source=source)
    db.add(m)
    db.commit()
    return m


def purge(db: Session, owner: str) -> int:
    n = db.execute(delete(Memory).where(Memory.owner == owner)).rowcount
    db.commit()
    return n


def command(db: Session, owner: str, message: str) -> str | None:
    """'기억해:'·'잊어줘:' 명령이면 처리하고 확인 문장을 돌려준다. 아니면 None."""
    if m := REMEMBER.match(message):
        if not enabled(db, owner):
            return "메모리가 꺼져 있어 저장하지 않았습니다 / memory is turned off"
        fact = add(db, owner, "fact", m.group(1), source="chat")
        return f"기억했습니다: {fact.content} / noted"
    if m := FORGET.match(message):
        needle = m.group(1).strip().lower()
        hit = [x for x in items(db, owner, "fact") if needle in x.content.lower()]
        for x in hit:
            db.delete(x)
        db.commit()
        return f"{len(hit)}개를 잊었습니다 / forgot {len(hit)}"
    return None


def context(db: Session, owner: str, query: str) -> str | None:
    if not enabled(db, owner):
        return None
    instr = [m.content for m in items(db, owner, "instruction")]
    facts = items(db, owner, "fact")
    if len(facts) > 8:  # 질문과 겹치는 단어가 많은 순(가벼운 관련도 — 임베딩 호출 없이)
        words = set(re.findall(r"\w{2,}", query.lower()))
        facts = sorted(facts, key=lambda f: -len(words & set(re.findall(r"\w{2,}", f.content.lower()))))[:8]
    if not instr and not facts:
        return None
    parts = []
    if instr:
        parts.append("User's custom instructions (follow them):\n" + "\n".join(f"- {i}" for i in instr))
    if facts:
        parts.append("Known facts about the user (use only when relevant):\n" + "\n".join(f"- {f.content}" for f in facts))
    return "\n\n".join(parts)


def touch(m: Memory) -> None:
    m.updated_at = utcnow()
