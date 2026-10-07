# 시험 결과 / Test Result — impl 17th (Epic 17 관측·평가)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · OTel 스팬 → 플랫폼 DB(trace_spans) · 호스트 Ollama(qwen3:8b 계획·판정, granite4.1:3b 합성) · 콘솔 /observe·/evals
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 8, 통과 Pass: 8, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 239 passed (E17 7 + 회귀 232) · 실 스택 5건 · `plaza test` 실 산출물 2건 · 콘솔 E2E 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E17-01 | PASS (round 2) | 실 스택: "게시판 글 목록을 보여줘" → 트레이스 invoke_agent orchestrator 14.4s · 스팬 4 · 트리 = chat plaza/orchestrator(qwen3, 415 tok, L2) → execute_tool board.manage(27ms) → chat plaza/chat(granite) |
| E17-02 | PASS | 1일 집계: 호출 101 · 토큰 33,157 · p50/p95 2,782/7,922ms · 모델별 5종(granite·qwen3·bge-m3·qwen2.5vl·ollama-oai) |
| E17-03 | PASS | 실 LLM 3사례(list·create·judge). 1차 2/3(list 가 create 로 계획됨) → 계획 프롬프트 수정 후 2차 list PASS, judge FAIL(점수 0.0) + 회귀 1 표시. 2차 judge 실패는 qwen3 가 "몇 개" 질문을 create 로 계획해 오류 답변을 낸 것 — 판정자가 근거 없는 답을 정확히 걸러냄(평가 기능의 의도된 동작) |
| E17-04 | PASS | 빈 expect·빈 input·잘못된 regex 422, 일반 사용자 obs/evals 403 |
| E17-05 | PASS | 실 스택: plaza/fast 2,097ms vs plaza/local 573ms 답변·비용 비교. pytest: 없는 별칭은 NoRoute 오류 행 |
| E17-06 | PASS | 마켓 board 1.0.0 산출물: 구조·문법·react export·SQL DDL·/health·인증·REST·MCP·A2A 카드 10/10. 새 service 스캐폴드: 11/11(evals wordcount·upper 포함), `--report` result.md 생성. pytest: DDL 위반·eval 불일치 시 FAIL·exit 1 |
| E17-07 | PASS | 30일 지난 스팬 retention 실행으로 삭제 |
| E17-08 | PASS | make test 239 · 콘솔: /observe 모델별 표·트레이스 상세 워터폴, /evals 묶음 점수·A/B 비교 결과 카드 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 실 스택 트레이스 목록이 비어 있음(pytest 는 통과) | FastAPI 0.142 가 환경 변수로 구성된 자체 공급자로 요청 스팬을 만들어, 우리 스팬의 부모가 저장소 밖(외부)에 있음 → '부모 없음' 루트 조건에 걸리지 않음 | 저장된 스팬 중 부모가 저장소에 없는 것을 '로컬 루트'로 묶음(app/api/obs.py) | 실 스택 트레이스 트리 정상 |
| 1 | 평가 list 사례 FAIL | 계획 프롬프트 예시가 create 뿐이라 qwen3 가 목록 요청도 create 로 계획 | 계획 프롬프트에 list 예시 + "요청 작업과 맞는 enum 값" 지시 추가(app/orchestrator/planner.py) | list PASS · 239 passed |

## 첨부 / Logs

- `logs/make-test.txt`(round 1, 239) · `logs/make-test-r2.txt`(round 2, 239) · `logs/e17-live.txt` · `logs/plaza-test/{board,svc17}-result.md` · `logs/e2e.txt` · `logs/e2e/screens/p1-17-*.png`
