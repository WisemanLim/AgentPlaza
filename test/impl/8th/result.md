# 시험 결과 / Test Result — impl 8th (Epic 8 표준 프로토콜 MCP·A2A)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · mcp 2.3.0 · a2a-sdk 1.2.2 · 실 스택(Traefik·runtime)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 13, 통과 Pass: 13, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 128 passed (E8 9 + 회귀) · 실 스택 4건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E8-01 | PASS | 요청별 세션 매니저(lifespan 불필요) |
| E8-02 | PASS | |
| E8-03 | PASS | |
| E8-04 | PASS | |
| E8-05 | PASS | |
| E8-06 | PASS | |
| E8-07 | PASS | |
| E8-08 | PASS | |
| E8-09 | PASS | |
| E8-10 | PASS | 17s |
| E8-11 | PASS | A2A Data Part 는 protobuf Struct 라 정수가 실수로 옴(100 → 100.0) |
| E8-12 | PASS | 원격 카드 미서명 → signature=absent 로 표시 |
| E8-13 | PASS | |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 0 | NFR-S5 스캔: 공개 카드 경로 미허용 | 새 공개 경로 | 카드·JWKS 허용목록, server.json 은 인증 필요로 | 119→128 passed |
| 0 | (설계) MCP 세션 매니저가 lifespan 필요 | SDK 구조 | 요청마다 매니저 생성·같은 코루틴에서 run→handle (실측 검증) | — |
| 1 | M1 카드가 포트 변경을 반영 못 함 | standalone compose 가 AGENT_PUBLIC_URL·PORT 미전달 | `AGENT_PUBLIC_URL=${AGENT_PUBLIC_URL:-http://127.0.0.1:${PORT:-8001}}` | E8-13 |
| 1 | 원격 연동 삭제 시 인증 비밀 파일 잔존 가능 | uninstall 이 secrets 미처리 | link 삭제 시 data/secrets/{id}.json 파기 | 잔여 0 |
| — | Traefik 이 /a/{id}/.well-known·/a2a 를 api 로 보내지 않음 | 라우터 규칙 | PathRegexp 추가 | E8-11 |

## 미실행·대체

- NFR-P1 의 MCP Inspector CLI(npx)는 네트워크 설치가 필요해 실행하지 않음 → 공식 python-sdk 클라이언트(2026-07-28·2025-11-25)로 대체.

## 첨부 / Logs

- `logs/sdk-probe/` (SDK 검증 스크립트), `logs/make-test.r0~r2.txt`, `logs/e8-install.txt`, `logs/e8-live-protocols.txt`, `logs/e8-live-link.txt`
