# 시험 결과 / Test Result — impl 21st (Epic 21 Assistant pydantic-ai 전환)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · pydantic-ai-slim 1.107.7(MIT) · FunctionModel → 게이트웨이 라우터 → Bifrost → Ollama
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 6, 통과 Pass: 6, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 262 passed (E21 3 + 회귀 259) · 실 스택 3건 · 콘솔 E2E(E15 채팅·인용) 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E21-01 | PASS | instructions → 첫 system, 이미지 → data:image/png;base64 |
| E21-02 | PASS | run_stream 1회·2회(기록 2개), 지침 "존댓말" 이 system 에, check() 오류 0 |
| E21-03 | PASS | degraded {from: mock/fail-local, model: mock/echo} · llm_unavailable AllTargetsFailed + RUN_ERROR |
| E21-04 | PASS (round 2) | round 1: e5_01 "토큰 단위 스트리밍" 실패(pydantic-ai 가 0.1초 단위로 증분을 묶음) → debounce_by=None → e5·e15·e16 38 passed |
| E21-05 | PASS | LLM 단독: 증분 16·AG-UI 오류 0 · 두 번째 턴 "플라자야입니다."(기록 회상) · 이미지(콘솔 화면) "AgentPlaza" 인식(비전 모드) |
| E21-06 | PASS | make test 262 · E2E E15(지식 선택 → 인용 카드) — 로컬 시험 데이터가 지워져 있어 E15 시나리오 데이터 다시 적재 후 통과 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 응답이 한 번에 몰려 옴(CONTENT 1개) | pydantic-ai stream_text 기본 debounce 0.1초 | `stream_text(delta=True, debounce_by=None)` | e5_01 PASS |
| 1 | (예방) 빈 응답 시 예외 | pydantic-ai UnexpectedModelBehavior | 빈 답변으로 START/END 마무리(라우팅 전이면 llm_unavailable) | 코드 경로 |
| 1 | (시험 데이터) E15 E2E 가 컬렉션 없음으로 시간 초과 | 로컬 DB 의 지식 컬렉션·메모리가 비어 있음(이전 정리) | E15 라이브 스크립트의 적재 부분 재실행(logs/seed15.txt) | PASS |

## 첨부 / Logs

- `logs/make-test.txt`(262) · `logs/e21-live.txt` · `logs/seed15.txt` · `logs/e2e.txt` · `logs/e2e/screens/p1-15-*.png`
