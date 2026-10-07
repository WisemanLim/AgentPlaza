# impl 13th · chunk-2 — 가드레일·리뷰어·게이트웨이 (D9-06, D2-05, D7-07)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E13-12 | 레드팀 세트 (NFR-S6) | 공격 28 · 정상 20 | 공격 차단 ≥95%, 정상 차단 0, 의심 ≤15% | P0 |
| E13-13 | 입력 가드레일 | 채팅 인젝션(block) · flag 모드 | 차단 문구·도구 미실행·원장 / 실행 + 검토 회부 | P0 |
| E13-14 | 리뷰어 게이트 (D2-05) | 외부(egress) 결과 · 도구 결과 인젝션 · mode off | revise/block 반영(검토 전 미노출) · 가드레일 하한 block · 꺼짐 | P0 |
| E13-15 | 리뷰어 에이전트 | reviewer 유형 에이전트 지정 | PII revise → [REDACTED] | P1 |
| E13-16 | 한국어 PII 패턴 | 10종 · Luhn 오탐 | 각 1건 · 주문번호 미탐 | P0 |
| E13-17 | 레이트리밋 (D7-07) | 한도 3/2 · Valkey(실 스택) | 429 + Retry-After · MCP JSON-RPC -32029 · Valkey 키 rl:* | P0 |
| E13-18 | MCP 툴 RBAC (D7-07) | Mcp-Method·Mcp-Name 헤더 · tools/list | user 403 + 원장 · 목록 숨김 · admin 200 | P0 |
| E13-19 | 실 LLM 리뷰어 | reviewer mode=always, 실 qwen3 | JSON 판정 파싱·review 이벤트 | P1 |
| E13-20 | 회귀·콘솔 | make test · 거버넌스/시크릿/채팅 화면 | 전체 통과 · 스크린샷 | P0 |
