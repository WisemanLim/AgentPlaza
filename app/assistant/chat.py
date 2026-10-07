"""AI Assistant 대화 실행 (D3-01·D3-03): AG-UI 이벤트를 큐로 받아 SSE 로 흘린다.

- 라우팅 가능한 에이전트가 있으면 Orchestrator 로(도구·승인 카드 이벤트 포함).
- 없으면 Orchestrator 없이 단일 LLM 채팅으로 강등(PRD 4.2) — 같은 이벤트 형식.
- P1(D3-04~06): "기억해:" 명령·맞춤지침/기억 주입, 지식 컬렉션 검색 → 인용(CUSTOM citations),
  문서 첨부는 문맥으로, 이미지 첨부는 비전 별칭(plaza/vision)으로.
"""
import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal, utcnow
from app.llm.router import Caller
from app.assistant import agent as assistant_agent
from app.assistant import files as attachments
from app.assistant import memory
from app.knowledge import service as kb
from app.models import ChatSession, Message, RunEvent
from app.orchestrator import service as orchestrator
from app.services import registry


def history(db: Session, session_id: str, limit: int) -> list[dict]:
    rows = db.execute(select(Message).where(Message.session_id == session_id, Message.kind == "text")
                      .order_by(Message.id.desc()).limit(limit)).scalars().all()
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def _title(message: str) -> str:
    first = message.strip().splitlines()[0] if message.strip() else "새 대화"
    return first[:40] + ("…" if len(first) > 40 else "")


_RUNNING: set = set()  # 클라이언트가 끊겨도 실행을 끝까지(참조 유지)
END = {"type": "CUSTOM", "name": "stream_end"}


def frame(seq: int, ev: dict) -> str:
    return f"id: {seq}\ndata: " + json.dumps(ev, ensure_ascii=False, default=str) + "\n\n"


async def run(*, principal: str, role: str, message: str, session_id: str | None, agent_scope: str | None,
              data_class: str, attachment_ids: list[str] | None = None,
              knowledge: list[str] | None = None, stream_id: str | None = None) -> AsyncIterator[str]:
    """이벤트마다 seq 를 매겨 기록(run_events)하고 SSE id 로 내보낸다 — 끊기면 /api/chat/streams/{id}?after=seq 로 재개."""
    queue: asyncio.Queue = asyncio.Queue()
    stream_id = stream_id or str(uuid.uuid4())
    counter = {"seq": 0}

    async def emit(ev: dict) -> None:
        counter["seq"] += 1
        seq = counter["seq"]
        with SessionLocal() as own:  # 워커 세션과 독립(트랜잭션 경합 없이 바로 보이게)
            own.add(RunEvent(stream_id=stream_id, owner=principal, seq=seq, data=json.loads(json.dumps(ev, default=str))))
            own.commit()
        await queue.put((seq, ev))

    async def worker() -> None:
        with SessionLocal() as db:
            try:
                s = db.get(ChatSession, session_id) if session_id else None
                if s is None or s.owner != principal:
                    s = ChatSession(id=str(uuid.uuid4()), owner=principal, title=_title(message),
                                    agent_scope=agent_scope, data_class=data_class)
                    db.add(s)
                scope = agent_scope or s.agent_scope
                past = history(db, s.id, settings.chat_history_turns * 2)
                files = attachments.owned(db, principal, attachment_ids or [])
                s.updated_at = utcnow()
                db.add(Message(session_id=s.id, role="user", content=message,
                               meta={"attachments": [{"id": f.id, "filename": f.filename, "kind": f.kind}
                                                     for f in files]} if files else {}))
                db.commit()
                await emit({"type": "CUSTOM", "name": "session", "value": {"id": s.id, "title": s.title,
                                                                            "agent_scope": scope}})
                if (reply := memory.command(db, principal, message)) is not None:  # "기억해:"·"잊어줘:"(D3-05)
                    await _reply(db, s, reply, emit, "memory")
                    return
                context, sources = await _context(db, principal, message, files, knowledge or [])
                if sources:
                    await emit({"type": "CUSTOM", "name": "citations", "value": [
                        {k: x[k] for k in ("n", "document", "collection", "score")} | {"snippet": x["text"][:300]}
                        for x in sources]})
                if any(f.kind == "image" for f in files):  # 이미지는 비전 모델 단독 답변(D3-04)
                    await _degraded_chat(db, s, message, past, principal, emit, context=context, images=files)
                elif registry.routable(db, scope, viewer=(principal, role)):
                    await orchestrator.start(db, principal=principal, role=role, message=message, session_id=s.id,
                                             agent_scope=scope, emit=emit, history=past, data_class=s.data_class,
                                             context=context)
                else:
                    await _degraded_chat(db, s, message, past, principal, emit, context=context)
            except Exception as exc:  # noqa: BLE001 — 스트림 소비자에게 RUN_ERROR 로 알린다
                await emit({"type": "RUN_ERROR", "message": f"{type(exc).__name__}: {exc}"})
            finally:
                await emit(END)
                await queue.put(None)

    await emit({"type": "CUSTOM", "name": "stream", "value": {"id": stream_id}})
    task = asyncio.create_task(worker())
    _RUNNING.add(task)
    task.add_done_callback(_RUNNING.discard)
    while (item := await queue.get()) is not None:  # 클라이언트가 끊기면 여기서 멈추고 워커는 계속 돈다
        yield frame(*item)


async def replay(stream_id: str, owner: str, after: int, *, poll: float = 0.3, timeout: float = 600) -> AsyncIterator[str]:
    """재연결(NFR-P4): after 다음 이벤트부터 기록을 흘리고, 실행이 진행 중이면 stream_end 까지 따라간다."""
    deadline = asyncio.get_running_loop().time() + timeout
    last = after
    while asyncio.get_running_loop().time() < deadline:
        with SessionLocal() as db:
            rows = list(db.execute(select(RunEvent).where(RunEvent.stream_id == stream_id, RunEvent.owner == owner,
                                                          RunEvent.seq > last).order_by(RunEvent.seq)).scalars())
        for r in rows:
            last = r.seq
            yield frame(r.seq, r.data)
            if r.data.get("type") == "CUSTOM" and r.data.get("name") == "stream_end":
                return
        await asyncio.sleep(poll)


def stream_exists(db: Session, stream_id: str, owner: str) -> bool:
    return db.execute(select(RunEvent.id).where(RunEvent.stream_id == stream_id, RunEvent.owner == owner).limit(1)).first() is not None


async def _context(db: Session, principal: str, message: str, files: list, knowledge: list[str]) -> tuple[str | None, list]:
    """시스템 문맥 = 맞춤지침·기억 + 지식 근거(인용 번호) + 첨부 문서 텍스트."""
    parts, sources = [], []
    if mem := memory.context(db, principal, message):
        parts.append(mem)
    if knowledge:
        cols = [kb.get_visible(db, cid, principal) for cid in knowledge]
        sources = await kb.search(db, cols, message, principal=principal)
        if sources:
            parts.append(kb.CITE + kb.context_block(sources))
    if doc := attachments.document_context(files):
        parts.append(doc)
    return ("\n\n".join(parts) if parts else None), sources


async def _reply(db: Session, s: ChatSession, text: str, emit, mode: str) -> None:
    run_id = str(uuid.uuid4())
    await emit({"type": "RUN_STARTED", "threadId": s.id, "runId": run_id})
    await emit({"type": "CUSTOM", "name": "mode", "value": mode})
    await orchestrator._emit_text(emit, f"msg_{run_id[:8]}", text)
    await emit({"type": "RUN_FINISHED", "threadId": s.id, "runId": run_id})
    db.add(Message(session_id=s.id, role="assistant", kind="text", content=text))
    db.commit()


async def _degraded_chat(db: Session, s: ChatSession, message: str, past: list[dict], principal: str, emit,
                         context: str | None = None, images: list | None = None) -> None:
    """Orchestrator·에이전트 없이 Assistant 에이전트(pydantic-ai, PRD Q2)만으로 대화(강등 모드). 이미지가 있으면 비전 별칭."""
    run_id = str(uuid.uuid4())
    await emit({"type": "RUN_STARTED", "threadId": s.id, "runId": run_id})
    blocked, _ = await orchestrator.input_guard(db, message, principal, emit, f"session:{s.id}")
    if blocked:  # 가드레일(D9-06): LLM 단독 모드에도 같은 입력 필터
        await orchestrator._emit_text(emit, f"msg_{run_id[:8]}", orchestrator.BLOCKED)
        await emit({"type": "RUN_FINISHED", "threadId": s.id, "runId": run_id})
        db.add(Message(session_id=s.id, role="assistant", kind="text", content=orchestrator.BLOCKED))
        db.commit()
        return
    parts = attachments.image_contents(images or [])
    await emit({"type": "CUSTOM", "name": "mode", "value": "vision" if parts else "llm-only"})
    text = await assistant_agent.converse(db, message=[message, *parts] if parts else message, past=past, context=context,
                                          level=s.data_class, caller=Caller(principal=principal), emit=emit,
                                          msg_id=f"msg_{run_id[:8]}", alias="plaza/vision" if parts else "plaza/chat")
    kind = "text"
    if text is None:
        kind, text = "error", "LLM 을 사용할 수 없습니다 / the LLM is unavailable"
        await emit({"type": "RUN_ERROR", "message": text})
    else:
        await emit({"type": "RUN_FINISHED", "threadId": s.id, "runId": run_id})
    db.add(Message(session_id=s.id, role="assistant", kind=kind, content=text))
    db.commit()


def purge_expired(db: Session) -> int:
    """보존 기간이 지난 대화(마지막 갱신 기준)와 첨부 파일(파일 보존 기간)을 파기한다(NFR-C3). 이벤트 기록은 1일."""
    attachments.purge_expired(db)
    db.execute(delete(RunEvent).where(RunEvent.created_at < utcnow() - timedelta(days=1)))
    from app.models import TraceSpan
    db.execute(delete(TraceSpan).where(TraceSpan.start < utcnow() - timedelta(days=settings.obs_retention_days)))
    db.commit()
    from app.services import sysconfig
    cutoff = utcnow() - timedelta(days=sysconfig.get(db, "retention_chat_days"))
    ids = [r for (r,) in db.execute(select(ChatSession.id).where(ChatSession.updated_at < cutoff))]
    if ids:
        db.execute(delete(Message).where(Message.session_id.in_(ids)))
        db.execute(delete(ChatSession).where(ChatSession.id.in_(ids)))
        db.commit()
    return len(ids)
