# 시험 결과 / Test Result — impl 1st (Epic 1 플랫폼 기반)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · local=sqlite / prod=postgres(pgvector:pg17)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 13, 통과 Pass: 13, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 11 passed (E1-01~10 + health) · 실 스택 local smoke · prod(PostgreSQL) 마이그레이션·트리거·체인 검증

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E1-01 | PASS | SQLite: users·api_keys·audit_events·settings·alembic_version |
| E1-02 | PASS | 201 → 409 |
| E1-03 | PASS | 틀린 비번·없는 계정 모두 401, 같은 문구 |
| E1-04 | PASS | 5회 실패 후 423 |
| E1-05 | PASS | user→목록 403, admin→admin 생성 403, admin→supervisor 변경 403, admin→user 생성 201 |
| E1-06 | PASS | 임시 비밀번호는 생성 응답에만, 목록 미노출, 변경 후 로그인 200 |
| E1-07 | PASS | 비활성화 후 기존 토큰 401 |
| E1-08 | PASS | `ap_sk_` 1회 노출 · x-api-key=service · aud 토큰 교환 200 · 범위 밖 403 · 폐기 후 401 |
| E1-09 | PASS | verify ok → SQL 변조 후 ok=false, broken_at 반환 |
| E1-10 | PASS | 허용목록(/health, setup 2, login, token) 외 APIRoute 전부 401 |
| E1-11 | PASS | local 실 스택: 셋업 201 · 로그인 200 · 키 생성 · x-api-key me · 무인증 401 · verify ok |
| E1-12 | PASS | `make db-migrate ENV=prod` → alembic_version 0001, 동일 테이블 |
| E1-13 | PASS | PG `UPDATE`/`DELETE audit_events` → `audit_events is append-only` · prod verify ok(3건, timestamptz 정규화 확인) |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | alembic DeprecationWarning (`path_separator`) | alembic 1.20 설정 키 변경 | `alembic.ini` 에 `path_separator = os` | round 2: 11 passed, 경고 0 |
| 1 | (시험 하네스) zsh 에서 `$DCP` 단어 분리 안 됨 | zsh 기본 동작 | compose 래퍼 스크립트로 실행 | E1-12·13 재실행 PASS |

## 첨부 / Logs

- `logs/make-test.r1.txt`, `logs/make-test.r2.txt`, `logs/e1-11-smoke-local.txt`, `logs/e1-12-migrate-prod.txt`, `logs/e1-13-pg-trigger.txt`
- 로컬 개발용 계정(시험 중 생성): local `admin@local.test`, prod 리허설 `admin@prod.test` — 실데이터 아님
