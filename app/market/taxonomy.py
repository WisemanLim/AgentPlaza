"""마켓 분류 3축 (PRD 17.1~17.4): 업무(W01~W19) · 업종(KSIC 대분류) · 도메인(생태계). 카테고리 slug = 업종 → 업무."""

WORK = {
    "W01": "대화·어시스턴트", "W02": "오케스트레이션", "W03": "지식·RAG", "W04": "워크플로·자동화",
    "W05": "플레이그라운드·평가", "W06": "가드레일·준법", "W07": "보안 운영", "W08": "취약점·공급망",
    "W09": "신원·접근·권한", "W10": "관측·모니터링", "W11": "AI/에이전트 보안", "W12": "모델·LLMOps",
    "W13": "인사·채용", "W14": "생산·수요·품질", "W15": "식품안전(HACCP)", "W16": "물류·통관",
    "W17": "문서·데이터 처리", "W18": "플랫폼·마켓", "W19": "공통 유틸",
}
INDUSTRY = {"-": "전업종", "J": "정보통신", "C": "제조", "H": "운수·창고", "O": "공공행정", "K": "금융",
            "M": "전문·과학기술", "G": "도소매"}
DOMAIN = {"common": "공통", "security": "보안", "llmops": "LLMOps", "governance": "거버넌스·준법", "platform": "플랫폼",
          "hr": "인사", "manufacturing": "제조", "food-safety": "식품안전", "logistics-customs": "물류·통관",
          "docintel": "문서지능"}
# 카테고리 트리(17.4 예시 준용): slug → (업종, 업무 목록, 이름)
CATEGORIES = {
    "common-assistant": ("-", ["W01"], "대화·어시스턴트"), "common-rag": ("-", ["W03"], "지식·RAG"),
    "common-workflow": ("-", ["W04"], "워크플로·자동화"), "common-playground": ("-", ["W05"], "플레이그라운드·평가"),
    "common-utility": ("-", ["W19"], "공통 유틸"), "common-docintel": ("-", ["W17"], "문서·데이터 처리"),
    "ict-security-soc": ("J", ["W07"], "보안운영"), "ict-security-vuln": ("J", ["W08"], "취약점·공급망"),
    "ict-security-iam": ("J", ["W09"], "신원·접근"), "ict-observability": ("J", ["W10"], "관측·모니터링"),
    "ict-ai-security": ("J", ["W11"], "AI·에이전트 보안"), "ict-governance": ("J", ["W06"], "거버넌스·준법"),
    "ict-llmops": ("J", ["W12"], "모델·LLMOps"), "ict-platform": ("J", ["W02", "W18"], "플랫폼·마켓"),
    "mfg-dopq": ("C", ["W14"], "생산·수요·품질"), "mfg-food-haccp": ("C", ["W15"], "식품안전(HACCP)"),
    "logi-customs": ("H", ["W16"], "물류·통관"), "hr-recruiting": ("M", ["W13"], "인사·채용"),
}


def tree() -> list[dict]:
    out = []
    for code, name in INDUSTRY.items():
        children = [{"slug": slug, "name": n, "work": w} for slug, (ind, w, n) in CATEGORIES.items() if ind == code]
        if children:
            out.append({"industry": code, "name": name, "children": children})
    return out
