# 시험 결과 / Test Result — impl 3rd (Epic 3 LLM 게이트웨이)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · 호스트 Ollama(host.docker.internal:11434, granite4.1:3b·qwen3:8b) · 퍼블릭 키 0개
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 16, 통과 Pass: 16, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 53 passed (E3 13 + 회귀) · 실 Ollama 3건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E3-01 | PASS | llama3.2(conditional)는 기본 카탈로그에서 제외, granite·qwen3(Apache-2.0) 활성 |
| E3-02 | PASS | |
| E3-03 | PASS | |
| E3-04 | PASS | 대상 타임아웃 0.3s 로 단축해 시험 |
| E3-05 | PASS | 원장 detail.blocked = ["mock/echo-public"] |
| E3-06 | PASS | |
| E3-07 | PASS | |
| E3-08 | PASS | |
| E3-09 | PASS | |
| E3-10 | PASS | |
| E3-11 | PASS | |
| E3-12 | PASS | |
| E3-13 | PASS | 공급자 = mock, ollama |
| E3-14 | PASS | "AgentPlaza는 멀티 에이전트 플랫폼으로…" usage 45/71 |
| E3-15 | PASS | |
| E3-16 | PASS | x-plaza-fallback-from: ollama/missing-model:1b |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | (없음) | — | 설계 단계에서 스트림 계량을 별도 세션으로 분리(요청 의존성 종료 후에도 스트림 지속) | — |

## 첨부 / Logs

- `logs/make-test.r1.txt`, `logs/e3-ollama-live.txt`, `logs/e3-ollama-fast.json`, `logs/e3-live-fallback.txt`
