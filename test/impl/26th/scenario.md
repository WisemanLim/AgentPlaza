# 시험 시나리오 — 26th: 문서 정리 + 전체 회귀 재검증 (구현 없음)

- 일자: 2026-10-07 · 근거: wds-implement 0-3 확인(5차) — "문서 정리 + 전체 회귀 재검증만"
- 대상: 전체 스택(P0·P1·P2, Epic 1–25) · local(SQLite) / prod 리허설(PostgreSQL 17 + pgvector, 로컬 Docker)
- 이번 차수에서 코드 변경 없음. 문서 변경: README(한/영) 오래된 줄 정리, 계획표 Epic 26–29(TODO, 다음 이터레이션) 등록, PRD §3.1·변경 이력, COMPLIANCE 미구현 줄.

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| R26-01 | 백엔드 전체 회귀 | `make test` | 284 passed, exit 0 | P0 |
| R26-02 | 추적성 | `python -m app.agentspec ... verify-coverage` | ok, P0 43 추적 · Epic 26–29 TODO 는 문제 아님 | P0 |
| R26-03 | 린트 | `ruff check --select F app test` | 새 위반 0 (기존 `a2a.types.Part` 1건은 범위 밖) | P1 |
| R26-04 | P0 콘솔 흐름 | `make e2e`(console.e2e — 로그인·채팅·마켓 설치·승인·i18n) | 4 passed | P0 |
| R26-05 | P1·P2 화면 | `E2E_SPEC=p1 make e2e`(E12–E25) | 전부 passed | P0 |
| R26-06 | 웹 위젯 | `E2E_SPEC=widget make e2e` | 허용 오리진 사이트에서 위젯 대화 PASS | P1 |
| R26-07 | 접근성 | `E2E_SPEC=a11y make e2e` | 65화면(라이트·다크·로그인·Addon) 위반 0 | P0 |
| R26-08 | prod 빌드 | `make prod-build` (web 이미지 안 `pnpm test && pnpm build`) | 빌드 성공 · vitest passed | P0 |
| R26-09 | prod 마이그레이션·DB | `make prod-all` → `make db-migrate ENV=prod` → `make db-ping ENV=prod` | alembic head 0015 · postgres OK | P0 |
| R26-10 | prod 스모크 | 게이트웨이 8091: health·상태·채널(위젯)·서명 없는 웹훅 401·이전 Epic API | 200/201/401 기대대로 | P0 |
| R26-11 | 정리 | `make prod-stop` | prod 컨테이너 0 | P0 |
| R26-12 | 문서 정합성 | README·PRD·계획표·COMPLIANCE grep | 'P2 범위 밖'·'알림 센터 미구현'(현행 서술) 0건 · TODO 행 = 26–29 | P1 |

비고: 실 결제대행 테스트 키(22nd)·실 메신저 연결(25th)은 계속 MANUAL. 시험 자격증명은 세션 임시값(스크래치패드), 문서에 옮기지 않음.
