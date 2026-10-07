# 시험 결과 / Test Result — impl 16th (Epic 16 LLM·프로토콜 확장)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · CLI 브리지(표준 라이브러리) · 호스트 Ollama /v1 · board 에이전트 OpenAPI
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 11, 통과 Pass: 11, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 232 passed (E16 16 + 회귀 216) · 콘솔 vitest 7 passed · 실 스택 6건 · 콘솔 E2E 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E16-01 | PASS | pytest: createItem→getItem({{s1.id}}) 체인, 문서 변경 시 unhealthy. 실 스택: board 백엔드 OpenAPI → 도구 5개, /mcp/board-rest tools/call health → {status: ok} |
| E16-02 | PASS | paths 없음 422 · vllm·llama-server·tei·cli-bridge 오버레이 compose config OK |
| E16-03 | PASS | 실 스택: /v1/models 에 agent/board 등 4개, agent/board 완료(실 qwen3 계획·board.manage) · 스트림 23 청크 |
| E16-04 | PASS | 실 스택: 호스트 Ollama /v1 을 서버로 등록 → 모델 15개 조회 → granite 추가 → L3 호출 x-plaza-model=ollama-oai/granite4.1:3b |
| E16-05 | PASS | 실 스택 브리지 컨테이너: ndjson "fake-claude: 테스트 코드 작성해줘", acp "(permission denied)", 기본 L2 403 |
| E16-06 | PASS | 7가지 형식 |
| E16-07 | PASS | |
| E16-08 | PASS | 오류 0, 잘못된 표본 탐지 |
| E16-09 | PASS | seq 1부터 연속, Last-Event-ID 재개 동일, 타인 404 |
| E16-10 | PASS | pytest + 실 스택: curl 2초 후 끊김(id 3까지) → 재연결 id 4부터 stream_end 까지, 합친 이벤트 AG-UI 검사 오류 0, 실 LLM 답변 완결 |
| E16-11 | PASS | make test 232 · 콘솔: OpenAI 호환 서버(목록·서빙 모델 찾기·추가 버튼), 원격 등록 OpenAPI 선택 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | e5 시험 3건이 첫/마지막 이벤트 단언에서 실패 | 재연결용 전송 계층 이벤트(CUSTOM stream·stream_end)가 앞뒤에 추가됨 | 의도된 변경 — e5 시험 헬퍼에서 전송 계층 이벤트를 걸러 실행 이벤트 순서만 검사, 재연결은 e16 에서 검사 | 232 passed |
| 1 | (예방) 빈 TEXT_MESSAGE_CONTENT 가능성 | 빈 답변이면 delta "" 를 보냈음(AG-UI 위반) | 내용이 있을 때만 CONTENT 이벤트 | AG-UI 검사 0 |

## 첨부 / Logs

- `logs/make-test.txt`(232 passed), `logs/e16-live.txt`, `logs/e2e/screens/p1-16-*.png`
