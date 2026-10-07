# 시험 결과 / Test Result — impl 19th (Epic 24 품질 기준 상향: 접근성·MCP 계약)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · local 스택 · 콘솔(React 19) · Playwright + @axe-core/playwright 4
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 7, 통과 Pass: 7, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 253 passed (E24 3 + 회귀 250) · 접근성 55화면(라이트 27·다크 27·로그인) 위반 0 · 실 스택 3건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E24-01 | PASS | protocol_contract 오류 0(discover·initialize 각각 tools/list) |
| E24-02 | PASS | initialize 거부 에이전트 → "MCP 2025-11-25(initialize) 계약 시험 실패: …" 1건 |
| E24-03 | PASS | result.json: contract:mcp·contract:mcp-initialize ok, "2025-11-25 version=2025-11-25" |
| E24-04 | PASS | e8_08: 거짓 에이전트의 tools 불일치를 두 핸드셰이크 모두 보고 |
| E24-05 | PASS (round 2) | round 1: 12화면 color-contrast(상태 배지 글자 #E8A317 2.2:1·#2F9E44 3.4:1, 다크 위험 버튼 흰 글자 3.7:1) → round 2: 위반 0 |
| E24-06 | PASS | calculator 설치 8단계 ok(7단계 healthy) · 게이트웨이 initialize protocolVersion 2025-11-25 · plaza test contract:rest·mcp·mcp-initialize·a2a-card PASS |
| E24-07 | PASS | make test 253 · web 이미지 빌드 vitest 7·tsc·vite |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 상태 배지·완료 단계 글자 대비 부족(WCAG 1.4.3) | 채움·테두리용 상태색(ok·warn·danger)을 글자색으로도 씀 | 글자용 토큰 `--ok-text #1E6E2F`·`--warn-text #8A5A00`·`--danger-text`(다크 #F07878) 분리 — bg·card·primary-soft 모두 4.5:1 이상 | 55화면 위반 0 |
| 1 | 다크 테마 primary·danger 버튼 흰 글자 대비 3.0·3.7 | 다크 채움색이 밝음 | `--on-primary`·`--on-danger` 토큰(다크 #0F1220, 6.3·5.0:1) | 위반 0 |
| 1 | 설치 7단계가 initialize 를 명시적으로 시험하지 않음 | discover 실패 시에만 initialize 폴백 | `link.mcp_tools(mode=)` 로 두 핸드셰이크를 각각 시험, `plaza test` 에 contract:mcp-initialize | E24-01~04 |
| 1 | (시험 도구) a11y 결과 일부 유실 | 실패 시 Playwright 워커 재시작으로 afterAll 상태 소실 | 화면마다 JSON lines 로 즉시 기록 | 55행 |

## 첨부 / Logs

- `logs/make-test.txt`(253) · `logs/e24-live.txt` · `logs/a11y/{a11y.jsonl,summary.txt}`
