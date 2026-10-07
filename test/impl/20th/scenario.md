# impl 20th — Epic 20 LLM 게이트웨이 Bifrost 전환·월 예산 기반 로컬 강제

FR: D1-01·D1-03·D1-05·D1-06 · PRD Q1(Bifrost, LiteLLM 미사용)·Q15(월 예산 80% 로컬 강제, UI J05) · NFR-L1·L2·L3·S3

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E20-01 | Bifrost 경유 | BIFROST_URL 설정, chat·stream·embed | 모델 = '<공급자>/<모델>' 로 Bifrost 호출, 퍼블릭 공급자는 api 쪽 키 없음 | P0 |
| E20-02 | Bifrost 장애 | 연결 거부 | 로컬 Ollama 는 직접 호출 폴백(횟수 집계), 퍼블릭은 오류 | P0 |
| E20-03 | 별칭 폴백 유지 | Bifrost 가 퍼블릭에 400(키 없음) | 별칭 다음 대상(로컬)으로, fallback_from 기록 | P0 |
| E20-04 | 예산 로컬 강제 | 월 예산 1.0·기준 0.8, 이번 달 사용 0.85 | 퍼블릭 제외·x-plaza-budget: local-forced·원장 달 1회, 로컬 대상 없으면 403(reason=budget), 예산 0 = 끔 | P0 |
| E20-05 | 권한·검증 | admin·user·잘못된 값 | 조회 admin+, 변경 supervisor, 422 | P1 |
| E20-06 | 격리·금지 패키지 | compose·pyproject·Bifrost 설정 | LiteLLM 없음 · api 퍼블릭 키 비움 · Bifrost 버전 고정·포트 미공개·read_only·cap_drop ALL · 설정 파일에 키 원문 없음 | P0 |
| E20-07 | 실 스택 | Bifrost v2.2.6 + 호스트 Ollama | 공급자 상태·메트릭 증가·L3 로컬·정지 시 직접 폴백·예산 강제(가상 유료 모델) | P0 |
| E20-08 | 회귀·콘솔 | make test · LLM 화면(Bifrost 배지·예산 카드) · 접근성 | 전체 통과 · 스크린샷 · 위반 0 | P0 |
