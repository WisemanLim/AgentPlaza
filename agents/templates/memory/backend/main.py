"""{{AGENT_NAME}} — memory 유형: 사용자별 장기 기억(사실·선호). 개인정보 최소화와 삭제권(forget)을 기본 제공."""
import time

from agentplaza_sdk import Agent, create_app
from agentplaza_sdk.db import connect, rows

agent = Agent.from_manifest("agent.yaml")


@agent.capability("remember")
def remember(payload: dict, ctx):
    with connect(ctx) as con:
        cur = con.execute("INSERT INTO facts (user_id, fact, created_at) VALUES (?, ?, ?)",
                          (payload["user"], payload["fact"], time.time()))
    return {"id": cur.lastrowid}


@agent.capability("recall")
def recall(payload: dict, ctx):
    q = f"%{payload.get('query', '')}%"
    with connect(ctx) as con:
        return rows(con.execute("SELECT id, fact, created_at FROM facts WHERE user_id = ? AND fact LIKE ? "
                                "ORDER BY id DESC LIMIT 20", (payload["user"], q)))


@agent.capability("forget")
def forget(payload: dict, ctx):
    with connect(ctx) as con:
        n = con.execute("DELETE FROM facts WHERE user_id = ?", (payload["user"],)).rowcount
    return {"deleted": n}


app = create_app(agent)
