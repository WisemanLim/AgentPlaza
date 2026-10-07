# 시험 결과 / Test Result — 완료 게이트 (전체 회귀 + prod 리허설)

- 일자 Date: 2026-10-07
- 대상 Target: 전체 스택 · local(SQLite) / prod 리허설(PostgreSQL 17 + pgvector, 로컬 Docker)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 계획표 11/11 DONE, BLOCKED 0
- 전체 회귀 `make test` **145 passed** · 콘솔 vitest 6 passed · E2E 4 passed · verify-coverage ok(P0 43 추적)
- prod 리허설: `make prod-build` → `make db-migrate ENV=prod`(0001~0005) → `make db-ping ENV=prod`(postgres OK) → 게이트웨이 스모크 → `make prod-stop` — **PASS**

## prod 스모크 (게이트웨이 8091)

| 항목 | 결과 |
|---|---|
| /health · 콘솔 | 200 env=prod postgres ok · 콘솔 HTML |
| 로그인 · LLM 별칭(prod 는 mock 없음) | 200 · plaza/fast → ollama/granite4.1:3b 200 |
| 마켓 설치(실 runtime) → REST via gateway | succeeded → 200 (경쟁 조건 수정 후 설치 직후 즉시 200, 2/2) |
| A2A 카드(공개, 서명) · 오케스트레이션 · 원장 verify · 삭제 잔여 | 서명 카드 · succeeded · ok · 컨테이너·네트워크 0 |

## 발견 오류 및 수정 / Bugs & Fixes

| 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|----------|-----------|----------|---------------|
| prod api 로그 `FileExistsError: platform-ed25519.pem` | prod 워커 2개가 서명 키를 동시에 처음 생성 | 임시 파일 완성 후 `os.link` 원자적 게시, 기존 키 재사용 + 6 프로세스 동시 기동 시험(E8-10) | 145 passed, 로그 0건 |
| 설치 succeeded 직후 게이트웨이 경로가 웹 콘솔(405)로 빠짐 | 컨테이너 healthy 이후 Traefik 라우터 반영까지 1~2s | 8단계 노출에서 Traefik 경유 `/a/{id}/health` 확인 후 완료(`GATEWAY_INTERNAL_URL`) | 설치 직후 즉시 호출 2/2 200 |

## 첨부 / Logs

- `logs/prod-build.txt`, `logs/prod-migrate.txt`, `logs/prod-smoke.txt`, `logs/prod-route-race.txt`, `logs/prod-stop.txt`
