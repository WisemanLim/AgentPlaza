"""대화 첨부 (D3-04): 문서는 텍스트로 뽑아 문맥에, 이미지는 비전 모델(plaza/vision)에 그대로 넘긴다.
보존 기간(설정 retention_file_days, 기본 90일)이 지나면 본문·메타를 함께 파기한다(NFR-C3)."""
import hashlib
import uuid
from datetime import timedelta
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.knowledge import extract
from app.models import StoredFile
from app.services import sysconfig

IMAGES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
IMG_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
DOC_CHARS = 8000


class FileError(ValueError):
    pass


def path_of(fid: str) -> Path:
    return Path(settings.data_dir) / "files" / fid


def save(db: Session, owner: str, filename: str, data: bytes, mime: str | None, session_id: str | None) -> StoredFile:
    if len(data) > settings.upload_file_max_mb * 1024 * 1024:
        raise FileError(f"파일 크기 초과 > {settings.upload_file_max_mb}MB")
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    kind_mime = IMG_EXT.get(ext) or extract.mime_of(filename, mime)
    if kind_mime in IMAGES:
        kind = "image"
    elif kind_mime in (*extract.TEXT_MIMES, "application/pdf"):
        kind = "document"
    else:
        raise FileError(f"지원하지 않는 형식 / unsupported type: {kind_mime}")
    f = StoredFile(id=str(uuid.uuid4()), owner=owner, session_id=session_id, filename=filename[:255], mime=kind_mime,
                   kind=kind, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    p = path_of(f.id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    db.add(f)
    db.commit()
    return f


def owned(db: Session, owner: str, ids: list[str]) -> list[StoredFile]:
    rows = list(db.execute(select(StoredFile).where(StoredFile.id.in_(ids), StoredFile.owner == owner)).scalars())
    if len(rows) != len(set(ids)):
        raise FileError("첨부를 찾을 수 없음 / attachment not found")
    return rows


def document_context(rows: list[StoredFile]) -> str | None:
    blocks = []
    for f in rows:
        if f.kind != "document":
            continue
        try:
            text = extract.text_of(path_of(f.id).read_bytes(), f.mime)
        except extract.ExtractError as exc:
            text = f"(읽을 수 없음: {exc})"
        blocks.append(f"### {f.filename}\n{text[:DOC_CHARS]}")
    return ("Attached documents:\n\n" + "\n\n".join(blocks)) if blocks else None


def image_contents(rows: list[StoredFile]) -> list:
    """pydantic-ai 입력용 이미지(BinaryContent) — Assistant 에이전트가 비전 별칭으로 보낸다."""
    from pydantic_ai import BinaryContent
    return [BinaryContent(data=path_of(f.id).read_bytes(), media_type=f.mime) for f in rows if f.kind == "image"]


def out(f: StoredFile) -> dict:
    return {"id": f.id, "filename": f.filename, "mime": f.mime, "kind": f.kind, "bytes": f.bytes,
            "session_id": f.session_id, "created_at": f.created_at}


def purge_expired(db: Session) -> int:
    cutoff = utcnow() - timedelta(days=sysconfig.get(db, "retention_file_days"))
    old = list(db.execute(select(StoredFile).where(StoredFile.created_at < cutoff)).scalars())
    for f in old:
        path_of(f.id).unlink(missing_ok=True)
    if old:
        db.execute(delete(StoredFile).where(StoredFile.id.in_([f.id for f in old])))
        db.commit()
    return len(old)


def delete_one(db: Session, f: StoredFile) -> None:
    path_of(f.id).unlink(missing_ok=True)
    db.delete(f)
    db.commit()
