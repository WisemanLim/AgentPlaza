# impl 4th — Epic 4 Orchestrator

FR: D2-01, D2-02, D2-03, D2-04, D2-06 · NFR: NFR-S4 · US8 · AG-UI 이벤트(PRD 12.5)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E4-01 | LLM 계획·순차 파이프라인 | service.upper → reviewer.review("{{s1.text}}") | 치환·결과 연결·이벤트 순서(RUN_STARTED…TOOL_CALL_*…TEXT_MESSAGE_*…RUN_FINISHED) | P0 |
| E4-02 | 병렬 패턴 | 독립 2단계 | depends_on 없음, 둘 다 실행 | P0 |
| E4-03 | 규칙 폴백 | LLM 출력이 JSON 아님 | source=rules, 키워드로 text-svc 선택 | P0 |
| E4-04 | registry_miss + general 폴백 | 없는 에이전트 계획 | CUSTOM registry_miss, LLM 일반 답 | P0 |
| E4-05 | 에이전트 스코프 | agent_scope=text-svc 에 calc 계획 | 단계 0, miss | P1 |
| E4-06 | 의존 실패 전파 | s1 실패 → s2 | s2 skipped, task failed | P1 |
| E4-07 | 도구 호출 감사 (NFR-S4) | 단계 실행 | tool.call 원장, args/result 해시 | P0 |
| E4-08 | HITL 승인 (US8) | hitl 단계 | waiting_approval · approval_required 이벤트 · user 403 · 본인 403 · 다른 admin 승인→재개 성공 · 재승인 409 · 원장 | P0 |
| E4-09 | HITL 거부 | reject | task failed, approval rejected | P0 |
| E4-10 | HITL 만료 (US8) | expires_at 과거 | 목록 제외, task canceled, 승인 409 | P0 |
| E4-11 | 에이전트 없음·카탈로그 | 등록 0 | general 답 · 내장 2종(assistant, orchestrator) | P0 |
| E4-12 | 작업 가시성 | 타인 작업 조회 | 404 (admin 은 200) | P1 |
| E4-13 | 실 LLM 계획 (qwen3:8b) + 실 컨테이너 | "17 곱하기 23 은 얼마인지 계산해줘" → 단독 calc 에이전트 | plan.source=llm, calc.calculate("17 * 23") → 391, 합성 답 | P0 |
