"""가드레일 (D9-06, NFR-S6): 프롬프트 인젝션 기본 필터 + 한국어 PII 마스킹.

인젝션: 가중 규칙(강 3·약 1) 합계 — 3 이상 = injection(차단 대상), 1~2 = suspicious(리뷰어 게이트).
정규화: NFKC·소문자·제로폭 제거, 그리고 공백을 모두 뺀 '압축' 문자열에도 핵심 문구를 대조한다(띄어쓰기 우회).
PII: 주민·외국인등록번호, 휴대폰·유선전화, 이메일, 카드번호(Luhn), 여권, 운전면허, 사업자번호, 계좌번호 형식.
"""
import re
import unicodedata

STRONG = [
    r"(ignore|disregard|forget|override|bypass)\s+(all\s+|any\s+|the\s+|your\s+)*(previous|prior|above|earlier|preceding|system|original)\s+(instructions?|prompts?|rules?|messages?|directions?)",
    r"(reveal|show|print|repeat|output|leak|tell me|display)\s+(me\s+)?(your|the)\s+(system|hidden|initial|original|secret)\s+(prompt|instructions?|message|rules)",
    r"you\s+are\s+now\s+(in\s+)?(dan|developer mode|jailbroken|unrestricted|an? unfiltered)",
    r"\bdo anything now\b|\bdan mode\b|developer mode (enabled|on)|\bjailbreak",
    r"<\|im_start\|>|<\|system\|>|\[/?inst\]|<<sys>>|^\s*#{2,}\s*(system|instruction)",
    r"new\s+(system\s+)?instructions?\s*:",
    r"(이전|앞의|위의|기존|모든|원래)\s*(의\s*)?(지시|지침|명령|규칙|설정|프롬프트)\S*\s*(모두\s*|전부\s*|다\s*)?(무시|잊어|잊고|따르지\s*마)",
    r"시스템\s*프롬프트\S*\s*(를|을)?\s*(그대로\s*|전부\s*|모두\s*)?(보여|출력|알려|공개|말해|복사)",
    r"(안전|보안)?\s*(제한|규칙|정책|필터|가드레일)\S*\s*(을|를)?\s*(모두\s*)?(해제|우회|무시|끄)",
    r"너는\s*이제(부터)?\s*.{0,30}(제한\s*없는|자유로운|탈옥|DAN)",
    r"탈옥|개발자\s*모드(로|를)?\s*(전환|활성|켜)",
    r"(관리자|루트|root|admin)\s*권한으로\s*(실행|행동|응답)",
]
WEAK = [
    r"system\s*prompt", r"시스템\s*프롬프트", r"\bact as\b", r"pretend (to be|you are)", r"역할극", r"you must comply",
    r"(api|access)\s*key|비밀\s*번호|토큰\s*(을|를)?\s*(출력|알려)", r"base64", r"instructions?\s+above",
    r"call (the )?tool|도구를\s*(호출|실행)해", r"\bimportant\s*:", r"반드시\s*따르", r"규칙을\s*따르지",
]
COMPACT = ["ignorepreviousinstructions", "ignoreallpreviousinstructions", "disregardpreviousinstructions",
           "이전지시를무시", "이전지시무시", "모든지시를무시", "시스템프롬프트를보여", "시스템프롬프트를출력", "revealyoursystemprompt"]
_STRONG = [re.compile(p, re.I | re.M) for p in STRONG]
_WEAK = [re.compile(p, re.I) for p in WEAK]
ZW = re.compile(r"[​-‏⁠﻿]")


def normalize(text: str) -> str:
    return ZW.sub("", unicodedata.normalize("NFKC", text or "")).lower()


def injection(text: str) -> dict:
    """{level: none|suspicious|injection, score, hits[]}"""
    t = normalize(text)
    compact = re.sub(r"[\s\W_]+", "", t)
    hits = [p.pattern[:40] for p in _STRONG if p.search(t)]
    score = 3 * len(hits)
    if not hits and any(c in compact for c in COMPACT):
        hits.append("compact-phrase")
        score += 3
    weak = [p.pattern[:30] for p in _WEAK if p.search(t)]
    score += len(weak)
    level = "injection" if score >= 3 else "suspicious" if score else "none"
    return {"level": level, "score": score, "hits": hits + weak}


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


PII = [  # 순서 중요: 구체적인 형식부터
    ("rrn", re.compile(r"(?<!\d)\d{6}[- ]?[1-8]\d{6}(?!\d)")),
    ("driver_license", re.compile(r"(?<!\d)\d{2}-\d{2}-\d{6}-\d{2}(?!\d)")),
    ("card", re.compile(r"(?<!\d)(?:\d{4}[- ]?){3}\d{1,7}(?!\d)")),
    ("phone", re.compile(r"(?<!\d)01[016789][- .]?\d{3,4}[- .]?\d{4}(?!\d)")),
    ("tel", re.compile(r"(?<!\d)0(?:2|[3-6][1-5]|70)[- .]?\d{3,4}[- .]?\d{4}(?!\d)")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("passport", re.compile(r"\b[MSRODG]\d{8}\b")),
    ("biz_no", re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{5}(?![\d-])")),
    ("account", re.compile(r"(?<![\d-])\d{3,6}-\d{2,6}-\d{2,7}(?:-\d{1,3})?(?![\d-])")),
]


def mask_pii(text: str) -> tuple[str, dict]:
    """→ (마스킹 문자열, {종류: 건수})"""
    found: dict = {}
    if not text:
        return text, found

    def sub(kind):
        def repl(m):
            if kind == "card" and not _luhn(re.sub(r"\D", "", m.group(0))):
                return m.group(0)
            found[kind] = found.get(kind, 0) + 1
            return f"[{kind.upper()}]"
        return repl

    for kind, pat in PII:
        text = pat.sub(sub(kind), text)
    return text, found


def mask_messages(messages: list[dict]) -> tuple[list[dict], dict]:
    total: dict = {}
    out = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            c, f = mask_pii(c)
            for k, v in f.items():
                total[k] = total.get(k, 0) + v
        out.append({**m, "content": c})
    return out, total
