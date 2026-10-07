# 시험 결과 / Test Result — 26th: 문서 정리 + 전체 회귀 재검증

- 일자 Date: 2026-10-07
- 대상 Target: 전체 스택(Epic 1–25) · local(SQLite) / prod 리허설(PostgreSQL 17 + pgvector, 로컬 Docker)
- 커밋 Commit: 없음 (git 미초기화) · 이번 차수 코드 변경 없음(문서·시험 데이터만)
- 판정 Verdict: **PASS** (12/12, round 2 — E18 E2E 시험 데이터 선택 수정)

## 요약 / Summary

- `make test` **284 passed** · verify-coverage ok(P0 43 추적, DONE Epic 25개) · 콘솔 vitest 7 passed(캐시 없이 web 이미지 재빌드)
- 콘솔 E2E: P0 4 · P1·P2 12(E12–E25) · 웹 위젯 1 · 접근성 65화면 위반 0
- prod 리허설: `make prod-build` → `make prod-all` → 마이그레이션 0015(head) → `postgres OK` → 스모크 → `make prod-stop`(잔여 0) — PASS
- 문서: README(한/영) 오래된 'P2 범위 밖'·'알림 센터 대신 배지' 줄 제거, 다음 이터레이션 줄 추가 · 계획표 Epic 26–29 TODO · PRD §3.1·변경 이력 · COMPLIANCE 미구현 줄

## 케이스 / Cases

| id | 판정 | 근거 |
|----|------|------|
| R26-01 | PASS | 284 passed in 99s (`logs/make-test.txt`) |
| R26-02 | PASS | `{"ok": true, "p0": 43, "planned": 43, "tested_p0": 43}` — Epic 26–29 TODO 는 문제 아님 (`logs/verify-coverage.txt`) |
| R26-03 | PASS(기존 경고) | 새 위반 0. 기존 25건: 테스트 픽스처 임포트 F811 20건(pytest 패턴, 오탐) · 미사용 임포트 F401 5건(`app/orchestrator/engine.py` operator, `app/protocols/link.py` a2a.types.Part, 시험 3건) — 이번 범위에서 수정하지 않음 (`logs/ruff.txt`) |
| R26-04 | PASS | FL-01·FL-02·FL-05·i18n 4 passed (`logs/e2e-p0.txt`) |
| R26-05 | PASS (round 2) | E12(acme-pro) 1 + 나머지 11 → E18 실패 → 시험 데이터 수정 후 E18 1 passed (`logs/e2e-p1a/b/c.txt`) |
| R26-06 | PASS | 허용 오리진 고객 사이트 → 위젯 대화 1 passed (`logs/e2e-widget.txt`) |
| R26-07 | PASS | 65 passed, `a11y.jsonl` 65행 위반 0 (`logs/a11y.txt`) |
| R26-08 | PASS | prod-build EXIT 0 · vitest 층이 캐시라 `build --no-cache web` 로 재실행 → Test Files 1 · Tests 7 passed (`logs/web-vitest-nocache.txt`) |
| R26-09 | PASS | alembic upgrade head EXIT 0 · `postgres OK` (`logs/prod-db.txt`) |
| R26-10 | PASS | health env=prod postgres ok · 0015(head) · 헬스 대시보드 전 구성요소 정상 · 위젯 생성 201·로더 200·CSP·실 답 · 메신저 서명 없음 401×3 · 이전 Epic API 200 · `/v1` plaza/fast 200 · 원장 verify ok · 무인증 401 (`logs/prod-smoke.txt`) |
| R26-11 | PASS | prod-stop EXIT 0 · prod 컨테이너 0 (`logs/prod-stop.txt`) |
| R26-12 | PASS | 오래된 문구 0건 · TODO 행 = 26 27 28 29 · DONE 25 (`logs/docs-check.txt`) |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1→2 | E18 E2E: 라이선스 검증 뒤 '등록' 버튼이 켜져 있음(기대: 꺼짐) | 시험 데이터 — 결제 완료 건이 2개(^0.1.0·^1.0.0)이고 목록 첫 건이 ^1.0.0 이라 카탈로그 현재 버전(1.0.0)을 덮어 6개 검증이 모두 통과(앱 동작은 정상) | E2E 변수에서 현재 버전을 덮지 않는 ^0.x 라이선스를 고르도록 실행 스크립트 수정(앱·시험 코드 변경 없음) | E18 1 passed |

## 남은 항목 / Remaining

- MANUAL: 실 결제대행 테스트 키(22nd) · 실 Slack/Telegram/카카오 연결(25th)
- 다음 이터레이션(계획표 TODO): Epic 26 OCI·사설 미러 설치 · 27 OIDC SSO · 28 메모리 LLM 자동 추출 · 29 기본 에이전트 컨테이너 분리
- 로컬 시험 데이터: E22 용 pending 구매 1건 추가(로컬 DB), E14 '지금 백업'·E18 게시 시도 기록이 늘어남

## 첨부 / Logs

`logs/make-test.txt` · `logs/verify-coverage.txt` · `logs/ruff.txt` · `logs/e2e-p0.txt` · `logs/e2e-p1a.txt`·`e2e-p1b.txt`·`e2e-p1c.txt` · `logs/e2e-widget.txt` ·
`logs/a11y.txt`·`logs/a11y/a11y.jsonl` · `logs/prod-build.txt` · `logs/web-vitest-nocache.txt` · `logs/prod-all.txt` · `logs/prod-db.txt` · `logs/prod-smoke.txt` · `logs/prod-stop.txt` · `logs/docs-check.txt`
