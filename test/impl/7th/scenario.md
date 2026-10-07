# impl 7th — Epic 7 런타임·compose·라우팅·격리

FR: D8-02, D8-03, D8-04, D8-05 · NFR: NFR-I1(매트릭스), NFR-I3, NFR-I4, NFR-I5, NFR-I6(실측), NFR-S5(에이전트 경로)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E7-01 | 생성 compose 린트 통과 | 8유형 federated compose | 위반 0 | P0 |
| E7-02 | 린트 거부 (NFR-I3·I5·D8-05) | privileged·host net·host pid·cap_add·cap_drop 없음·rw 루트·docker.sock·bind·포트·메모리 무제한·GPU·runtime·no-new-privileges 없음 | 각각 거부 | P0 |
| E7-03 | 격리 네트워크·egress | federated / tool-proxy | 전용 외부 네트워크, egress 없으면 internal, 프로젝트 라벨, forwardAuth 미들웨어 | P0 |
| E7-04 | forwardAuth (D8-03) | 무인증·Bearer·쿠키·범위 밖 키·비활성·잘못된 URI | 401·200(+X-Api-Key)·200·403·403·403 | P0 |
| E7-05 | 루트 include (D8-02) | 현재 버전 1 + 이전 1 | 현재 버전만 include | P1 |
| E7-06 | 플랫폼 compose 정책 | docker-compose.yml · ollama-gpu 오버레이 | api 에 docker.sock 없음, traefik ro, GPU 는 LLM 공급자만 | P0 |
| E7-07 | runtime 표준 라이브러리 | lint.py + service.py import | stdlib 만 | P1 |
| E7-08 | 실 설치 E2E | board(app)+svc2(service) 업로드 | 8단계 성공(11s), runtime 빌드·기동 | P0 |
| E7-09 | Traefik 경유 인증 라우팅 | /a/board/health 무인증 / Bearer / invoke / 쿠키 UI / UI→api | 401 / 200 / 200(키 주입) / 200 / 200 | P0 |
| E7-10 | 에이전트 간 격리 (NFR-I4) | board-be → svc2-be (DNS·IP) | 이름 해석 실패 · Network unreachable | P0 |
| E7-11 | egress 차단 | board-be → https://example.com | 실패 | P0 |
| E7-12 | 에이전트 → 게이트웨이 LLM | svc2 summarize (Ollama) | source=llm 요약 | P0 |
| E7-13 | 설치 에이전트 오케스트레이션 | "게시판에 … 글을 등록해줘" / "날씨 알려줘" | board.manage create 실행 / 에이전트 없음 정직 답변 | P0 |
| E7-14 | 실 삭제 60초 (NFR-I6) | DELETE svc2, board | 1.2s·1.4s, 컨테이너·볼륨·네트워크·이미지·카탈로그·include 잔여 0 | P0 |
| E7-15 | M1 매트릭스 (NFR-I1) | 8유형 `compose --profile standalone up --wait` | 전부 /health 200 | P0 |
