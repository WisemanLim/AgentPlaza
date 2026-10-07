# impl 1st — Epic 1 플랫폼 기반 (데이터 모델·인증·RBAC·API 키·감사 원장)

FR: D10-06, D9-01, D9-02, D9-03, D9-07 · NFR: NFR-O5, NFR-S4(일부), NFR-S5 · COMPLIANCE: 감사로그 무결성

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E1-01 | 스키마 (SQLite) | `alembic upgrade head` | users·api_keys·audit_events·settings | P0 |
| E1-02 | 최초 관리자 1회 | `POST /api/setup/admin` ×2 | 201 → 409 | P0 |
| E1-03 | 로그인·일반화 오류 | 올바름/틀린 비번/없는 계정 | 200 / 401·401 같은 문구 | P0 |
| E1-04 | 5회 실패 잠금 | 틀린 비번 5회 후 정상 로그인 | 423 | P1 |
| E1-05 | RBAC 하위권한만 | user→/api/users, admin→admin 생성, admin→supervisor 변경 | 403·403·403, admin→user 생성 201 | P0 |
| E1-06 | 임시 비밀번호 1회·변경 | 생성 응답 / 목록 / 변경 후 로그인 | 1회 노출 · 미노출 · 200 | P1 |
| E1-07 | 비활성 계정 차단 | 비활성화 후 기존 토큰 | 401 | P0 |
| E1-08 | API 키 수명주기 | 생성·x-api-key·토큰 교환(aud)·범위 밖·폐기 | 1회 노출 · service · 200 · 403 · 401 | P0 |
| E1-09 | 감사 해시 체인·변조 탐지 | 이벤트 생성 → verify → SQL 변조 → verify | ok=true → ok=false, broken_at | P0 |
| E1-10 | 무인증 경로 허용목록 (NFR-S5) | 모든 APIRoute 를 자격증명 없이 호출 | 허용목록 외 전부 401 | P0 |
| E1-11 | 실 스택 smoke (local) | curl 셋업→로그인→키 생성→x-api-key→감사 verify | 201·200·201·200·ok | P0 |
| E1-12 | PostgreSQL 마이그레이션 (NFR-O5) | `make db-migrate ENV=prod` | 동일 리비전 0001 적용 | P0 |
| E1-13 | PG append-only 트리거 | `UPDATE audit_events …` (prod) | `audit_events is append-only` 오류 | P1 |
