"""{{AGENT_NAME}} — hitl 유형: 부작용 있는 작업. agent.yaml 에 humanApprovalRequired 로 선언하고
승인은 플랫폼 게이트(Orchestrator D2-06)가 집행한다(DP8). 이 코드는 승인된 요청만 받는다고 가정하지 않고
게이트가 넘긴 승인 ID 를 기록해 감사 추적을 남긴다."""
import time

from agentplaza_sdk import Agent, CapabilityError, create_app
from agentplaza_sdk.db import connect, rows

agent = Agent.from_manifest("agent.yaml")


@agent.capability("execute_action")
def execute_action(payload: dict, ctx):
    approval = ctx.caller.get("approval-id")
    if not approval:
        raise CapabilityError("approval required (x-plaza-approval-id)", status=403)
    with connect(ctx) as con:
        cur = con.execute("INSERT INTO actions (action, target, approval_id, executed_at) VALUES (?, ?, ?, ?)",
                          (payload["action"], payload.get("target", ""), approval, time.time()))
    return {"executed": True, "action_id": cur.lastrowid, "approval_id": approval}


@agent.capability("history")
def history(payload: dict, ctx):
    with connect(ctx) as con:
        return rows(con.execute("SELECT * FROM actions ORDER BY id DESC LIMIT 50"))


app = create_app(agent)
