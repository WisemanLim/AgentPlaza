# impl 16th — Epic 16 LLM·프로토콜 확장

> ⚠️ 요구사항 변경으로 재시험 필요 — OpenAI 호환 서버·에이전트=모델 경로가 Bifrost 전환 영향(PRD Q1) → Epic 20 (2026-10-07) → 재시험 완료: 20th·21st(Bifrost 경유·Assistant 전환 후 e16 통과), 2026-10-07

FR: D1-02, D1-04, D7-05, D7-06 · NFR: NFR-P4 · UI LLM 'OpenAI 호환 서버'·원격 등록 OpenAPI·채팅 자동 재연결

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E16-01 | OpenAPI → 도구 (D7-05) | 가짜 REST(인증 헤더) · 실 board 백엔드 /api/openapi.json | operation 마다 capability·MCP 도구, path/query/본문 매핑, 핀 변경 시 rug-pull 의심 | P0 |
| E16-02 | 잘못된 문서·오버레이 | paths 없는 문서 · vllm/llama-server/tei/cli-bridge 오버레이 | 422 · compose config OK | P1 |
| E16-03 | 에이전트 = 모델 (D7-05) | /v1/models · model=agent/<id> 완료·스트림 · 범위 밖 키 · 없는 에이전트 | 목록에 agent/*, Orchestrator 결과 답변·SSE, 403, 404 | P0 |
| E16-04 | OpenAI 호환 서버 (D1-02) | 서버 등록(키) → 모델 조회 → 카탈로그 → 별칭 호출 · 삭제 · 예약어 | 키는 시크릿 저장소, L3 로컬 허용, 삭제 시 모델 비활성, 422 | P0 |
| E16-05 | CLI 브리지 (D1-04) | 가짜 claude stream-json · 가짜 ACP, local=false | L0 응답·스트림, L2 403(퍼블릭 차단), ACP 권한 요청 거절, 잘못된 토큰 401 | P0 |
| E16-06 | NDJSON 형식 | claude assistant·stream_event·result · codex item/msg · gemini message · system | 증분·최종 텍스트 추출 | P1 |
| E16-07 | 오류·ACP 직접 | is_error 결과 · run_acp | BridgeError · 텍스트+권한 거절 | P1 |
| E16-08 | AG-UI 적합 (D7-06) | LLM 단독·병렬 도구 흐름 · 잘못된 순서 표본 | check() 오류 0 · 잘못된 표본 오류 ≥3 | P0 |
| E16-09 | 재연결 재개 (NFR-P4) | 완료 스트림 Last-Event-ID 3 · after=0 · 다른 사용자 | 4번부터 동일 · 전체 · 404 | P0 |
| E16-10 | 끊김 후 계속 실행 | 첫 이벤트만 읽고 끊음 → 재연결 · 실 스택 curl 2초 끊김 | RUN_FINISHED·stream_end 까지 수신, id 연속 | P0 |
| E16-11 | 회귀·콘솔 | make test · LLM 서버 화면 · 원격 등록 OpenAPI | 전체 통과 · 스크린샷 | P0 |
