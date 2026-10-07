"""평가 실행기 (D10-05): 시나리오마다 Orchestrator 를 실제로 돌리고 기대값으로 채점한다.

expect(모두 선택):
  contains / not_contains: [문자열]  답변에 있어야/없어야(대소문자 무시)
  regex: 패턴                       답변이 일치
  tool: "agent.verb"               그 도구가 성공적으로 실행됨
  state: succeeded|failed|waiting_approval
  judge: {rubric, threshold=0.7}   LLM 채점(plaza/orchestrator, 0~1)
점수 = 통과한 검사 비율(judge 는 그 점수). 사례 통과 = 모든 검사 통과. 직전 실행과 비교해 회귀(통과→실패)를 표시한다.
"""
import json
import re
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal, utcnow
from app.llm.providers import ChatRequest
from app.llm.router import AllTargetsFailed, Caller, NoRoute, PolicyDenied, get_router
from app.models import EvalRun, EvalSuite

JUDGE = ("You grade an AI assistant answer against a rubric. Respond with ONLY JSON {\"score\": <0..1>, \"reason\": "
         "\"<short>\"}.")
KEYS = {"contains", "not_contains", "regex", "tool", "state", "judge"}


def validate_cases(cases) -> list[str]:
    errs = []
    if not isinstance(cases, list) or not cases:
        return ["cases 는 1개 이상 목록"]
    for i, c in enumerate(cases):
        if not isinstance(c, dict) or not isinstance(c.get("input"), str) or not c["input"].strip():
            errs.append(f"#{i} input 문자열 필요")
            continue
        exp = c.get("expect") or {}
        if not isinstance(exp, dict) or not exp or set(exp) - KEYS:
            errs.append(f"#{i} expect 는 {sorted(KEYS)} 중 1개 이상")
        if "regex" in exp:
            try:
                re.compile(exp["regex"])
            except re.error as exc:
                errs.append(f"#{i} regex 오류: {exc}")
    return errs


async def _judge(db: Session, rubric: str, question: str, answer: str, principal: str) -> tuple[float, str]:
    req = ChatRequest(messages=[{"role": "system", "content": JUDGE},
                                {"role": "user", "content": json.dumps({"rubric": rubric, "question": question,
                                                                        "answer": answer[:4000]}, ensure_ascii=False)}],
                      temperature=0, response_format={"type": "json_object"})
    try:
        res, _ = await get_router().complete(db, "plaza/orchestrator", req, caller=Caller(principal=principal))
        m = re.search(r"\{.*\}", re.sub(r"<think>.*?</think>", "", res.content, flags=re.S), re.S)
        data = json.loads(m.group(0)) if m else {}
        return max(0.0, min(1.0, float(data.get("score", 0)))), str(data.get("reason", ""))[:200]
    except (AllTargetsFailed, NoRoute, PolicyDenied, ValueError, TypeError) as exc:
        return 0.0, f"judge unavailable: {type(exc).__name__}"


async def score_case(db: Session, case: dict, out: dict, principal: str) -> tuple[list[dict], float]:
    answer = out.get("answer") or ""
    exp = case.get("expect") or {}
    checks = []
    for s in exp.get("contains", []):
        checks.append({"check": f"contains:{s}", "ok": s.lower() in answer.lower()})
    for s in exp.get("not_contains", []):
        checks.append({"check": f"not_contains:{s}", "ok": s.lower() not in answer.lower()})
    if "regex" in exp:
        checks.append({"check": f"regex:{exp['regex']}", "ok": re.search(exp["regex"], answer) is not None})
    if "tool" in exp:
        ran = {f"{r.get('agent')}.{r.get('capability')}" for r in (out.get("results") or {}).values() if r.get("ok")}
        checks.append({"check": f"tool:{exp['tool']}", "ok": exp["tool"] in ran, "detail": sorted(ran)})
    if "state" in exp:
        checks.append({"check": f"state:{exp['state']}", "ok": out.get("state") == exp["state"], "detail": out.get("state")})
    judge_score = None
    if "judge" in exp:
        j = exp["judge"] if isinstance(exp["judge"], dict) else {"rubric": str(exp["judge"])}
        judge_score, reason = await _judge(db, j["rubric"], case["input"], answer, principal)
        checks.append({"check": "judge", "ok": judge_score >= float(j.get("threshold", 0.7)), "score": judge_score,
                       "detail": reason})
    ratio = sum(c["ok"] for c in checks) / len(checks) if checks else 0.0
    return checks, (judge_score if judge_score is not None and len(checks) == 1 else ratio)


async def run(run_id: str, role: str) -> None:
    from app.orchestrator import service as orchestrator
    with SessionLocal() as db:
        r = db.get(EvalRun, run_id)
        suite = db.get(EvalSuite, r.suite_id)
        results = []
        for i, case in enumerate(suite.cases):
            started = time.monotonic()
            try:
                out = await orchestrator.start(db, principal=r.started_by, role=role, message=case["input"],
                                               agent_scope=case.get("agent_scope") or suite.agent_scope,
                                               data_class=case.get("data_class", "L2"))
            except Exception as exc:  # noqa: BLE001 — 사례 하나의 실패가 실행 전체를 멈추지 않는다
                out = {"state": "error", "answer": f"{type(exc).__name__}: {exc}", "results": {}}
            checks, score = await score_case(db, case, out, r.started_by)
            results.append({"id": case.get("id") or f"c{i + 1}", "input": case["input"], "answer": (out.get("answer") or "")[:800],
                            "state": out.get("state"), "task_id": out.get("task_id"), "checks": checks,
                            "passed": bool(checks) and all(c["ok"] for c in checks), "score": round(score, 3),
                            "latency_ms": int((time.monotonic() - started) * 1000)})
        prev = db.execute(select(EvalRun).where(EvalRun.suite_id == suite.id, EvalRun.status == "done", EvalRun.id != r.id)
                          .order_by(EvalRun.started_at.desc())).scalars().first()
        before = {x["id"]: x["passed"] for x in (prev.results if prev else [])}
        for x in results:
            x["regression"] = before.get(x["id"]) is True and not x["passed"]
        r.results, r.total = results, len(results)
        r.passed = sum(x["passed"] for x in results)
        r.score = round(sum(x["score"] for x in results) / len(results), 3) if results else 0.0
        r.status, r.finished_at = "done", utcnow()
        db.commit()
