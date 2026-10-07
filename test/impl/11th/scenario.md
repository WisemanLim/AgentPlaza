# impl 11th — Epic 11 웹 콘솔 (React 19) P0 핵심 흐름

> ⚠️ 요구사항 변경으로 재시험 필요 — 접근성 기준 KWCAG 2.2 / WCAG 2.2 AA 상향(PRD Q9) → Epic 24 (2026-10-07) → 재시험 완료: 19th·완료 게이트(접근성 57화면 위반 0), 2026-10-07

FR: D3-01(UI), D6-01(UI), D10-01(UI), D5-07(iframe) · NFR: NFR-U3, NFR-U4(기본), NFR-U5 · UI: A01·A02·B01·B02·C01·C02·C05·D01~D05·D11·E01~E04·I04·J01·J02·J04·K01·K04·L01·L02·M03·N01
도구: vitest(단위, 이미지 빌드 단계에서 실행) · Playwright Chromium 컨테이너(E2E, `make e2e`) — Chrome 확장 미연결로 대체

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E11-01 | SSE 파서 | 완결/미완결 프레임·[DONE]·깨진 JSON·CRLF | 이벤트만 추출, 나머지 보존 | P0 |
| E11-02 | 라우터 | /agents/:id · 쿼리 | 파라미터·쿼리 | P1 |
| E11-03 | i18n 커버리지 (NFR-U3) | ko/en 사전 · 소스 t("…") 키 | 키 집합 동일, 누락 0, 사용 키 > 80 | P0 |
| E11-04 | 타입·빌드 | tsc -b · vite build | 오류 0 | P0 |
| E11-05 | FL-01 첫 대화 | 로그인 → 대시보드 → 채팅 | 타일 6, 스트리밍 답, 세션 목록 갱신 | P0 |
| E11-06 | FL-02 마켓 설치 → Addon | 게시판 설치(8단계) → 네비 → iframe | 진행 succeeded, 네비 Board, iframe src=apps 오리진(8092), iframe 안 글 등록·목록 반영, 부모 sessionStorage 접근 차단 | P0 |
| E11-07 | FL-05 승인 | 스코프 채팅 → 승인 카드 → 승인 | 카드 표시·approved·결과 답변 | P0 |
| E11-08 | i18n·접근성·반응형 | en 전환 · 입력 레이블 · 이름 없는 버튼 · 랜드마크 · 390px 드로어 | 영어 화면, 무레이블 0, 무명 버튼 0, main/nav, 드로어 x=0 | P0 |
| E11-09 | 보안 헤더 | 콘솔 CSP · Addon CSP | frame-ancestors 'none' + frame-src apps 오리진 · Addon frame-ancestors 콘솔 오리진 | P0 |
