"""관측·평가 API (D10-04 자체 경량 LLM 관측, D10-05 평가). admin 이상.

- 사용량·비용: llm_usage 집계(일·모델·별칭·에이전트·사용자, 지연 p50/p95, 폴백·오류)
- 트레이스: trace_spans(플랫폼 OTel 스팬) — 목록(루트 스팬)·상세(트리)·세션별
- 평가: 시나리오 묶음 CRUD · 실행(백그라운드) · 결과·회귀 · 플레이그라운드 비교(같은 프롬프트를 여러 별칭에)
"""
import time
import uuid
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin
from app.db import get_db, utcnow
from app.evals import runner
from app.llm.providers import ChatRequest
from app.llm.router import AllTargetsFailed, Caller, NoRoute, PolicyDenied, get_router, parse_data_class
from app.models import EvalRun, EvalSuite, LlmUsage, TraceSpan
from app.observability import flush
from app.services import audit

router = APIRouter(tags=["observability"], dependencies=[Depends(require_admin)])


def _pct(values: list[int], p: float) -> int:
    if not values:
        return 0
    v = sorted(values)
    return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]


@router.get("/api/obs/usage")
def usage(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    rows = list(db.execute(select(LlmUsage).where(LlmUsage.ts >= utcnow() - timedelta(days=days))).scalars())

    def group(key):
        out: dict = {}
        for r in rows:
            k = key(r) or "-"
            g = out.setdefault(k, {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0, "errors": 0, "fallbacks": 0,
                                   "lat": []})
            g["calls"] += 1
            g["tokens_in"] += r.tokens_in
            g["tokens_out"] += r.tokens_out
            g["cost"] += r.cost
            g["errors"] += r.outcome != "ok"
            g["fallbacks"] += r.fallback_from is not None
            g["lat"].append(r.latency_ms)
        return [{"key": k, **{x: v for x, v in g.items() if x != "lat"}, "cost": round(g["cost"], 6),
                 "p50_ms": _pct(g["lat"], 0.5), "p95_ms": _pct(g["lat"], 0.95)}
                for k, g in sorted(out.items(), key=lambda kv: -kv[1]["calls"])]
    total = group(lambda r: "all")
    return {"days": days, "total": total[0] if total else {"calls": 0, "cost": 0.0},
            "by_day": sorted(group(lambda r: r.ts.date().isoformat()), key=lambda x: x["key"]),
            "by_model": group(lambda r: r.model), "by_alias": group(lambda r: r.alias),
            "by_agent": group(lambda r: r.agent_id), "by_user": group(lambda r: r.principal),
            "by_class": group(lambda r: r.data_class)}


def _span_out(s: TraceSpan) -> dict:
    return {"trace_id": s.trace_id, "span_id": s.span_id, "parent_id": s.parent_id, "name": s.name, "kind": s.kind,
            "start": s.start, "duration_ms": s.duration_ms, "status": s.status, "attributes": s.attributes}


@router.get("/api/obs/traces")
def traces(limit: int = Query(50, ge=1, le=200), q: str | None = None, session_id: str | None = None,
           db: Session = Depends(get_db)):
    """최근 트레이스(로컬 루트 기준) + 요약(스팬 수·오류·도구·모델·토큰).
    로컬 루트 = 같은 트레이스 안에 부모가 저장돼 있지 않은 스팬. 부모는 외부(호출자 traceparent·FastAPI 요청 스팬)일 수 있다."""
    flush()
    recent = list(db.execute(select(TraceSpan).order_by(TraceSpan.start.desc()).limit(limit * 30)).scalars())
    by_trace: dict[str, list[TraceSpan]] = {}
    for sp in recent:
        by_trace.setdefault(sp.trace_id, []).append(sp)
    out = []
    for tid, spans in by_trace.items():
        ids = {x.span_id for x in spans}
        roots = sorted((x for x in spans if x.parent_id not in ids), key=lambda x: (not x.name.startswith("invoke_agent"), x.start))
        r = roots[0]
        if q and q.lower() not in r.name.lower():
            continue
        if session_id and r.attributes.get("plaza.session_id") != session_id:
            continue
        out.append({**_span_out(r), "spans": len(spans), "errors": sum(x.status == "error" for x in spans),
                    "tools": sorted({x.attributes.get("plaza.capability") for x in spans if x.attributes.get("plaza.capability")}),
                    "models": sorted({x.attributes.get("plaza.model") for x in spans if x.attributes.get("plaza.model")}),
                    "tokens": sum(int(x.attributes.get("gen_ai.usage.input_tokens", 0) or 0)
                                  + int(x.attributes.get("gen_ai.usage.output_tokens", 0) or 0) for x in spans)})
        if len(out) >= limit:
            break
    return out


@router.get("/api/obs/traces/{trace_id}")
def trace(trace_id: str, db: Session = Depends(get_db)):
    flush()
    spans = list(db.execute(select(TraceSpan).where(TraceSpan.trace_id == trace_id).order_by(TraceSpan.start)).scalars())
    if not spans:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "트레이스 없음 / not found")
    return {"trace_id": trace_id, "spans": [_span_out(s) for s in spans]}


class SuiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    agent_scope: str | None = None
    cases: list[dict] = Field(min_length=1, max_length=200)


def _suite_out(s: EvalSuite, last: EvalRun | None = None) -> dict:
    return {"id": s.id, "name": s.name, "agent_scope": s.agent_scope, "cases": s.cases, "created_by": s.created_by,
            "created_at": s.created_at, "last_run": _run_out(last, brief=True) if last else None}


def _run_out(r: EvalRun, brief: bool = False) -> dict:
    out = {"id": r.id, "suite_id": r.suite_id, "status": r.status, "passed": r.passed, "total": r.total, "score": r.score,
           "started_at": r.started_at, "finished_at": r.finished_at,
           "regressions": sum(x.get("regression", False) for x in r.results)}
    return out if brief else {**out, "results": r.results}


@router.get("/api/evals/suites")
def list_suites(db: Session = Depends(get_db)):
    out = []
    for s in db.execute(select(EvalSuite).order_by(EvalSuite.created_at)).scalars():
        last = db.execute(select(EvalRun).where(EvalRun.suite_id == s.id).order_by(EvalRun.started_at.desc())).scalars().first()
        out.append(_suite_out(s, last))
    return out


@router.post("/api/evals/suites", status_code=201)
def create_suite(body: SuiteIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    errs = runner.validate_cases(body.cases)
    if errs:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "; ".join(errs))
    s = EvalSuite(id=str(uuid.uuid4()), name=body.name, agent_scope=body.agent_scope, cases=body.cases, created_by=p.actor)
    db.add(s)
    db.commit()
    return _suite_out(s)


@router.delete("/api/evals/suites/{sid}")
def delete_suite(sid: str, db: Session = Depends(get_db)):
    s = db.get(EvalSuite, sid)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "없음 / not found")
    db.delete(s)
    db.commit()
    return {"deleted": sid}


@router.post("/api/evals/suites/{sid}/runs", status_code=202)
def start_run(sid: str, background: BackgroundTasks, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    s = db.get(EvalSuite, sid)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "없음 / not found")
    r = EvalRun(id=str(uuid.uuid4()), suite_id=sid, status="running", results=[], started_by=p.actor)
    db.add(r)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="eval.started", resource=f"eval:{sid}", detail={"run": r.id})
    background.add_task(runner.run, r.id, p.role)
    return {"run_id": r.id}


@router.get("/api/evals/runs/{rid}")
def get_run(rid: str, db: Session = Depends(get_db)):
    r = db.get(EvalRun, rid)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "없음 / not found")
    return _run_out(r)


@router.get("/api/evals/suites/{sid}/runs")
def list_runs(sid: str, db: Session = Depends(get_db)):
    q = select(EvalRun).where(EvalRun.suite_id == sid).order_by(EvalRun.started_at.desc()).limit(50)
    return [_run_out(r, brief=True) for r in db.execute(q).scalars()]


class CompareIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    targets: list[str] = Field(min_length=2, max_length=4)
    system: str | None = None


@router.post("/api/evals/compare")
async def compare(body: CompareIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db),
                  x_plaza_data_class: str | None = Header(default=None)):
    """플레이그라운드 A/B(UI H01·H02): 같은 프롬프트를 별칭 여럿에 보내 답·지연·토큰·비용을 나란히."""
    try:
        level = parse_data_class(x_plaza_data_class)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    messages = ([{"role": "system", "content": body.system}] if body.system else []) + [{"role": "user", "content": body.prompt}]
    out = []
    for alias in body.targets:
        started = time.monotonic()
        try:
            res, meta = await get_router().complete(db, alias, ChatRequest(messages=messages), level=level,
                                                    caller=Caller(principal=p.actor))
            usage_row = db.execute(select(LlmUsage).where(LlmUsage.alias == alias).order_by(LlmUsage.id.desc())).scalars().first()
            out.append({"target": alias, "model": meta.model, "answer": res.content, "usage": res.usage,
                        "latency_ms": int((time.monotonic() - started) * 1000), "cost": usage_row.cost if usage_row else 0.0})
        except (PolicyDenied, NoRoute, AllTargetsFailed) as exc:
            out.append({"target": alias, "error": f"{type(exc).__name__}: {exc}"})
    return {"results": out}
