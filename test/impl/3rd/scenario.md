# impl 3rd — Epic 3 LLM 게이트웨이·모델 카탈로그·데이터 등급

> ⚠️ 요구사항 변경으로 재시험 필요 — LLM 게이트웨이 엔진 Bifrost 전환·예산 80% 로컬 강제(PRD Q1·Q15) → Epic 20 (2026-10-07) → 재시험 완료: 20th(Bifrost·예산), 2026-10-07

FR: D1-01, D1-03, D1-05, D1-06 · NFR: NFR-L1~L5, NFR-S3 · US4

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E3-01 | 카탈로그 기본값·필수 필드 | 최초 기동 / 필드 누락 POST | granite(Apache-2.0) 활성 · 별칭 4종 · 422 | P0 |
| E3-02 | 별칭 라우팅·계량 | `plaza/t-local` L3 | 200, x-plaza-model, usage 1건 | P0 |
| E3-03 | 퍼블릭 장애 폴백 (NFR-L1) | [fail-public, echo-local] L0 | 200 · degraded=true · fallback-from · <30s | P0 |
| E3-04 | 타임아웃 폴백 | [slow-public, echo-local] | 200 · fallback-from slow | P0 |
| E3-05 | confidential 로컬 강제 (NFR-L3·US4) | mixed L3 / public-only L3 | 로컬 응답 / 403 policy_denied + 원장 | P0 |
| E3-06 | 헤더 없음 = L2 | public-only 무헤더 / L0 / bogus | 403 / 200 / 422 | P0 |
| E3-07 | 전 대상 장애·없는 별칭 | t-dead / plaza/nope | 503 / 404 | P1 |
| E3-08 | 스트리밍·스트림 폴백 | stream=true | SSE 조립 = 원문, [DONE], 첫 토큰 전 폴백, 종료 후 계량 | P0 |
| E3-09 | API 키 Bearer (OpenAI 클라이언트) | Authorization: Bearer ap_sk_… | 200, /v1/models | P0 |
| E3-10 | 라이선스 게이트 (D1-06) | conditional 활성화 무동의 / 동의 / prohibited | 409 / 200 / 409 | P1 |
| E3-11 | 별칭 관리 권한·검증 | admin PUT / 없는 모델 / plaza/ 외 / user PUT | 200 / 422 / 422 / 403 | P1 |
| E3-12 | 오버헤드 p95 ≤ 50ms (NFR-L4) | mock 지연 0, 60회 | p95 < 50ms | P1 |
| E3-13 | 키 0개 동작 (NFR-L2·S3) | 퍼블릭 키 없음 | 퍼블릭 공급자 미등록, 로컬 200 | P0 |
| E3-14 | 실 Ollama (D1-01) | `plaza/fast` L3 → granite4.1:3b | 200, 한국어 응답, usage | P0 |
| E3-15 | 실 Ollama 스트리밍 | `plaza/local` confidential stream | SSE 청크·종료 | P0 |
| E3-16 | 실 공급자 장애 폴백 | [ollama/missing-model, granite] | degraded=true, fallback-from missing | P1 |
