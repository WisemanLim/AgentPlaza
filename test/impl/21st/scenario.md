# impl 21st — Epic 21 Assistant pydantic-ai 전환

FR: D3-01·D3-02·D3-03 · PRD Q2(Assistant SDK = pydantic-ai) · NFR: AG-UI 적합(D7-06), 데이터 등급·폴백(NFR-L1·L3)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E21-01 | 메시지 변환 | 플랫폼 기록 · 이미지 BinaryContent · instructions | pydantic-ai 메시지 ↔ OpenAI chat(system·user·assistant, data URI) | P0 |
| E21-02 | pydantic-ai 실행 경로 | 강등 모드 대화 + 맞춤지침 · 두 번째 턴 | Agent.run_stream 경유, 지침이 system 에, 기록 전달(system·user·assistant·user), AG-UI 오류 0 | P0 |
| E21-03 | 이벤트 유지 | 폴백 · 전부 실패 | degraded(from·model) · llm_unavailable + RUN_ERROR | P0 |
| E21-04 | 회귀 | e5(대화·세션·승인)·e15(첨부·비전·메모리·지식)·e16(재연결·AG-UI) | 전부 통과(토큰 단위 스트리밍 유지) | P0 |
| E21-05 | 실 스택 | Bifrost → granite·qwen2.5vl | LLM 단독·기록 회상·이미지 질의 응답, AG-UI 오류 0 | P0 |
| E21-06 | 회귀·콘솔 | make test · 채팅 화면(지식·인용) | 전체 통과 | P0 |
