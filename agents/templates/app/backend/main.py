"""{{AGENT_NAME}} — app 유형: 게시물 CRUD + 화면(frontend/)."""
import time

from agentplaza_sdk import Agent, CapabilityError, create_app
from agentplaza_sdk.db import connect, rows

agent = Agent.from_manifest("agent.yaml")


@agent.capability("manage")
def manage(payload: dict, ctx):
    action = payload["action"]
    with connect(ctx) as con:
        if action == "create":
            if not payload.get("title"):
                raise CapabilityError("title required")
            cur = con.execute("INSERT INTO items (title, body, created_at) VALUES (?, ?, ?)",
                              (payload["title"], payload.get("body", ""), time.time()))
            return {"id": cur.lastrowid}
        if action == "list":
            return rows(con.execute("SELECT id, title, created_at FROM items ORDER BY id DESC LIMIT ?",
                                    (int(payload.get("limit", 50)),)))
        if action == "get":
            found = rows(con.execute("SELECT * FROM items WHERE id = ?", (payload.get("id"),)))
            if not found:
                raise CapabilityError("not found", status=404)
            return found[0]
        if action == "delete":
            con.execute("DELETE FROM items WHERE id = ?", (payload.get("id"),))
            return {"deleted": payload.get("id")}
    raise CapabilityError(f"unknown action: {action}")


app = create_app(agent)
