# 시험 결과 / Test Result — impl 2nd (Epic 2 agent.yaml·템플릿·스캐폴드·SDK)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` (플랫폼) · 생성 에이전트 `board`(app, python:3.12-slim + nginx-unprivileged)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 15, 통과 Pass: 15, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 40 passed (E2 29 케이스 파라미터 포함 + E1 회귀) · 실제 M1 단독 구동(round 5)

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E2-01 | PASS | 9유형 모두 유효 |
| E2-02 | PASS | 8가지 변형 모두 해당 오류 |
| E2-03 | PASS | |
| E2-04 | PASS | `stock-check` → verb `stock_check`, env.required 승계 |
| E2-05 | PASS | 결정적 zip, sha256 일치 |
| E2-06 | PASS | |
| E2-07 | PASS | |
| E2-08 | PASS | |
| E2-09 | PASS | |
| E2-10 | PASS | `__import__('os')…` → 400 |
| E2-11 | PASS | |
| E2-12 | PASS | |
| E2-13 | PASS | |
| E2-14 | PASS | `{"ok": true, "p0": 43, "planned": 43}` |
| E2-15 | PASS (round 5) | be/fe healthy, UI·프록시 200, ReadonlyRootfs·CapDrop ALL·Pids 256/128·User agent/101 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | Starlette `HTTP_422_UNPROCESSABLE_ENTITY` deprecated 경고 | Starlette 1.7 상수명 변경 | `HTTP_422_UNPROCESSABLE_CONTENT` | 경고 0 |
| 1 | E2-15 `can't set distinct values on 'pids_limit' and 'deploy.resources.limits.pids'` | compose v5 정규화 규칙 | pids 를 `deploy.resources.limits.pids` 로 일원화, E2-07 단언 갱신 | round 2 config 통과 |
| 2–3 | `127.0.0.1:8021 bind: address already in use` | macOS launchd 소켓이 8021 점유(사용자 lsof 로는 보이지 않음) | 시험 포트 8031/8032 사용, 이후 포트 확인은 `nc -z` | round 4 기동 |
| 4 | UI HTTP 000 | read_only + tmpfs `/etc/nginx/conf.d` 가 root 소유 → 비루트 nginx 가 envsubst 결과를 못 써 server 블록 없음 | tmpfs 를 `uid=101,gid=101` 로 마운트 | round 5 UI·프록시 200 |
| — | (시험 하네스) impl 차수 3rd 빈 디렉터리 생성 | 2nd 를 수동 생성 후 next-iteration 실행 | 빈 3rd 삭제(내용 없음 확인) | — |

## 첨부 / Logs

- `logs/make-test.r1.txt`, `logs/make-test.r2.txt`, `logs/verify-coverage.txt`, `logs/m1-up.r*.txt`, `logs/e2-m1-standalone.r5.txt`
- `logs/agents/board/` — 시험용 생성 에이전트(비커밋)
