# impl 6th — Epic 6 패키지·레지스트리 8단계

> ⚠️ 요구사항 변경으로 재시험 필요 — 설치 7단계 MCP 계약 시험에 initialize 명시 시험(PRD Q8) → Epic 24 (2026-10-07) → 재시험 완료: 19th(설치 7단계 두 핸드셰이크), 2026-10-07

FR: D5-01, D5-02, D5-05, D5-06, D5-07 (+ D4-07 API) · NFR: NFR-S1, NFR-S2(미검증 배지), NFR-I2, NFR-I6 · PRD 10.4

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E6-01 | 8단계 정상 경로 | app zip | ok·ok·skipped·skipped·ok·ok·ok·ok, healthy, federated compose(포트 0), .env 600(AGENT_API_KEY·게이트웨이 키), 산출물·버전, nav, 원장 | P0 |
| E6-02 | 다중 업로드 | zip 2개 | 파일별 작업 ID, 모두 성공 | P0 |
| E6-03 | 악성 코퍼스 (NFR-S1) | zip-slip·절대경로·심볼릭 링크·중첩·폭탄·비zip·매니페스트 없음·v1 flat | 2단계 거부 + 사유, 런타임 미호출 | P0 |
| E6-04 | 업로드 크기 상한 | 상한 0MB | 크기 초과 | P1 |
| E6-05 | SQL DDL 만 | CREATE/INDEX · INSERT · ATTACH · PRAGMA | 통과 · 거부 · 거부 · 거부 | P0 |
| E6-06 | FTS5·금지·경고·문법 | rag 템플릿 · docker.sock · subprocess · 문법 오류 | 통과 · 거부 · 경고만 · 거부 | P0 |
| E6-07 | 정책 게이트 (NFR-I2) | inprocess · docker:true · 내장 id · federation | 모두 거부(사유) | P0 |
| E6-08 | required_env | 누락 / 제공 + 미선언 키 | 거부 / 성공, 선언 키만 주입 | P0 |
| E6-09 | 버전 규칙 | 동일 버전 · force · 상위 버전 | 거부 · 재설치 · 업그레이드, current 갱신 | P0 |
| E6-10 | 업그레이드 실패 복구 | 0.2.0 기동 실패 | rolled_back, 0.1.0 current 복원 | P0 |
| E6-11 | 신규 설치 실패 무흔적 | 빌드 실패 · 헬스 실패 | failed(5) · rolled_back(7), 카탈로그·capability·workdir 없음 | P0 |
| E6-12 | 계약 시험 (DP4·NFR-P3) | 선언 manage / 실제 process | rolled_back, capability 불일치 | P0 |
| E6-13 | 삭제 60초 (NFR-I6) | DELETE | down, 카탈로그·capability·버전·키·workdir·산출물 제거 < 60s, 내장 409 | P0 |
| E6-14 | 비활성화 | is_active=false | 라우팅 제외, nav 숨김 | P0 |
| E6-15 | 내보내기·롤백 API | export(파생) · export-standalone · rollback 0.1.0 | provenance · standalone 프로파일 · 0.1.0 복원 | P0 |
| E6-16 | 업로드 권한 | user | 403 | P0 |
| E6-17 | 실 스택 게이트 | evil.zip + 정상 zip (런타임 미설정) | evil 2단계 zip-slip · 정상 5단계 "runtime 미설정" 명확한 실패 | P0 |
