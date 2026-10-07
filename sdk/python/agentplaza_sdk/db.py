"""SQLite 헬퍼 (db.isolation=file). database/migrations/*.sql 을 이름순으로 1회씩 적용한다(멱등)."""
import os
import sqlite3
from pathlib import Path

from agentplaza_sdk.agent import Context


def connect(ctx: Context, migrations_dir: str | Path | None = None) -> sqlite3.Connection:
    ctx.data_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ctx.data_dir / "agent.db")
    con.row_factory = sqlite3.Row
    mdir = Path(migrations_dir or ctx.migrations_dir or os.environ.get("AGENT_MIGRATIONS", "database/migrations"))
    con.execute("CREATE TABLE IF NOT EXISTS _plaza_migrations (name TEXT PRIMARY KEY)")
    done = {r[0] for r in con.execute("SELECT name FROM _plaza_migrations")}
    for f in sorted(mdir.glob("*.sql")) if mdir.is_dir() else []:
        if f.name not in done:
            con.executescript(f.read_text(encoding="utf-8"))
            con.execute("INSERT INTO _plaza_migrations (name) VALUES (?)", (f.name,))
    con.commit()
    return con


def rows(cur: sqlite3.Cursor) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]
