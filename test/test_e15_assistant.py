"""Epic 15 — 어시스턴트 확장 (D3-04 파일·멀티모달, D3-05 메모리·개인화, D3-06 지식(RAG), D1-07 임베딩·재정렬, NFR-L2·C3).

임베딩은 mock 해시 임베딩(결정적), 채팅·비전은 mock 공급자. 받은 메시지는 seen 에 남겨 문맥 주입을 검증한다.
"""
import json
from datetime import timedelta

import pytest

from app import db as appdb
from app.db import utcnow
from app.llm.providers import MockProvider
from app.llm.router import get_router
from app.models import LlmModel, LlmRoute, StoredFile
from app.assistant import files as attachments
from helpers import auth, make_user

PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a4170000000049454e44ae426082")


def pdf_bytes(text: str) -> bytes:
    """텍스트 한 줄짜리 최소 PDF(ASCII) — pypdf 추출 시험용."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)


@pytest.fixture
def llm(client, monkeypatch):
    seen = []
    default = MockProvider.responder

    def responder(model, req):
        seen.append((model, req.messages))
        return default(model, req)

    monkeypatch.setattr(MockProvider, "responder", staticmethod(responder))
    with appdb.SessionLocal() as s:  # 시험은 결정적 mock 만(호스트 Ollama 가 보여도 쓰지 않는다)
        for alias, target in (("plaza/chat", "mock/echo"), ("plaza/orchestrator", "mock/echo"),
                              ("plaza/embed", "mock/embed"), ("plaza/vision", "mock/vision")):
            s.merge(LlmRoute(alias=alias, targets=[target]))
        s.merge(LlmModel(id="mock/public-embed", provider="mock", model_id="embed", local=False, context=8192,
                         tool_call=False, vision=False, license="test", kind="embedding"))
        s.merge(LlmRoute(alias="t/public-embed", targets=["mock/public-embed"]))
        s.commit()
    return seen


def stream(client, token, **body):
    res = client.post("/api/chat/stream", json=body, headers=auth(token))
    assert res.status_code == 200, res.text
    return [json.loads(ln[6:]) for ln in res.text.splitlines() if ln.startswith("data: ")]


def text_of(events):
    return "".join(e.get("delta", "") for e in events if e["type"] == "TEXT_MESSAGE_CONTENT")


def system_text(messages):
    return "\n".join(m["content"] for m in messages if m["role"] == "system" and isinstance(m["content"], str))


# ---------------- D1-07 ----------------

def test_e15_01_embeddings_api_and_policy(client, sup_token, llm):
    res = client.post("/v1/embeddings", json={"model": "plaza/embed", "input": ["휴가 규정", "휴가 규정"]},
                      headers=auth(sup_token) | {"X-Plaza-Data-Class": "L3"})
    assert res.status_code == 200 and res.headers["x-plaza-model"] == "mock/embed"
    data = res.json()["data"]
    assert len(data) == 2 and len(data[0]["embedding"]) == 256 and data[0]["embedding"] == data[1]["embedding"]
    denied = client.post("/v1/embeddings", json={"model": "t/public-embed", "input": "x"},
                         headers=auth(sup_token) | {"X-Plaza-Data-Class": "L2"})
    assert denied.status_code == 403  # 등급 규칙은 임베딩에도(NFR-L3)
    assert client.post("/v1/embeddings", json={"model": "plaza/chat", "input": "x"},
                       headers=auth(sup_token)).status_code == 404  # 채팅 모델은 임베딩 대상 아님


def test_e15_02_rerank_cosine_fallback(client, sup_token, llm):
    docs = ["주식 시장 동향 보고", "연차 휴가 신청 절차와 휴가 일수", "점심 메뉴 추천"]
    res = client.post("/v1/rerank", json={"query": "휴가 신청 절차", "documents": docs, "top_n": 2, "return_documents": True},
                      headers=auth(sup_token))
    body = res.json()
    assert res.status_code == 200 and body["model"] == "mock/embed" and len(body["results"]) == 2
    assert body["results"][0]["index"] == 1 and body["results"][0]["document"] == docs[1]
    assert body["results"][0]["relevance_score"] >= body["results"][1]["relevance_score"]


# ---------------- D3-06 ----------------

def make_collection(client, token, **kw):
    res = client.post("/api/kb/collections", json={"name": "사내 규정", **kw}, headers=auth(token))
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_e15_03_ingest_txt_md_pdf_and_reject_binary(client, sup_token, llm):
    cid = make_collection(client, sup_token)
    files = [("files", ("leave.txt", "연차 휴가는 입사 1년 후 15일이 주어진다.\n\n병가는 별도로 연 10일까지 쓴다.".encode(), "text/plain")),
             ("files", ("security.md", "# 보안\n\n노트북은 퇴근 시 잠금 서랍에 보관한다.".encode(), "text/markdown")),
             ("files", ("travel.pdf", pdf_bytes("Business travel per diem is 50000 KRW"), "application/pdf")),
             ("files", ("tool.exe", b"MZ\x90\x00binary", "application/octet-stream"))]
    res = client.post(f"/api/kb/collections/{cid}/documents", files=files, headers=auth(sup_token))
    docs = {d["filename"]: d for d in res.json()}
    assert res.status_code == 201 and docs["leave.txt"]["status"] == "ready" and docs["leave.txt"]["chunks"] >= 1
    assert docs["travel.pdf"]["status"] == "ready" and docs["tool.exe"]["status"] == "failed"
    hits = client.post("/api/kb/search", json={"collections": [cid], "query": "연차 휴가 며칠?"}, headers=auth(sup_token)).json()
    assert hits["results"][0]["document"] == "leave.txt" and hits["results"][0]["n"] == 1
    pdf = client.post("/api/kb/search", json={"collections": [cid], "query": "travel per diem"}, headers=auth(sup_token)).json()
    assert pdf["results"][0]["document"] == "travel.pdf" and "50000" in pdf["results"][0]["text"]
    listed = client.get(f"/api/kb/collections/{cid}/documents", headers=auth(sup_token)).json()
    assert len(listed) == 4
    assert client.delete(f"/api/kb/collections/{cid}/documents/{docs['tool.exe']['id']}", headers=auth(sup_token)).status_code == 200


def test_e15_04_chat_with_knowledge_citations(client, sup_token, llm):
    cid = make_collection(client, sup_token)
    client.post(f"/api/kb/collections/{cid}/documents", headers=auth(sup_token),
                files=[("files", ("leave.txt", "연차 휴가는 입사 1년 후 15일이 주어진다.".encode(), "text/plain"))])
    events = stream(client, sup_token, message="연차 휴가는 며칠이야?", knowledge=[cid])
    cites = next(e["value"] for e in events if e.get("name") == "citations")
    assert cites[0]["n"] == 1 and cites[0]["document"] == "leave.txt" and "15일" in cites[0]["snippet"]
    sent = system_text(llm[-1][1])
    assert "[1] (leave.txt)" in sent and "cite them like [1]" in sent  # 근거 블록이 생성 모델에 들어갔다
    other = make_user(client, sup_token, "u15@example.test")[1]
    res = client.post("/api/chat/stream", json={"message": "x", "knowledge": [cid]}, headers=auth(other))
    assert res.status_code == 404  # 남의 비공개 컬렉션


def test_e15_05_collection_access(client, sup_token, llm):
    _, user = make_user(client, sup_token, "u15b@example.test")
    private = make_collection(client, sup_token)
    shared = make_collection(client, sup_token, name="공용", shared=True)
    ids = {c["id"] for c in client.get("/api/kb/collections", headers=auth(user)).json()}
    assert shared in ids and private not in ids
    assert client.post("/api/kb/collections", json={"name": "x", "shared": True}, headers=auth(user)).status_code == 403
    assert client.delete(f"/api/kb/collections/{shared}", headers=auth(user)).status_code == 403
    assert client.post(f"/api/kb/collections/{shared}/documents", headers=auth(user),
                       files=[("files", ("a.txt", b"x", "text/plain"))]).status_code == 403


# ---------------- D3-05 ----------------

def test_e15_06_memory_instructions_facts_and_erasure(client, sup_token, llm):
    h = auth(sup_token)
    assert client.post("/api/me/memories", json={"kind": "instruction", "content": "항상 존댓말로 짧게 답해"}, headers=h).status_code == 201
    events = stream(client, sup_token, message="기억해: 나는 채식주의자야")
    assert "기억했습니다" in text_of(events) and any(e.get("value") == "memory" for e in events)
    events = stream(client, sup_token, message="점심 메뉴 추천해줘")
    sent = system_text(llm[-1][1])
    assert "항상 존댓말로 짧게 답해" in sent and "나는 채식주의자야" in sent
    stream(client, sup_token, message="기억해: 내 주민번호는 900101-1234567")  # 최소화: 민감 형식은 마스킹 저장
    items = client.get("/api/me/memories", headers=h).json()["items"]
    assert any("[RRN]" in m["content"] for m in items) and not any("1234567" in m["content"] for m in items)
    assert "1개를 잊었습니다" in text_of(stream(client, sup_token, message="잊어줘: 채식주의자"))
    client.put("/api/me/memory-settings", json={"memory_enabled": False}, headers=h)
    stream(client, sup_token, message="점심 메뉴 추천해줘")
    assert "존댓말" not in system_text(llm[-1][1])  # 꺼지면 주입 안 함
    _, other = make_user(client, sup_token, "u15c@example.test")
    mid = items[0]["id"]
    assert client.delete(f"/api/me/memories/{mid}", headers=auth(other)).status_code == 404
    out = client.delete("/api/me/memories", headers=h).json()
    assert out["deleted"] == 2 and client.get("/api/me/memories", headers=h).json()["items"] == []
    assert client.get("/api/audit?action=memory.purged", headers=h).json()


# ---------------- D3-04 ----------------

def upload(client, token, name, data, mime):
    return client.post("/api/files", files={"file": (name, data, mime)}, headers=auth(token))


def test_e15_07_document_and_image_attachments(client, sup_token, llm):
    doc = upload(client, sup_token, "회의록.md", "## 결정\n\n다음 배포는 금요일 오후 3시".encode(), "text/markdown").json()
    assert doc["kind"] == "document"
    events = stream(client, sup_token, message="첨부한 회의록의 배포 일정은?", attachments=[doc["id"]])
    assert "금요일 오후 3시" in system_text(llm[-1][1]) and text_of(events)
    img = upload(client, sup_token, "chart.png", PNG, "image/png").json()
    assert img["kind"] == "image"
    events = stream(client, sup_token, message="이 그림을 설명해줘", attachments=[img["id"]])
    model, messages = llm[-1]
    parts = messages[-1]["content"]
    assert any(e.get("value") == "vision" for e in events)
    assert isinstance(parts, list) and parts[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert upload(client, sup_token, "run.exe", b"MZ", "application/octet-stream").status_code == 422
    _, other = make_user(client, sup_token, "u15d@example.test")
    assert client.post("/api/chat/stream", json={"message": "x", "attachments": [img["id"]]}, headers=auth(other)).status_code == 404
    assert client.get(f"/api/files/{img['id']}/content", headers=auth(other)).status_code == 404
    assert client.get(f"/api/files/{img['id']}/content", headers=auth(sup_token)).content == PNG


def test_e15_08_vision_without_vision_model(client, sup_token, llm):
    with appdb.SessionLocal() as s:
        s.get(LlmModel, "mock/vision").enabled = False
        s.commit()
    img = upload(client, sup_token, "a.png", PNG, "image/png").json()
    events = stream(client, sup_token, message="설명해줘", attachments=[img["id"]])
    assert any(e.get("name") == "llm_unavailable" for e in events) and any(e["type"] == "RUN_ERROR" for e in events)


def test_e15_09_file_retention_purge(client, sup_token, llm):
    """NFR-C3: 파일 보존 기간(설정 retention_file_days) 지나면 본문·메타 파기."""
    f = upload(client, sup_token, "old.txt", b"old", "text/plain").json()
    with appdb.SessionLocal() as s:
        s.get(StoredFile, f["id"]).created_at = utcnow() - timedelta(days=91)
        s.commit()
    assert client.post("/api/admin/retention/run", headers=auth(sup_token)).status_code == 200
    assert not attachments.path_of(f["id"]).exists()
    assert client.get("/api/files", headers=auth(sup_token)).json() == []


def test_e15_10_local_only_no_public_keys(client, sup_token, llm):
    """NFR-L2: 퍼블릭 키 0개로 RAG·메모리·첨부가 모두 동작(위 시험) — 공급자 목록에 퍼블릭이 없다."""
    assert set(get_router().providers) <= {"mock", "ollama"}
