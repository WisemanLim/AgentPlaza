# impl 8th — Epic 8 표준 프로토콜 MCP·A2A

> ⚠️ 요구사항 변경으로 재시험 필요 — MCP 계약 시험 기준 initialize 포함(PRD Q8) → Epic 24 (2026-10-07) → 재시험 완료: 19th(e8_08 두 핸드셰이크 보고), 2026-10-07

FR: D7-01, D7-02, D7-03, D7-04 (+ D6-04 경로 C 엔진) · NFR: NFR-P1, NFR-P2, NFR-P3, NFR-S5 · US5, US6
SDK: mcp 2.3.0(LATEST 2026-07-28) · a2a-sdk 1.2.2(프로토콜 1.0) — 사용법은 `logs/sdk-probe/` 의 검증 스크립트 기준

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E8-01 | 에이전트 SDK MCP 두 버전 | 공식 클라이언트 discover / initialize | tools=[calculate], call 42, 잘못된 인자 is_error, 키 없음 거부 | P0 |
| E8-02 | 에이전트 SDK A2A | 서명 카드 검증 + SendMessage(Data/텍스트) · hitl · 다중 capability | COMPLETED·GetTask · FAILED(승인 없음) · FAILED(지정 필요) | P0 |
| E8-03 | 플랫폼 MCP 게이트웨이 (US5) | /mcp/calc x-api-key(범위 calc) | tools/list·call 성공, 원장 channel=mcp, 범위 밖 403·무인증 401·없는 에이전트 404·비활성 403 | P0 |
| E8-04 | 승인 우회 차단 (DP8) | MCP 로 hitl.execute_action | is_error + tool.approval_bypass_blocked | P0 |
| E8-05 | Orchestrator 를 MCP·A2A 로 (PRD 4.2) | orchestrate 도구 · A2A Task | succeeded · COMPLETED, 무인증 A2A 401 | P0 |
| E8-06 | 플랫폼 A2A 카드·프록시 (D7-03) | 공개 카드 · 인증 프록시 | 서명(EdDSA, kid=JWKS) · skills=agent.yaml · 7*6=42 · 무인증 401 · server.json 인증 필요 | P0 |
| E8-07 | 경로 C 원격 연동 (US6·D7-02·D7-04) | 원격 A2A·MCP 등록 → 계획 실행 → 재검증 → 원격 도구 변경 | 201(external) · 42 → review pass · ok · rug_pull 탐지(unhealthy) · 잘못된 URL 422 | P0 |
| E8-08 | 생성물 vs 런타임 (NFR-P3) | 선언과 다른 앱 | MCP tools 불일치·카드 불일치 검출 | P0 |
| E8-09 | JWKS·카드 변조 | jwks · 서명 후 변조 | kid 일치 · 검증 실패 | P1 |
| E8-10 | 실 설치 계약 시험 | calc 업로드(mcp·a2a 포함 이미지) | 8단계 성공, 7단계에서 실 MCP tools/list·서명 카드 검증 | P0 |
| E8-11 | 실 MCP·A2A (Traefik 경유) | curl: 카드 · discover/list/call · initialize · 무인증 · SendMessage | 공개 서명 카드 · 2026-07-28 · 144 · 2025-11-25 · 401 · COMPLETED | P0 |
| E8-12 | 실 경로 C | 호스트 단독 reviewer 를 A2A·MCP 로 등록 → 실 LLM 계획 | 등록 · PII revise · 재검증 ok | P0 |
| E8-13 | M1 카드 외부 주소 | PORT=8099 / AGENT_PUBLIC_URL 지정 | 자동 8099 · 지정값 | P1 |
