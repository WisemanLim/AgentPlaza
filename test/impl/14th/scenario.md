# impl 14th — Epic 14 실행 내구성·운영

FR: D2-07, D8-06, D8-07 · NFR: NFR-O4 · UI 에이전트 백업 섹션·설정 전체 백업·채팅 재시도/보상 알림

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E14-01 | 체크포인트 재개 (D2-07) | s1 완료 후 s2 중 크래시 → 복구 루프 | s1 다시 안 함, s2 만 실행, succeeded, 원장 task.recovered | P0 |
| E14-02 | 실 스택 크래시 복구 | 느린 단계 실행 중 api 컨테이너 재시작 | 진행 신호 정지 후 복구 루프가 체크포인트에서 이어서 완료 | P0 |
| E14-03 | 살아 있는 작업 보호 | 최근 heartbeat 의 running 작업 | 복구 대상 아님(다른 워커 작업 탈취 없음) | P0 |
| E14-04 | 재시도 | 연결 실패 1회 · 비멱등 503 · 멱등 503 | 2회 성공 · 1회 · 3회(한도) + retry 이벤트·원장 attempts | P0 |
| E14-05 | 사가 보상 | s1 글 생성 → s2 실패 | s1 compensation(삭제) 실행·결과 기록·원장 tool.compensated | P0 |
| E14-06 | 보상 선언 검증 | 없는 verb 를 compensation 으로 | agent.yaml 검증 오류 | P1 |
| E14-07 | 업그레이드 사전 백업·롤백 복원 (NFR-O4) | v1.1(정상) · v1.2(계약 실패) — Fake + 실 runtime | build→backup→up · 실패 시 down→restore→up(이전 태그), 데이터 보존 | P0 |
| E14-08 | 백업 실패 시 중단 | backup 오류 주입 | 5단계 실패, 이전 버전 유지 | P1 |
| E14-09 | 볼륨 백업·복원 (D8-06) | 실 runtime: board 글 → 백업 → 삭제 → 복원 | 일시정지 스냅숏 tar.gz·manifest, 복원 후 글 복구, 경로 검증 422·없는 백업 404 | P0 |
| E14-10 | 플랫폼 백업 | POST /api/admin/backup · make backup | SQLite 온라인 백업 파일(표 확인) + 에이전트 백업, supervisor 전용 | P0 |
| E14-11 | 오프라인 번들 (D8-07) | make offline-bundle(이미지 제한) → 이미지 삭제 → make offline-load | manifest.sha256 검증·docker load 복원·trivy DB 볼륨 적재·모델 목록 | P0 |
| E14-12 | 회귀·콘솔 | make test · 백업 섹션 화면 | 전체 통과 · 스크린샷 | P0 |
