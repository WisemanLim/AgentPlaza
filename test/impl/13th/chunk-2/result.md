# 시험 결과 — impl 13th · chunk-2 (가드레일·리뷰어·게이트웨이, D9-06·D2-05·D7-07)

- 일자 Date: 2026-10-07 · 대상: local 스택(실 qwen3:8b·Valkey) + pytest + 콘솔 E2E

## 요약 / Summary

- 전체 Total: 9, 통과 Pass: 9, 실패 Fail: 0, 최종 Verdict: **PASS**

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E13-12 | PASS | 레드팀 공격 28/28 차단, 정상 20 중 차단 0 · 의심 2(리뷰어 회부만) |
| E13-13 | PASS | 실 채팅: guardrail blocked 이벤트·차단 문구·도구 미실행·원장. flag 모드는 실행 + 검토 |
| E13-14 | PASS | revise/block 반영(검토 전 토큰 미노출), 도구 결과 인젝션 신호 + 가드레일 하한 block, mode off |
| E13-15 | PASS | reviewer 유형 에이전트 지정 시 PII revise([REDACTED]) |
| E13-16 | PASS | 한국어 PII 10종 + 카드 Luhn 오탐 방지 |
| E13-17 | PASS | 실 스택 Valkey: 5/min → 6번째 429, Retry-After·X-RateLimit-*, 키 `rl:user:…:<창>` 확인. MCP 는 JSON-RPC -32029 |
| E13-18 | PASS (round 2) | 실 스택 user 키 tools/call 403 + gateway.tool_denied(mcp-header), tools/list 숨김, admin 키 200 |
| E13-19 | PASS (round 2) | 실 qwen3:8b 판정 JSON 파싱 → revise, review 이벤트·원장 |
| E13-20 | PASS | make test 197 passed · 콘솔 E2E(거버넌스·가드레일 점검·시크릿·채팅 알림) |
