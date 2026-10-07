# impl 19th — Epic 24 품질 기준 상향: 접근성·MCP 계약

NFR: NFR-U4(접근성 — KWCAG 2.2 / WCAG 2.2 AA, PRD Q9) · NFR-P1(MCP 계약 — 2026-07-28 + 2025-11-25 initialize, PRD Q8)
COMPLIANCE 추가 시험: 접근성 자동 검사(axe)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E24-01 | 설치 7단계 계약: 두 핸드셰이크 | 템플릿 에이전트 | server/discover·initialize 각각 tools == 선언, 오류 0 | P0 |
| E24-02 | initialize 미지원 탐지 | initialize 를 거부하는 에이전트(2026-07-28 만) | "MCP 2025-11-25(initialize) 계약 시험 실패" 1건 → 설치 롤백 사유 | P0 |
| E24-03 | `plaza test` 계약 항목 | 새 service 스캐폴드 | contract:mcp(2026-07-28)·contract:mcp-initialize(2025-11-25) PASS | P0 |
| E24-04 | 회귀(계약 메시지 변경) | e8_08 불일치 에이전트 | 두 핸드셰이크 각각 불일치 보고 | P1 |
| E24-05 | 접근성 자동 검사 | 로그인 + 콘솔 27화면 × 라이트·다크(axe wcag2a/aa·21a/aa·22aa, Addon iframe 포함) | 위반 0 | P0 |
| E24-06 | 실 스택 | 마켓 설치(7단계) · 게이트웨이 /mcp initialize · 마켓 산출물 plaza test | 8단계 ok · protocolVersion 2025-11-25 · 계약 4항목 PASS | P0 |
| E24-07 | 회귀 | make test · 콘솔 빌드(vitest) | 전체 통과 | P0 |
