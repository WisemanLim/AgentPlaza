# impl 5th — Epic 5 AI Assistant API

> ⚠️ 요구사항 변경으로 재시험 필요 — Assistant pydantic-ai 전환(PRD Q2) → Epic 21 (2026-10-07) → 재시험 완료: 21st(pydantic-ai, e5 회귀 통과), 2026-10-07

FR: D3-01(API), D3-02, D3-03 · NFR: NFR-C3(삭제권·보존), NFR-U5(스코프 채팅 API) · US8(채팅 승인 카드) · AG-UI SSE

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E5-01 | LLM 단독(강등) 스트리밍·세션 | `POST /api/chat/stream` | CUSTOM session → RUN_STARTED → mode=llm-only → TEXT_MESSAGE_* 다수 → RUN_FINISHED, 세션·메시지 저장, 자동 제목 | P0 |
| E5-02 | 대화 이력 전달 | 같은 세션 2턴 | LLM 입력 = system + 이전 2 + 현재 | P0 |
| E5-03 | Orchestrator 경로 도구 이벤트 | calc 계획 | TOOL_CALL_START/ARGS/END/RESULT, 결과 메타 저장 | P0 |
| E5-04 | 채팅 승인 카드 → 재개 | hitl 계획 → 승인 | approval_required·STATE_SNAPSHOT·RUN_FINISHED(waiting) · approval 메시지 · 승인 후 답변 메시지 추가 | P0 |
| E5-05 | 에이전트 스코프 채팅 | agent_scope=calc 에 ops 계획 | 세션 scope=calc, registry_miss | P0 |
| E5-06 | 세션 CRUD·검색·폴더·보관·내보내기·삭제권 | | 본문 검색 · 폴더 필터 · 보관 숨김 · md/json · 타인 404 · 삭제 시 메시지 파기 + 원장 | P0 |
| E5-07 | 보존 기간 파기 (NFR-C3) | 366일 전 세션 | purge 1, 404 | P1 |
| E5-08 | 저하·불가 이벤트 | [fail, echo] / [fail] | CUSTOM degraded{from,model} / RUN_ERROR + error 메시지 | P0 |
| E5-09 | 잘못된 등급 | data_class=L9 | 422 | P1 |
| E5-10 | 실 Ollama 스트리밍 | 한국어 질문 | 첫 바이트 즉시, 다수 청크, 한국어 답 | P0 |
