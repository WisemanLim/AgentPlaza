"""개인화 API (D3-04·D3-05, UI C03·C04): 내 맞춤지침·기억(삭제권) · 대화 첨부 파일."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assistant import files, memory
from app.core.config import settings
from app.core.deps import Principal, require_user
from app.db import get_db
from app.models import Memory, StoredFile
from app.services import audit, sysconfig

router = APIRouter(tags=["personal"], dependencies=[Depends(require_user)])


class MemoryIn(BaseModel):
    kind: str = Field(pattern="^(instruction|fact)$")
    content: str = Field(min_length=1, max_length=1000)


class MemoryPatch(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class MemorySettings(BaseModel):
    memory_enabled: bool


def _mem(m: Memory) -> dict:
    return {"id": m.id, "kind": m.kind, "content": m.content, "source": m.source, "created_at": m.created_at,
            "updated_at": m.updated_at}


@router.get("/api/me/memories")
def list_memories(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    return {"enabled": memory.enabled(db, p.actor), "items": [_mem(m) for m in memory.items(db, p.actor)]}


@router.post("/api/me/memories", status_code=201)
def add_memory(body: MemoryIn, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    try:
        return _mem(memory.add(db, p.actor, body.kind, body.content))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None


def _own_memory(db: Session, mid: int, p: Principal) -> Memory:
    m = db.get(Memory, mid)
    if m is None or m.owner != p.actor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "없음 / not found")
    return m


@router.patch("/api/me/memories/{mid}")
def patch_memory(mid: int, body: MemoryPatch, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    m = _own_memory(db, mid, p)
    m.content = memory._minimize(body.content)
    memory.touch(m)
    db.commit()
    return _mem(m)


@router.delete("/api/me/memories/{mid}")
def delete_memory(mid: int, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    db.delete(_own_memory(db, mid, p))
    db.commit()
    return {"deleted": mid}


@router.delete("/api/me/memories")
def purge_memories(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    """삭제권(NFR-C3): 내 기억·지침 전부 즉시 파기. 원장에는 사실(개수)만 남긴다."""
    n = memory.purge(db, p.actor)
    audit.record(db, actor=p.actor, actor_type=p.type, action="memory.purged", detail={"items": n})
    return {"deleted": n}


@router.put("/api/me/memory-settings")
def memory_settings(body: MemorySettings, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    prof = sysconfig.blob(db, f"profile:{p.actor}")
    sysconfig.put_blob(db, f"profile:{p.actor}", {**prof, "memory_enabled": body.memory_enabled})
    return {"memory_enabled": body.memory_enabled}


@router.post("/api/files", status_code=201)
async def upload_file(file: UploadFile = File(...), session_id: str | None = Form(default=None),
                      p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    data = await file.read(settings.upload_file_max_mb * 1024 * 1024 + 1)
    try:
        f = files.save(db, p.actor, file.filename or "upload", data, file.content_type, session_id)
    except files.FileError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    return files.out(f)


@router.get("/api/files")
def list_files(p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    q = select(StoredFile).where(StoredFile.owner == p.actor).order_by(StoredFile.created_at.desc()).limit(200)
    return [files.out(f) for f in db.execute(q).scalars()]


def _own_file(db: Session, fid: str, p: Principal) -> StoredFile:
    f = db.get(StoredFile, fid)
    if f is None or f.owner != p.actor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "파일 없음 / not found")
    return f


@router.get("/api/files/{fid}/content")
def file_content(fid: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    f = _own_file(db, fid, p)
    return Response(files.path_of(f.id).read_bytes(), media_type=f.mime,
                    headers={"Content-Disposition": f'inline; filename="{f.id}"', "X-Content-Type-Options": "nosniff"})


@router.delete("/api/files/{fid}")
def delete_file(fid: str, p: Principal = Depends(require_user), db: Session = Depends(get_db)):
    files.delete_one(db, _own_file(db, fid, p))
    return {"deleted": fid}
