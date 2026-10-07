# impl 10th — Epic 10 콘솔 API·셋업 위저드·OTel

FR: D10-01, D10-02, D10-03 · NFR: NFR-O1, NFR-U1(흐름), NFR-C3(설정 반영) · UI B02·M04·L01·L02·A02

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E10-01 | LLM 스팬 GenAI 속성 (NFR-O1) | /v1 호출 · 스트림 폴백 | gen_ai.system·request/response.model·usage·data_class, 프롬프트 원문 없음 · fallback_from·stream·degraded | P0 |
| E10-02 | 도구 스팬·부모·traceparent | 채팅→오케스트레이터→probe 에이전트 | execute_tool(tool.name·agent.id·capability·session_id), invoke_agent 의 자식, 에이전트 요청에 traceparent | P0 |
| E10-03 | 대시보드 타일 (B02) | GET dashboard | 6 타일, 30초 폴링 | P0 |
| E10-04 | 시스템 설정 (L01) | 보존 30일 · 0 · 미지정 키 · admin | 반영 · 422 · 422 · 403, 31일 세션 파기 | P0 |
| E10-05 | 내 프로필 (L02) | locale·theme | 저장·조회, 잘못된 theme 422 | P1 |
| E10-06 | 셋업 위저드 (A02) | progress → llm(조건부 409, 정상) → complete 409 → models skip → agents → complete | 별칭 구성, board 설치·healthy, 완료, 런타임 상태, user 403 | P0 |
| E10-07 | 실 Ollama 감지 | GET /api/setup/llm | reachable, 권장 모델, 퍼블릭 키 보유 여부(값 비노출) | P0 |
| E10-08 | 실 수집기 스팬 | LLM·오케스트레이터·도구 호출 | collector 에 chat·execute_tool·invoke_agent + GenAI 속성 | P0 |
| E10-09 | 플랫폼 재생성 후 네트워크 복구 | api 재생성 / 강제 분리 | 기동 시 즉시 · 10초 주기 재연결, 오케스트레이션 성공 | P0 |
