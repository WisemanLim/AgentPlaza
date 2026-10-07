# 구현 계획표 — AgentPlaza P0·P1·P2 (wds-implement)

> 근거: [PRD.md](../PRD.md) §3.1 P0 43개 · 확인 2026-10-06 (범위 P0 Epic 1–11, mock+호스트 Ollama, 내장 라우터+LangGraph, runtime 서비스만 docker.sock).
> 2차 확인 2026-10-07: P1 Epic 12–18 포함 · 관측 UI 자체 경량 · cosign·syft·trivy · mock 결제 + Ed25519 라이선스 토큰.
> 3차 결정 2026-10-07 (PRD Open Questions 답변): P1 추가 범위 Epic 20–24 — 다음 wds-implement 이터레이션(0-3 확인에서 순서·세부 확정).
> 3차 확인 2026-10-07: 순서 24→20→21→22→23 · Bifrost compose 서비스 + 정책 계층 유지 · 호스티드 결제 + 웹훅(가짜 서버 시험) · 기본 조직 + 그룹 + deploy_scope.
> 4차 확인 2026-10-07: P2 포함 — Epic 19(D10-07 알림·상태, 자체 경량 + mailpit) → Epic 25(D3-07 채널·임베드: 웹 위젯·Slack·Telegram·카카오).
> 5차 확인 2026-10-07: 이번 실행 = 문서 정리 + 전체 회귀 재검증(26th, 구현 없음). 가정으로 남은 갭 4건을 Epic 26–29(TODO)로 등록 — 다음 이터레이션.
> 상태: TODO → DONE / BLOCKED. 차수 = `test/impl/<Nth>/` (Epic 1개 = 차수 1개).

| # | Epic | 기능(FR) | 수용 기준 / 시험 케이스 | 의존 | 차수 | 상태 |
|---|---|---|---|---|---|---|
| 1 | 플랫폼 기반: 데이터 모델·인증·RBAC·API 키·감사 원장 | D10-06, D9-01, D9-02, D9-03, D9-07 | SQLite·PG 동일 마이그레이션(NFR-O5) · 최초 관리자 셋업 · 역할별 403 · API 키→서비스 JWT · 감사 해시체인 검증·변조 탐지 · 무인증 경로 허용목록(NFR-S5) | — | 1st | DONE |
| 2 | agent.yaml 규격·템플릿 9유형·스캐폴드·SDK·내보내기 | D4-01, D4-02, D4-03, D4-04, D4-07, D8-01 | 스키마 유효/무효 · 9유형 zip 생성 · `plaza init/validate` · Standalone 번들 `compose --profile standalone config` · 누락 검증(verify-coverage) | 1 | 2nd | DONE |
| 3 | LLM 게이트웨이·모델 카탈로그·데이터 등급 | D1-01, D1-03, D1-05, D1-06 | 별칭 라우팅 · 퍼블릭 장애 30초 내 로컬 폴백+강등 이벤트(NFR-L1) · confidential→퍼블릭 403+원장(US4) · 퍼블릭 키 0개 동작(NFR-L2) · 카탈로그 필수 필드(NFR-L5) | 1 | 3rd | DONE |
| 4 | Orchestrator | D2-01, D2-02, D2-03, D2-04, D2-06 | 의도 분류(구조화 출력+규칙 폴백) · capability 라우팅·registry_miss · sequential/parallel · 도구 실행 · HITL 승인/거부/만료(US8) | 1, 3 | 4th | DONE |
| 5 | AI Assistant API | D3-01(API), D3-02, D3-03 | AG-UI SSE 이벤트 순서 · 세션 CRUD·검색·내보내기 · 도구/승인 이벤트 · 스코프 채팅 · Orchestrator 부재 시 단일 LLM 강등 | 3, 4 | 5th | DONE |
| 6 | 패키지·레지스트리 8단계 | D5-01, D5-02, D5-05, D5-06, D5-07 | 다중 업로드·100MB 상한 · zip-slip/심볼릭 링크/압축 폭탄/중첩 거부(NFR-S1) · SQL DDL만 · 컨테이너 모드 기본(NFR-I2) · 설치 상태 · 삭제 60초 내 흔적 제거(NFR-I6) | 2 | 6th | DONE |
| 7 | 런타임·compose·라우팅·격리 | D8-02, D8-03, D8-04, D8-05 | installed/*.compose.yaml + include · Traefik `/a/{id}/…` · compose 린트(docker.sock·host·privileged 거부, NFR-I3) · 리소스 상한(NFR-I5) · 샘플 에이전트 M1 `/health`(NFR-I1) | 6 | 7th | DONE |
| 8 | 표준 프로토콜 MCP·A2A | D7-01, D7-02, D7-03, D7-04 | `/mcp/{agent}` tools/list·tools/call + x-api-key(US5) · 외부 MCP 등록 · Agent Card 생성+JWS 서명·검증 · A2A Task 왕복 · 생성물↔런타임 diff(NFR-P3) | 2, 6 | 8th | DONE |
| 9 | 마켓플레이스 설치 3경로 | D6-01(API), D6-02, D6-03, D6-04 | 검색·상세·신뢰 배지 · 경로 A→8단계(US2) · 경로 B zip/URL · 경로 C 원격 Card/MCP→계약 시험(US6) · 실패 롤백 | 6, 7, 8 | 9th | DONE |
| 10 | 콘솔 API·셋업 위저드·OTel | D10-01, D10-02, D10-03 | 셋업(관리자→LLM 감지→기본 에이전트) · OTel GenAI 필수 속성(NFR-O1) · 에이전트 상태·헬스·버전 | 1, 3 | 10th | DONE |
| 11 | 웹 콘솔 (React 19) P0 핵심 흐름 | D3-01(UI), D6-01(UI), D10-01(UI), D5-07(iframe) | FL-01 설치→첫 대화 · FL-02 마켓 설치 · FL-05 승인 · ko/en(NFR-U3) · 접근성 기본(NFR-U4) | 1–10 | 11th | DONE |
| 12 | 공급망 신뢰 게이트 | D4-06, D5-03, D5-04 | `plaza keygen/publish` → zip·checksums·sbom.json·signature.sig(cosign) · 신뢰 키 등록·철회 · 3단계: 신뢰 키 서명=검증 배지, 서명 없음=미검증 배지, 변조·철회 키=거부(NFR-S2) · SBOM(syft) 생성·비교 · trivy Critical 거부 · 4단계: 라이선스 G1–G5(G4 격리 표시·파생 금지, G5 차단) · 선언 egress vs 조직 정책 · 플랫폼 의존성 G4 0건(NFR-C1) · 설치 산출물 출처·라이선스 기록(NFR-C2) | 6, 9 | 12th | DONE |
| 13 | 거버넌스·보안 | D9-04, D9-05, D9-06, D2-05, D7-07 | 암호화 시크릿 저장소(원문이 DB·workdir 에 없음)·compose secrets 주입·회전·로그 마스킹(NFR-S3) · 정책 엔진(등급별 모델·도구·내보내기 제한, 원장) · 가드레일(인젝션 필터·한국어 PII 마스킹·도구 허용목록, 레드팀 세트, NFR-S6) · 리뷰어 게이트(외부 결과 포함 시 기본 켜짐, 통과·수정·차단 원장) · 레이트리밋 429·Mcp-Name 툴 단위 RBAC | 1, 3, 4, 8 | 13th | DONE |
| 14 | 실행 내구성·운영 | D2-07, D8-06, D8-07 | 실행 상태 체크포인트·api 재시작 후 재개 · 단계 재시도(백오프)·보상 capability · 업그레이드 = 이미지 태그 고정 + 사전 백업 + 실패 롤백(NFR-O4) · 볼륨·DB 백업/복원 · 오프라인 번들(이미지 tar·카탈로그·모델 목록) 생성·적재 | 4, 6, 7 | 14th | DONE |
| 15 | 어시스턴트 확장 | D3-04, D3-05, D3-06, D1-07 | 파일·이미지 첨부(보존 경과 파기)·비전 모델 라우팅 · 맞춤지침·장기 메모리 CRUD·삭제권·프롬프트 주입 · 지식 컬렉션(업로드→청크→임베딩→검색)·인용 · `/v1/embeddings`·`/v1/rerank`(Ollama·mock) · 퍼블릭 키 0개로 RAG 동작(NFR-L2) | 3, 5 | 15th | DONE |
| 16 | LLM·프로토콜 확장 | D1-02, D1-04, D7-05, D7-06 | 고성능 서빙 오버레이(vLLM·llama-server)·OpenAI 호환 로컬 공급자 등록 · CLI 에이전트 NDJSON 브리지(가짜 CLI 로 시험) · 에이전트를 `/v1` 모델(`agent/<id>`)로 노출·OpenAPI→MCP 도구 변환 · AG-UI 재연결 재개(NFR-P4)·ACP 어댑터 | 3, 5, 8 | 16th | DONE |
| 17 | 관측·평가 | D10-04, D10-05, D4-05 | 트레이스·세션·비용 대시보드(자체 경량, 스팬 DB 저장, NFR-O1) · 평가 시나리오·품질 점수·회귀 실행 · `plaza test`(구조·문법·SQL·로컬 기동·MCP/A2A 계약·시나리오) | 3, 4, 10 | 17th | DONE |
| 18 | 마켓 상거래·퍼블리셔 | D6-05, D6-06, D6-07 | 퍼블리셔 등록·서명 키·회전·철회 · 게시→심사(D5 게이트 자동 + 관리자 승인)→릴리스·다운로드 통계 · 유료 리스팅: mock 결제→영수증→Ed25519 라이선스 토큰(오프라인 검증·좌석·기간), 없으면 설치 거부(NFR-C4) · 업데이트 알림·자동 갱신·롤백 · 레지스트리 API(MCP registry server.json 호환)·오프라인 번들 export | 12 | 18th | DONE |
| 19 | 알림·상태 (P2) | D10-07 | 헬스 대시보드(플랫폼 구성요소·에이전트·LLM 공급자) · 상태 변화 감시 루프 · 알림 센터(B03, 읽음·벨 배지) · 알림 규칙(에이전트 장애·복구·LLM 공급자 장애·예산 로컬 강제·업데이트·설치 실패·라이선스 만료 임박) · 발송(Slack·Telegram 웹훅·SMTP 메일, 중복 억제) · 사용량 리포트(주간·수동 발송) · mailpit 오버레이 | 1–18, 20 | 24th | DONE |
| 25 | 채널·임베드 (P2) | D3-07 | 채널 등록(UI C07)·비밀값은 시크릿 저장소 · 웹 위젯(위젯 키·허용 오리진·iframe+postMessage·SSE) · Slack Events(서명 v0)·Telegram 웹훅(secret token)·카카오 i 오픈빌더 스킬(헤더 토큰·콜백) → Assistant 응답 · 채널 사용자별 세션 · 승인 필요 작업은 콘솔로 안내 · 서명 틀림 401 | 5, 13, 21 | 25th | DONE |
| 20 | LLM 게이트웨이 Bifrost 전환·예산 기반 로컬 강제 | D1-01, D1-03, D1-05, D1-06 (Q1, Q15) | Bifrost(Apache-2.0) 를 공급자 호출 엔진으로 — 별칭·폴백·데이터 등급·계량 회귀 유지(3rd·16th 재시험) · 월 예산 80% 도달 시 로컬 강제 라우팅 + 배지·원장(J05) · LiteLLM 미사용(금지 패키지 CI) | 3, 16, 17 | 20th | DONE |
| 21 | Assistant pydantic-ai 전환 | D3-01, D3-02, D3-03 (Q2) | Assistant 를 pydantic-ai 에이전트로 — AG-UI 이벤트·도구/승인 카드·세션·재연결 회귀(5th·16th 재시험) | 5, 20 | 21st | DONE |
| 22 | 결제 어댑터 Lago·Polar·Stripe | D6-05 (Q6) | 어댑터 3종(시험 모드·웹훅 서명 검증) · 카드 정보 비보관(호스티드 결제) · mock 유지 · 영수증·라이선스 발급 회귀(18th) · 실결제 금지(비운영) | 18 | 22nd | DONE |
| 23 | 조직·부서 단위 배치·조직 화면 | X09 일부, D6-02 (Q7, Q12) | orgs·org_groups·구성원 · deploy_scope org\|group\|user — 범위 밖 구성원에게 네비·도구·MCP 미노출 · K02 화면·FL-07 도입 흐름 · 조직 admin 권한 · 원장 | 1, 9, 18 | 23rd | DONE |
| 24 | 품질 기준 상향: 접근성·MCP 계약 | NFR-U4, NFR-P1 (Q9, Q8) | 콘솔·Addon 템플릿 KWCAG 2.2 / WCAG 2.2 AA(axe 자동 검사 E2E) · 설치 7단계·`plaza test` 계약 시험이 server/discover 와 initialize(2025-11-25) 를 둘 다 명시적으로 시험(6th·8th·11th 재시험) | 6, 8, 11 | 19th | DONE |
| 26 | 경로 B OCI 아티팩트·사설 미러 설치 (P0 갭) | D6-03, D4-06 | `oci://<레지스트리>/<저장소>:<태그>` 참조(ORAS 아티팩트 형식)로 설치 · 사설 미러 레지스트리(인증은 시크릿 저장소) · `plaza publish --oci` 푸시 · 설치 7단계·서명·SBOM 게이트 동일 적용 · 다이제스트 고정 · 시험용 registry:2 오버레이 | 6, 12, 14 | — | TODO |
| 27 | OIDC SSO 로그인 | D9-01, D7-07 (IdP 위임) | 콘솔 로그인을 외부 IdP(OIDC Authorization Code + PKCE)로 · 첫 로그인 시 계정 연결·기본 조직 가입 · 역할 매핑(클레임→admin/user) · 로컬 비밀번호 로그인 병행/끄기 · state·nonce·발급자·audience 검증 · 시험은 가짜 IdP | 1, 23 | — | TODO |
| 28 | 메모리 LLM 자동 추출 | D3-05 | 대화에서 기억할 사실을 LLM 이 제안 → 사용자 승인 후 저장(자동 저장 없음) · PII 걸러냄·삭제권 유지 · 끄기 설정 · 규칙 명령(기억해:·잊어줘:) 회귀 | 15, 21 | — | TODO |
| 29 | 기본 에이전트 컨테이너 분리 | D2-01~04, D3-01~03 | Orchestrator·Assistant 를 별 compose 서비스로(agent.yaml 계약 그대로) · AG-UI·승인·체크포인트 재개 회귀(4th·5th·14th·21st) · 서비스 장애 시 단일 LLM 강등 유지 · 플랫폼 api 와 내부 인증 | 4, 5, 14, 21 | — | TODO |

## 가정 (기본값으로 진행)

| 항목 | 가정 | 근거 |
|---|---|---|
| PRD 상충 Q5 | P0 = 43 (FR 표 집계) | PRD Q5 |
| Q6·Q7·Q11·Q12 | (P0 당시) 결제·멀티테넌시·조직·워크플로·플레이그라운드는 이번 범위 제외 → Q6 결제·Q7·Q12 조직은 Epic 22·23 에서 구현, Q11 은 Addon | P1/X09 |
| Q8 MCP 버전 | 공식 SDK 최신판이 지원하는 사양 버전 + initialize 호환 | 2026-07-28 세부는 SDK 에 위임 |
| Q13–Q15 UI | 화면 목록 기준. 보존기간 = 설정값(대화 365일·파일 90일), 2FA = IdP 위임(P1) | UI 설계서 p.9–12, p.92 |
| 기본 에이전트 배치 | Orchestrator·Assistant 는 P0 에서 플랫폼 프로세스 내 모듈(계약은 agent.yaml 과 동일). 컨테이너 분리는 Epic 29(TODO) | 범위·시간 |
| 스캐폴드 엔진 | Copier 대신 내장 토큰 치환 생성기(재템플릿 update 는 후속) | 의존성 최소 |
| 마켓 카탈로그 | P0 = 정적 git+JSON 카탈로그(무료·사내). 유료 마켓 서버는 S7 | PRD 15.4 |
| 경로 B 소스 | zip 업로드·zip URL·Git(subdir·ref) 구현. OCI 아티팩트·사설 미러는 미구현(레지스트리 클라이언트 필요) → Epic 26(TODO) | D6-03 일부 |
| verify-coverage | PRD 10.8 의 "70 항목 = 70 agent.yaml" 대신 P0 FR ↔ 계획표 ↔ 시험 추적 검사 | 범위 |
| MCP Inspector CLI | 네트워크 설치 제한으로 미사용, 공식 python-sdk 클라이언트로 계약 시험 | NFR-P1 대체 |
| 채팅 UI | PRD 1순위 assistant-ui(react-ag-ui) 대신 AG-UI 이벤트를 직접 소비하는 경량 컴포넌트(2026 패키지 API 검증 불가). 교체 가능하도록 SSE 파서·이벤트 매핑을 분리 | D3-01 구현 선택 |
| Addon 화면 격리 | 에이전트별 서브도메인 대신 Traefik 별도 진입점(apps 포트)으로 오리진 분리 + CSP frame-ancestors | PRD 13.1 의 로컬 대응 |
| 콘솔 E2E | Chrome 확장 미연결 → Playwright(Chromium) 컨테이너로 실행(`make e2e`) | wds-test §4 |
| 공급망 정책 엔진(D5-04·D9-05) | OPA/Rego 대신 정책을 데이터(settings)로 두고 내장 평가기로 판정 — 외부 바이너리 없이 동일 규칙(G1~G5·egress·서명 필수·차단 등급) | 의존성 최소, 계획표 2차 확인 |
| 서명 방식(D4-06) | cosign 키 서명(Ed25519, 오프라인, Rekor 미사용). 키리스(Fulcio)·OCI 푸시(ORAS)는 미구현 | 폐쇄망 전제 |
| 취약점 DB | trivy DB(약 1.4GB)는 이미지에 넣지 않고 `trivycache` 볼륨에 `make trivy-db` 로 받음. 없으면 '미스캔' 경고(정책으로 차단 가능) | 이미지 크기·갱신 주기 |
| 시크릿 주입(D9-04) | compose secrets 대신 pull: 에이전트가 자기 내부 키로 /api/agent/secrets 에서 env.secretRefs 만 받는다(SDK ctx.secret, 30초 캐시). Compose 5.5 는 read_only 서비스에 file 시크릿만 허용하고 runtime(DinD)은 호스트 경로가 없다. OpenBao·SOPS·Infisical 은 저장소 드라이버 후보 | 실측(Compose 5.5.1) |
| 시크릿 마스터 키 | SECRETS_MASTER_KEY(base64 32바이트) — 비우면 JWT_SECRET 에서 HKDF 파생(로컬 전용) | 운영은 주입 |
| 가드레일(D9-06) | 내장 규칙(인젝션 가중 규칙·한국어 PII 10종). 외부 가드레일 엔진(Llama Guard 등)은 리뷰어 에이전트로 연결 | 의존성 최소 |
| 원격 도구 등급 기본값 | external_tool_max_level 기본 L2(L3 만 차단) — 기본 요청 등급 L2 에서 P0 경로 C 가 동작해야 함. 조직은 L1 로 강화 | 회귀 방지 |
| OAuth(D7-07) | 게이트웨이 인증은 API 키·JWT. OAuth(OIDC SSO)는 범위 밖(P1 시크릿·SSO 중 SSO 미포함) → 콘솔 OIDC SSO 로그인은 Epic 27(TODO) | PRD D9 IdP 위임 |
| 장기 작업 엔진(D2-07) | Temporal 미도입 — LangGraph 체크포인터(SQLite/PostgreSQL) + 진행 신호 기반 복구 루프(30초 주기, task_stale_seconds 120)로 크래시 재개. 재개는 at-least-once(죽은 superstep 의 단계는 다시 실행) | 의존성 최소 |
| 백업(D8-06) | offen/docker-volume-backup·restic 대신 runtime 서비스가 일시정지 스냅숏 tar.gz(자기 이미지로 실행) · PostgreSQL 은 pg_dump -Fc · SQLite 는 온라인 백업 API. 외부 저장소 전송은 운영 범위 | 오프라인·의존성 최소 |
| 오프라인(D8-07) | 번들 = docker save 이미지 + 카탈로그 + trivy DB + 모델 목록(INCLUDE_MODELS=1 이면 ~/.ollama/models). 사설 미러 레지스트리 미포함 | 단일 호스트 compose |
| 벡터 저장(D3-06) | 임베딩을 JSON 으로 저장하고 코사인 계산(SQLite·PostgreSQL 공용). pgvector 색인·HNSW 는 문서 수만 건 이상에서 도입 | 양쪽 엔진 동일 동작 |
| 재정렬(D1-07) | 기본은 임베딩 코사인, 교차 인코더는 TEI 오버레이(compose-optional/tei.yml, TEI_RERANK_URL) 선택 | 의존성 최소 |
| 음성(D3-04 STT/TTS) | Addon(X03) 연계 대상 — 코어 미구현 | PRD X03 |
| 메모리 추출(D3-05) | "기억해:"·"잊어줘:" 규칙 명령 + 수동 등록. LLM 자동 추출(Mem0 등)은 Epic 28(TODO) | 오탐·개인정보 최소화 |
| CLI 백엔드(D1-04) | CLI 를 api 에서 실행하지 않고 별도 브리지 서비스(compose-optional/cli-bridge.yml)가 OpenAI 호환으로 감싼다. 실제 CLI 설치·로그인은 사용자(빌드 인자·볼륨), 시험은 가짜 CLI(stream-json·ACP) | 자격 증명 비보관·격리 |
| ACP(D7-06) | 브리지가 ACP 클라이언트(initialize·session/new·session/prompt). 권한·파일·터미널 요청은 모두 거절(대화 중계만) | 안전 기본값 |
| AG-UI 범위(D7-06) | 표준 이벤트 부분집합(RUN·STEP·TEXT·TOOL·STATE·CUSTOM)을 검사기로 보장. SUBAGENT_*·THINKING_* 는 내보내지 않음 | 사양 세부 미확정 |
| 고성능 서빙(D1-02) | vLLM·llama-server 는 선택 오버레이 + 'OpenAI 호환 서버' 등록으로 연결(Apple Silicon 은 GPU 컨테이너 불가 — 호스트 Ollama 를 같은 경로로 검증) | PRD R10 |
| P1 화면 E2E | 토큰 주입(E2E_TOKEN)으로 로그인 없이 P1 화면 확인(`E2E_SPEC=p1`) | 시험 자격증명 비보관 |
| LLM 관측(D10-04) | Langfuse·Opik·Grafana 미도입 — OTel 스팬을 플랫폼 DB(trace_spans)에 BatchSpanProcessor 로 저장하고 자체 화면(/observe)으로 조회. 외부 OTLP 수출은 OTEL_EXPORTER_OTLP_ENDPOINT 로 병행 | 사용자 선택(자체 경량 UI) |
| 트레이스 묶음 | FastAPI 0.142 가 자체 공급자로 요청 스팬을 만들어 우리 스팬의 부모가 외부에 있음 → 저장된 스팬 중 부모가 없는 것을 '로컬 루트'로 묶어 목록화 | 실 스택 E17-01 |
| 평가 러너(D10-05) | promptfoo·DeepEval 대신 내장 러너(contains·not_contains·regex·tool·state·judge). judge 는 plaza/orchestrator 별칭 LLM 이 0~1 점수. 직전 실행 대비 PASS→FAIL 을 회귀로 표시 | 폐쇄망·의존성 최소 |
| plaza test(D4-05) | 로컬 기동은 같은 프로세스에서 백엔드 앱을 임포트해 계약 검사(REST·MCP·A2A 카드). 컨테이너 빌드 기동은 설치 파이프라인 담당 | 시험 속도 |
| 결제(D6-05, Q6 결정) | 어댑터 인터페이스(charge) + mock. PAYMENT_ADAPTER=none(prod 기본)이면 구매 버튼은 꺼지고 키 직접 입력만. 정산·세금(X12)·환불 미구현 | 실결제 없음 |
| 라이선스 토큰 | apl1.<본문>.<Ed25519 서명> — 발급 키는 인스턴스별(시크릿 저장소), 버전 범위 기본 ^MAJOR(0.x 는 ^0.MINOR), 기간 = 개월×30일, 호스트 = 구매 인스턴스 id | 오프라인 검증 |
| 좌석 | 좌석 = 유료 에이전트를 쓰는 사용자(actor) 수. 첫 실행(Orchestrator 단계·MCP 호출) 때 배정, admin 이 반납. 계획 후보에서는 빼지 않고 실행 시 license_blocked 로 사유를 보인다 | UX(사유 표시) |
| 유료 판정 | 마켓 설치(경로 A)·업데이트·레지스트리 산출물에서 검사. 경로 B(직접 zip 업로드)는 관리자 자신의 패키지로 보고 검사하지 않음 | 범위 |
| 심사 | 자동 검사 = D5 게이트(구조·서명·SBOM·취약점·라이선스·egress) + 퍼블리셔 키 서명 필수. evals 는 목록만 보고(업로드 코드를 플랫폼에서 실행하지 않음, DP5). 게시자 알림 = 원장 기록 | NFR-I2 |
| 레지스트리 API | MCP registry /v0.1/servers·versions 읽기 부분만(게시는 /api/market/releases). 커서 = 불투명 오프셋. 원격에서 받은 리스팅은 다시 노출하지 않음(순환 방지). 산출물 주소는 요청한 호스트 기준 | 공식 레지스트리 쓰기 API 범위 밖 |
| 업데이트 알림 | '설치됨·업데이트' 화면 배지 + 원장(market.update_available, 버전당 1회) + 알림 센터(update_available, Epic 19 이후). 자동 갱신 주기 = MARKET_SYNC_INTERVAL | Epic 18 → 19 |
| 접근성(Q9) | 자동 검사 = axe-core(wcag2a·2aa·21a·21aa·22aa)로 콘솔 27화면 × 라이트·다크 + Addon iframe. 수동 항목(스크린리더 낭독·인지 부하 등 KWCAG 2.2 의 자동화 불가 항목)은 범위 밖 | 자동화 가능 범위 |
| Bifrost 연결(Q1) | maximhq/bifrost:v2.2.6 파일 설정(config/logs store 끔 — Bifrost 자체 UI·거버넌스 미사용), 포트 미공개. Ollama 는 allow_private_network. 모델 = '<공급자>/<모델>'. 연결 실패 시 Ollama 만 직접 폴백(퍼블릭 키는 api 에 없음) | 정책 계층은 플랫폼 |
| 예산(Q15) | 전체 단일 월 예산(USD, 카탈로그 단가 기준 비용), 달 경계 UTC, 집계 30초 캐시. 별칭·사용자별 예산은 미구현 | 범위 |
| Assistant SDK(Q2) | pydantic-ai-slim(코어만). 강등·비전 대화가 Agent.run_stream, 모델은 FunctionModel → 게이트웨이 라우터(정책 유지). 도구 실행은 계속 Orchestrator(LangGraph) — Assistant 에이전트에 도구를 직접 붙이지 않음(소형 로컬 모델의 도구 호출 변동 회피) | 회귀 최소 |
| 결제 어댑터(Q6) | 호스티드 결제만(카드 정보 미취급). Stripe = Checkout Session(일회성), Polar = custom price 상품 1개(POLAR_PRODUCT_ID)에 금액 지정, Lago = add-on 일회성 인보이스 + payment_url(실 결제는 Lago 에 연결된 결제대행). 구독 갱신·환불·세금은 X12. 실 테스트 키 검증은 MANUAL | 결제대행 계정 필요 |
| 조직 배치(Q7·Q12) | 노출 범위 통제(데이터 분리 아님). 범위 행 없음 = 모두. 플랫폼 admin 은 관리 목록에서 전부 보지만 실행·MCP·Addon 은 범위를 따름, supervisor 는 항상. API 키(서비스 주체)는 키의 agents 범위로. 조직 admin = 구성원·그룹 관리(배치 범위 지정은 플랫폼 admin). 공공 노출정책은 deploy_scope 로 대체 | 범위 |
| 알림·상태(D10-07) | uptime-kuma 미도입(자체 경량). 감시 대상 = DB·Valkey·Bifrost·runtime·게이트웨이·Ollama·설치 에이전트 /health(원격 연동은 등록 상태만). 외부 발송은 admins·all 대상 알림만(개인 알림은 콘솔만), 같은 종류·대상은 기본 30분 억제. 주간 리포트 = 마지막 발송 후 7일 | 범위 |
| 채널·임베드(D3-07) | 채널 주체 = channel:<id>:<외부 대화>(플랫폼 계정 아님, 배치 범위 있는 에이전트는 보이지 않음) · 유료 좌석은 채널 하나 · 승인은 콘솔로 안내 · 위젯 = 플랫폼 오리진 iframe(CSP frame-ancestors) + 위젯 세션 토큰(2시간) · 카카오 동기 블록 4.5초 · Slack 재전송은 무시 · 메시지 서식은 일반 텍스트 | 범위 |
