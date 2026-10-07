# 시험 결과 / Test Result — impl 4th (Epic 4 Orchestrator)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · LangGraph 1.2(StateGraph, 라이브러리만) · 계획 LLM: mock(시험) / qwen3:8b(실)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 13, 통과 Pass: 13, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 65 passed (E4 12 + 회귀) · 실 LLM 계획 + 실 에이전트 컨테이너 1건(6초)

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E4-01 | PASS | |
| E4-02 | PASS | |
| E4-03 | PASS | llm_error=ValueError |
| E4-04 | PASS | |
| E4-05 | PASS | |
| E4-06 | PASS | |
| E4-07 | PASS | |
| E4-08 | PASS | four-eyes: hitl_allow_self_approval=false |
| E4-09 | PASS | |
| E4-10 | PASS | |
| E4-11 | PASS | |
| E4-12 | PASS | |
| E4-13 | PASS | 답변이 영어로 생성됨(granite4.1:3b 합성) — 언어 일치는 프롬프트 개선 여지, 기능 판정에는 영향 없음 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 0 (설계) | SDK 가 AGENT_DATA_DIR·AGENT_MIGRATIONS 를 호출 시점 env 에서 읽음 → 한 프로세스 다중 에이전트 시 경로 혼선 | 전역 env 의존 | Agent 생성 시 경로 고정, 마이그레이션 기본 경로 = agent.yaml 위치 기준 | E2·E4 통과 |
| 1 | 실 시험 후 에이전트 삭제 시 SQLite 에 capability 고아 행 1건 | SQLite FK 기본 비활성(PG 와 동작 차이) | 엔진 connect 시 `PRAGMA foreign_keys=ON`, 고아 행 정리 | round 2: 65 passed |

## 첨부 / Logs

- `logs/make-test.r1.txt`, `logs/make-test.r2.txt`, `logs/e4-live-orchestrate.json`, `logs/e4-live-summary.txt`, `logs/calc-up.txt`
