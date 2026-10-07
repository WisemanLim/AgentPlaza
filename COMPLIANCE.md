# COMPLIANCE — 정보통신·SaaS (KSIC J)

> 자동 생성 (wds-scaffold). 근거: `domains/ict-saas.yaml`. 규제는 변하므로 아래 출처로 재확인한다.
> 제품 요구 정본: [PRD.md](PRD.md) (원문 `.docs/AgentPlaza_PRD.v2.pdf` 13장 보안·법적·윤리).

## 분류 — KSIC · ISIC/NACE/NAICS

| 체계 | 코드 | 비고 |
|---|---|---|
| KSIC | J (중분류 58·59·60·61·62·63) | 정보통신 — 소프트웨어 기본 도메인(베이스라인) |
| ISIC | J | |
| NACE | J | |
| NAICS | 51 | |

AgentPlaza 플랫폼 자체는 J 다. 업종 Addon 팩(제조 C·물류 H·HR M·공공 O)을 고객에게 도입할 때는 해당 업종 오버레이를 추가로 검토한다 (PRD 원문 p.60–62).

## 한국 규제 (1순위)

| 규제 | 시행/변경 | 영향 |
|---|---|---|
| 정보통신망법 | — | 네트워크·정보보호 의무(§47 = ISMS 근거), 침해사고 신고 |
| 개인정보보호법(PIPA) | — | PII 동의·최소화·유출통지(§32-2) |
| ISMS-P | — | 대형 ICT 서비스 의무. 접근로그·변경관리·암호화 증적, 3년 주기 |
| CSAP(클라우드) | 2025 온라인 발급 | 공공/정부 클라우드 판매 시 IaaS/SaaS/DaaS 인증 — 공공 판매가 확정되면 `govtech` 오버레이 추가 검토 |
| 장애인차별금지법·KWCAG 2.2(웹 접근성) | — | 콘솔·Addon 화면 KWCAG 2.2 / WCAG 2.2 AA(PRD Q9 결정, P1 추가 범위) — axe 자동 검사 |
| 전자상거래법·전자금융거래법(결제) | — | Lago·Polar·Stripe 결제 어댑터(PRD Q6 결정) — 영수증·거래 기록 보관, 카드 정보는 결제대행(호스티드 결제)에 위임하고 플랫폼은 저장하지 않음 `가정: PCI-DSS 범위 최소화(SAQ-A 수준)` · 정산·세금은 X12 |

## 국제 기준

- SOC 2 Type II (US SaaS, 6~12개월 통제)
- ISO/IEC 27001 (SOC 2 와 통제 40~85% 중첩)
- GDPR (EU 고객/테넌트) — PRD 13.4: 국제 고객이 있으면 데이터 처리 계약과 퍼블릭 LLM 제공자의 학습 미사용 조건 확인

## 데이터 등급

| 데이터 | 등급 | 처리 |
|---|---|---|
| 테넌트 데이터 | 민감 | 고객별 격리(RLS/스키마/DB). AgentPlaza 는 멀티테넌시가 범위 밖(X09) → Addon DB 격리 3방식(own·shared-schema·file)으로 대체. 단일 테넌트 안의 조직·부서 단위 배치(deploy_scope, PRD Q7 결정)는 노출 범위 통제이며 데이터 분리가 아니다 |
| 결제 정보(카드·계좌) | **규제대상** | 플랫폼 미저장(결제대행 위임). 어댑터는 시험 모드 키만 비운영 환경에 사용 — **local/prod 리허설을 포함한 비운영 환경에 실결제·실카드 반입 금지** |
| 고객 PII | 민감 | PIPA/GDPR. 대화·파일·메모리에 보존기간·삭제권·등급 부여(NFR-C3) |
| 인증/아이덴티티(RBAC) | **규제대상** | 접근통제. **local/prod 리허설을 포함한 비운영 환경에 실데이터 반입 금지** |
| 감사로그/텔레메트리 | 내부 | SOC 2/ISO 보관·삭제 정책. 감사 원장은 프롬프트 원문 대신 해시 기본(PRD 12.1, 13.4) |

## 인프라 패턴

`infra_patterns`:
- 멀티테넌트 격리(RLS/스키마/DB-per-tenant) — **적용 보류**: PRD 범위 밖(X09, Open Question Q7·Q12)
- 관측성(OTel 콜렉터 → 티어드 스토리지, 검증된 삭제 CC6.5/A.8.10)
- 피처플래그, API 게이트웨이, 수평 오토스케일, 시크릿 관리
- 표준 CI/CD

`stack_overrides` 와 실제 선택의 차이:

| 항목 | ict-saas 권장 | 이 저장소 | 근거 |
|---|---|---|---|
| frontend | Next.js(App Router) + TS + Tailwind/shadcn | React 19 + TS + Vite, 디자인 토큰 CSS(외부 UI 라이브러리 없음). 채팅은 assistant-ui 대신 AG-UI 이벤트를 직접 소비하는 경량 컴포넌트 | PRD D3-01·7.1 — 콘솔 SPA + Addon iframe 마운트. 폐쇄망 번들·의존성 최소 |
| backend | NestJS 또는 FastAPI | FastAPI (`python-fastapi`) | PRD 9.1 — v1 승계, OpenAPI = 도구 카탈로그 |
| data | PostgreSQL + Prisma, Redis | PostgreSQL 17 + pgvector (`DB_IMAGE=pgvector/pgvector:pg17`), SQLAlchemy 2 + Alembic, **Valkey** (`compose/redis.yml`) | PRD P04(pgvector)·P05(Valkey — Redis 3중 라이선스 회피). prod `--db postgres` 와 일치 |
| tenancy | subdomain/RLS → schema/DB-per-tenant | 해당 없음(X09) | PRD 4.1 범위 밖 |
| observability | OpenTelemetry 티어드 보관, 피처플래그 | OTel Collector(`ops/otel-collector.yaml`, 기본 debug exporter) + GenAI semconv 스팬(chat·execute_tool·invoke_agent)·traceparent 전파. Opik·티어드 보관은 P1 | PRD D10-03(P0)·D10-04(P1) |

## 개발환경 특수 요구

- 테넌트 격리 테스트(크로스테넌트 누출 단언, RLS 강제) → AgentPlaza 에서는 **에이전트 간 네트워크·DB 격리 시험**(NFR-I4, 에이전트별 DB role)으로 대체
  (구현 2026-10-07: 에이전트별 전용 네트워크 + 전용 데이터 볼륨으로 격리, 시험 E7-03·E7-10. 공유 RDBMS 의 에이전트별 DB role 은 미사용)
- 표준 CI/CD(lint/type/test/build/deploy)
- 텔레메트리 보관/삭제 검증(CC6.5/A.8.10), OpenAPI 계약 테스트
- SOC 2/ISO 통제 증적 자동화(접근로그·변경관리)

## 추가 시험

`test/dev-env`·`test/impl/<Nth>` 시나리오에 포함한다.

| 시험 | AgentPlaza 대응 |
|---|---|
| 크로스테넌트 데이터 누출 차단(RLS) | 에이전트 간 데이터 접근 차단(NFR-I4) — 멀티테넌시 도입 시 원래 항목으로 복귀 |
| OpenAPI 계약 적합성(contract test) | agent.yaml 생성물(Card·server.json·OpenAPI) ↔ 런타임 diff 시험(NFR-P3) |
| 감사로그 보관기간 경과 삭제 증명 | 대화·파일 보존기간 경과 삭제 시험(NFR-C3). 감사 원장은 append-only 해시 체인 무결성 검사 병행(D9-07) |
| 접근성 자동 검사 | 콘솔 E2E 에 axe(WCAG 2.2 AA) 검사 — `E2E_SPEC=a11y`(구현됨, E24) |
| 조직 경계 노출 시험 | 다른 조직·그룹 구성원에게 배치되지 않은 에이전트의 네비·도구·MCP·Addon 이 보이지 않음(구현됨, E23) |
| 결제 어댑터 시험 모드 | 가짜 결제대행·stripe-mock 으로 서명 검증·금액 대조, 실결제 0건(구현됨, E22). 실 테스트 키 결제는 MANUAL |

## 구현 대응 현황 (2026-10-07)

P0·P1·P2(Epic 1–25) 구현 기준이다. 시험 ID 는 `test/impl/<Nth>/` 시나리오와 `test/test_e*.py` 를 가리킨다.

| 통제 | 구현 | 시험 |
|---|---|---|
| 접근통제(RBAC) | supervisor > admin > user, 하위 권한만 부여, 서버 403. 로그인 5회 실패 잠금, 일반화된 오류 메시지 | E1-03·E1-04 |
| 감사 원장 | 도구 호출·관리 작업을 해시 체인으로 기록, `/api/audit/verify` 무결성 검사. PostgreSQL 은 마이그레이션 0001 트리거로 UPDATE/DELETE 차단 | E1-09·E4-07 |
| 데이터 등급 | L0–L3, 헤더 없으면 L2. L2 이상은 로컬 모델만(폴백보다 우선), 거부는 원장 기록 | E3-06·E5-09 |
| 보존·삭제 | 설정값(대화 365일·파일 90일), 보존 경과 파기 작업(`/api/admin/retention/run`) — 대화와 함께 실행 이벤트(run_events)·첨부 파일 파기, 트레이스 스팬은 관측 보존 기간 경과 시 파기, 메모리는 사용자 삭제권(`잊어줘:`·삭제 API) | E5-07·E10-04·E15·E17-07 |
| 격리 | 업로드 코드는 컨테이너만(in-process 거부), compose 린트, 에이전트별 네트워크(egress 미선언 시 internal), docker.sock 은 runtime 만 | E7-03·E7-10 |
| 계약 적합성 | 생성 Card·server.json ↔ 런타임 `/api/capabilities`·MCP tools/list 대조, 불일치 시 롤백 | E6-12·E8-08 |
| 시크릿 | 퍼블릭 LLM 키는 api 만 보유, 에이전트 내부 키는 HMAC 파생(미저장). 시크릿 저장소 = AES-256-GCM 암호문(scope·이름 AAD, HKDF 마스터 키), 에이전트는 선언한 secretRefs 만 자기 키로 pull, 로그 마스킹, 원격 레지스트리 토큰·라이선스 발급 키도 저장소에만 | E6·E8·E13·E18 |
| 공급망 | 등록 3·4단계: checksums·cosign 서명(신뢰 키, 철회 키 거부)·SBOM(syft)·취약점(trivy, Critical 차단)·라이선스 G1–G5(G5 차단·G4 격리)·egress 정책. 마켓 게시는 퍼블리셔 키 서명 필수, 설치 산출물의 출처·라이선스 기록(NFR-C1·C2) | E12·E18-03 |
| 개인정보 보호(가드레일) | 프롬프트 인젝션 차단, 한국어 PII 10종 마스킹(외부 LLM 전송 전), 데이터 등급별 모델·도구·내보내기 정책, 외부 결과 리뷰어 게이트, 레이트리밋·툴 단위 RBAC — 판정은 원장 기록 | E13 |
| 백업·복구 | 업그레이드 전 사전 백업·실패 시 복원(NFR-O4), 에이전트 볼륨·플랫폼 DB 백업, 폐쇄망 오프라인 번들(sha256 검증) | E14·E18-10 |
| 상거래 증적 | 유료 거래는 영수증(JSON)·Ed25519 라이선스 토큰·원장(market.purchase·license.*)을 남긴다. 결제는 호스티드(Stripe·Polar·Lago) — 카드 정보 미수집, 웹훅 서명·재전송 시각·금액·통화 대조, Lago 고객 식별자는 이메일 해시. 정산·세금은 X12 범위(NFR-C4) | E18-05·E22 |
| 접근성 | 콘솔·Addon 화면 KWCAG 2.2 / WCAG 2.2 AA — axe 자동 검사(57화면 라이트·다크 위반 0), 글자용 대비 토큰 | E24·완료 게이트 |
| 노출 범위(조직) | 조직·그룹·사용자 단위 배치 범위 밖이면 목록·계획·MCP·A2A·Addon 화면 차단, 변경은 원장(agent.scope_set) | E23 |
| 외부 채널(메신저·위젯) | 채널 대화는 외부 메신저(Slack·Telegram·카카오)를 거친다 — 채널 데이터 등급 기본 L2(설정 가능), 메신저 쪽 보존·처리는 각 서비스 약관을 따른다. 웹훅 서명·토큰 인증, 위젯은 허용 오리진만(CSP), 위젯 토큰은 플랫폼 API 불가, 채널 사용자 세션도 대화 보존 기간·삭제권을 따른다 | E25 |
| 알림 | 장애·예산·설치 실패·라이선스 만료를 알림 센터와 Slack·Telegram·메일로 — 비밀값(웹훅 URL·봇 토큰·SMTP 암호)은 시크릿 저장소, 외부 발송은 관리자·전체 대상 알림만 | E19 |
| LLM 키 격리 | 퍼블릭 LLM 키는 Bifrost 서비스에만(api 비움), Bifrost 는 포트 미공개·read_only·cap_drop ALL | E20 |

미구현: OIDC SSO·코어 2FA(IdP 위임), 구독 갱신·환불·정산·세금(X12), 텔레메트리 티어드 보관·삭제 증명, gVisor 강제(runsc 없는 호스트는 runc + 경고), 키리스 서명(Fulcio)·OCI 아티팩트. 이 중 OCI 아티팩트·사설 미러 설치와 OIDC SSO 는 다음 이터레이션(계획표 Epic 26·27, TODO).

## 출처

- https://isms-p.or.kr/sysm/intro/selectSysmCertDetail.do (ISMS-P)
- https://isms.kisa.or.kr/main/csap/notice/ (CSAP 2025)
- https://secureframe.com/blog/soc-2-vs-iso-27001
- https://oneuptime.com/blog/post/2026-02-06-telemetry-retention-soc2-iso27001/view
- https://www.ideadope.com/roadmaps/how-to-build-multi-tenant-saas-2025
