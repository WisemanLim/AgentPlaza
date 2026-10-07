"""Assistant 채팅·세션 API (D3-01·D3-02·D3-03, UI C01·C02·C05)."""
import json
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.assistant import chat
from app.assistant import files as attachments
from app.core.deps import Principal, require_admin, require_user
from app.db import SessionLocal, get_db, utcnow
from app.knowledge import service as kb
from app.llm.router import parse_data_class
from app.models import ChatSession, Message
from app.services import audit

router = APIRouter(tags=["assistant"], dependencies=[Depends(require_user)])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    session_id: str | None = None
    agent_scope: str | None = None
    data_class: str | None = None
    attachments: list[str] = Field(default_factory=list, max_length=10)  # /api/files 로 올린 id(D3-04)
    knowledge: list[str] = Field(default_factory=list, max_length=10)  # 지식 컬렉션 id(D3-06)


class SessionIn(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    agent_scope: str | None = None
    folder: str | None = Field(default=None, max_length=100)


class SessionPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    folder: str | None = Field(default=None, max_length=100)
    archived: bool | None = None


def session_out(s: ChatSession, count: int | None = None) -> dict:
    out = {"id": s.id, "title": s.title, "agent_scope": s.agent_scope, "folder": s.folder, "data_class": s.data_class,
           "created_at": s.created_at, "updated_at": s.updated_at, "archived": s.archived_at is not None}
    if count is not None:
        out["messages"] = count
    return out


def message_out(m: Message) -> dict:
    return {"id": m.id, "role": m.role, "kind": m.kind, "content": m.content, "task_id": m.task_id, "meta": m.meta,
            "created_at": m.created_at}


def _own(db: Session, session_id: str, p: Principal) -> ChatSession:
    s = db.get(ChatSession, session_id)
    if s is None or s.owner != p.actor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "세션 없음 / not found")
    return s


@router.post("/api/chat/stream")
async def chat_stream(body: ChatIn, p: Principal = Depends(require_user)):
    """AG-UI 이벤트 SSE (PRD 12.3: POST /api/chat/stream)."""
    try:
        level = parse_data_class(body.data_class)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    with SessionLocal() as db:  # 첨부·컬렉션 접근 검사는 스트림 시작 전에(오류를 422/404 로)
        try:
            attachments.owned(db, p.actor, body.attachments)
            for cid in body.knowledge:
                kb.get_visible(db, cid, p.actor)
        except (attachments.FileError, kb.KnowledgeError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    stream_id = str(uuid.uuid4())
    gen = chat.run(principal=p.actor, role=p.role, message=body.message, session_id=body.session_id,
                   agent_scope=body.agent_scope, data_class=level, attachment_ids=body.attachments,
                   knowledge=body.knowledge, stream_id=stream_id)
    return StreamingResponse(gen, media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Plaza-Stream": stream_id})


@router.get("/api/chat/streams/{stream_id}")
async def resume_stream(stream_id: str, after: int = Query(0, ge=0), last_event_id: str | None = Header(default=None),
                        p: Principal = Depends(require_user)):
    """재연결 후 재개(NFR-P4): Last-Event-ID(또는 after) 다음 이벤트부터. 본인 스트림만."""
    with SessionLocal() as db:
        if not chat.stream_exists(db, stream_id, p.actor):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "스트림 없음 / not found")
    start = int(last_event_id) if last_event_id and last_event_id.isdigit() else after
    return StreamingResponse(chat.replay(stream_id, p.actor, start), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Plaza-Stream": stream_id})


@router.get("/api/sessions")
def list_sessions(q: str | None = None, folder: str | None = None, archived: bool = False,
                  limit: int = Query(50, ge=1, le=200), p: Principal = Depends(require_user),
                  db: Session = Depends(get_db)):
    """목록·검색(D3-02). q 는 제목과 메시지 본문을 함께 찾는다."""
    counts = (select(Message.session_id, func.count().label("n")).group_by(Message.session_id).subquery())
    stmt = (select(ChatSession, counts.c.n).outerjoin(counts, counts.c.session_id == ChatSession.id)
            .where(ChatSession.owner == p.actor).order_by(ChatSession.updated_at.desc()).limit(limit))
    stmt = stmt.where(ChatSession.archived_at.is_not(None) if archived else ChatSession.archived_at.is_(None))
    if folder:
        stmt = stmt.where(ChatSession.folder == folder)
    if q:
        like = f"%{q}%"
        hit = select(Message.session_id).where(Message.content.ilike(like))
        stmt = stmt.where(or_(ChatSession.title.ilike(like), ChatSession.id.in_(hit)))
    return [session_out(s, n or 0) for s, n in db.execute(stmt).all()]


@router.post("/api/sessions", status_code=201)
def create_session(body: SessionIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    s = ChatSession(id=str(uuid.uuid4()), owner=p.actor, title=body.title or "새 대화", agent_scope=body.agent_scope,
                    folder=body.folder)
    db.add(s)
    db.commit()
    return session_out(s, 0)


@router.get("/api/sessions/{session_id}")
def get_session(session_id: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    s = _own(db, session_id, p)
    msgs = db.execute(select(Message).where(Message.session_id == s.id).order_by(Message.id)).scalars().all()
    return {**session_out(s, len(msgs)), "messages": [message_out(m) for m in msgs]}


@router.patch("/api/sessions/{session_id}")
def patch_session(session_id: str, body: SessionPatch, p: Principal = Depends(require_user),
                  db: Session = Depends(get_db)):
    s = _own(db, session_id, p)
    if body.title is not None:
        s.title = body.title
    if body.folder is not None:
        s.folder = body.folder or None
    if body.archived is not None:
        s.archived_at = utcnow() if body.archived else None
    db.commit()
    return session_out(s)


@router.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    """삭제권(NFR-C3): 메시지까지 즉시 파기. 원장에는 사실만 남긴다(내용 없음)."""
    s = _own(db, session_id, p)
    n = db.query(Message).filter(Message.session_id == s.id).delete()
    db.delete(s)
    audit.record(db, actor=p.actor, actor_type=p.type, action="session.deleted", resource=f"session:{session_id}",
                 detail={"messages": n})
    return {"deleted": session_id, "messages": n}


@router.get("/api/sessions/{session_id}/export")
def export_session(session_id: str, format: str = Query("json", pattern="^(json|md)$"),
                   p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    from app.governance import policy as gov
    s = _own(db, session_id, p)
    if not gov.export_allowed(gov.get(db), s.data_class):  # D9-05 등급별 내보내기 제한
        audit.record(db, actor=p.actor, actor_type=p.type, action="policy.export_denied", resource=f"session:{session_id}",
                     outcome="denied", detail={"data_class": s.data_class})
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"{s.data_class} 대화는 내보낼 수 없음(정책) / export blocked by policy")
    data = get_session(session_id, p, db)
    if format == "json":
        return PlainTextResponse(json.dumps(data, ensure_ascii=False, indent=2, default=str),
                                 media_type="application/json",
                                 headers={"Content-Disposition": f'attachment; filename="session-{session_id}.json"'})
    lines = [f"# {data['title']}", ""]
    for m in data["messages"]:
        if m["kind"] == "text":
            lines += [f"**{m['role']}** ({m['created_at']}):", "", m["content"], ""]
    return PlainTextResponse("\n".join(lines), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="session-{session_id}.md"'})


@router.post("/api/admin/retention/run", dependencies=[Depends(require_admin)])
def run_retention(p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    n = chat.purge_expired(db)
    audit.record(db, actor=p.actor, actor_type=p.type, action="retention.purged", detail={"sessions": n})
    return {"purged_sessions": n}
