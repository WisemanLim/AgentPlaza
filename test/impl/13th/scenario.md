# impl 13th — Epic 13 거버넌스·보안

청크: chunk-1 = 시크릿·정책 엔진(E13-01~11) · chunk-2 = 가드레일·리뷰어·게이트웨이(E13-12~20) — 케이스 20 > 15(청킹 §B)

FR: D9-04, D9-05, D9-06, D2-05, D7-07 · NFR: NFR-S3, NFR-S6 · UI 거버넌스·시크릿 화면, 채팅 가드레일/검토 알림, 에이전트 키 회전

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E13-01 | 시크릿 저장소 (D9-04) | PUT·회전·목록·삭제, AAD 바꿔치기 | 암호문만 저장(원문 없음), version 증가, 목록에 값 없음, 다른 이름 복호화 실패, user 403 | P0 |
| E13-02 | secretRefs 주입 (D9-04) | secretRefs 선언 에이전트 설치(실 runtime) · 회전 | Install.env·workdir/.env·compose·docker inspect 에 원문 없음, 에이전트가 자기 키로 pull(타 키 401), 회전 30초 내 반영, 삭제 시 파기 | P0 |
| E13-03 | SDK 시크릿 | env 우선·캐시·로그 마스킹 | M1 은 env, 설치는 pull 1회 캐시, 로그에 값 없음 | P1 |
| E13-04 | 플랫폼 로그 마스킹 | 저장 값·ap_sk_·sk-·JWT·PEM | [REDACTED] | P0 |
| E13-05 | 게이트웨이 키 회전 | POST rotate-key | 새 키 1개 활성·이전 폐기, .env 갱신, 컨테이너 재생성 | P1 |
| E13-06 | 정책 API (D9-05) | 잘못된 값·미지 키·user | 422·422·403 | P0 |
| E13-07 | 등급별 허용 모델 | L1=local 로 변경 후 퍼블릭 별칭 | 403 + llm.policy_denied | P0 |
| E13-08 | 퍼블릭 PII 마스킹 (D9-06) | 주민번호·휴대폰 포함 메시지 → 퍼블릭/로컬 | 퍼블릭으로는 [RRN]·[PHONE], 로컬은 원문 | P0 |
| E13-09 | 도구 정책 | L3 + 비인가 에이전트 · approval_at_levels · 툴 RBAC · 거부 목록 | 계획 제외(miss) · 승인 대기 · user 제외/admin 실행 · 제외 | P0 |
| E13-10 | 내보내기 제한 | L3 세션 export | 403 + policy.export_denied | P1 |
| E13-11 | 감사 수준 | auditLevel=full · audit_level_min=full | 인자·결과 PII 마스킹 요약 기록 | P1 |
| E13-12 | 레드팀 세트 (NFR-S6) | 공격 28 · 정상 20 | 공격 차단 ≥95%, 정상 차단 0, 의심 ≤15% | P0 |
| E13-13 | 입력 가드레일 | 채팅 인젝션(block) · flag 모드 | 차단 문구·도구 미실행·원장 / 실행 + 검토 회부 | P0 |
| E13-14 | 리뷰어 게이트 (D2-05) | 외부(egress) 결과 · 도구 결과 인젝션 · mode off | revise/block 반영(검토 전 미노출) · 가드레일 하한 block · 꺼짐 | P0 |
| E13-15 | 리뷰어 에이전트 | reviewer 유형 에이전트 지정 | PII revise → [REDACTED] | P1 |
| E13-16 | 한국어 PII 패턴 | 10종 · Luhn 오탐 | 각 1건 · 주문번호 미탐 | P0 |
| E13-17 | 레이트리밋 (D7-07) | 한도 3/2 · Valkey(실 스택) | 429 + Retry-After · MCP JSON-RPC -32029 · Valkey 키 rl:* | P0 |
| E13-18 | MCP 툴 RBAC (D7-07) | Mcp-Method·Mcp-Name 헤더 · tools/list | user 403 + 원장 · 목록 숨김 · admin 200 | P0 |
| E13-19 | 실 LLM 리뷰어 | reviewer mode=always, 실 qwen3 | JSON 판정 파싱·review 이벤트 | P1 |
| E13-20 | 회귀·콘솔 | make test · 거버넌스/시크릿/채팅 화면 | 전체 통과 · 스크린샷 | P0 |
