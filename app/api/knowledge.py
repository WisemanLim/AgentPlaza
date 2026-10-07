"""지식(RAG) API (D3-06, UI G01·G02·C06): 컬렉션·문서 업로드·검색. 공유 컬렉션은 소유자·관리자만 바꾼다."""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Principal, require_user
from app.db import get_db
from app.knowledge import service as kb
from app.llm.router import AllTargetsFailed, NoRoute, PolicyDenied, parse_data_class
from app.models import ROLE_RANK, KbCollection, KbDocument
from app.services import audit

router = APIRouter(prefix="/api/kb", tags=["knowledge"], dependencies=[Depends(require_user)])


class CollectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    shared: bool = False
    data_class: str = "L2"


class SearchIn(BaseModel):
    collections: list[str] = Field(min_length=1, max_length=10)
    query: str = Field(min_length=1, max_length=4000)
    top_n: int = Field(default=5, ge=1, le=20)


def _out(c: KbCollection, docs: int = 0) -> dict:
    return {"id": c.id, "name": c.name, "description": c.description, "owner": c.owner, "shared": c.shared,
            "data_class": c.data_class, "documents": docs, "created_at": c.created_at}


def _doc_out(d: KbDocument) -> dict:
    return {k: getattr(d, k) for k in ("id", "collection_id", "filename", "mime", "bytes", "status", "error", "chunks",
                                       "created_by", "created_at")}


def _get(db: Session, cid: str, p: Principal, write: bool = False) -> KbCollection:
    try:
        c = kb.get_visible(db, cid, p.actor)
    except kb.KnowledgeError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    if write and c.owner != p.actor and ROLE_RANK.get(p.role, 0) < ROLE_RANK["admin"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "소유자·관리자만 / owner or admin only")
    return c


@router.get("/collections")
def list_collections(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(KbDocument.collection_id, func.count()).group_by(KbDocument.collection_id)).all())
    return [_out(c, counts.get(c.id, 0)) for c in kb.visible(db, p.actor)]


@router.post("/collections", status_code=201)
def create_collection(body: CollectionIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    try:
        level = parse_data_class(body.data_class)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    if body.shared and ROLE_RANK.get(p.role, 0) < ROLE_RANK["admin"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "공유 컬렉션은 관리자만 / admin only")
    c = KbCollection(id=str(uuid.uuid4()), name=body.name, description=body.description, owner=p.actor,
                     shared=body.shared, data_class=level)
    db.add(c)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="kb.collection_created", resource=f"kb:{c.id}",
                 detail={"name": c.name, "shared": c.shared, "data_class": level})
    return _out(c)


@router.delete("/collections/{cid}")
def delete_collection(cid: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    c = _get(db, cid, p, write=True)
    db.delete(c)  # 문서·청크는 FK CASCADE
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="kb.collection_deleted", resource=f"kb:{cid}")
    return {"deleted": cid}


@router.get("/collections/{cid}/documents")
def list_documents(cid: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    _get(db, cid, p)
    q = select(KbDocument).where(KbDocument.collection_id == cid).order_by(KbDocument.created_at.desc())
    return [_doc_out(d) for d in db.execute(q).scalars()]


@router.post("/collections/{cid}/documents", status_code=201)
async def upload_documents(cid: str, files: list[UploadFile] = File(...), p: Principal = Depends(require_user),
                           db: Session = Depends(get_db)):
    c = _get(db, cid, p, write=True)
    limit = settings.upload_file_max_mb * 1024 * 1024
    out = []
    for f in files:
        data = await f.read(limit + 1)
        if len(data) > limit:
            out.append({"filename": f.filename, "status": "failed", "error": f"크기 초과 > {settings.upload_file_max_mb}MB"})
            continue
        doc = await kb.ingest(db, c, f.filename or "upload", data, f.content_type, p.actor)
        out.append(_doc_out(doc))
    audit.record(db, actor=p.actor, actor_type=p.type, action="kb.documents_added", resource=f"kb:{cid}",
                 detail={"files": [o["filename"] for o in out], "ok": sum(o["status"] == "ready" for o in out)})
    return out


@router.delete("/collections/{cid}/documents/{did}")
def delete_document(cid: str, did: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    _get(db, cid, p, write=True)
    d = db.get(KbDocument, did)
    if d is None or d.collection_id != cid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서 없음 / not found")
    db.delete(d)
    db.commit()
    return {"deleted": did}


@router.post("/search")
async def search(body: SearchIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    cols = [_get(db, cid, p) for cid in body.collections]
    try:
        return {"results": await kb.search(db, cols, body.query, top_n=body.top_n, principal=p.actor)}
    except (PolicyDenied, NoRoute, AllTargetsFailed) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"임베딩 불가 / embedding unavailable: {exc}") from None
