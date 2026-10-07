"""{{AGENT_NAME}} — rag 유형: 문서 수집·검색(SQLite FTS5 BM25)·근거 있는 답변과 인용."""
import re

from agentplaza_sdk import Agent, CapabilityError, create_app
from agentplaza_sdk.db import connect, rows

agent = Agent.from_manifest("agent.yaml")
CHUNK = 600


def _chunks(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out: list[str] = []
    for p in paras:
        out += [p[i:i + CHUNK] for i in range(0, len(p), CHUNK)]
    return out or [text[:CHUNK]]


def _fts_query(q: str) -> str:
    terms = re.findall(r"\w+", q)
    if not terms:
        raise CapabilityError("query has no searchable terms")
    return " OR ".join(f'"{t}"' for t in terms)


def _search(con, query: str, k: int) -> list[dict]:
    return rows(con.execute(
        "SELECT doc_id, title, chunk_no, snippet(chunks, 3, '[', ']', '…', 16) AS snippet, bm25(chunks) AS score "
        "FROM chunks WHERE chunks MATCH ? ORDER BY score LIMIT ?", (_fts_query(query), k)))


@agent.capability("ingest")
def ingest(payload: dict, ctx):
    with connect(ctx) as con:
        doc_id = payload.get("doc_id") or f"doc-{con.execute('SELECT count(*) FROM documents').fetchone()[0] + 1}"
        con.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        con.execute("INSERT OR REPLACE INTO documents (doc_id, title) VALUES (?, ?)", (doc_id, payload["title"]))
        parts = _chunks(payload["text"])
        con.executemany("INSERT INTO chunks (doc_id, title, chunk_no, body) VALUES (?, ?, ?, ?)",
                        [(doc_id, payload["title"], i, c) for i, c in enumerate(parts)])
    return {"doc_id": doc_id, "chunks": len(parts)}


@agent.capability("search")
def search(payload: dict, ctx):
    with connect(ctx) as con:
        return _search(con, payload["query"], int(payload.get("k", 5)))


@agent.capability("ask")
async def ask(payload: dict, ctx):
    with connect(ctx) as con:
        hits = _search(con, payload["question"], int(payload.get("k", 3)))
    citations = [{"doc_id": h["doc_id"], "title": h["title"], "chunk": h["chunk_no"]} for h in hits]
    if not hits:
        return {"answer": None, "citations": [], "note": "no supporting documents"}
    context = "\n\n".join(f"[{i + 1}] {h['snippet']}" for i, h in enumerate(hits))
    if ctx.llm.available:
        answer = await ctx.llm.chat([
            {"role": "system", "content": "Answer only from the numbered context and cite like [1]."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {payload['question']}"}])
        return {"answer": answer, "citations": citations, "source": "llm"}
    return {"answer": context, "citations": citations, "source": "extractive"}


app = create_app(agent)
