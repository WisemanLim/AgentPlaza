"""운영 작업 (D8-06·NFR-O4): 플랫폼 DB·에이전트 볼륨 백업. `make backup [ENV=]` 이 이 모듈을 부른다.

- local(SQLite): sqlite3 온라인 백업 API 로 data/backups/platform/<stamp>.sqlite
- prod(PostgreSQL): runtime 서비스가 db 컨테이너에서 pg_dump -Fc → data/backups/platform/<stamp>.dump
- 설치 에이전트: runtime 이 일시정지 스냅숏으로 볼륨을 tar.gz 로 → data/backups/agents/<id>/<stamp>/
"""
import asyncio
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.db import SessionLocal
from app.models import AgentVersion
from app.runtime.driver import RuntimeFailure, get_runtime


def backup_platform_db() -> dict:
    if settings.database_url.startswith("sqlite:///"):
        src = settings.database_url.removeprefix("sqlite:///")
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out = Path(settings.data_dir) / "backups" / "platform" / f"{stamp}.sqlite"
        out.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(src) as a, sqlite3.connect(out) as b:
            a.backup(b)
        data = out.read_bytes()
        return {"backup": stamp, "file": str(out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    raise RuntimeFailure("PostgreSQL 은 runtime 서비스의 pg_dump 로 백업 — backup_all 사용 / use backup_all")


async def backup_all() -> dict:
    """플랫폼 DB + 설치 에이전트 전부. API(관리자)와 CLI 가 같이 쓴다."""
    rt = get_runtime()
    if settings.database_url.startswith("sqlite:///"):
        platform = await asyncio.to_thread(backup_platform_db)
    else:
        platform = await rt.backup_db()
    with SessionLocal() as db:
        agents = sorted(set(db.execute(select(AgentVersion.agent_id).where(AgentVersion.current.is_(True))).scalars()))
    out = {"platform": platform, "agents": {}}
    for aid in agents:
        try:
            out["agents"][aid] = (await rt.backup(aid))["backup"]
        except RuntimeFailure as exc:
            out["agents"][aid] = f"error: {exc}"
    return out


def main(argv: list[str]) -> int:
    if argv[:1] == ["backup"]:
        print(json.dumps(asyncio.run(backup_all()), ensure_ascii=False, indent=1))
        return 0
    print("usage: python -m app.ops backup", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
