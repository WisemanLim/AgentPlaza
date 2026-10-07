# 시험 결과 / Test Result — dev-env 1st

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · local=sqlite / prod=postgres(`pgvector/pgvector:pg17`) · extras=redis(`valkey/valkey:8-alpine`) · domain=ict-saas
- 커밋 Commit: 없음 (git 저장소 미초기화)
- 환경: macOS (Apple Silicon) · Docker Compose v5.5.1

## 요약 / Summary

- 전체 Total: 11, 통과 Pass: 11, 실패 Fail: 0, 최종 Verdict: **PASS**
- round 1 에서 ENV-02 실패(포트 충돌) → 포트 변경 후 round 2 에서 ENV-02~11 전부 통과

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| ENV-01 | PASS | `Preflight OK`. WARN: `.env.prod` CHANGE_ME (리허설 허용) |
| ENV-02 | PASS (round 2) | api healthy · redis(valkey) up, `127.0.0.1:8010`·`6390` |
| ENV-03 | PASS | HTTP 200 `{"status":"ok","env":"local","db":{"engine":"sqlite","status":"ok"}}` |
| ENV-04 | PASS | `sqlite OK: /app/data/app.db` |
| ENV-05 | PASS | `1 passed, 1 warning` — StarletteDeprecationWarning(httpx → httpx2 권고), 기능 영향 없음 |
| ENV-06 | PASS | api·db healthy, valkey up, `127.0.0.1:8011`·`6391` |
| ENV-07 | PASS | `accepting connections` → `postgres OK` |
| ENV-08 | PASS | `wise-agentplaza` 컨테이너 0개 (볼륨 유지). 다른 프로젝트 컨테이너는 건드리지 않음 |
| ENV-09 | PASS | `PONG`, `valkey_version:8.1.10` — Valkey 이미지 교체 검증 |
| ENV-10 | PASS | `CREATE EXTENSION` · `vector 0.8.4` · L2 거리 `[1,2,3]<->[1,2,4] = 1` — pgvector 이미지 교체 검증 |
| ENV-11 | PASS | HTTP 200 `{"status":"ok","env":"prod","db":{"engine":"postgres","status":"ok"}}` |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | ENV-02 `Bind for 127.0.0.1:8000 failed: port is already allocated` | ① 같은 호스트의 다른 프로젝트(`aegismesh-local-api-1`)가 8000 점유 ② 스캐폴드 기본값이 local·prod 모두 API 8000·Valkey 6379 → 시나리오 순서(local 기동 중 prod 기동, ENV-06)에서도 충돌 | `.env.local` API 8010·Valkey 6390, `.env.prod`·`.env.example` API 8011·Valkey 6391. `scenario.md` ENV-03 포트 갱신 | round 2: ENV-02~11 PASS |

## 첨부 / Logs

- `logs/` 참조 (비커밋): `env-01-preflight.txt` … `env-11-prod-health.txt`, round 1 실패 로그 `env-02-local-all.txt`
