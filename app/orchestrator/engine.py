"""실행 패턴 엔진 (D2-03) — LangGraph StateGraph(라이브러리만, PRD 13.3).

run_ready 노드가 의존이 충족된 단계를 동시에 실행(parallel)하고, 남은 단계가 있으면 자신으로 되돌아간다
(sequential 은 depends_on 사슬). 승인 필요 단계를 만나면 pending 을 세우고 종료 → Task 에 저장 → 승인 후 재개.
이벤트는 AG-UI 1.0 이름(PRD 12.5)으로 emit 한다.

내구성(D2-07): 체크포인터가 superstep 마다 상태를 저장(크래시 후 재개), 일시 장애는 지수 백오프 재시도
(연결 실패는 항상, 5xx·시간 초과는 idempotent capability 만), 실패하면 끝난 단계를 compensation 으로 되돌린다(사가).
"""
import asyncio
import json
import operator
import re
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.governance import guardrails
from app.governance import policy as gov
from app.market import licensing
from app.models import Approval, Task
from app.orchestrator import checkpoint, executor
from app.services import approvals, audit, registry

Emit = Callable[[dict], Awaitable[None]]
REF = re.compile(r"^\{\{(\w+)((?:\.\w+)*)\}\}$")


def _merge(a: dict, b: dict) -> dict:
    return {**a, **b}


class State(TypedDict):
    steps: list[dict]
    results: Annotated[dict, _merge]
    pending: dict | None


def resolve_args(args, results: dict):
    """'{{s1}}' / '{{s1.field}}' → 앞 단계 결과로 치환(순차 파이프라인)."""
    if isinstance(args, dict):
        return {k: resolve_args(v, results) for k, v in args.items()}
    if isinstance(args, list):
        return [resolve_args(v, results) for v in args]
    if isinstance(args, str) and (m := REF.match(args)):
        value = results.get(m.group(1), {}).get("result")
        for part in filter(None, m.group(2).split(".")):
            value = value.get(part) if isinstance(value, dict) else None
        return value if isinstance(value, (str, int, float, bool)) or value is None else json.dumps(value, ensure_ascii=False)
    return args


def _audit_args(level: str, args, result) -> tuple:
    """감사 수준(D9-05): minimal = 해시 없음, standard = 인자·결과 해시, full = 해시 + PII 마스킹 요약."""
    if level == "minimal":
        return None, None, {}
    if level == "full":
        dump = lambda v: guardrails.mask_pii(json.dumps(v, ensure_ascii=False, default=str))[0][:2000]  # noqa: E731
        return args, result, {"args": dump(args), "result": dump(result)}
    return args, result, {}


async def run(db: Session, task: Task, caps: dict[tuple[str, str], dict], emit: Emit, *, resume: bool = False) -> State:
    pol = gov.get(db)
    level = task.data_class or "L2"

    async def execute(step: dict, results: dict) -> dict:
        cap = caps[(step["agent"], step["capability"])]
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        args = resolve_args(step.get("args", {}), results)
        why = gov.tool_decision(pol, cap, role=task.principal_role, level=level)
        if why:  # 계획 이후 정책이 바뀌었거나 재개 시점 — 실행 직전에 다시 판정한다
            audit.record(db, actor=task.principal, actor_type="user", agent_id=step["agent"], action="policy.tool_blocked",
                         resource=f"{step['agent']}.{step['capability']}", outcome="denied", detail={"reason": why,
                                                                                                    "task": task.id})
            await emit({"type": "CUSTOM", "name": "policy_blocked", "value": {"step": step["id"], "reason": why}})
            return {"ok": False, "error": f"policy: {why}", "agent": step["agent"], "capability": step["capability"]}
        why = licensing.check_use(db, step["agent"], task.principal, claim=True)
        if why:  # 유료 에이전트: 유효한 라이선스·남은 좌석이 있어야 실행(D6-05)
            audit.record(db, actor=task.principal, actor_type="user", agent_id=step["agent"], action="license.denied",
                         resource=f"{step['agent']}.{step['capability']}", outcome="denied", detail={"reason": why,
                                                                                                    "task": task.id})
            await emit({"type": "CUSTOM", "name": "license_blocked", "value": {"step": step["id"], "reason": why}})
            return {"ok": False, "error": f"license: {why}", "agent": step["agent"], "capability": step["capability"]}
        await emit({"type": "STEP_STARTED", "stepName": step["id"]})
        await emit({"type": "TOOL_CALL_START", "toolCallId": call_id, "toolCallName": f"{step['agent']}.{step['capability']}"})
        await emit({"type": "TOOL_CALL_ARGS", "toolCallId": call_id, "delta": json.dumps(args, ensure_ascii=False)})
        await emit({"type": "TOOL_CALL_END", "toolCallId": call_id})
        attempts = 0
        while True:  # 일시 장애 재시도(D2-07)
            attempts += 1
            out = await executor.call(cap, args, principal=task.principal, task_id=task.id,
                                      approval_id=step.get("approval_id"), session_id=task.session_id)
            kind = out.get("transient")
            retry = kind == "connect" or (kind in ("timeout", "status") and cap.get("idempotent"))
            if out["ok"] or not retry or attempts >= settings.step_max_attempts:
                break
            await emit({"type": "CUSTOM", "name": "retry", "value": {"step": step["id"], "attempt": attempts,
                                                                     "error": str(out.get("error"))[:200]}})
            await asyncio.sleep(settings.step_retry_backoff * 2 ** (attempts - 1))
        out["attempts"] = attempts
        # NFR-S4: 모든 도구 호출을 원장에 남긴다(감사 수준에 따라 해시·마스킹 요약).
        a_args, a_res, extra = _audit_args(gov.audit_level(pol, cap), args, out.get("result", out.get("error")))
        audit.record(db, actor=task.principal, actor_type="user", agent_id=step["agent"], action="tool.call",
                     resource=f"{step['agent']}.{step['capability']}", outcome="ok" if out["ok"] else "error",
                     args=a_args, result=a_res, detail={"task": task.id, "attempts": attempts, **extra})
        if out["ok"] and pol["guardrails"]["scan_tool_results"]:  # 간접 인젝션(도구 결과에 숨긴 지시)
            found = guardrails.injection(json.dumps(out.get("result"), ensure_ascii=False, default=str))
            if found["level"] != "none":
                out["flags"] = [f"tool_result:{found['level']}"]
                await emit({"type": "CUSTOM", "name": "guardrail", "value": {"step": step["id"], "result": found["level"]}})
        await emit({"type": "TOOL_CALL_RESULT", "toolCallId": call_id, "messageId": call_id,
                    "content": json.dumps(out, ensure_ascii=False, default=str)})
        await emit({"type": "STEP_FINISHED", "stepName": step["id"]})
        return {**out, "agent": step["agent"], "capability": step["capability"], "args": args}

    async def run_ready(state: State) -> dict:
        task.heartbeat_at = utcnow()  # 진행 신호 — 이게 멈춘 running 작업은 복구 대상(D2-07)
        db.commit()
        done = state["results"]
        ready = [s for s in state["steps"] if s["id"] not in done and all(d in done for d in s["depends_on"])]
        if not ready:
            return {"pending": None}
        skipped = {s["id"]: {"ok": False, "error": "skipped: dependency failed", "agent": s["agent"],
                             "capability": s["capability"]}
                   for s in ready if any(not done[d].get("ok") for d in s["depends_on"])}
        ready = [s for s in ready if s["id"] not in skipped]
        if not ready:
            return {"results": skipped}
        for s in ready:
            cap = caps[(s["agent"], s["capability"])]
            if not gov.needs_approval(pol, cap, level):  # 등급 정책이 승인을 강제할 수 있다(D9-05)
                continue
            ap = db.get(Approval, s["approval_id"]) if s.get("approval_id") else None
            if ap is None:
                ap = approvals.create(db, task, s, task.principal)
                s["approval_id"] = ap.id
                pending = {"approval_id": ap.id, "step": s["id"], "agent": s["agent"], "capability": s["capability"],
                           "args": s.get("args", {}), "expires_at": ap.expires_at.isoformat()}
                await emit({"type": "CUSTOM", "name": "approval_required", "value": pending})
                await emit({"type": "STATE_SNAPSHOT", "snapshot": {"task": task.id, "state": "waiting_approval",
                                                                    "pending": pending}})
                return {"pending": pending, "steps": state["steps"]}
            if ap.status != "approved":  # rejected / expired 는 실행하지 않고 결과로 남긴다
                return {"results": {s["id"]: {"ok": False, "error": f"approval {ap.status}", "agent": s["agent"],
                                              "capability": s["capability"]}}}
        outs = await asyncio.gather(*(execute(s, done) for s in ready))
        return {"results": {**skipped, **{s["id"]: o for s, o in zip(ready, outs, strict=True)}}}

    def route(state: State) -> str:
        if state.get("pending"):
            return END
        done = state["results"]
        left = [s for s in state["steps"] if s["id"] not in done]
        progress = any(all(d in done for d in s["depends_on"]) for s in left)
        return "run_ready" if left and progress else END

    g = StateGraph(State)
    g.add_node("run_ready", run_ready)
    g.add_edge(START, "run_ready")
    g.add_conditional_edges("run_ready", route, ["run_ready", END])
    initial = {"steps": task.plan["steps"], "results": dict(task.results or {}), "pending": None}
    config = {"configurable": {"thread_id": task.id}, "recursion_limit": 50}
    async with checkpoint.saver() as cp:
        graph = g.compile(checkpointer=cp)
        if resume and (await graph.aget_state(config)).values:
            return await graph.ainvoke(None, config)  # 마지막 체크포인트에서 이어서(끝난 단계는 다시 안 함)
        return await graph.ainvoke(initial, config)


def _render(value, ctx: dict):
    """보상 인자 템플릿: '{{result.id}}' · '{{args.title}}' → 원 단계의 결과·인자 값."""
    if isinstance(value, dict):
        return {k: _render(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [_render(v, ctx) for v in value]
    if isinstance(value, str) and (m := re.match(r"^\{\{(result|args)((?:\.\w+)*)\}\}$", value)):
        out = ctx.get(m.group(1))
        for part in filter(None, m.group(2).split(".")):
            out = out.get(part) if isinstance(out, dict) else None
        return out
    return value


async def compensate(db: Session, task: Task, results: dict, caps: dict[tuple[str, str], dict], emit: Emit) -> dict:
    """사가 보상(D2-07): 실패한 실행에서 이미 성공한 단계를 역순으로 compensation capability 로 되돌린다."""
    results = dict(results)
    for sid in reversed(list(results)):
        r = results[sid]
        cap = caps.get((r.get("agent"), r.get("capability")))
        comp = (cap or {}).get("compensation")
        if not r.get("ok") or r.get("compensated") or not comp:
            continue
        comp_cap = caps.get((r["agent"], comp["capability"])) or next(
            (c for c in registry.routable(db, r["agent"]) if c["verb"] == comp["capability"]), None)
        if comp_cap is None:
            results[sid] = {**r, "compensated": {"ok": False, "error": "compensation capability unavailable"}}
            continue
        args = _render(comp.get("args", {}), {"result": r.get("result"), "args": r.get("args")})
        out = await executor.call(comp_cap, args, principal=task.principal, task_id=task.id, session_id=task.session_id)
        audit.record(db, actor=task.principal, actor_type="user", agent_id=r["agent"], action="tool.compensated",
                     resource=f"{r['agent']}.{comp['capability']}", outcome="ok" if out["ok"] else "error",
                     args=args, result=out.get("result", out.get("error")), detail={"task": task.id, "step": sid})
        await emit({"type": "CUSTOM", "name": "compensation", "value": {"step": sid, "capability": comp["capability"],
                                                                        "ok": out["ok"]}})
        results[sid] = {**r, "compensated": {"capability": comp["capability"], "args": args, "ok": out["ok"],
                                             **({"result": out["result"]} if out["ok"] else {"error": out.get("error")})}}
    return results
