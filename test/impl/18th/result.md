# 시험 결과 / Test Result — impl 18th (Epic 18 마켓 상거래·퍼블리셔)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · local 스택(SQLite, 실 cosign·syft·trivy, runtime 컨테이너) · prod 리허설(PostgreSQL 17) · 콘솔
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 14, 통과 Pass: 14, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 250 passed (E18 11 + 회귀 239) · 콘솔 vitest 7 passed · 실 스택 10단계 · prod 리허설(0012 마이그레이션·스모크·인스턴스 간 동기화) · 콘솔 E2E 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E18-01 | PASS | 비구성원 키 등록 403 · 회전 시 이전 키 철회(활성 1/전체 2) · 일반 사용자 403 |
| E18-02 | PASS | admin 게시 → pending → supervisor 승인 → origin=release·서명 검증 배지 · 키 철회 후 '미검증' 강등 |
| E18-03 | PASS | 서명 없음·다른 퍼블리셔 키·Critical → blocked 기록 · 정적 board(agentplaza 소유) 409 · 같은 버전 409 · 미게시 덮어쓰기 · 사유 없는 거부 422 |
| E18-04 | PASS | ^·범위 비교 · 변조 = 서명 불일치 · 형식 오류 · 만료·호스트 실패 항목 · 외부 발급자 등록 전 422 → 후 통과 |
| E18-05 | PASS | 라이선스 없이 설치 402 · 어댑터 none 409 · mock 결제 60,000 KRW(2좌석×3개월)·^1.0.0 · 영수증(토큰 포함) · 설치 성공·통계 install 1 |
| E18-06 | PASS | 좌석 1: 첫 사용자 실행, 두 번째 "좌석 초과" · 반납 후 허용 · 철회 후 "유효한 라이선스 없음" · license.denied 원장 |
| E18-07 | PASS | 1.1.0(승인 필요 도구 추가) = needs_consent·409 · 알림 1회 · 자동 갱신 건너뜀 → 동의 갱신 · 1.2.0(변화 없음) 자동 갱신 · 통계 install 1·update 2 |
| E18-08 | PASS | server.json(2025-12-11)·_meta official·isLatest · 페이지 4+6 · 검색·증분 · 버전 2개 · 이전 버전 산출물 sha 일치 · 유료 402 → 토큰 200 · 익명 401 → 공개 후 200 |
| E18-09 | PASS | 잘못된 토큰 auth_failed · 2페이지 동기화(패키지 리스팅 + MCP 서버 remote-mcp) · board 충돌·패키지 전용 건너뜀 · 체크섬 변경 거부 · 원격 산출물로 설치 · 삭제 시 2건 제거 |
| E18-10 | PASS | 번들 4파일 · 충돌 건너뜀 → 덮어쓰기 편입 · 변조·SHA256SUMS 없음 422 |
| E18-11 | PASS | 추천 정렬·배지 · 숨김 목록 제외 · admin 403 |
| E18-12 | PASS | 실 스택: plaza keygen → 퍼블리셔 키 → `plaza publish --registry`(supervisor 즉시 게시, 실 trivy scanned C0) · admin 0.2.0 심사 승인 · 서명 없는 0.3.0 차단 · 유료 402 → mock 결제 118,800 KRW(12개월) → 실제 컨테이너 설치 8단계 ok · MCP 좌석(감독자 HELLO SEAT → admin 좌석 초과 → 반납 후 허용) · 레지스트리 산출물 무료 200·유료 402/200 · 업데이트 0.1.1(범위 안) 실제 갱신, 1.0.0(범위 밖) 402 · 번들 shasum -c OK |
| E18-13 | PASS | prod 리허설 스택(PostgreSQL)에 prod-notes 게시·호스트 공개 → local 이 http://host.docker.internal:8091/registry 동기화(편입 1·충돌 8 건너뜀) → 원격 산출물로 실제 설치 성공 · prod 다운로드 통계 1 |
| E18-14 | PASS | make test 250 · 콘솔: 마켓 가격 배지·라이선스 키 검증 체크리스트·결제 금액, 게시 게이트 차단 보고서, 퍼블리셔 키, 설치됨(새 버전 라이선스 필요), 원격 레지스트리 화면 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 라이선스 발급 키 저장 실패(SecretError) | 시크릿 저장소 scope 가 global·agent·link 만 허용, 이름은 대문자 규칙 | scope 에 market·registry:<이름> 추가, 이름 LICENSE_SIGNING_KEY·TOKEN | E18 11 passed |
| 1 | (예방) 원격 클라이언트가 산출물을 못 받음 | 산출물 주소를 PUBLIC_BASE_URL 로 만들어, 다른 호스트(예: host.docker.internal)로 접속한 클라이언트에 닿지 않는 주소를 줌 | 레지스트리 API 가 요청 기준 URL 로 산출물 주소 생성 | E18-13 원격 설치 성공 |
| 1 | 콘솔 체크박스·라디오가 한 줄을 차지 | 전역 input width:100% | 기존 규칙대로 style width:auto | 스크린샷 확인 |
| 1 | prod 리허설 스모크 404 | `make prod-all` 은 빌드하지 않아 예전 prod 이미지(0005)로 기동 | `make prod-build`(up --build) 후 0012 마이그레이션 | 스모크 전부 200 |
| 1 | (시험 절차) 실 스택 스크립트 버전·리허설 로그인 | 템플릿 기본 버전 0.1.0, prod DB 는 P0 리허설에서 이미 초기화 | 스크립트 버전 정정(round 2), 리허설 토큰은 컨테이너 안에서 단기 발급 | PASS |

## 첨부 / Logs

- `logs/make-test.txt`(250) · `logs/make-test-final.txt`(250) · `logs/e18-live.txt` · `logs/prod-{all,build,db,smoke,stop}.txt` · `logs/e2e.txt` · `logs/e2e/screens/p1-18-*.png`
