"""Orchestrator 진입점: start(계획→실행→합성) · resume(승인 후 재개). 결과는 Task 행에 남긴다."""
import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal, utcnow
from app.governance import guardrails, reviewer
from app.governance import policy as gov
from app.llm.providers import ChatRequest
from app.llm.router import CLASS_TO_LEVEL, AllTargetsFailed, Caller, NoRoute, PolicyDenied, get_router
from app.models import Message, Task
from app.orchestrator import checkpoint, engine, planner
from app.observability import tracer
from app.services import audit, registry

Emit = Callable[[dict], Awaitable[None]]
LEVEL_ORDER = ["L0", "L1", "L2", "L3"]


async def _noop(_: dict) -> None:
    return None


def _caps(db: Session, agent_scope: str | None, *, role: str = "user", level: str = "L2",
          user: str | None = None) -> tuple[list[dict], dict]:
    """라우팅 후보 = 레지스트리 ∩ 배치 범위(PRD Q7) ∩ 정책 허용(D9-05·D9-06·D7-07). 막힌 도구는 계획에 오르지 않는다."""
    pol = gov.get(db)
    caps = [c for c in registry.routable(db, agent_scope, viewer=(user, role) if user else None)
            if gov.tool_decision(pol, c, role=role, level=level) is None]
    return caps, {(c["agent"], c["verb"]): c for c in caps}


def _level(cap_index: dict, steps: list[dict], base: str = "L2") -> str:
    """요청 등급과 사용된 에이전트 등급 중 가장 높은 것으로 합성 LLM 호출 등급을 정한다."""
    levels = [base] + [CLASS_TO_LEVEL.get(cap_index[(s["agent"], s["capability"])]["data_class"], "L2")
                       for s in steps if (s["agent"], s["capability"]) in cap_index]
    return max(levels, key=LEVEL_ORDER.index)


def format_results(results: dict) -> str:
    lines = []
    for sid, r in results.items():
        head = f"[{sid}] {r.get('agent')}.{r.get('capability')}"
        body = r.get("result") if r.get("ok") else f"오류 / error: {r.get('error')}"
        lines.append(f"{head}: {json.dumps(body, ensure_ascii=False, default=str)[:1500]}")
    return "\n".join(lines)


async def _llm_stream(db: Session, messages: list[dict], level: str, caller: Caller, emit: Emit,
                      msg_id: str, alias: str = "plaza/chat") -> str | None:
    """합성·일반 답변을 토큰 스트리밍으로 emit 한다(D3-01). 실패하면 None → 호출부가 폴백 문구를 쓴다."""
    try:
        meta, chunks = await get_router().stream(db, alias, ChatRequest(messages=messages), level=level,
                                                 caller=caller)
    except (AllTargetsFailed, NoRoute, PolicyDenied) as exc:
        await emit({"type": "CUSTOM", "name": "llm_unavailable", "value": {"reason": type(exc).__name__}})
        return None
    if meta.degraded:  # UI 저하 배지(MSG-011)
        await emit({"type": "CUSTOM", "name": "degraded", "value": {"from": meta.fallback_from, "model": meta.model}})
    await emit({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})
    parts = []
    async for c in chunks:
        if c.get("delta"):
            parts.append(c["delta"])
            await emit({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": c["delta"]})
    await emit({"type": "TEXT_MESSAGE_END", "messageId": msg_id})
    return "".join(parts)


SYNTH = ("The agent steps below were ALREADY executed. Report what was done (past tense) and any failures, based only "
         "on the results. Reply in the same language as the request (Korean request → Korean answer). Cite step ids "
         "like [s1].")


def review_signals(task: Task, cap_index: dict) -> list[str]:
    """리뷰어 게이트를 켤 근거(D2-05): 입력 인젝션 의심 · 외부(원격·egress) 도구 결과 · 도구 결과 인젝션 의심."""
    reasons = list(task.plan.get("guard", {}).get("flags", []))
    for sid, r in (task.results or {}).items():
        cap = cap_index.get((r.get("agent"), r.get("capability")), {})
        if r.get("ok") and (cap.get("source") == "link" or cap.get("egress")):
            reasons.append(f"external:{r.get('agent')}")
        reasons += [f"{sid}:{f}" for f in r.get("flags", [])]
    return reasons


async def _emit_text(emit: Emit, msg_id: str, text: str) -> None:
    await emit({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})
    if text:  # AG-UI: content delta 는 비어 있으면 안 된다
        await emit({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": text})
    await emit({"type": "TEXT_MESSAGE_END", "messageId": msg_id})


async def _llm_text(db: Session, messages: list[dict], level: str, caller: Caller) -> str | None:
    try:
        res, _ = await get_router().complete(db, "plaza/chat", ChatRequest(messages=messages), level=level, caller=caller)
        return res.content
    except (AllTargetsFailed, NoRoute, PolicyDenied):
        return None


async def _finish(db: Session, task: Task, cap_index: dict, emit: Emit, history: list[dict] | None = None,
                  context: str | None = None) -> dict:
    caller = Caller(principal=task.principal)
    steps, results = task.plan.get("steps", []), task.results or {}
    msg_id = f"msg_{task.id[:8]}"
    pol = gov.get(db)
    signals = review_signals(task, cap_index)
    gated = reviewer.needed(pol["reviewer"]["mode"], signals)
    extra = [{"role": "system", "content": context}] if context else []  # 메모리·지식 근거·첨부(D3-04~06)
    if steps:
        messages = [{"role": "system", "content": SYNTH}, *extra,
                    {"role": "user", "content": f"Request: {task.message}\n\nResults:\n{format_results(results)}"}]
        fallback = format_results(results)
        level = _level(cap_index, steps, task.data_class or "L2")
        ok = all(r.get("ok") for r in results.values())
    else:
        # 도구를 실행하지 않았다는 사실을 숨기지 않는다(실행했다고 말하는 환각 방지).
        messages = [{"role": "system", "content": "You are a helpful assistant. Reply in the user's language. No agent or "
                     "tool was executed for this message: never claim that you performed an action; if the user asked "
                     "for one, say no matching agent is installed."}, *extra,
                    *(history or []), {"role": "user", "content": task.message}]
        fallback = "적합한 에이전트가 없고 LLM 을 사용할 수 없습니다 / no agent matched and the LLM is unavailable"
        level, ok = task.data_class or "L2", True
    if gated:  # 검토 전에는 사용자에게 흘리지 않는다 — 전체 생성 → 판정 → 한 번에 전달
        answer = await _llm_text(db, messages, level, caller) or fallback
        verdict = await reviewer.review(db, pol, request=task.message, answer=answer, reasons=signals, level=level,
                                        principal=task.principal, task_id=task.id)
        answer = verdict["answer"]
        task.plan = {**task.plan, "review": {k: verdict.get(k) for k in ("verdict", "reason", "reviewer")}}
        await emit({"type": "CUSTOM", "name": "review", "value": {k: verdict.get(k) for k in ("verdict", "reason", "reviewer")}})
        await _emit_text(emit, msg_id, answer)
    else:
        answer = await _llm_stream(db, messages, level, caller, emit, msg_id)
        if answer is None:
            answer = fallback
            await _emit_text(emit, msg_id, answer)
    task.answer, task.state, task.ended_at = answer, "succeeded" if ok else "failed", utcnow()
    if steps:
        await checkpoint.forget(task.id)  # 끝난 작업의 체크포인트(도구 인자·결과)는 남기지 않는다
    if task.session_id:
        db.add(Message(session_id=task.session_id, role="assistant", kind="text", content=answer, task_id=task.id,
                       meta={"results": {k: {"agent": v.get("agent"), "capability": v.get("capability"),
                                             "ok": v.get("ok")} for k, v in results.items()}}))
    db.commit()
    await emit({"type": "RUN_FINISHED", "threadId": task.session_id or task.id, "runId": task.id})
    return out(task)


async def _execute(db: Session, task: Task, cap_index: dict, emit: Emit, history: list[dict] | None = None,
                   resume: bool = False, context: str | None = None) -> dict:
    missing = [s for s in task.plan["steps"] if (s["agent"], s["capability"]) not in cap_index]
    if missing:  # 재개 사이에 에이전트가 삭제·비활성화된 경우
        task.state, task.ended_at = "failed", utcnow()
        task.answer = f"에이전트 사용 불가 / unavailable: {[s['agent'] for s in missing]}"
        db.commit()
        await emit({"type": "RUN_ERROR", "message": task.answer})
        return out(task)
    final = await engine.run(db, task, cap_index, emit, resume=resume)
    task.plan = {**task.plan, "steps": final["steps"]}
    task.results = dict(final["results"])
    if not final.get("pending") and not all(r.get("ok") for r in task.results.values()):
        task.results = await engine.compensate(db, task, task.results, cap_index, emit)  # 사가(D2-07)
    if final.get("pending"):
        task.state = "waiting_approval"
        if task.session_id:
            db.add(Message(session_id=task.session_id, role="assistant", kind="approval", content="",
                           task_id=task.id, meta={"pending": final["pending"]}))
        db.commit()
        await emit({"type": "RUN_FINISHED", "threadId": task.session_id or task.id, "runId": task.id,
                    "result": {"state": "waiting_approval"}})
        return {**out(task), "pending": final["pending"]}
    return await _finish(db, task, cap_index, emit, history, context)


async def start(db: Session, *, principal: str, role: str, message: str, session_id: str | None = None,
                agent_scope: str | None = None, emit: Emit = _noop, history: list[dict] | None = None,
                data_class: str = "L2", context: str | None = None) -> dict:
    with tracer().start_as_current_span("invoke_agent orchestrator") as span:
        span.set_attributes({"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.id": "orchestrator",
                             "gen_ai.agent.name": "AgentPlaza Orchestrator", "plaza.session_id": session_id or "",
                             "plaza.agent_scope": agent_scope or ""})
        out = await _start(db, principal=principal, role=role, message=message, session_id=session_id,
                           agent_scope=agent_scope, emit=emit, history=history, data_class=data_class,
                           context=context)
        span.set_attributes({"plaza.task_id": out["task_id"], "plaza.task_state": out["state"],
                             "plaza.steps": len(out["plan"].get("steps", []))})
        return out


BLOCKED = "보안 정책으로 이 요청을 처리할 수 없습니다(프롬프트 인젝션 의심) / blocked by the security policy (suspected prompt injection)"


async def input_guard(db: Session, message: str, principal: str, emit: Emit, resource: str) -> tuple[bool, list[str]]:
    """입력 가드레일(D9-06·NFR-S6) → (차단 여부, 리뷰어 신호). 차단·의심 모두 원장에 남긴다(원문 대신 해시)."""
    mode = gov.get(db)["guardrails"]["injection"]
    if mode == "off":
        return False, []
    found = guardrails.injection(message)
    if found["level"] == "none":
        return False, []
    blocked = mode == "block" and found["level"] == "injection"
    audit.record(db, actor=principal, actor_type="user", action="guardrail.blocked" if blocked else "guardrail.flagged",
                 resource=resource, outcome="denied" if blocked else "ok", args=message,
                 detail={"level": found["level"], "score": found["score"], "hits": found["hits"][:5]})
    await emit({"type": "CUSTOM", "name": "guardrail", "value": {"input": found["level"],
                                                                 "action": "blocked" if blocked else "flagged"}})
    return blocked, [f"input:{found['level']}"]


async def _start(db: Session, *, principal: str, role: str, message: str, session_id: str | None,
                 agent_scope: str | None, emit: Emit, history: list[dict] | None, data_class: str = "L2",
                 context: str | None = None) -> dict:
    task = Task(id=str(uuid.uuid4()), session_id=session_id, principal=principal, principal_role=role,
                message=message, plan={}, results={}, data_class=data_class, heartbeat_at=utcnow())
    db.add(task)
    db.commit()
    await emit({"type": "RUN_STARTED", "threadId": session_id or task.id, "runId": task.id})
    blocked, flags = await input_guard(db, message, principal, emit, f"task:{task.id}")
    if blocked:
        task.state, task.answer, task.ended_at = "blocked", BLOCKED, utcnow()
        task.plan = {"steps": [], "guard": {"blocked": True}}
        if task.session_id:
            db.add(Message(session_id=task.session_id, role="assistant", kind="text", content=BLOCKED, task_id=task.id))
        db.commit()
        await _emit_text(emit, f"msg_{task.id[:8]}", BLOCKED)
        await emit({"type": "RUN_FINISHED", "threadId": session_id or task.id, "runId": task.id})
        return out(task)
    caps, cap_index = _caps(db, agent_scope, role=role, level=data_class, user=principal)
    plan = await planner.make_plan(db, get_router(), message, caps, Caller(principal=principal), level=data_class)
    if flags:
        plan["guard"] = {"flags": flags}
    if context:
        plan["context"] = True  # 근거·메모리를 썼다는 사실만(내용은 Task 에 저장하지 않는다)
    for miss in plan.get("misses", []):
        await emit({"type": "CUSTOM", "name": "registry_miss", "value": miss})
    await emit({"type": "CUSTOM", "name": "plan", "value": {"source": plan["source"], "pattern": plan["pattern"],
                                                            "steps": plan["steps"]}})
    task.plan = plan
    db.commit()
    return await _execute(db, task, cap_index, emit, history, context=context)


async def resume(db: Session, task: Task, emit: Emit = _noop) -> dict:
    if task.state != "waiting_approval":
        return out(task)
    task.state = "running"
    db.commit()
    await emit({"type": "RUN_STARTED", "threadId": task.session_id or task.id, "runId": task.id})
    _, cap_index = _caps(db, None, role=task.principal_role, level=task.data_class or "L2", user=task.principal)
    return await _execute(db, task, cap_index, emit)


async def recover_stale() -> list[str]:
    """크래시 복구(D2-07): 진행 신호가 task_stale_seconds 넘게 멈춘 running 작업을 체크포인트에서 이어서 끝낸다.
    여러 워커가 동시에 돌아도 조건부 UPDATE 로 한 워커만 가져간다."""
    cutoff = utcnow() - timedelta(seconds=settings.task_stale_seconds)
    with SessionLocal() as db:
        ids = list(db.execute(select(Task.id).where(Task.state == "running", or_(
            Task.heartbeat_at < cutoff, Task.heartbeat_at.is_(None) & (Task.created_at < cutoff)))).scalars())
    done = []
    for tid in ids:
        with SessionLocal() as db:
            claimed = db.execute(update(Task).where(Task.id == tid, Task.state == "running").values(
                state="recovering", heartbeat_at=utcnow())).rowcount
            db.commit()
            if not claimed:
                continue
            task = db.get(Task, tid)
            task.state = "running"
            audit.record(db, actor="system", actor_type="system", action="task.recovered", resource=f"task:{tid}",
                         detail={"steps_done": len(task.results or {})})
            _, cap_index = _caps(db, None, role=task.principal_role, level=task.data_class or "L2",
                                 user=task.principal)
            await _execute(db, task, cap_index, _noop, resume=True)
            done.append(tid)
    return done


def out(task: Task) -> dict:
    return {"task_id": task.id, "state": task.state, "answer": task.answer, "plan": task.plan,
            "results": task.results, "session_id": task.session_id, "data_class": task.data_class}
