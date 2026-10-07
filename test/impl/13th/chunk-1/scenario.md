# impl 13th · chunk-1 — 시크릿·정책 엔진 (D9-04, D9-05)

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
