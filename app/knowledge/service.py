"""지식 서비스 (D3-06): 수집(추출·청크·임베딩) · 검색(코사인 후보 → 재정렬) · 접근 제어.

임베딩은 게이트웨이 별칭 plaza/embed(로컬 bge-m3, 시험은 mock) — 컬렉션 등급으로 호출하므로 L2 이상은 로컬 모델만(NFR-L3).
퍼블릭 키가 0개여도 전부 동작한다(NFR-L2). 임베딩은 JSON 으로 저장하고 파이썬 코사인으로 찾는다(pgvector 색인은 규모 확장 시).
"""
import hashlib
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.knowledge import extract
from app.llm.router import Caller, cosine, get_router
from app.models import KbChunk, KbCollection, KbDocument

EMBED_BATCH = 32


class KnowledgeError(ValueError):
    pass


def visible(db: Session, owner: str) -> list[KbCollection]:
    return list(db.execute(select(KbCollection).where(or_(KbCollection.owner == owner, KbCollection.shared.is_(True)))
                           .order_by(KbCollection.created_at)).scalars())


def get_visible(db: Session, cid: str, owner: str) -> KbCollection:
    c = db.get(KbCollection, cid)
    if c is None or (c.owner != owner and not c.shared):
        raise KnowledgeError("컬렉션 없음 / collection not found")
    return c


async def ingest(db: Session, c: KbCollection, filename: str, data: bytes, mime: str | None, actor: str) -> KbDocument:
    kind = extract.mime_of(filename, mime)
    doc = KbDocument(id=str(uuid.uuid4()), collection_id=c.id, filename=filename[:255], mime=kind, bytes=len(data),
                     sha256=hashlib.sha256(data).hexdigest(), created_by=actor)
    db.add(doc)
    try:
        pieces = extract.chunks(extract.text_of(data, kind))
        if not pieces:
            raise extract.ExtractError("텍스트 없음 / no text")
        vectors, model = [], ""
        for i in range(0, len(pieces), EMBED_BATCH):
            vecs, meta = await get_router().embed(db, "plaza/embed", pieces[i:i + EMBED_BATCH], level=c.data_class,
                                                  caller=Caller(principal=actor))
            vectors += vecs
            model = meta.model
        for n, (text, vec) in enumerate(zip(pieces, vectors, strict=True)):
            db.add(KbChunk(document_id=doc.id, collection_id=c.id, ord=n, text=text, embedding=vec, model=model))
        doc.chunks, doc.status = len(pieces), "ready"
    except Exception as exc:  # noqa: BLE001 — 실패도 문서 행으로 남겨 사용자가 본다
        doc.status, doc.error = "failed", f"{type(exc).__name__}: {exc}"[:500]
    db.commit()
    return doc


async def search(db: Session, collections: list[KbCollection], query: str, *, top_n: int = 5, candidates: int = 20,
                 principal: str | None = None) -> list[dict]:
    """→ [{n, score, text, document, document_id, collection, ord}] — n 은 인용 번호([1], [2] …)."""
    if not collections or not query.strip():
        return []
    level = max((c.data_class for c in collections), key=["L0", "L1", "L2", "L3"].index)
    ids = [c.id for c in collections]
    rows = list(db.execute(select(KbChunk).where(KbChunk.collection_id.in_(ids))).scalars())
    if not rows:
        return []
    qv, _ = await get_router().embed(db, "plaza/embed", [query], level=level, caller=Caller(principal=principal))
    pool = sorted(rows, key=lambda r: -cosine(qv[0], r.embedding))[:candidates]
    ranked, _ = await get_router().rerank(db, query, [r.text for r in pool], top_n=top_n, level=level,
                                          caller=Caller(principal=principal))
    docs = {d.id: d for d in db.execute(select(KbDocument).where(KbDocument.id.in_({r.document_id for r in pool}))).scalars()}
    names = {c.id: c.name for c in collections}
    out = []
    for n, r in enumerate(ranked, start=1):
        ch = pool[r["index"]]
        out.append({"n": n, "score": round(r["relevance_score"], 4), "text": ch.text, "ord": ch.ord,
                    "document_id": ch.document_id, "document": docs[ch.document_id].filename,
                    "collection": names.get(ch.collection_id)})
    return out


def context_block(sources: list[dict]) -> str:
    """답변 생성용 근거 블록. 모델은 [n] 으로 인용한다."""
    return "\n\n".join(f"[{s['n']}] ({s['document']}) {s['text'][:1200]}" for s in sources)


CITE = ("Answer using ONLY the numbered sources below when they are relevant, and cite them like [1] or [2]. "
        "If the sources do not contain the answer, say so. Reply in the user's language.\n\nSources:\n")
