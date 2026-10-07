"""큐레이션 카탈로그 생성(`plaza market-build`): 템플릿에서 결정적으로 산출물 zip + catalog.json 을 만든다.

정적 git+JSON 카탈로그(P0)의 원본이며, 산출물 sha256 을 카탈로그에 고정한다(설치 시 대조).
"""
import hashlib
import json
from pathlib import Path

from app.agentspec import generator as gen
from app.agentspec.validate import validate_manifest

# (id, type, 이름 ko/en, 설명 ko/en, 카테고리, 업종, 업무, 도메인, 태그)
SEEDS = [
    ("board", "app", ("사내 게시판", "Board"), ("게시글 등록·조회·삭제 화면과 API", "Posts CRUD with a UI"),
     ["common-utility"], "-", "W19", "common", ["board", "crud"]),
    ("knowledge-rag", "rag", ("지식 검색(RAG)", "Knowledge RAG"), ("문서 수집·BM25 검색·인용 답변", "Ingest, search and cite"),
     ["common-rag"], "-", "W03", "common", ["rag", "search", "citation"]),
    ("pii-guard", "reviewer", ("개인정보 검토", "PII Guard"), ("PII·프롬프트 인젝션 검토와 마스킹", "PII and injection review"),
     ["ict-governance"], "J", "W06", "governance", ["pii", "guardrail", "isms-p"]),
    ("calculator", "execution", ("계산기", "Calculator"), ("안전한 산술식 계산(AST 화이트리스트)", "Safe arithmetic"),
     ["common-utility"], "-", "W19", "common", ["math"]),
    ("user-memory", "memory", ("사용자 기억", "User Memory"), ("사실·선호 기억과 삭제권", "Facts with right to erasure"),
     ["common-assistant"], "-", "W01", "common", ["memory", "personalization"]),
    ("ops-approval", "hitl", ("승인 작업 실행", "Ops Approval"), ("휴먼 승인 후에만 실행되는 운영 작업", "Ops actions after approval"),
     ["common-workflow"], "-", "W04", "platform", ["hitl", "approval"]),
    ("text-tools", "service", ("텍스트 도구", "Text Tools"), ("변환·단어 수·요약(LLM 있으면 사용)", "Transform, count, summarize"),
     ["common-docintel"], "-", "W17", "docintel", ["text", "summarize"]),
    ("http-tool", "tool-proxy", ("HTTP 도구 프록시", "HTTP Tool Proxy"), ("외부 REST API 1개를 도구로", "Wrap one REST API"),
     ["common-utility"], "-", "W19", "common", ["http", "proxy"]),
]
VERSION = "1.0.0"


def build(out: Path, key: bytes | None = None) -> dict:
    """key(Ed25519 PEM)를 주면 산출물을 서명 패키지로 만든다(D4-06). 키는 저장소에 두지 않는다."""
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    listings = []
    for aid, type_, (ko, en), (dko, den), cats, industry, work, domain, tags in SEEDS:
        m = gen.build_manifest(aid, en, type_, description=dko, version=VERSION, publisher="agentplaza")
        m["metadata"].update({"displayName": {"ko": ko, "en": en}, "description": {"ko": dko, "en": den},
                              "categories": cats, "tags": tags,
                              "publisher": {"id": "agentplaza", "name": "AgentPlaza", "url": "https://agentplaza.local"}})
        m["spec"].update({"industry": industry, "work": work})
        assert validate_manifest(m) == [], aid
        signature = None
        if key:
            from app.supplychain.publish import publish
            data, kid, _ = publish(gen.render_files(m), key)
            signature = {"keyId": kid, "format": "cosign-ed25519"}
        else:
            data = gen.pack(gen.render_files(m))
        rel = f"artifacts/{aid}-{VERSION}.zip"
        (out / rel).write_bytes(data)
        spec = m["spec"]
        listings.append({
            "id": aid, "version": VERSION, "type": type_, "name": {"ko": ko, "en": en}, "description": {"ko": dko, "en": den},
            "categories": cats, "industry": industry, "work": work, "domain": domain, "tags": tags,
            "publisher": {"id": "agentplaza", "name": "AgentPlaza", "verified": True}, "license": m["metadata"]["license"],
            "trust": "official", "pricing": "free",
            "capabilities": [c["verb"] for c in spec["capabilities"]],
            "approval": [c["verb"] for c in spec["capabilities"] if c.get("humanApprovalRequired")],
            "required_env": spec.get("env", {}).get("required", []),
            "permissions": {"egress": spec.get("permissions", {}).get("network", {}).get("egress", []),
                            "docker": False, "dataClassification": spec.get("governance", {}).get("dataClassification")},
            "hasFrontend": bool(spec.get("ui", {}).get("hasFrontend")),
            "compat": spec.get("compat", {}),
            "source": {"type": "zip", "path": rel, "sha256": hashlib.sha256(data).hexdigest()},
            **({"signature": signature} if signature else {}),
        })
    catalog = {"schema": "agentplaza/catalog/v1", "name": "AgentPlaza 기본 카탈로그", "listings": listings}
    (out / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return catalog
