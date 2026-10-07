# One-Page PRD: AgentPlaza

> 로컬·퍼블릭 LLM 겸용 멀티 에이전트 플랫폼 및 에이전트 마켓플레이스.
> 이 문서는 기획서 2종(본문 PRD v2·UI 설계서)을 One-Page 형식으로 요약·매핑한 초안이다. 상세 규격(agent.yaml 전문, compose 전문, 프로토콜 실측, 후보 303종 전수표)은 원문을 정본으로 한다.
> 표기: `(출처: 파일 p.N)` = 원문 PDF 쪽번호, `가정:` = 원문에 없어 추정한 값.

## 1. 개요

- **한 줄 요약**: 로컬 LLM 과 퍼블릭 AI 서비스를 하나의 게이트웨이로 쓰고, Orchestrator·AI Assistant 를 기본 제공하며, Zip(agent.zip)으로 포장된 Addon 에이전트를 마켓플레이스에서 골라 docker compose 로 독립 또는 연계 구동하는 멀티 에이전트 플랫폼. (출처: AgentPlaza_PRD.v2.pdf p.1, p.12)
- **구성 단위**: 기능 항목 하나 = 에이전트 하나. 도메인 70 + 후순위 12 + 플랫폼 공유 서비스 12 = 94종. 모든 에이전트는 다른 에이전트 없이 홀로 실행된다(M1). (출처: AgentPlaza_PRD.v2.pdf p.12)
- **왜 지금**: v1 구현(사내 템플릿 `[REDACTED]/pub-MultiAIAgent-Template`)이 Orchestrator·Assistant·Zip 핫 디플로이·MCP·A2A 를 이미 갖췄지만 **서명·권한 선언·격리·마켓플레이스·상거래** 5가지가 없다. 또 MCP(2026-07-28 무상태 재설계)·A2A(v1.0.1) 사양이 바뀌어 v1 프로토콜 구현이 현행과 어긋난다. 본 제품은 v1 을 대체하지 않고 승계·확장한다. (출처: AgentPlaza_PRD.v2.pdf p.4)
- **작성 / 날짜 / 버전**: 원문 v2 2026-09-18 · 본 One-Page 초안 v0.1 2026-10-06(wds-prd 생성) · 작성자: `가정: 기입 필요`

## 2. 문제와 대상 (Why & Who)

- **핵심 문제 (문제–영향–근거)**: 여러 AI 에이전트를 한 곳에서 등록·구동·연계하려 하지만, v1 은 업로드한 Zip 코드를 플랫폼 프로세스 안에서 그대로 실행(importlib)하고 라이선스 조건이 다른 엔진을 한 프로세스에 섞는다. 그래서 임의 코드 실행 위험이 있고, 에이전트 하나만 떼어 납품할 수 없으며, 로컬↔퍼블릭 LLM 을 바꾸려면 코드를 고쳐야 한다. 실측 결과 참고 저장소 20개 중 그대로 내장 가능한 것은 6개뿐이다. (출처: AgentPlaza_PRD.v2.pdf p.4)
- **비즈니스 목표**: ① 에이전트 단위 부분 도입·납품(M1) ② 사내·유료 마켓을 통한 재사용·판매 ③ 폐쇄망(퍼블릭 키 0개) 고객 대응 ④ 업종별 스타터 팩(제조·식품안전·물류통관·HR·보안·공공)으로 도메인 확장. (출처: AgentPlaza_PRD.v2.pdf p.13, p.21, p.62)
- **사용자 가치**: 코드 수정 없이 마켓에서 고른 에이전트를 5분 안에 쓰고, 내부 문서가 퍼블릭 LLM 으로 새지 않으며, 위험한 작업은 승인 후에만 실행된다. (출처: AgentPlaza_PRD.v2.pdf p.19)
- **근거 데이터**: GitHub REST 실측 저장소 361개·LICENSE 판독 77건, 라이선스 함정 6건(LangGraph 서버 ELv2, LiteLLM enterprise, Redis 8 3중 라이선스 등), 로컬 런타임 9종의 Anthropic `/v1/messages` 지원, 참조 프로젝트 11종에서 Addon 후보 303종 도출. (출처: AgentPlaza_PRD.v2.pdf p.1, p.4, p.62) `가정: 사용자 VOC·운영 로그 정량 근거는 원문에 없음`
- **타깃 사용자**: 플랫폼 운영자(supervisor/admin), 일반 사용자(채팅·화면), Addon 개발자·퍼블리셔, 외부 시스템(MCP/A2A 클라이언트: Claude Desktop·Cursor·Open WebUI·타사 에이전트). (출처: AgentPlaza_PRD.v2.pdf p.12, p.14)
- **대표 사용 상황**: 인터넷이 끊긴 사무실에서 사내 문서 질의, 마켓에서 게시판 에이전트 5분 설치, 고객사 서버에 에이전트 하나만 납품, 파트너 에이전트를 코드 설치 없이 연동. (출처: AgentPlaza_PRD.v2.pdf p.19)

## 3. 범위 (What — In / Out)

### 3.1 이번 릴리스 핵심 기능 (P0 — 첫 릴리스 필수, 도메인 FR 70개 중 43개)

| # | 핵심 기능 (P0) | 사용자가 보는 결과 | 관련 FR |
|---|---|---|---|
| 1 | **LLM 통합 게이트웨이** | 로컬(Ollama)·퍼블릭(OpenAI·Claude·Gemini) 모델을 같은 별칭(`plaza/chat` 등)으로 호출, 퍼블릭 장애 시 로컬 폴백, 데이터 등급별 허용 모델 강제 | D1-01, D1-03, D1-05, D1-06 |
| 2 | **기본 에이전트 2종** | 설치 직후 Assistant 채팅(스트리밍·세션·도구 진행/승인 카드)과 Orchestrator(의도 분류·라우팅·실행 패턴·도구 호출·휴먼 승인)만으로 대화·도구 호출 가능 | D2-01~04, D2-06, D3-01~03 |
| 3 | **Addon 개발·등록 파이프라인** | 템플릿 9유형·스캐폴드 위저드/CLI·SDK·agent.yaml 검증 → Zip 업로드·구조 검증 → 컨테이너 디플로이 → 콘솔 화면 자동 노출, 독립 실행 번들 내보내기 | D4-01~04, D4-07, D5-01, D5-02, D5-05~07 |
| 4 | **마켓플레이스 설치 3경로** | 스토어(검색·상세·신뢰 배지)에서 A 다운로드 설치 / B 직접 설치(zip·Git·OCI·미러) / C 원격 A2A·MCP 연동 | D6-01~04 |
| 5 | **표준 프로토콜·런타임·거버넌스 기반** | 모든 에이전트가 MCP·A2A 로 노출/호출, compose 골격·루트 include·Traefik 라우팅·격리·GPU, 계정·RBAC·API 키·감사 원장, 콘솔·셋업 위저드·OTel·공통 데이터 모델 | D7-01~04, D8-01~05, D9-01~03, D9-07, D10-01~03, D10-06 |

(출처: AgentPlaza_PRD.v2.pdf p.15–18, p.31)

- **P1 (두 번째 릴리스, 25개)**: 고성능 서빙·CLI 에이전트 백엔드·임베딩(D1-02/04/07), 리뷰어 게이트·내구성(D2-05/07), 멀티모달·메모리·RAG(D3-04~06), 계약 시험·서명 패키징(D4-05/06), 서명·SBOM·라이선스 게이트(D5-03/04), 구매·퍼블리셔·업데이트(D6-05~07), OpenAI 호환 노출·AG-UI/ACP·게이트웨이 정책(D7-05~07), 업그레이드·오프라인 설치(D8-06/07), 시크릿·정책 엔진·가드레일(D9-04~06), LLM 관측 UI·평가(D10-04/05). (출처: AgentPlaza_PRD.v2.pdf p.15–18)
- **P1 추가 범위 (2026-10-07 결정 — Open Questions 답변, 다음 구현 이터레이션)**: ① LLM 게이트웨이 엔진 Bifrost(Apache-2.0) 채택(Q1) ② Assistant 에이전트 SDK pydantic-ai(Q2) ③ 결제 어댑터 Lago·Polar·Stripe(Q6, mock 은 시험용으로 유지) ④ 조직·부서 단위 배치(orgs·org_groups, deploy_scope org|group|user)와 조직·그룹·구성원 화면 K02·조직 도입 흐름 FL-07(Q7·Q12) ⑤ 월 예산 80% 도달 시 로컬 강제 라우팅(J05, Q15) ⑥ 접근성 KWCAG 2.2 / WCAG 2.2 AA(Q9) ⑦ MCP 계약 시험에 2025-11-25 `initialize` 핸드셰이크 포함(Q8). (출처: AgentPlaza_PRD.v2.pdf p.17, p.20–21, p.56, p.58, p.62; AgentPlaza_UI_Design.pdf p.18, p.53, p.83, p.87)
- **P2 (2개)**: 채널·임베드(D3-07), 알림·상태(D10-07). (출처: AgentPlaza_PRD.v2.pdf p.16, p.18)
  - **범위 이동(2026-10-07, SCOPE)**: P2 2개를 이번 구현에 포함 — D10-07 알림·상태(헬스 대시보드·알림 센터 B03·Slack/Telegram/메일 알림·사용량 리포트, 자체 경량 + 메일 시험용 mailpit 오버레이), D3-07 채널·임베드(웹 위젯 iframe+postMessage·Slack·Telegram·카카오 i 오픈빌더 스킬, UI C07). 실 서비스 토큰은 사용자가 넣고 시험은 가짜 서버로. (출처: AgentPlaza_PRD.v2.pdf p.16, p.18; AgentPlaza_UI_Design.pdf p.9–10)
- **다음 이터레이션 (2026-10-07, 5차 확인 — 구현 가정으로 남은 갭 보강, F)**: ① 경로 B OCI 아티팩트·사설 미러 설치(D6-03, P0 갭) ② 콘솔 OIDC SSO 로그인(D9-01, IdP 위임) ③ 메모리 LLM 자동 추출(D3-05 — 제안 → 사용자 승인 후 저장, 자동 저장 없음) ④ 기본 에이전트(Orchestrator·Assistant) 컨테이너 분리 → 구현 계획표 Epic 26–29(TODO). 우선순위·순서는 다음 wds-implement 0-3 확인에서 정한다. 가정: 범위·수용 기준은 계획표 행 기준.

### 3.2 비기능 핵심 (품질 기준 요지)

| 영역 | 핵심 요구 | 검증 |
|---|---|---|
| 격리·독립 구동(최상위) | 모든 에이전트 `compose --profile standalone up` → `/health` ok · 업로드 코드는 기본 별 컨테이너 · docker.sock/host network/privileged 금지 · 삭제 시 60초 내 흔적 제거 | CI M1 기동 시험, compose 린트 (NFR-I1~I6) |
| LLM 공급 | 퍼블릭 장애 30초 내 로컬 폴백 + 강등 배지 · 퍼블릭 키 0개로 전 기능 동작 · confidential 은 local 모델만 · 게이트웨이 오버헤드 p95 ≤ 50ms | 장애 주입·에어갭·벤치 (NFR-L1~L5) |
| 보안 | zip-slip·심볼릭 링크·압축 폭탄 거부 · Critical 취약점 설치 거부 · 퍼블릭 키는 게이트웨이만 보유 · 무인증 엔드포인트는 `/health`·agent-card 뿐 | 악성 코퍼스·라우트 스캔 (NFR-S1~S6) |
| 사용성 | 빈 서버→첫 대화 30분 · 마켓 설치→네비 노출 5분 · 한국어 기본/영어 폴백 · 접근성 KWCAG 2.2 / WCAG 2.2 AA(원문 WCAG 2.1 AA 에서 상향, Q9 결정) | 타이머·i18n 린트·axe (NFR-U1~U5) |
| 운영·준법 | Linux x86_64/arm64 + macOS Apple Silicon · SQLite↔PostgreSQL 동일 마이그레이션 · G4(AGPL 등) 코드 기본 이미지 미링크 · 개인정보 보존기간·삭제권 | 3플랫폼 CI·SBOM 스캔 (NFR-O1~O5, NFR-C1~C4) |

(출처: AgentPlaza_PRD.v2.pdf p.20–21)

### 3.3 하지 않을 것 (Out of Scope)

- 멀티테넌시(X09, 테넌트 간 데이터 분리) — 단, 단일 테넌트 안의 조직·부서 단위 배치는 범위 In 으로 이동(Q7 결정, P1 추가 범위). 상거래 정산·세금(X12 — 라이선스 키 발급·검증·영수증 증적과 Lago·Polar·Stripe 결제 어댑터까지), 파인튠 학습 UI(X08 → LLMForge 위임), 모바일 앱(X11, 콘솔 PWA 우선), 에이전트 프레임워크 자체 개발. (출처: AgentPlaza_PRD.v2.pdf p.12, p.18, p.52)
- Kubernetes 배포(X10) — compose 가 1차, K8s 는 변환 대상. 비주얼 플로우 빌더·이미지 생성·음성·n8n 연계·코드 샌드박스·브라우저 에이전트·RAGFlow(X01~X07)는 P2 Addon 으로 후순위. UI 설계서의 워크플로(F01~F04)·플레이그라운드(H01~H03)·가드레일 카탈로그(I01) 화면도 코어가 아닌 Addon 으로 둔다(Q11 결정). (출처: AgentPlaza_PRD.v2.pdf p.13, p.18; AgentPlaza_UI_Design.pdf p.9–12)
- 라이선스상 금지: Open WebUI 포크, langgraph-api(ELv2) 서버 런타임 사용, Dify·n8n·AutoGPT platform 내장(연계만), Redis 8(→ Valkey). (출처: AgentPlaza_PRD.v2.pdf p.51)

## 4. 사용자 경험 (How — User Flow)

- **시나리오 1 — 최초 설치 → 첫 대화 (운영자)**: `git clone` 또는 번들 → `plaza up` → 셋업 위저드(관리자 생성 → LLM 연결: Ollama 자동 감지 또는 퍼블릭 키 입력 → 모델 pull) → Assistant 채팅 시작. 목표 30분 이내. 화면: A02 설치 위저드 5단계(관리자 → LLM 연결 → 모델 pull → 기본 에이전트 → 완료) → A01 로그인 → B02 대시보드 → C01 채팅. (출처: AgentPlaza_PRD.v2.pdf p.14, p.21; AgentPlaza_UI_Design.pdf p.14, p.23)
- **시나리오 2 — 마켓 설치, 경로 A (운영자)**: 마켓 탭 → 검색 → 상세(라이선스·권한·서명 배지 확인) → 설치(유료면 라이선스 키) → 필수 환경값(required_env) 입력 → 등록 8단계 자동 진행(업로드·구조 검증·서명/SBOM·라이선스 정책·빌드·등록·기동/헬스·노출) → 콘솔 네비에 화면, Assistant 에 도구, `/mcp`·Agent Card 노출. 목표 5분 이내. 화면: E01 카탈로그 → E02 3축 브라우즈 → E03 자산 상세 → (유료면 E12) → E04 도입 위저드 → D05 설치 진행 → D02 에이전트 상세. (출처: AgentPlaza_PRD.v2.pdf p.14, p.42; AgentPlaza_UI_Design.pdf p.15)
- **시나리오 3 — 조직 단위 도입 (운영자, P1 추가 범위·Q7)**: 마켓 도입 위저드에서 배치 대상(deploy_scope = 조직·그룹·사용자)을 고른다 → 해당 조직·그룹 구성원에게만 네비·도구가 노출된다. 조직·그룹·구성원은 K02 화면에서 관리한다(supervisor·조직 admin). **모델 확정(2026-10-07 3차)**: 기본 조직 + 그룹(부서) + 구성원, 에이전트별 deploy_scope = 조직 전체 | 그룹 목록 | 사용자 목록 — 범위 밖 사용자에게는 네비·도구·MCP·계획에서 제외. 기존 사용자·에이전트는 기본 조직으로 이관(동작 변화 없음). 조직 admin = 그 조직의 구성원·그룹 관리, supervisor = 전체. `가정: 공공 노출정책은 deploy_scope 로 대체(별도 정책 미구현)` (출처: AgentPlaza_UI_Design.pdf p.18, p.53, p.87; AgentPlaza_PRD.v2.pdf p.58, p.62)
- **기타 흐름**: Addon 개발(`plaza init → test → publish`), 직접 설치(ZIP 업로드, 경로 B), 원격 연동(A2A Card/MCP URL 등록 → 계약 시험, 경로 C), 독립 납품(Standalone 번들 추출 → 대상 서버 `compose up`), 외부 사용(Cursor 의 `/mcp/{agent}`, Open WebUI 의 `/v1`). (출처: AgentPlaza_PRD.v2.pdf p.14)

**수용 기준 (Given-When-Then, 대표 사용자 스토리 8)** (출처: AgentPlaza_PRD.v2.pdf p.19)

| ID | Given | When | Then |
|---|---|---|---|
| US1 | 퍼블릭 API 가 차단된 사무실, Ollama 와 사내 문서 RAG 가 설치됨 | 일반 사용자가 사내 문서로 질문 | Ollama 로 응답하고 인용을 포함한다 |
| US2 | 운영자가 마켓에 접속 | 게시판 에이전트를 설치 | 5분 안에 콘솔 네비에 노출되고 코드 편집은 0건 |
| US3 | 개발자가 템플릿으로 재고 에이전트를 만듦 | `plaza init/test/publish` 후 zip 업로드 | 업로드 성공, MCP 도구 목록에 보인다 |
| US4 | 문서 등급이 confidential | 퍼블릭 LLM 으로 요청이 향함 | 게이트웨이가 거부(403)하고 감사 원장에 남긴다 |
| US5 | 외부 개발자가 API 키를 보유 | Cursor 에서 `/mcp/{agent}` 에 x-api-key 로 연결 | `tools/list` 가 성공한다 |
| US6 | 파트너가 자사 ADK 에이전트의 Agent Card URL 보유 | 원격 에이전트로 등록 | 계약 시험 통과 후 Orchestrator 가 라우팅한다 |
| US7 | 고객사가 에이전트 번들 하나를 받음 | 압축 해제 후 `compose up` | `/health` ok, MCP·A2A 응답 |
| US8 | 승인 필요(human_approval_required) 작업이 요청됨 | 관리자가 승인 카드를 승인 / 미승인 만료 | 승인 시 재개, 만료 시 취소 |

## 5. 성공 지표 (Success)

| 지표 | 기준선 | 목표 | 측정 방법 |
|---|---|---|---|
| M1 독립 기동 성공률(70 항목) | v1: 내장 2 + 템플릿 4 | 100% | `/health` ok CI 매트릭스 |
| 마켓 설치 → 네비 노출 | v1 zip: 30초(프론트 재빌드) | 5분 이내(이미지 빌드 포함) | 타이머 |
| 빈 서버 → 첫 대화 | 없음 | 30분 이내 | 신규 운영자 측정 |
| 퍼블릭 장애 시 로컬 폴백 | v1: 텍스트만 | 30초 내, 도구 호출 유지 | 장애 주입 시험 |
| 프라이버시 등급 위반 | 없음 | 0건 | 게이트웨이 403 로그 + 감사 원장 |
| MCP·A2A 계약 시험 통과 | v1: v0.x 스타일 | MCP 2026-07-28 · A2A v1.0.1 100% | MCP Inspector · a2a 클라이언트 |
| G4 코드 기본 이미지 링크 | 미측정 | 0건 | SBOM 라이선스 CI |
| Agent Card·server.json 과 런타임 불일치 | v1: 손코딩 | 0건 | 생성물 diff 시험 |
| 감사 누락 도구 호출 | 없음 | 0건 | 원장 샘플링 |
| 한국어 UI 키 커버리지 | v1: ko/en | 100% | i18n 린트 |

(출처: AgentPlaza_PRD.v2.pdf p.55 — 원문이 기준선을 `가정` 으로 표기함)

## 6. 리스크 및 메모

- **주요 리스크**: MCP 사양 파괴적 개정 재발(R1 → 버전 협상을 게이트웨이에 집중) · LiteLLM enterprise/·langgraph-api ELv2 라이선스 경계(R3·R4 → 법무 확인, Bifrost 병행 PoC, 금지 패키지 CI) · 직접 업로드 zip 의 임의 코드 실행(R5 → 컨테이너 기본 + gVisor + egress 차단) · compose include 이름 충돌(R6 → 접두어 CI) · 모델 라이선스 조건 변경(R9) · Apple Silicon GPU 컨테이너 미지원(R10 → 호스트 네이티브 Ollama 브리지) · 유료 마켓 결제·세금 법규(R12 → X12 분리). (출처: AgentPlaza_PRD.v2.pdf p.55–56)
- **의존성**: 외부 사양(MCP 2026-07-28, A2A v1.0.1, AG-UI 1.0, Compose Spec v5, OTel GenAI semconv) · OSS(LiteLLM/Bifrost, Ollama, LangGraph 라이브러리, Traefik, Valkey, cosign/syft/trivy) · v1 템플릿 저장소 · 선행 내부 문서(AgentNexus, AgentStackHub, AegisMesh/AgentSentry, LLMForge) · 법무 검토(라이선스·전자상거래·개인정보보호법/ISMS-P/CSAP). (출처: AgentPlaza_PRD.v2.pdf p.1, p.7, p.51–52)
- **단계(로드맵)**: S0 골격(2주) → S1 v1 이식(4주) → S2 패키지·레지스트리(4주) → S3 프로토콜 정식화(3주) → S4 마켓 3경로(4주) = P0 약 17주(원문 가정). S5~S7 신뢰·격리/관측·평가/구매·퍼블리셔 P1, S8 Addon 확장 P2. (출처: AgentPlaza_PRD.v2.pdf p.55)

### 미결정 사항 (Open Questions)

| # | 질문 | 출처 |
|---|---|---|
| Q1 | 게이트웨이를 LiteLLM(기능 폭) vs Bifrost(전부 Apache-2.0) 중 무엇으로? — 법무 답변 종속. **결정(2026-10-06)**: 1차는 플랫폼 내장 경량 라우터(OpenAI 호환 `/v1`, 별칭·폴백·데이터 등급·계량). LiteLLM/Bifrost 는 업스트림 공급자 옵션으로 연결 · **결정(2026-10-07 2차)**: 게이트웨이 엔진은 **Bifrost**(전부 Apache-2.0). LiteLLM 미사용. **연결 확정(2026-10-07 3차)**: Bifrost 는 compose 서비스, 별칭·데이터 등급·계량·예산 정책 계층은 플랫폼 `/v1` 에 유지, 공급자 호출(Ollama·퍼블릭)만 Bifrost 경유 — 퍼블릭 키는 Bifrost 에만, Bifrost 장애 시 직접 호출 폴백 | AgentPlaza_PRD.v2.pdf p.56 |
| Q2 | Assistant 에이전트 SDK 를 openai-agents-python vs pydantic-ai 중 무엇으로? **결정(2026-10-06)**: P0 는 SDK 미고정 — Orchestrator 는 LangGraph 라이브러리, Assistant 는 게이트웨이 직접 호출 · **결정(2026-10-07 2차)**: Assistant SDK = **pydantic-ai** | AgentPlaza_PRD.v2.pdf p.56 |
| Q3 | Addon 프론트 통합에서 Module Federation 허용 범위(1st-party 만 vs 전면 iframe) · **구현 가정(2026-10-07)**: P0 는 전면 iframe — Addon 화면을 Traefik 별도 진입점(apps 포트) 오리진에 띄우고 CSP frame-ancestors 로 제한. Module Federation 미사용 · **결정(2026-10-07 2차)**: **전면 iframe** 확정(구현과 일치) | AgentPlaza_PRD.v2.pdf p.56 |
| Q4 | MCP 포트 모드(v1 호환) 유지 기간, Temporal 도입 시점, 무료 git+JSON 카탈로그 ↔ 유료 마켓 서버 이원화 시점 · **구현 가정(2026-10-07)**: MCP 포트 모드 미구현(게이트웨이 경로 `/mcp/{id}` 만) · Temporal 미도입 · 카탈로그는 무료 정적 git+JSON(`market/catalog.json`)만 · **결정(2026-10-07 2차)**: 무료 카탈로그↔유료 마켓 서버 **이원화는 P1(Epic 18)에서 완료**로 확정 — 정적 git+JSON 카탈로그(큐레이션) + 마켓 서버(DB 리스팅·구매·레지스트리 API) 병행. MCP 포트 모드 미구현·Temporal 미도입은 현 가정 유지 | AgentPlaza_PRD.v2.pdf p.56 |
| Q5 | **상충**: P0 수량 — 본문 "첫 릴리스(P0 41종)" vs 같은 쪽 표·FR 집계 "P0 43". 본 PRD 는 FR 표 집계(43)를 따름 · **구현 가정(2026-10-07)**: 43 으로 추적(`plaza verify-coverage`) · **결정(2026-10-07 2차)**: **P0 = 43** 확정 | AgentPlaza_PRD.v2.pdf p.31 vs p.15–18 |
| Q6 | **상충**: 결제 어댑터 — D6-05 "Lago/Polar/Stripe" vs 로드맵 S7 "Kill Bill 어댑터" · **구현 가정(2026-10-07)**: 결제는 범위 제외(P1 S7) · **결정(2026-10-07)**: 결제는 어댑터 인터페이스 + mock(실결제 없음), 라이선스는 Ed25519 서명 토큰(오프라인 검증·좌석·기간). Lago/Polar/Stripe·Kill Bill 은 어댑터 후보 · **결정(2026-10-07 2차)**: 결제 어댑터는 **Lago·Polar·Stripe**(Kill Bill 미채택). mock 은 시험·폐쇄망용으로 유지 | AgentPlaza_PRD.v2.pdf p.17 vs p.55 |
| Q7 | **상충**: 멀티테넌시는 범위 밖(X09)이나, v2 마켓 설계는 조직·부서 단위 배치(orgs/org_groups, deploy_scope org\|group\|user)와 공공 노출정책을 채택. 조직 단위 배치를 첫 릴리스에 넣는가? · **구현 가정(2026-10-07)**: 조직 단위 배치 제외 — 단일 조직, 사용자·역할만 · **결정(2026-10-07 2차)**: **조직·부서 단위 배치 포함**(orgs·org_groups, deploy_scope org\|group\|user) — P1 추가 범위. 테넌트 분리(X09)는 계속 범위 밖 | AgentPlaza_PRD.v2.pdf p.12 vs p.58, p.62 |
| Q8 | MCP 계약 시험 기준: NFR-P1 은 `initialize` 를 시험하나, 현행 2026-07-28 은 initialize 핸드셰이크를 제거. 2025-11-25 동시 광고 범위에서만 시험하는지 명시 필요 · **구현 가정(2026-10-07)**: 2026-07-28(server/discover)·2025-11-25(initialize) 둘 다 응답. 계약 시험은 공식 python-sdk 클라이언트로 tools/list + /api/capabilities + 카드 skills·서명 대조 · **결정(2026-10-07 2차)**: 계약 시험에 **initialize(2025-11-25) 핸드셰이크를 명시적으로 시험**. 현재 설치 7단계·`plaza test` 는 server/discover 우선(initialize 는 폴백) → 두 핸드셰이크 모두 시험하도록 보완 필요 | AgentPlaza_PRD.v2.pdf p.4, p.17, p.20 |
| Q9 | 접근성 기준: 원문 NFR-U4 는 WCAG 2.1 AA 목표. `가정: KWCAG 2.2 / WCAG 2.2 AA 로 상향 권장` · **결정(2026-10-07 2차)**: **KWCAG 2.2 / WCAG 2.2 AA 로 상향** | AgentPlaza_PRD.v2.pdf p.21 |
| Q10 | 참조 프로젝트·사용자 저장소 LICENSE 대부분 미확인 — 마켓 게시·고객 전달 전 부여 필요(R13) · **미결(2026-10-07 2차, 확인 필요)**: 마켓 게시·고객 전달 전 LICENSE 부여 여부를 저장소별로 확인한다 | AgentPlaza_PRD.v2.pdf p.55, p.57 |
| Q11 | **상충**: 워크플로 — UI 는 워크플로 목록·빌더·실행 이력·트리거(F01~F04)를 코어 콘솔 P1 화면으로 두지만, PRD 는 비주얼 플로우 빌더를 X01(P2, Langflow Addon)로 두고 FR-D 에 워크플로 항목이 없다. 마찬가지로 플레이그라운드(H01~H03)·가드레일 카탈로그(I01)도 코어 화면인지 Addon 인지 결정 필요 · **구현 가정(2026-10-07)**: 워크플로·플레이그라운드·가드레일 카탈로그 화면 제외(P0 36화면 기준) · **결정(2026-10-07 2차)**: 워크플로·플레이그라운드·가드레일 카탈로그 화면은 **Addon**(코어 아님). 코어의 평가 묶음·A/B 비교(D10-05, Epic 17)는 FR 이므로 유지 `가정` | AgentPlaza_UI_Design.pdf p.9–12, p.63–66 vs AgentPlaza_PRD.v2.pdf p.18, p.58 |
| Q12 | **상충(Q7 연장)**: UI 는 조직·그룹·구성원 화면(K02, P1, X09 추적)과 조직 도입 흐름(FL-07)을 정의했는데, 멀티테넌시는 PRD 범위 밖이다 · **구현 가정(2026-10-07)**: 조직·그룹 화면 제외, 사용자·API 키(K01·K04)만 · **결정(2026-10-07 2차)**: **조직·그룹 화면(K02)·조직 도입 흐름(FL-07)까지 포함** — P1 추가 범위 | AgentPlaza_UI_Design.pdf p.18, p.87 vs AgentPlaza_PRD.v2.pdf p.12 |
| Q13 | **UI 설계서 내부 불일치**: 같은 ID 가 IA 와 화면 목록에서 서로 다른 화면을 가리킨다 — B04(IA·FL-01 은 "온보딩 체크리스트", 목록은 "전역 검색"), D10("디플로이 모드" vs "삭제·해제 확인"), E09("버전·호환" vs "비교"). 또 SCR-L03 은 참조되지만 정의가 없고, 등록 파이프라인 단계명이 쪽마다 다르다(p.15 vs p.41, p.108 은 "7단계") · **구현 가정(2026-10-07)**: 화면 목록 ID 기준, 등록 파이프라인은 8단계 · **결정(2026-10-07 2차)**: **화면 목록 ID 기준** 확정 | AgentPlaza_UI_Design.pdf p.7, p.9, p.14–15, p.26, p.41, p.46, p.58, p.108 |
| Q14 | **UI 설계서 내부 불일치**: 권한 매트릭스와 화면 목록의 권한이 다르다(D01·D09: 목록은 "로그인"인데 매트릭스에서 user 는 "—", C07: 목록은 admin 인데 매트릭스에서 user 가 허용) · **구현 가정(2026-10-07)**: 화면 목록 권한 기준 + 서버 403 이중 차단 · **결정(2026-10-07 2차)**: **화면 목록 권한 기준 + 서버 403 이중 차단** 확정 | AgentPlaza_UI_Design.pdf p.9–10 vs p.13 |
| Q15 | **UI 에만 있는 규칙 — PRD 반영 여부 확인 필요**: 월 예산 80% 도달 시 로컬 강제 라우팅(J05), 보존 기간 기본값 대화 365일·파일 90일(L01), 로그인 5회 실패 시 잠금·코어 2FA(A01). PRD 는 MFA 를 IdP 에 위임하고 보존 기간 값은 정하지 않았다 · **구현 가정(2026-10-07)**: 보존 기간은 설정값(대화 365일·파일 90일), 로그인 5회 실패 잠금 구현. 코어 2FA·예산 80% 로컬 강제 라우팅은 미구현(IdP 위임·P1) · **결정(2026-10-07 2차)**: **월 예산 80% 도달 시 로컬 강제 라우팅 구현**(J05) — P1 추가 범위. 코어 2FA 는 IdP 위임 유지 | AgentPlaza_UI_Design.pdf p.22, p.83, p.92 vs AgentPlaza_PRD.v2.pdf p.18, p.21 |

## 7. 디자인 요구

- **디자인 방향 / 레퍼런스**: 신뢰감 있는 B2B 운영 콘솔. 참조 구현(SeCMP·MAS)의 AppLayout 시각 언어를 디자인 토큰으로 일반화하고, 폐쇄망 전제로 웹폰트·CDN 을 로컬 번들로 둔다. 색은 의미 전달에만 쓰고 항상 텍스트를 함께 쓴다. 본문은 좌측 정렬하고(중앙 정렬 금지), 화면당 primary 버튼은 1개만 둔다. 상태 표현은 KRDS(디지털 정부서비스 UI/UX 가이드라인)와 Material 3 의 4상태(로딩·빈·오류·콘텐츠) 원칙을 따른다. (출처: AgentPlaza_UI_Design.pdf p.2, p.19, p.26, p.110)
- **디자인 토큰 (잠정 — 실제 값은 디자인 시스템 문서에서 확정)**: primary `#3F51E5`/다크 `#7C8CFF` · bg/card/border `#F6F7FB`/`#FFFFFF`/`#D9DCE5` · ok/warn/danger/muted `#2F9E44`/`#E8A317`/`#C92A2A`/`#868E96` · 신뢰 등급 배지 4종(official·partner·community·external, 색+텍스트) · radius 카드 12px/버튼·입력 6px/배지 999px · 폰트 Pretendard·Noto Sans KR(14/12/15/18/24px, 숫자는 tabular-nums) · 간격 4pt 그리드 · 테마 light/dark/system(프로필 저장, Addon 에 postMessage 로 전파). (출처: AgentPlaza_UI_Design.pdf p.19, p.26, p.110)
- **레이아웃·반응형**: 셸 = 좌측 네비 240px(접으면 64px) + 상단바 64px + 본문 최대 1152px. 그리드는 ≥1280px 4열, ≥1024px 3열, ≥768px 2열, <768px 1열(네비는 오버레이 드로어, 표는 카드형). 로그인(A01)·설치 위저드(A02)·워크플로 빌더(F02)만 전체화면. Addon 화면은 별도 오리진 iframe(N01)으로 띄우고 토스트·모달·네비는 코어가 소유한다. (출처: AgentPlaza_UI_Design.pdf p.19)
- **화면 규모**: 80개 화면, 14그룹(A 인증·설치 / B 메인 / C 어시스턴트 / D 에이전트 관리 / E 마켓 / F 워크플로 / G 지식(RAG) / H 플레이그라운드·평가 / I 거버넌스 / J LLM / K 조직 / L 설정 / M 관측 / N Addon 규약). 유형은 페이지 49·모달/위저드 18·탭 10·공통 규약 3이고, 우선순위는 P0 36·P1 39·P2 5. 화면 ID 는 `SCR-<그룹><2자리>` 형식이다. (출처: AgentPlaza_UI_Design.pdf p.1, p.6, p.9–12)
- **P0 핵심 화면 (36)**: 로그인·설치 위저드·비밀번호(A01·A02·A04) · 셸·대시보드(B01·B02) · 채팅·세션·스코프 채팅(C01·C02·C05) · 에이전트 목록·상세·스캐폴드·ZIP 업로드·설치 진행(8단계 SSE)·MCP 노출·추출·삭제 확인·원격 등록(D01~D06·D08·D10·D11) · 마켓 카탈로그·3축 브라우즈·자산 상세·도입 위저드·직접 설치·설치됨(E01~E05·E11) · 승인함(I04) · 모델 카탈로그·공급자 키·로컬 런타임·라우팅 폴백(J01~J04) · 사용자·API 키(K01·K04) · 시스템 설정·내 프로필(L01·L02) · 관측 대시보드·감사 원장(M01·M03) · iframe 마운트 규약·Addon 템플릿(N01·N02). (출처: AgentPlaza_UI_Design.pdf p.9–12)
- **핵심 컴포넌트**: 도구 호출 카드(CMP-16)·승인 카드(CMP-15)·리뷰 게이트 카드를 대화 안에 인라인 표시, 에이전트 카드(CMP-05), 진행·사용량 바(CMP-10: 85% 황색·95% 적색), 신뢰 배지, 스테퍼, ⌘K 커맨드 팔레트(B04), 토스트(최대 3개). Addon SDK `@agentplaza/ui` 는 Table·Form·Drawer·EmptyState·Skeleton·Badge·Toast·Modal·PageContainer 를 제공한다. `가정: CMP-01~16 전체 목록은 원문에 없어 디자인 시스템 확정 시 정의 필요` (출처: AgentPlaza_UI_Design.pdf p.19, p.26, p.29–30, p.101)
- **권한·상태 규칙**: 역할은 supervisor > admin > user 3단이고, 라우트 가드와 서버 403 으로 이중 차단한다. 권한 없는 동작은 숨기지 않고 비활성 + 툴팁으로 보이며, 페이지 단위로 권한이 없으면 403 화면을 띄운다. 상태는 ST-01~08(로딩: 300ms 이하면 미표시 후 스켈레톤 / 빈 / 오류: 재시도 + 5xx 는 추적 ID / 권한 없음 / 부분 실패 / 저하 / 대기 / 오프라인), 메시지는 MSG-001~020 으로 관리한다. (출처: AgentPlaza_UI_Design.pdf p.13, p.20, p.105)
- **접근성·i18n**: 원문 기준은 KRDS 를 통한 WCAG 2.1 AA 다. 모든 모달에 포커스 트랩과 Esc 닫기, 토스트는 `aria-live=polite`, 폼 오류 시 첫 오류 필드로 포커스 이동, iframe 은 `title` 필수, Addon 은 axe 검사 대상, 워크플로 빌더는 키보드 대체 편집 모드를 제공한다. 한국어 기본·영어 폴백이며, 화면에 i18n 키 노출을 금지하고(빌드 검사), 데이터 다국어는 `{ko,en}` 형식, IME 조합 중 Enter 는 무시한다. **결정(Q9)**: 목표 기준을 KWCAG 2.2 / WCAG 2.2 AA 로 상향 (출처: AgentPlaza_UI_Design.pdf p.20, p.22, p.64, p.100–101, p.105, p.109–110)

## 출처 문서 / Sources

| # | 문서 | 역할 | 반영 섹션 |
|---|------|------|-----------|
| 1 | `.docs/AgentPlaza_PRD.v2.pdf` (89쪽, v2 2026-09-18) | main | §1 개요, §2 문제·대상, §3 범위(FR·NFR·Out), §4 흐름·수용 기준, §5 지표, §6 리스크·의존성·Open Questions |
| 2 | `.docs/AgentPlaza_UI_Design.pdf` (110쪽, v1.0 2026-09-19, 80화면) | design | §4 흐름(화면 ID), §7 디자인 요구, §6 Open Questions(Q11~Q15) |

## 변경 이력 / Changelog

| 날짜 | 변경 | 근거 |
|------|------|------|
| 2026-10-06 | One-Page PRD 초안 v0.1 생성 | wds-prd · 입력 문서 2종 |
| 2026-10-06 | 구현 결정 반영: 범위 P0 Epic 1–11 · LLM 은 mock(시험)+호스트 Ollama(T3 브리지) · 게이트웨이 내장 라우터(Q1)·SDK 미고정(Q2) · Addon 빌드·기동은 전용 `runtime` 서비스만 docker.sock 보유(api·에이전트 컨테이너 금지, NFR-I3 유지) | wds-implement 0-3 확인 |
| 2026-10-07 | 구현 완료 반영: P0 Epic 1–11 DONE(BLOCKED 0) · 회귀 145·E2E 4·prod 리허설 PASS · Open Questions Q3–Q8·Q11–Q15 에 구현 가정 표기 · Addon 화면 오리진 분리(Traefik apps 진입점) · 에이전트별 격리 네트워크(egress 미선언 시 internal) · 경로 B OCI·사설 미러와 서명·SBOM·라이선스 게이트는 미구현(미검증 배지) · 채팅 UI 는 assistant-ui 대신 AG-UI 경량 컴포넌트 | wds-implement 완료 게이트 · `.docs/IMPLEMENT_PLAN.md` 가정 표 · `test/impl/final/result.md` |
| 2026-10-07 | 범위 확장(SCOPE): P1 25개를 Epic 12–18 로 이번 구현에 포함(P2 D3-07·D10-07 은 계속 제외) · 결정: LLM 관측 UI 는 자체 경량(스팬·비용 DB 저장, Opik/Langfuse 미도입) · 공급망 게이트 도구 cosign·syft·trivy(이미지 포함, 취약점 DB 는 볼륨) · 결제는 mock 어댑터 + Ed25519 라이선스 토큰(Q6) | wds-implement 0-3 확인(2차) |
| 2026-10-07 | 구현 완료 반영: P1 Epic 12–18 DONE(BLOCKED 0) · 회귀 250·P1 E2E 7·prod 리허설(마이그레이션 0012) PASS · 결제는 mock 어댑터(PAYMENT_ADAPTER, prod 기본 none)·라이선스 토큰 apl1(Ed25519, 좌석 = 사용자 수) · 레지스트리 API = MCP registry /v0.1 읽기 호환 · 업데이트 알림은 콘솔 배지 + 원장(알림 센터 미구현) · OIDC SSO 미포함 | wds-implement 완료 게이트 · `.docs/IMPLEMENT_PLAN.md` 가정 표 · `test/impl/18th/result.md` |
| 2026-10-07 | Open Questions 결정 반영(F·NF·SCOPE·DESIGN): Q1 Bifrost · Q2 pydantic-ai · Q3 전면 iframe · Q4 카탈로그/마켓 서버 이원화 P1 완료 · Q5 P0 43 · Q6 Lago/Polar/Stripe · Q7·Q12 조직·부서 단위 배치 + K02·FL-07 범위 In · Q8 initialize 계약 시험 · Q9 KWCAG 2.2/WCAG 2.2 AA · Q10 미결 · Q11 워크플로·플레이그라운드·가드레일 카탈로그 = Addon · Q13 화면 목록 ID · Q14 목록 권한 + 서버 403 · Q15 예산 80% 로컬 강제 라우팅 → 신규 요구는 P1 추가 범위(다음 이터레이션) | 사용자 답변(wds-prd 재실행, wds-living-doc) · README.md · README.en.md · COMPLIANCE.md · .docs/IMPLEMENT_PLAN.md |
| 2026-10-07 | 구현 방식 확정(3차 확인): Epic 순서 24→20→21→22→23 · Bifrost = compose 서비스 + 플랫폼 정책 계층 유지(공급자 호출만 경유) · 결제 = 호스티드 결제 + 서명 검증 웹훅(Stripe·Polar·Lago, 시험은 가짜 서버, 실 테스트 키 검증은 MANUAL) · 조직 = 기본 조직 + 그룹 + deploy_scope | wds-implement 0-3 확인 |
| 2026-10-07 | 구현 완료 반영: P1 추가 Epic 20–24 DONE(BLOCKED 0) · 회귀 272·콘솔 E2E P1 10·접근성 57화면 위반 0·prod 리허설(마이그레이션 0013) PASS · Bifrost v2.2.6(사설 IP 허용은 Ollama 만)·pydantic-ai 1.107(FunctionModel → 게이트웨이)·결제 호스티드 일회성(Stripe Checkout·Polar custom price·Lago add-on 인보이스, 실 테스트 키 결제는 MANUAL)·조직 배치는 노출 범위 통제(supervisor 예외, API 키는 키 범위) | wds-implement 완료 게이트 · `.docs/IMPLEMENT_PLAN.md` 가정 표 · `test/impl/19th`~`23rd` |
| 2026-10-07 | 범위 이동(SCOPE): P2 D10-07 알림·상태 + D3-07 채널·임베드(웹 위젯·Slack·Telegram·카카오)를 이번 구현에 포함 — 헬스·알림은 자체 경량(+ mailpit 오버레이), 채널 실 토큰은 사용자 입력·시험은 가짜 서버 | wds-implement 0-3 확인(4차) · README.md · .docs/IMPLEMENT_PLAN.md |
| 2026-10-07 | 구현 완료 반영: P2 Epic 19(D10-07)·25(D3-07) DONE — PRD 전 범위(P0·P1·P2) 구현 · 회귀 284·접근성 65화면 위반 0·prod 리허설(마이그레이션 0015) PASS · 채널 사용자 = 채널 주체(플랫폼 계정 아님, 유료 좌석은 채널 하나) · 카카오 동기 블록 5초 제한(긴 답은 콜백) · 실 메신저·실 결제 테스트 키 연결은 MANUAL | wds-implement 완료 게이트 · `test/impl/24th`·`25th` |
| 2026-10-07 | 문서 정리·회귀 재검증(5차 확인, 구현 없음): README 의 오래된 'P2 범위 밖'·'알림 센터 미구현' 문구 정리 · 가정으로 남은 갭 4건(OCI·사설 미러 설치, OIDC SSO, 메모리 LLM 자동 추출, 기본 에이전트 컨테이너 분리)을 다음 이터레이션 Epic 26–29(TODO)로 등록 | wds-implement 0-3 확인(5차) · README.md · README.en.md · .docs/IMPLEMENT_PLAN.md · `test/impl/26th` |
