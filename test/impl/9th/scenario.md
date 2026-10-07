# impl 9th — Epic 9 마켓플레이스 설치 3경로

FR: D6-01(API), D6-02, D6-03, D6-04 · US2, US6 · PRD 10.5(다형 source), 17장(3축 분류)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E9-01 | 스토어 분류·검색·배지 | categories · q · category · type · 상세 | 업종 트리·업무 19 · 필터 결과 · official/서명 미검증/게시자 검증 배지 · README | P0 |
| E9-02 | 경로 A 설치 (US2) | install/board | 8단계 성공, source=market, trust=official, nav 노출, installed 표시 | P0 |
| E9-03 | required_env 폼 | http-tool env 없음/있음 | 422 / 성공 | P0 |
| E9-04 | 산출물 변조 | sha256 불일치 카탈로그 | 422 | P0 |
| E9-05 | 업데이트 표시·업그레이드 | 0.1.0 설치 후 리스팅 1.0.0 | update_available=true → 마켓 설치로 1.0.0 | P1 |
| E9-06 | 경로 B zip URL | sha 일치 · 불일치 · ftp · 404 | 성공 · 422 · 422 · 422 | P0 |
| E9-07 | 경로 B Git subdir·ref | file:// 저장소 agents/x@main · ../ · 없는 경로 | 성공(source=git) · 422 · 422 | P0 |
| E9-08 | 경로 C 원격 리스팅 (US6) | remote-a2a 리스팅 설치 | path C, source=link, trust=external | P0 |
| E9-09 | 권한 | user 탐색/설치 | 200 / 403 | P0 |
| E9-10 | 카탈로그 무결성 | 저장소 market/ | 모든 산출물 sha256·id·버전 일치 | P0 |
| E9-11 | 실 스택 US2 시간 | 이미지 없이 마켓 설치 board | ≤ 300s, nav 노출, Traefik UI 200 | P0 |
