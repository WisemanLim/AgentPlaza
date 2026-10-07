"""LangGraph 체크포인터 (D2-07): 실행 그래프의 단계(superstep)마다 상태를 저장한다 — api 가 죽어도 마지막 체크포인트에서 재개.

- local(SQLite): AsyncSqliteSaver — 플랫폼 DB 와 분리된 data/checkpoints.sqlite (쓰기 잠금 경합 방지)
- prod(PostgreSQL): AsyncPostgresSaver — 같은 DB(langgraph-checkpoint-postgres, MIT). 표는 처음 열 때 setup()
작업이 끝나면 스레드(task id)를 지운다 — 도구 인자·결과가 오래 남지 않게(대기 중인 승인 작업만 유지).
"""
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings

_pg_ready = False


@asynccontextmanager
async def saver():
    global _pg_ready
    url = settings.database_url
    if url.startswith("sqlite"):
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        path = Path(settings.data_dir) / "checkpoints.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        async with AsyncSqliteSaver.from_conn_string(str(path)) as s:
            yield s
    else:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        async with AsyncPostgresSaver.from_conn_string(url.replace("postgresql+psycopg://", "postgresql://")) as s:
            if not _pg_ready:
                await s.setup()
                _pg_ready = True
            yield s


async def forget(thread_id: str) -> None:
    async with saver() as s:
        await s.adelete_thread(thread_id)
