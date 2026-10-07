                                                AgentPlaza
로컬·퍼블릭 LLM 겸용 멀티 에이전트 플랫폼 및 에이전트 마켓플레이스 PRD (v2)

       로컬 LLM 과 퍼블릭 AI 서비스를 하나의 게이트웨이로 쓰고, Orchestrator·AI Assistant 를 기본으로 제공하며,
frontend·backend·database 를 담은 Zip 에이전트를 마켓플레이스에서 골라 docker compose 로 독립 또는 연계 구동하는 멀
티 에이전트 플랫폼의 제품 요구사항 정의서. v2 에서 참조 프로젝트 11종을 분석해 독립 구동(Zip) Addon-Agent 후보군을
                                          업무·업종·도메인 3축으로 분류·배치한다.




                                              작성일 2026-09-18 (v2) · v1 2026-09-18
분석 원천: 인포그래픽 「20 AI GitHub Repos」 · GitHub 검색 Multi-ai Agent(300건) · WisemanLim 저장소·스타 교차 · v2: 참조 프로젝트 11종(SeCuardian
                                         4·MAS 3·DOPQ·HRAgent·SmartHaccp·Bonded) 소스 실독

                    실측: GitHub REST API 2026-09-18, 저장소 361개 라이선스·스타·커밋·릴리스 조회, LICENSE 판독 77건

      표준: MCP 2026-07-28 · A2A v1.0.1 · AG-UI 1.0 · ACP v1 · OTel GenAI semconv · Compose Spec(v5) · OWASP GenAI 2026 · 개인정보보호법
목차
1. 개요
 1.1 이 문서가 다루는 것 1.2 왜 항목 단위 에이전트인가 1.3 핵심 발견 1.4 문서 구성
2. 출처와 라이선스 표기
 2.1 원천 네 가지 2.2 실측 방법 2.3 표기 규칙 2.4 인용 원칙 2.5 선행 PRD 와의 경계
3. 원천 전수 분석
 3.1 인포그래픽 「20 AI GitHub Repos」 전수표 3.2 결합 방식 판정 근거
 3.3 GitHub 검색 「Multi-ai Agent」 상위 결과 3.4 v1 템플릿 3.5 v1 규격 전사
 3.6 요구사항 8개 → 도메인 추적표
4. 목표 시스템
 4.1 제품 정의 4.2 기본 에이전트 둘 4.3 운용 3모드 4.4 설계 원칙 4.5 사용자 흐름
5. 기능 요구사항
 5.1 읽는 법 5.2 FR-D1 LLM 공급 5.3 FR-D2 오케스트레이터 5.4 FR-D3 대화형 어시스턴트
 5.5 FR-D4 애드온 SDK·스캐폴드 5.6 FR-D5 패키지·레지스트리 5.7 FR-D6 마켓플레이스
 5.8 FR-D7 프로토콜 게이트웨이 5.9 FR-D8 런타임·컴포즈 5.10 FR-D9 신원·거버넌스 5.11 FR-D10 콘솔·관측
 5.12 FR-X 후순위·공백 5.13 FR-P 플랫폼 공유 서비스 5.14 사용자 스토리
6. 비기능 요구사항
 6.1 NFR-I 격리·독립 구동 6.2 NFR-L LLM 공급 6.3 NFR-P 프로토콜 적합성 6.4 NFR-S 보안
 6.5 NFR-U 사용성·즉시 사용 6.6 NFR-O 운영·관측·이식성 6.7 NFR-C 준법·라이선스
7. 아키텍처
 7.1 계층 7.2 LLM 공급 계층 7.3 디렉터리 7.4 에이전트 공통 골격 7.5 프로토콜 표면 7.6 실패와 강등
 7.7 배포 토폴로지
8. 에이전트 카탈로그
 8.1 카탈로그 읽는 법 8.2 AG-D1 LLM 공급 8.3 AG-D2 오케스트레이터 8.4 AG-D3 대화형 어시스턴트
 8.5 AG-D4 애드온 SDK·스캐폴드 8.6 AG-D5 패키지·레지스트리 8.7 AG-D6 마켓플레이스
 8.8 AG-D7 프로토콜 게이트웨이 8.9 AG-D8 런타임·컴포즈 8.10 AG-D9 신원·거버넌스 8.11 AG-D10 콘솔·관측
 8.12 AG-X 후순위 8.13 AG-P 플랫폼 공유 서비스 8.14 수량과 v1 대비
9. 기술 스택 — 실측 기반 선정
 9.1 결정 요약 9.2 D1 LLM 공급 9.3 D2 오케스트레이션 9.4 D3 어시스턴트
 9.5 D4·D5·D6 패키징·레지스트리·마켓 9.6 D7 프로토콜 9.7 D8 런타임·compose·운영 9.8 플랫폼형 참조
 9.9 아카이브·이전·정체 총람 9.10 라이선스 5등급 9.11 사용자 저장소 재사용
10. 독립 구동, 연계, 즉시 사용
 10.1 세 모드 계약 10.2 agent.yaml 규격 10.3 compose.yaml 규격 10.4 등록 8단계
 10.5 카탈로그 소스 다형 필드와 신뢰 등급 10.6 v1 → AgentPlaza 마이그레이션 10.7 프로파일
 10.8 누락 검증 CI
11. 표준 프로토콜 — 현행 사양 실측과 반영
 11.1 요약 11.2 MCP 2026-07-28 변경 요지와 대응 11.3 MCP SDK·레지스트리·게이트웨이 실측
 11.4 A2A v1.0.1 핵심 모델과 대응 11.5 그 밖의 표준 11.6 프로토콜 비교와 경쟁 관계
 11.7 Orchestrator 의 MCP·A2A 결정 규칙 11.8 외부 에이전트 등록 게이트 11.9 미확인 항목
12. 데이터 모델과 API
 12.1 플랫폼 스키마 12.2 Addon DB 격리 3방식 12.3 플랫폼 REST 12.4 에이전트 표면
 12.5 AG-UI 이벤트 매핑 12.6 관측 속성
13. 보안, 법적, 윤리
 13.1 위협 모델 13.2 신뢰 등급과 격리 연동 13.3 오픈소스 라이선스 13.4 개인정보·데이터 13.5 마켓·상거래
 13.6 윤리·오용 13.7 알려진 실패 모드
14. 원천 검증 — 인포그래픽·검색·v1 의 주장 검토
 14.1 인포그래픽 20 저장소 검증 14.2 GitHub 검색 결과 검증 14.3 v1 템플릿 주장 검증
 14.4 표준 사양 가정 검증 14.5 누락 검증
15. 지표, 로드맵, 리스크
 15.1 성공 지표 15.2 단계 15.3 리스크 15.4 다음 결정
16. 참조 프로젝트 분석 (v2)
 16.1 참조 프로젝트 11종 16.2 세 갈래 계열 16.3 인벤토리 방법 16.4 마켓플레이스 설계 준용 16.5 배치 토폴로지
17. Addon-Agent 후보 카탈로그 — 분류 체계 (v2)
 17.1 분류 축 1 17.2 분류 축 2 17.3 분류 축 3 17.4 카테고리 slug 체계 17.5 독립 구동
 17.6 후보 수량과 도메인 분포 17.7 업종별 스타터 팩
18. 카테고리별 세부 Agent 배치 (v2)
 18.1 읽는 법 18.2 공통 18.3 플랫폼 18.4 보안 18.5 LLMOps 18.6 거버넌스·준법 18.7 인사
 18.8 제조 18.9 식품안전 18.10 물류·통관 18.11 문서지능 18.12 종합 18.99 후보 도출 원칙과 한계
부록 A. 용어
부록 B. 출처 총람
 B.1 원천·검색·사용자 B.2 표준 사양 B.3 법령·프레임워크 B.4 선행 내부 문서 B.5 실측 저장소 전수
부록 C. 사용자 즐겨찾기 교차
부록 D. 이미지·그림 출처
부록 E. 한계
부록 F. v1 → v2 변경 이력
부록 G. 참조 프로젝트 출처
1. 개요

1.1 이 문서가 다루는 것
이 문서는 여러 AI 에이전트를 한 플랫폼에서 등록·구동·연계하는 제품의 요구사항이다. 사용자가 제시한 여덟 요구는 다음과 같다.
(1) 로컬 LLM 지원, (2) 퍼블릭 AI 서비스(ChatGPT·Claude Code 등) LLM 지원, (3) 기본 에이전트로 Orchestrator 와 대화형 AI Assistant 제공,
(4) Addon 에이전트용 템플릿(Scaffold)과 Zip 업로드, (5) Zip 은 frontend·backend·database·meta 로 구성, (6) Zip 구매 또는 마켓플레이스
(다운로드/설치·직접설치·연동/연계)로 획득, (7) MCP·A2A 표준 프로토콜 연계, (8) 각 에이전트는 docker compose 로 독립 구동.
목표 시스템 이름은 AgentPlaza 이다. 광장(Plaza)은 에이전트가 모이고 거래되는 곳이다. 여덟 요구를 10개 영역·70개 항목으로 분해
했고, 항목 하나하나가 홀로 기동하는 에이전트다. 플랫폼은 조립·발견·정책 수단이지 실행 전제가 아니다.
사용자가 첨부했다고 언급한 인포그래픽 파일은 본 세션에 전달되지 않았다. 대신 작업 디렉터리의 요약 보고서 Summary-
Repos(2026-09-15)가 정리한 「20 AI GitHub Repos」 20개 저장소 목록·분류·라이선스를 전사 원천으로 삼았고(3.1), 20개 모두
AgentPlaza 의 결합 방식(기본 엔진·Addon·연계·참고·제외)을 부여했다(그림 9).

1.2 왜 항목 단위 에이전트인가
     라이선스가 갈린다. 20개 중 그대로 내장할 수 있는 것은 6개다. n8n(Sustainable Use)·Dify(멀티테넌트 금지)·AutoGPT
      platform(Polyform Shield)·Open WebUI(브랜딩 조항)·ComfyUI(GPL)는 한 프로세스에 넣을 수 없다. 컨테이너 경계가 라이선스 경계
      다.
     공급자가 바뀐다. 로컬 Ollama 와 퍼블릭 Claude 를 같은 코드로 부르려면 에이전트가 공급자를 몰라야 한다. 게이트웨이 별칭
      하나만 안다.
     임의 코드를 받는다. Zip 업로드는 곧 코드 실행이다. v1 은 플랫폼 프로세스 안에서 importlib 로 실행했다. AgentPlaza 는 컨테이
      너 격리를 기본으로 바꾼다.
     부분 도입이 현실이다. 게시판 에이전트 하나만 고객사에 납품해야 한다. agent.zip 하나가 compose 로 혼자 뜬다(M1).
     표준이 있다. MCP 는 도구 계약, A2A 는 에이전트 계약, AG-UI 는 화면 계약이다. 네 문을 agent.yaml 하나에서 생성하면 손코딩 불
      일치가 사라진다.

1.3 핵심 발견
    1. v1 이 이미 있다. 사용자 저장소 WisemanLim/pub-MultiAIAgent-Template · 1★ 는 Orchestrator·Assistant·flat zip 핫 디플로이·per-
       agent MCP·A2A·standalone compose export·오프라인 실행을 갖춘 본 요구의 v1 구현이다(F1~F32). 빠진 것은 서명·권한 선언·격
       리·마켓플레이스·상거래 다섯 가지다. 본 PRD 는 v1 을 대체하지 않고 승계·확장한다(3.4).
    2. MCP 는 고정 사양이 아니다. 현행 사양은 2026-07-28 이며 세션·initialize 핸드셰이크를 없앤 무상태 재설계다(server/discover 필
       수, Tasks 확장 분리, MRTR, Roots·Sampling·Logging 폐기 예고). v1 의 MCP 프록시와 A2A 라우터(v0.x 스타일)는 둘 다 현행과 어
       긋난다. A2A 는 v1.0.1(a2a.proto 정본, Agent Card JWS 서명, LF 산하)이다(11장).
    3. Anthropic Messages API 가 로컬 런타임의 제2 표준이 되었다. ollama/ollama * · 181,183★, ggml-org/llama.cpp * · 128,619★,
       vllm-project/vllm * · 92,055★, sgl-project/sglang * · 36,116★ 등 9개 런타임이 /v1/messages 를 네이티브로 제공한다. 동기는
       Claude Code 를 로컬 모델에 붙이기 위해서다. 요구 (1)(2)는 'OpenAI 호환을 내부 표준, Anthropic 병행'으로 한 게이트웨이에서
       풀린다(9.2).
    4. 라이선스 함정 6건. langchain-ai/langgraph * · 41,863★ 저장소는 MIT 이지만 서버 런타임 langgraph-api 는 Elastic-2.0(관리형 제공
       금지) → 라이브러리만 사용. BerriAI/litellm * · 59,036★ 은 enterprise/ 프로덕션 사용 유료. redis/redis · 76,398★ 8 은 3중 라이선
       스 → Valkey. open-webui/open-webui * · 152,425★ 는 브랜딩 변경 시 50 사용자 상한. microsoft/autogen * · 61,035★ 은 유지보
       수 모드 + CC-BY-4.0. daytonaio/daytona * · 71,721★ 는 2026-06 유지보수 중단 + AGPL.
 5. 마켓 서버 오픈소스 선례는 둘. openclaw/clawhub · 9,422★(MIT — Claw 패키지 = 에이전트 한 개 전체, SHA-256 사전 제시, 발행 거
      부 10사유)와 modelcontextprotocol/registry · 7,260★(server.json 에 oci·mcpb 가 1급). Claude Code 마켓은 git + marketplace.json
      정적 카탈로그라 서버가 필요 없다. 무료·사내는 정적, 유료만 API 서버로 이원화한다(D6).
 6. 아카이브·이전 다수. tensorzero/tensorzero * · 11,720★(2026-06)·FlowiseAI/Flowise * · 55,467★(2026-08-13)·huggingface/text-
      generation-inference · 10,886★·containrrr/watchtower · 24,650★ 아카이브. 경로 이전 23건(comfyanonymous→Comfy-Org,
      anthropics/mcpb→modelcontextprotocol, zed-industries→agentclientprotocol, sst/opencode→anomalyco, awslabs/agent-
      squad→2FastLabs 등). 9.9 총람.
 7. compose 는 v5 다. docker/compose · 38,178★ 릴리스 v5.5.1 (2026-09-03). v5.0.0 은 Compose 를 SDK 로 공식 개방하고
      models·provider 요소를 갖는다. include 는 이름 충돌 시 병합하지 않고 경고만 하므로 서비스·네트워크·볼륨에 에이전트 접두
      어를 강제한다. v1 의 network_mode:host·docker.sock 마운트는 폐기한다(10.3).
 8. 검색 결과는 플랫폼 후보를 주지 않는다. 「Multi-ai Agent」 2,256건 상위는 튜토리얼과 'CLI 에이전트 여러 개 묶기' 도구다. 후자에
      서 'CLI 에이전트를 LLM 백엔드로 정식화'(D1-04)라는 설계 신호를 얻었다.

1.4 문서 구성
 장       제목                          내용
 1       개요                          여덟 요구, 항목 에이전트 근거, 핵심 발견 8

 2       출처와 라이선스 표기                 네 원천, 실측 방법, 표기 규칙, 선행 PRD 경계

 3       원천 전수 분석                    인포그래픽 20 전수·결합 방식, 검색 14, v1 승계표 18, 요구→도메인 추적

 4       목표 시스템                      제품 정의, 기본 에이전트 둘, 운용 3모드, 설계 원칙 DP1~10, 사용자 흐름 7

 5       기능 요구사항                     FR-D 70 + FR-X 12 + FR-P 12, 사용자 스토리 8

 6       비기능 요구사항                    격리·독립(최상위)·LLM·프로토콜·보안·사용성·운영·준법

 7       아키텍처                        9계층, LLM 계층, 디렉터리, agent.zip 골격, 프로토콜 표면, 강등, 토폴로지

 8       에이전트 카탈로그                   70+12+12 종, 우선순위 수량

 9       기술 스택                       실측 저장소 기반 선정, 결정 요약 35행, 영역별 표, 아카이브·이전 총람, 라이선스 5등급, 사용자 저장소 재사용

 10      독립·연계·즉시 사용                 세 모드 계약, agent.yaml 전문, compose 전문, 등록 8단계, 프로파일 6, 누락 CI

 11      표준 프로토콜                     MCP 2026-07-28·A2A v1.0.1·ACP·AG-UI·OTel 실측과 반영, 결정 규칙, 등록 게이트

 12      데이터 모델·API                  플랫폼 스키마, DB 격리 3방식, REST, 에이전트 표면, AG-UI 매핑, 관측 속성

 13      보안·법적·윤리                    위협 모델, 신뢰 등급×격리, 라이선스 결정, 개인정보, 상거래, 실패 모드

 14      원천 검증                       인포그래픽 20·검색·v1·표준 가정 판정, 누락 검증

 15      지표·로드맵·리스크                  성공 지표 10, 단계 S0~S8, 리스크 14, 다음 결정 6

 16      참조 프로젝트 분석 (v2)             로컬 11종(SeCuardian 4·MAS 3·DOPQ·HRAgent·SmartHaccp·Bonded) 인벤토리, 마켓 설계 준용

 17      Addon-Agent 후보 카탈로그 (v2)    업무·업종·도메인 3축 분류, 토폴로지, agent.zip 독립 구동 규격, 후보 수량

 18      카테고리별 세부 Agent 배치 (v2)      도메인별 후보 전수표(공통·보안·LLMOps·거버넌스·HR·제조·식품안전·물류통관·문서·플랫폼)
 부록      A~F                         용어, 출처 총람·실측 전수, 스타 교차, 그림 출처, 한계, v1→v2 변경 이력




v2 요지. v1(1~15장·부록 A~E)은 그대로 두고, 16~18장과 부록 F 를 추가했다. 사용자 로컬 참조 프로젝트 11종을 소스 수준으로 분
석해 독립 구동(Zip) 가능한 Addon-Agent 후보군을 도출하고, 업무·업종·도메인 3축으로 분류해 배치했다. 이전 산출물은 old/ 로 이동
했다(부록 F).
2. 출처와 라이선스 표기

2.1 원천 네 가지
    구분                  원천                                                                 본 문서에서의 위치              확인 상태
    ① 인포그래픽             「20 AI GitHub Repos」 — 20개 오픈소스 카드형 이미지. 사용자                       3.1 전수표, 그림 9, 14장 검증   원 게시자·URL 미확인. 이미지 파일은 본 세션에 첨부되
                        가 이전 세션에 제시, 요약 보고서 Summary-Repos(2026-09-15)                                              지 않아 요약 보고서의 20개 목록·분류·라이선스를 전사
                        로 정리됨                                                                                      원천으로 삼았다
    ② GitHub 검색         https://github.com/search?q=Multi-ai+Agent&type=repositories —     3.2 검색 분석               실측(stars·license·pushed_at)
                        2026-09-18 REST API 로 300건 수집, 상위 60건 판독
    ③ 사용자 저장소           https://github.com/WisemanLim?tab=repositories — 47개. 핵심은          3.3 v1 승계표, 7·8·10장     트리·README·PRD.md·소스 실독
                        pub-MultiAIAgent-Template(v1), pub-wsa-for-sdd, pub-Server-Init,
                        pub-SSL-Cert-Manager, pub-wise-dev-std
    ④ 사용자 스타            https://github.com/WisemanLim?tab=stars — 5,764건 스냅숏               본문 * 표기, 부록 C           실측 교차
                        (stars_all.tsv, 2026-09-18)




2.2 실측 방법
본문의 저장소 수치는 사람이 옮겨 적지 않고 repos.tsv 에서 렌더된다. 2026-09-18 GitHub REST API 로 저장소마다 세 번 조회했다.
gh api repos/{owner}/{repo}                                            # stargazers_count, license.spdx_id, archived, default_branch,
full_name(리다이렉트 감지)
gh api repos/{r}/commits/{default_branch}                                       # 기본 브랜치 최신 커밋 일자
gh api repos/{r}/releases/latest                                                # 최신 릴리스 태그
gh api repos/{r}/license | base64 -d                                            # spdx_id 가 NOASSERTION/NONE 이면 LICENSE 첫 줄 판독 →
LIC_FIX



요청 경로와 응답 full_name 이 다르면 이전(리다이렉트) 으로 표기한다. 이번 실측에서 comfyanonymous/ComfyUI →
Comfy-Org/ComfyUI, anthropics/mcpb → modelcontextprotocol/mcpb, casbin/casbin → apache/casbin, microsandbox/microsandbox →
superradcompany/microsandbox 가 이전이었다. containrrr/watchtower 는 archived=true 다.

2.3 표기 규칙
    표기                                                   뜻
    owner/repo * · 1,234★ · MIT                          저장소 · 사용자 스타 목록 포함(*) · 스타 수 · 라이선스. 모두 repos.tsv 값
    [아카이브]                                               GitHub archived=true. 신규 채택 금지, 대체 명시
    [미확인]                                                1차 출처에서 확인하지 못함. 추정 금지
    G1~G5                                                라이선스 등급(9.7). 빌드 게이트가 강제
    E/A/L/R/X                                            결합 방식: 기본 엔진 / Addon 컨테이너 / 연계만 / 패턴 참고 / 제외·대체
    v1                                                   사용자 저장소 pub-MultiAIAgent-Template(2026-07-30 최신 커밋) 의 구현




2.4 인용 원칙
        코드 비복제. G4(AGPL·SSPL·BUSL·Sustainable Use·Polyform·Open WebUI License·Dify 추가조건) 저장소는 아키텍처·규격만 참고하고
         코드를 가져오지 않는다.
        이미지 비복제. 인포그래픽 원본을 문서에 삽입하지 않는다. 그림 1~9는 본 문서가 자체 재구성한 도식이다(부록 D).
        출처 명시. 표준 사양(MCP·A2A·Compose Spec·OTel)은 저장소 경로와 버전·날짜를 11장과 부록 B 에 적는다.
        파생 표기. v1 F26 규칙을 그대로 따라, 마켓에서 파생된 에이전트의 agent.yaml 에는 base 출처와 라이선스가 자동 기록된다.
        양식. 문서 양식은 기존 내부 PRD 를 따랐으며 그 내용은 출처가 아니다.
2.5 선행 PRD 와의 경계
선행 PRD                       다루는 것                                본 문서와의 관계

AgentNexus (2026-09-16)      MCP + AI Gateway + A2A 통합 에이전트 플랫폼   프로토콜·게이트웨이 스택 조사를 재사용. 본 문서는 마켓·Zip·compose 독립 구동
                                                                  을 추가
AgentStackHub (2026-09-15)   20종 에이전트 스택 레퍼런스                     스택 조합표 참고. 본 문서는 제품(플랫폼) 요구를 정의
AegisMesh / AgentSentry      에이전트 보안 위험·통제                        13장 보안은 요지만. 상세 통제는 해당 문서
LLMForge (2026-09-17)        파인튠·가드레일 앱 빌더                        X08 파인튠은 LLMForge 로 위임
3. 원천 전수 분석
네 원천을 항목 단위로 전사하고, 각 항목이 AgentPlaza 의 어느 에이전트(도메인·ID)로 귀속되는지 추적한다. 누락 검증은 14장.

3.1 인포그래픽 「20 AI GitHub Repos」 전수표
요약 보고서 Summary-Repos 의 20행을 순서 그대로 전사했다. 실측 열은 2026-09-18 값이다.
#    이름                       저장소 실측 (★ · 라이선스)                                                        분류(원문 요약)                 결합                AgentPlaza 귀속

1    OpenClaw                 openclaw/openclaw * · 390,029★ · MIT (OpenClaw Foundation)               개인 AI 어시스턴트 / 에이전트 게이트웨   R + D1-04 백엔      D3-07, D1-04, D6
                                                                                                       이                         드 후보
2    Langflow                 langflow-ai/langflow * · 154,959★ · MIT                                  비주얼 에이전트/워크플로 빌더          A                 X01

3    TensorFlow               tensorflow/tensorflow · 200,160★ · Apache-2.0                            딥러닝 프레임워크                 A(선택)             X08

4    Transformers             huggingface/transformers * · 166,261★ · Apache-2.0                       사전학습 모델 정의 프레임워크          E(D1-02 대체) / A   D1-02, D1-07, X08

5    AutoGPT                  Significant-Gravitas/AutoGPT * · 187,421★ · Polyform Shield              자율 에이전트 플랫폼               R/L               D2, D6
                              (autogpt_platform/) + MIT (그 외)

6    CrewAI                   crewAIInc/crewAI * · 58,715★ · MIT                                       멀티에이전트 프레임워크              E(선택)             D2-03

7    n8n                      n8n-io/n8n * · 205,085★ · Sustainable Use License (.ee 파일은 Enterprise)   워크플로 자동화 / AI 에이전트 플랫폼    L                 X04

8    ComfyUI                  Comfy-Org/ComfyUI * · 133,706★ · GPL-3.0                                 생성형 AI 노드 그래프 엔진          A(격리)             X02

9    Ollama                   ollama/ollama * · 181,183★ · MIT                                         로컬 LLM 실행 런타임             E                 D1-01

10   Whisper                  openai/whisper · 109,302★ · MIT                                          음성 인식 모델(ASR)             A                 D3-04, X03

11   Stable Diffusion WebUI   AUTOMATIC1111/stable-diffusion-webui * · 164,996★ · AGPL-3.0             이미지 생성 웹 UI               X                 X02 대체

12   llama.cpp                ggml-org/llama.cpp * · 128,619★ · MIT                                    LLM/VLM 추론 엔진             E                 D1-02

13   RAGFlow                  infiniflow/ragflow * · 90,911★ · Apache-2.0                              RAG 엔진 + 에이전트 플랫폼         A/L               X07, D3-06

14   LangChain                langchain-ai/langchain * · 146,562★ · MIT                                LLM 앱 / 에이전트 프레임워크        E                 D2-03, D2-04

15   Claude Code              anthropics/claude-code * · 145,936★ · Anthropic Commercial Terms         터미널 에이전트 코딩 도구            D1-04 백엔드 / R     D1-04, D6
                              (LICENSE.md, 소스 비공개)

16   PyTorch                  pytorch/pytorch · 103,076★ · BSD-3-Clause (LICENSE 파일 판독)                딥러닝 프레임워크                 E(간접)             D1-02, X08

17   Dify                     langgenius/dify * · 156,215★ · Apache-2.0 변형 (멀티테넌트·로고 제거                LLM 앱 개발 플랫폼              R/L               D5, D6
                              금지 추가 조건)

18   DeepSeek-V3              deepseek-ai/DeepSeek-V3 * · 104,464★ · MIT                               오픈 가중치 LLM(MoE)           모델                D1-06

19   Gemini CLI               google-gemini/gemini-cli * · 107,051★ · Apache-2.0                       터미널 AI 에이전트               D1-04 백엔드         D1-04, D7-06

20   Open WebUI               open-webui/open-webui * · 152,425★ · Open WebUI License (BSD-3 기반        셀프호스팅 AI 채팅 플랫폼           R/L               D3, D5
                              + 브랜딩 조건)
                                                     그림 9. 인포그래픽 20 저장소의 결합 방식 (자체 재구성)


3.2 결합 방식 판정 근거
이름                       AgentPlaza 에서의 역할                                                             판정 근거

OpenClaw                 메신저 채널 어댑터·스킬(ClawHub) 마켓 선례·개인 비서 UX                                         규격·UX 선례. 코드 비복제

Langflow                 비주얼 플로우 빌더 Addon(MIT). 플로우를 Addon Agent 로 내보내기                                독립 컨테이너로 격리해 API 만 호출. GPL 또는 대형 의존성

TensorFlow               ML Agent 템플릿의 학습·추론 백엔드(선택). 서빙은 TF Serving 컨테이너                              독립 컨테이너로 격리해 API 만 호출. GPL 또는 대형 의존성

Transformers             로컬 모델 적재·서빙(transformers serve)·임베딩·파인튠 파이프라인                                 허용 라이선스 + 핵심 계층. 기본 스택에 내장

AutoGPT                  블록 기반 자율 에이전트 패턴·마켓 UX 참고. platform 은 Polyform Shield → 내장 금지                 규격·UX 선례. 코드 비복제

CrewAI                   역할 기반 크루(Orchestrator 실행 패턴 엔진 후보 2)                                          허용 라이선스 + 핵심 계층. 기본 스택에 내장

n8n                      외부 자동화 연계(웹훅·MCP 노드). Sustainable Use → 내장·재판매 금지, 연계만                        라이선스 추가 조건(재판매·멀티테넌트·브랜딩) → M2 연계만

ComfyUI                  이미지·비디오 생성 Addon. GPL-3.0 → 별 컨테이너, API 호출만                                   독립 컨테이너로 격리해 API 만 호출. GPL 또는 대형 의존성

Ollama                   로컬 LLM 1순위 런타임. OpenAI·Anthropic 호환 API, 모델 pull·keep-alive                   허용 라이선스 + 핵심 계층. 기본 스택에 내장

Whisper                  음성 입력 Addon(faster-whisper 서빙). 어시스턴트 STT                                     독립 컨테이너로 격리해 API 만 호출. GPL 또는 대형 의존성

Stable Diffusion WebUI   2024-07 이후 커밋 없음. ComfyUI 로 대체. AGPL                                          정체·대체 존재

llama.cpp                llama-server(OpenAI 호환) 로컬 엔진 2. GGUF. Ollama 의 기반                            허용 라이선스 + 핵심 계층. 기본 스택에 내장

RAGFlow                  문서 이해 RAG 엔진 연계(Apache-2.0). RAG Addon 의 상위 엔진 선택지                            독립 컨테이너로 격리해 API 만 호출. GPL 또는 대형 의존성

LangChain                도구·로더·모델 어댑터 라이브러리. Orchestrator 그래프 엔진은 LangGraph                            허용 라이선스 + 핵심 계층. 기본 스택에 내장

Claude Code              Public AI 코딩 에이전트 백엔드(헤드리스 -p, Agent SDK). 플러그인 마켓(marketplace.json) 규        코드가 아니라 모델. 카탈로그 항목
                         격 선례
PyTorch                  vLLM·Transformers 의 기반. 직접 노출 없음                                              허용 라이선스 + 핵심 계층. 기본 스택에 내장

Dify                     플러그인 규격(.difypkg manifest·마켓) 선례. 라이선스 추가 조건(멀티테넌트·로고) → 연계만                  규격·UX 선례. 코드 비복제

DeepSeek-V3              오픈 가중치 모델 후보(로컬 vLLM 서빙 또는 퍼블릭 API). 가중치는 Model License                       코드가 아니라 모델. 카탈로그 항목

Gemini CLI               Public AI 코딩 에이전트 백엔드(Apache-2.0, 헤드리스·ACP). 확장(gemini-extension.json) 규격 선   코드가 아니라 모델. 카탈로그 항목
                         례
Open WebUI               어시스턴트 UI 기능 기준선·Pipelines/Functions 규격 선례. 브랜딩 조건 → 코드 내장 대신 자                규격·UX 선례. 코드 비복제
                         체 UI
핵심 결론. 20개 중 그대로 내장(E)할 수 있는 것은 Ollama·llama.cpp·Transformers·CrewAI·LangChain·PyTorch(간접) 6개다. 플랫폼형 5개
(AutoGPT platform·n8n·Dify·Open WebUI·OpenClaw 중 OpenClaw 는 MIT 라 예외)는 라이선스 추가 조건 때문에 연계 또는 규격 참고에
머문다. 이 판정이 곧 '에이전트를 독립 컨테이너로 쪼개고 표준 프로토콜로 잇는다'는 본 문서 아키텍처의 첫 근거다.

3.3 GitHub 검색 「Multi-ai Agent」 상위 결과
2026-09-18 REST API 로 300건을 스타순 수집했다. 1위 metaskills/experts 가 1,064★, 10위권 아래는 100★ 미만이다. 상위 60건 중 절
반 이상이 강의 노트북(crewAI·LangGraph 튜토리얼) 이며 LICENSE 가 없는 저장소가 다수다. 생산 스택은 검색이 아니라 사용자 스타
목록과 표준 사양에서 나온다.
 저장소 실측                                                                  요지                                                             판정
 metaskills/experts · 1,064★ · MIT                                       OpenAI Assistants 를 도구로 연결하는 멀티 에이전트 JS 라이브러리                  패턴 참고. 2024-09 정체, OpenAI 종속

 mco-org/squad · 816★ · MIT                                              터미널에서 여러 AI CLI 에이전트를 협업시키는 Rust 도구                            D1-04 CLI 백엔드 협업 패턴 참고

 FerroxLabs/ijfw · 210★ · MIT                                            로컬 우선 AI 코딩 에이전트 인프라(공유 메모리·라우팅·교차 감사)                         로컬 우선 라우팅 참고

 vishalmysore/Tools4AI · 190★ · MIT                                      Java 에이전트 프레임워크(Gemini·OpenAI·LocalAI·Anthropic)               Java 생태계 참고

 GalaxyLLMCI/lyraios · 137★ · Apache-2.0                                 멀티 AI 에이전트용 MCP 운영체제 개념                                        개념 참고. 2025-03 정체

 feiyun0112/AgentBridge · 28★ · LICENSE 파일 없음                            Claude·Codex·Gemini·Cursor 등 여러 에이전트에 채팅하는 브리지(C#)             D1-04 브리지 패턴 참고

 agent-tools-org/ai-dispatch · 12★ · MIT                                 gemini·codex·opencode·cursor 에 작업을 분배하는 Rust CLI 팀 오케스트레       D1-04·D2 참고
                                                                         이터
 dankefox/multi-ai-collaboration · 20★ · AGPL-3.0                        Claude·Codex·Gemini 협업 채널 아키텍처 문서                              AGPL-3.0. 개념만

 kaymen99/langgraph-email-automation · 274★ · NONE                       LangGraph 고객지원 이메일 자동화                                         튜토리얼. 라이선스 없음
 (LICENSE 확인 필요)

 AIAnytime/Multi-Agents-System-from-Scratch · 72★ · MIT                  프레임워크 없는 순수 파이썬 멀티 에이전트                                        교육용

 ksm26/Multi-AI-Agent-Systems-with-crewAI · 168★ · NONE                  DeepLearning.AI crewAI 강의 노트북                                  교육용. 라이선스 없음
 (LICENSE 확인 필요)

 lainXXX/multi-ai-chat-skill · 37★ · MIT                                 6개 웹 AI 를 병렬 질의·교차검증하는 스킬                                      교차검증 패턴 참고

 snowdreamtech/template · 15★ · MIT                                      멀티 AI IDE 협업용 저장소 템플릿(AGENTS.md 단일 진실)                         D4 개발 표준 참고

 pnganga813-commits/Aether-desktop-orchestrator · 85★ ·                  멀티 AI 데스크톱 자동화 플랫폼(HTML)                                       라이선스 없음. 제외
 NONE (LICENSE 확인 필요)




검색이 준 설계 신호 세 가지. (1) squad·ai-dispatch·AgentBridge·ijfw·multi-ai-collaboration 은 모두 'Claude Code·Codex·Gemini CLI 를 여러
개 묶어 협업'시키는 도구다 → AgentPlaza 는 CLI 에이전트를 LLM 백엔드의 한 종류(D1-04)로 정식화한다. (2) lyraios 는 'MCP 를 에이
전트 OS 로' 보는 관점 → D7 프로토콜 게이트웨이. (3) snowdreamtech/template 은 AGENTS.md 단일 진실 원칙 → D4 개발 표준(사용자
wise-dev-std 와 동일 방향).

3.4 v1 템플릿(pub-MultiAIAgent-Template) 승계표
사용자 본인 저장소 WisemanLim/pub-MultiAIAgent-Template · 1★ 는 본 요구사항의 v1 구현이다. FastAPI + React 19 +
SQLite/PostgreSQL + Claude/Ollama, Orchestrator + Addon Agent flat zip 핫 디플로이, per-agent MCP, A2A v1.0 엔드포인트, Standalone
compose export 를 이미 갖췄다. PRD.md(2026-07-04 갱신) 의 F1~F32 를 전사하고 AgentPlaza 에서의 처리를 적는다.
 v1 기능                                     요지                                                                   AgentPlaza 처리                            대상 ID

 F1 Orchestrator                           의도 분류→라우팅→합성, Claude 도구호출 + Ollama 폴백                                승계·확장(그래프 엔진, 다중 백엔드)                    D2-01~04, D1-04

 F3 Ollama 폴백                              Claude 장애 시 Ollama /api/chat 텍스트 전환                                  승계·일반화(게이트웨이 라우팅·폴백 정책)                  D1-05, D1-06

 F4 Addon ZIP 핫 디플로이                       {Name}-app.py/-front.tsx/-sql.sql/-meta.json flat zip, importlib 로   승계(v1 호환 모드) + 컨테이너 모드 추가                D5-01, D5-05
                                           드
 F7 SSE 스트리밍 채팅                            POST /api/agent/chat/stream                                          승계·AG-UI 이벤트로 표준화                        D3-01, D7-06

 F8 Agent 활성화 설정                           tbl_agent_config 토글·모델·프롬프트·설명                                       승계                                       D10-01

 F12 Per-agent MCP 프록시                     에이전트별 MCP 서버, 포트 20000–59999 자동 할당                                   승계·경로 기반 라우팅으로 개선(포트 노출 0)               D7-01, D8-03

 F12 A2A v1.0 엔드포인트                        /.well-known/agent-card.json, /a2a/tasks, SSE                        승계·사양 현행 검증(3장·11장)                      D7-03

 F22 Agent 카탈로그 9유형                        app/service/rag/tool-proxy/reviewer/execution/hitl/memory/           승계                                       D4-01
                                           federation

 F23 Capability 인덱스                        tbl_addon_agent_capabilities verb/domain                             승계·레지스트리 라우팅 정식화                         D2-02, D5-06
 F25 Reviewer·HITL 게이트               옵트인 registry_dynamic_routing, reviewer_gate, hitl_gate          승계·기본 켜짐 정책 선택                                                 D2-05, D2-06

 F26 파생 export                       새 이름 zip 추출, base_agent 출처 자동 명시                                승계                                                             D4-07

 F27 Standalone 번들                   Dockerfile·compose·.env 자동생성, docker save                       승계·agent.zip 규격의 compose 포함으로 통합                               D4-07, D8-01

 F28 오프라인 실행                         uv --no-sync, preflight 비차단, 폴백                                 승계                                                             D8-07

 F29 Orchestrator·Assistant MCP      general/chat 를 MCP 도구로, x-api-key→서비스 JWT                       승계                                                             D7-01, D9-03

 F30 Ollama 실행옵션                     compose ollama 서비스 cpu/gpu/mlx, preflight                       승계·LLM Provider Agent 로 분리                                     D1-01, D8-05

 F31 사용자 관리                          상태 토글·임시 비밀번호·하위권한 규칙                                           승계                                                             D9-02, D10-01

 F32 설명 다국어                          description_en 폴백                                               승계·전 메타 필드 다국어                                                 D4-04

 Out of Scope(v1)                    SSO, 멀티테넌시, 마켓플레이스                                              본 PRD 에서 SSO·마켓플레이스를 범위 안으로. 멀티테넌                              D9-01, D6, X09
                                                                                                     시는 X09




3.5 v1 규격 전사 — flat zip 과 meta.json
v1 의 zip 은 서브디렉터리 없이 네 파일이다. 본 문서의 agent.zip(10.2)은 이를 상위 호환한다.
{Name}.zip
├── {Name}-app.py      # FastAPI `router` export → /api/addon/{agent_key}/…
├── {Name}-front.tsx   # React 컴포넌트 (선택) → front/src/pages/addon/deployed/{key}.tsx
├── {Name}-sql.sql     # CREATE TABLE IF NOT EXISTS (선택, PG→SQLite 자동 변환)
└── {Name}-meta.json   # agent_type(9
종)·version·display_name·description(_en)·capabilities[]·governance·required_env·min_platform_version


 meta.json 필드                            v1 뜻                                                                    agent.yaml(10.2) 대응

 agent_type                              app·service·rag·tool-proxy·reviewer·execution·hitl·memory·federation    spec.type (동일 9종 유지)

 capabilities[].verb/domain              Orchestrator 라우팅 키 ({category}.{subdomain})                             spec.capabilities[] (+ input/output schema, qos)

 governance.*                            data_classification, human_approval_required, audit_level               spec.governance (동일) + policy 참조

 required_env / optional_env             미설정 시 배포 경고                                                             spec.env.required/optional + secretRef

 min_platform_version                    하위 호환 검사                                                                spec.platform.min

 (없음)                                    -                                                                       추가: protocols{mcp,a2a,openai_compat,agui},
                                                                                                                 llm{required,local_ok,min_context}, permissions{network,fs,secrets,docker},
                                                                                                                 resources, runtime.mode, ui{route,mount}, db{engine,isolation}, license, publisher,
                                                                                                                 signature




3.6 요구사항 8개 → 도메인 추적표
사용자 요구 (1)~(8) 이 어느 도메인·항목으로 구현되는지. 빈 칸이 없어야 한다.
 요구             내용                                                           1차 도메인                  항목 ID                                                   보조

 (1)            로컬 LLM 지원                                                    D1                      D1-01, D1-02, D1-06, D1-07                              D8-05 GPU, D8-07 오프라인

 (2)            Public AI 서비스(ChatGPT, Claude Code 등) LLM 지원                 D1                      D1-03, D1-04, D1-05                                     D9-04 키 보관

 (3)            기본 Agent: Orchestrator + 대화형 AI Assistant                    D2, D3                  D2-01~07, D3-01~07                                      D7-01 MCP 노출(v1 F29)

 (4)            Addon-Agents 템플릿(Scaffold) + Zip 업로드                         D4, D5                  D4-01, D4-02, D5-01, D5-02                              D4-07 파생

 (5)            Zip = frontend·backend·database·meta                         D4                      D4-04 agent.yaml, 10.2 규격                               D5-07 프론트 통합, D10-06 DB 격리

 (6)            구매 또는 마켓(다운로드/설치·직접설치·연동/연계)                                 D6                      D6-01~07                                                D5 8단계

 (7)            MCP·A2A 표준 프로토콜 연계                                           D7                      D7-01~07                                                11장 사양 검증

 (8)            docker compose 독립 구동                                         D8                      D8-01~07                                                10.3 compose 전문, M1 모드

 (공통)           각 항목이 독립 구동 + 등록 즉시 사용                                       전체                      70 항목 전부 M1 가능                                          10.1 세 모드 계약, 10.5 누락 CI
4. 목표 시스템

4.1 제품 정의
제품명                       AgentPlaza
한 줄 정의                    로컬 LLM 과 퍼블릭 AI 서비스를 하나의 게이트웨이로 쓰고, Orchestrator·AI Assistant 를 기본으로 제공하며, Zip 으
                          로 포장된 Addon 에이전트를 마켓플레이스에서 골라 docker compose 로 독립 또는 연계 구동하는 멀티 에이전트
                          플랫폼
구성 단위                     기능 항목 하나 = 에이전트 하나. 도메인 70종, 후순위 12종, 플랫폼 공유 서비스 12종 = 94종
기본 에이전트                   Orchestrator(D2) 와 AI Assistant(D3). 설치 직후 이 둘만으로 대화·라우팅·도구 호출이 된다
Addon 에이전트                agent.zip = agent.yaml + frontend/ + backend/ + database/ + compose.yaml. 스캐폴드로 만들고, 업로드하거나 마
                          켓에서 받는다
핵심 성질                     모든 에이전트는 다른 에이전트 없이 단독 실행된다(M1). 플랫폼은 조립·발견·정책 수단이지 실행 전제가 아니다
표준 표면                     REST(OpenAPI) · MCP 서버 · A2A Agent Card · AG-UI 이벤트. 네 문은 agent.yaml 하나에서 생성
대상 사용자                    플랫폼 운영자(supervisor/admin), 일반 사용자(채팅·화면), Addon 개발자·퍼블리셔, 외부 시스템(MCP/A2A 클라이
                          언트)
배포 형태                     docker compose(1차) · 폐쇄망 번들 · Kubernetes(X10 선택). macOS Apple Silicon 은 LLM 만 호스트 네이티브 브리지
범위 밖                      멀티테넌시(X09), 상거래 정산·세금(X12), 파인튠 학습 UI(X08 → LLMForge), 모바일 앱(X11), 프레임워크 자체 개발




4.2 기본 에이전트 둘




                                 그림 1. AgentPlaza 개요 — 기본 에이전트 2종, Addon, LLM 공급, 마켓, 런타임
항목           Orchestrator (D2)                                        AI Assistant (D3)
책임           의도 분류·계획·레지스트리 라우팅·실행 패턴·도구 실행·Reviewer/HITL 게이트·        대화 UI·세션·스트리밍·도구 호출 UX·파일·멀티모달·메모리·RAG·채널
             상태·합성
입력               Assistant 또는 외부(MCP tool orchestrate, A2A Task)                       사용자 브라우저, 위젯, 메신저 채널, OpenAI 호환 /v1
출력               AG-UI 이벤트 스트림 + 최종 답 + 감사 이벤트                                         화면 렌더 + 승인 카드 + 세션 저장

LLM              게이트웨이 별칭 plaza/orchestrator(구조화 출력 필수)                                게이트웨이 별칭 plaza/chat(스트리밍 필수)
독립 구동            compose orchestrator.yaml 단독. MCP·A2A 로 외부에서 호출 가능(v1 F29)            compose assistant.yaml 단독. Orchestrator 없으면 단일 LLM 채팅으로 강등

v1 대응            app/agents/orchestrator.py + F25 게이트                                  front ChatPage + POST /api/agent/chat/stream




4.3 운용 3모드




                                                        그림 5. M1 독립 · M2 연계 · M3 즉시 사용
모드               정의                                     실행 형태                                                대표 상황
M1 독립            agent.zip 하나가 플랫폼 없이 돈다                docker compose --profile standalone                  고객사에 에이전트 하나만 납품, 개발자 로컬 시험, v1
                                                        up — 자체 db, 자체 포트, 자체 MCP/A2A 노출                     Standalone 번들

M2 연계            플랫폼 네트워크에 합류하거나 원격으                    루트 compose include(로컬) 또는 A2A Card/MCP URL 등록        사내 플랫폼, 타사 에이전트 연동, n8n·Dify·RAGFlow 같은
                 로 등록된다                                 (원격). 포트 노출 0, Traefik 경로                            G4 시스템 연계

M3 즉시 사용         마켓에서 고르고 설치하면 콘솔에 바                    8단계 자동 통과 → include 자동 생성 → 헬스 → 네비                  게시판·RAG·리뷰어 5분 설치, 폐쇄망은 오프라인 번들
                 로 뜬다                                   노출. 코드 작업 없음




4.4 설계 원칙
번호      원칙                      내용                                                                    위반 시
DP1     항목이 곧 경계                D1–D10 소항목 하나에 에이전트 하나. 감사·라이선스·배포 단위가 일치                             한 컨테이너에 GPL 과 MIT 가 섞인다

DP2     홀로 서기                   agent.yaml dependencies 는 비어 있어야 한다. 플랫폼 서비스는 있으면 쓰고                  M1 불가, 부분 도입 불가
                                없으면 강등
DP3     공급자 무지                  에이전트 코드는 LLM 공급자를 모른다. 게이트웨이 별칭만 부른다                                  로컬↔퍼블릭 전환에 코드 수정

DP4     네 문 동일                  REST·MCP·A2A·AG-UI 를 agent.yaml 에서 생성. 손으로 쓴 Card 금지                  Card 와 실제 capability 불일치

DP5     Zip 은 신뢰하지 않는다          업로드 코드는 컨테이너 모드 기본. in-process 는 서명된 신뢰 퍼블리셔만                         임의 코드가 플랫폼 프로세스에서 실행(v1 위험)

DP6     데이터 등급이 모델을             confidential 은 local:true 모델만. 게이트웨이가 강제                              내부 문서가 퍼블릭 API 로 유출
        고른다
DP7     G4 비링크                  AGPL·SSPL·BUSL·SUL·Polyform·브랜딩 조건 코드는 연계만                            호스팅 소스 공개·재판매 금지 위반

DP8     승인은 데이터                 human_approval_required 는 메타에 선언, 게이트가 집행, 원장에 기록                     UI 만 승인하고 API 는 우회

DP9     compose 가 1차            Kubernetes 는 kompose/Helm 변환 대상. compose 로 안 되는 기능은 넣지 않              소규모 도입 장벽
                                는다
DP10    출처를 남긴다                 파생·설치·연계 모두 base·publisher·license 를 자동 기록                            라이선스 고지 누락
4.5 사용자 흐름
 1. 최초 설치. git clone 또는 번들 → plaza up → 셋업 위저드(관리자 생성, LLM 연결: Ollama 자동 감지 또는 퍼블릭 키 입
    력, 모델 pull) → Assistant 채팅 시작.
 2. Addon 개발. 콘솔 '새 Agent 만들기' 또는 plaza init MyAgent --type app → frontend/backend/database 작성 →
    plaza test → plaza publish → agent.zip.
 3. 직접 설치(경로 B). 콘솔 'ZIP 업로드 등록'(다중 선택) → 8단계 → 콘솔 네비에 화면, Assistant 에 도구, /mcp 와 Agent Card 노출.
 4. 마켓 설치(경로 A). 마켓 탭 → 검색 → 상세(라이선스·권한·서명 배지) → 설치(유료면 라이선스 키) → required_env 입력 → 8단
    계.
 5. 연동·연계(경로 C). '원격 에이전트 등록' → A2A Card URL 또는 MCP 서버 URL + 인증 → 계약 시험 → 카탈로그 편입. 코드 미설
    치.
 6. 독립 납품(M1). 콘솔 '추출 → Standalone 번들' → agent.zip(compose 포함) → 대상 서버에서 docker compose --
    profile standalone up -d.
 7. 외부에서 쓰기. Claude Desktop·Cursor 는 /mcp/{agent} 를, 다른 에이전트는 /.well-known/agent-card.json 을,
    Open WebUI 는 /v1 OpenAI 호환을 연결.
5. 기능 요구사항
FR-D 는 도메인 항목 70개와 1:1 이다. FR-X 는 후순위 12개, FR-P 는 플랫폼 공유 서비스 12개. 합계 94개. 각 FR 은 '하는 일'(사용자 관
점)과 '구현 요지'(개발자 관점)를 함께 적어 구현 시 해석 여지를 줄인다.

5.1 읽는 법
 열               뜻
 ID              FR-D{도메인}-{번호}. 에이전트 ID 와 같다(8장 카탈로그, 10.5 누락 CI 의 키)
 P               P0 = 첫 릴리스 필수, P1 = 두 번째 릴리스, P2 = 이후
 하는 일            사용자·운영자가 관찰 가능한 결과
 구현 요지           기술 선택·경계·v1 승계 여부. 9장 스택과 연결
 참고 OSS          구현 엔진 후보. 필수 링크가 아니다(DP3·DP7)




5.2 FR-D1 LLM 공급 — 로컬·퍼블릭·CLI 에이전트 백엔드를 하나의 게이트웨이로
 ID       P    에이전트                하는 일                                                            구현 요지

 D1-01    P0   Ollama 로컬 런타임 어댑터   로컬 모델을 pull·서빙하고 OpenAI·Anthropic 호환 API 로 노출한                  compose ollama 서비스(cpu/gpu 오버레이) + OLLAMA_RUNTIME=mlx 시
                                   다. Apple Silicon 은 호스트 네이티브 Ollama 로 브리지한다.                     host.docker.internal 브리지. keep_alive, 모델 예열, 헬스.

 D1-02    P1   고성능 로컬 서빙 엔진        GPU 서버에서 vLLM/SGLang/llama-server/LocalAI 로 다중 사용자 동            OpenAI 호환 /v1 서버 컨테이너. GGUF 는 llama-server, safetensors 는 vLLM.
                                   시 추론을 제공한다.                                                     도구호출·구조화출력 파서 옵션.

 D1-03    P0   퍼블릭 LLM API 어댑터     OpenAI(ChatGPT)·Anthropic(Claude)·Google(Gemini)·OpenRouter 등   공식 SDK 3종 + OpenAI 호환 폴백. 키는 D9-04 시크릿. 요금·토큰 계량은
                                   상용 API 를 같은 인터페이스로 호출한다.                                        D10-03.

 D1-04    P1   CLI 에이전트 백엔드 브리지    Claude Code·Codex CLI·Gemini CLI·OpenClaw 같은 에이전트형 CLI          1차 NDJSON 어댑터(claude -p --output-format stream-json, codex exec --json,
                                   를 백엔드로 삼아 코딩·파일 작업을 위임한다.                                       gemini -p), 2차 ACP(gemini --acp, opencode 네이티브). Claude Agent SDK 병
                                                                                                   행. 작업 디렉터리 샌드박스. 승인은 D2-06.

 D1-05    P0   통합 게이트웨이·라우터        모든 에이전트가 부르는 단일 OpenAI 호환 엔드포인트. 라우팅·폴                          LiteLLM(MIT 범위만, enterprise/ 는 유료) 또는 Bifrost(전부 Apache-2.0). 모델
                                   백(퍼블릭↔로컬)·예산·키·캐시·재시도.                                          별칭(plaza/fast, plaza/local). 프라이버시 등급 헤더가 폴백보다 우선. 강등
                                                                                                   을 이벤트로 알림.

 D1-06    P0   모델 카탈로그·데이터 등급      모델 메타(컨텍스트, 도구호출, 비전, 라이선스, 로컬 여부)를 관리                          models.yaml + DB. commercial_use(allowed|conditional|prohibited) 별도 필
               정책                  하고 데이터 등급별 허용 모델을 강제한다.                                         드, 프라이버시 등급 L0~L3 별 허용 목록. conditional 모델은 기본 비활성.
                                                                                                   오픈 가중치 라이선스 표.

 D1-07    P1   임베딩·리랭크 서빙          RAG·메모리 에이전트가 쓰는 임베딩·리랭크 모델을 로컬 또는 퍼                            Ollama embed 기본, TEI 컨테이너(임베딩+리랭크, Metal 지원) 표준. 리랭
                                   블릭으로 제공한다.                                                      크는 내부 규격 POST /v1/rerank 로 TEI·llama.cpp 흡수. 차원·모델명을 컬렉
                                                                                                   션에 기록.




5.3 FR-D2 오케스트레이터 — 의도·계획·라우팅·실행 패턴·게이트·상태
 ID       P    에이전트                하는 일                                                            구현 요지

 D2-01    P0   의도 분류·계획            사용자 메시지를 하나 이상의 intent 로 분류하고 실행 계획(순서·                         LLM 구조화 출력(JSON) + 규칙 매처 폴백(keyword_rules). 계획은 그래프
                                   병렬·의존)을 만든다.                                                    로 D2-03 에 전달.

 D2-02    P0   레지스트리 라우팅           capability(verb·domain) 인덱스에서 intent 를 처리할 에이전트를                D5-06 인덱스 질의. 후보 다수면 점수(정확도·비용·지연·데이터등급). v1
                                   찾는다. 없으면 general 폴백과 registry_miss 이벤트.                         F23/F25 승계.

 D2-03    P0   실행 패턴 엔진            sequential·parallel·loop·handoff·supervisor 패턴으로 다중 에이전트        LangGraph 라이브러리(MIT)만 자체 FastAPI 안에서 실행 —
                                   를 실행한다. 체크포인트로 재개한다.                                            langgraph-api/langgraph dev 는 Elastic-2.0 이라 금지. CrewAI·ADK·OpenAI
                                                                                                   Agents SDK 어댑터 선택.

 D2-04    P0   도구 호출 실행기           MCP 도구·내부 REST·A2A 원격 에이전트를 호출하고 결과를 정규                         MCP 클라이언트(D7-02)와 A2A 클라이언트(D7-04) 위. 결과 포맷터(v1
                                   화·요약한다.                                                         _format_api_result 승계). 타임아웃·재시도.

 D2-05    P1   리뷰어 게이트             응답 품질·위험도를 별 에이전트가 검토하고 통과·수정·차단을 결                             agent_type=reviewer. 옵트인→기본 켜짐(외부 도구 결과 포함 시). 판정
                                   정한다.                                                            을 감사(D9-07)에 기록.

 D2-06    P0   휴먼 승인 게이트           human_approval_required 인 capability 는 승인 대기·타임아웃·재             agent_type=hitl. 승인 카드(D3-03), 대기 상태 체크포인트, 만료 정책. 승인
                                   개를 거친다.                                                         자는 RBAC(D9-02).

 D2-07    P1   상태·내구성·합성           실행 상태를 저장하고 실패를 재시도·보상하며 다중 결과를 하나                              langgraph-checkpoint-postgres(MIT). 장기 작업은 Temporal 선택(Inngest
                                   의 답으로 합성한다.                                                     SSPL·Restate BUSL 회피). 합성 프롬프트와 인용 유지.
5.4 FR-D3 대화형 어시스턴트 — 채팅 UI·세션·도구 UX·멀티모달·메모리·채널
ID      P    에이전트                    하는 일                                                                   구현 요지

D3-01   P0   채팅 UI·스트리밍              웹 채팅 화면. 토큰 스트리밍, 마크다운·코드·표, 다크모드, ko/en.                              assistant-ui(MIT, react-ag-ui 패키지) + React 19. 완제품 포크 금지(Open
                                                                                                            WebUI 브랜딩 조항). v1 ChatPage 승계.

D3-02   P0   세션·히스토리                 대화를 저장·검색·제목 자동화·폴더화한다. 삭제·내보내기.                                       sessions/messages 테이블(D10-06). 전문 검색. 보존 기간 정책.

D3-03   P0   도구 호출 UX·에이전트 스         진행 표시, 승인 카드(HITL), 결과 카드(표·차트·파일), 특정 에이전                             이벤트 tool_start/tool_end/hitl_pending. /addon/{key} 폴백 화면(v1 승계).
             코프 채팅                   트로 범위를 좁힌 채팅.

D3-04   P1   파일·멀티모달 입력              문서·이미지 업로드, 비전 모델 이해, 음성 입력(STT), 음성 출력                                파일 저장(볼륨/S3 호환). 비전 가능 모델은 D1-06 카탈로그. STT 는 X03
                                     (TTS, 선택).                                                             Addon 호출.

D3-05   P1   메모리·개인화                 사용자 맞춤지침, 장기 메모리(사실·선호), 프로필을 유지한다.                                    agent_type=memory. Mem0/Letta 선택. 개인정보 최소화, 삭제권.

D3-06   P1   지식(RAG) 연결              문서 컬렉션을 만들고 RAG Addon 을 통해 근거 있는 답과 인용을                                RagAgent 템플릿(D4-01) 기본, RAGFlow 연계 선택. 인용 카드. 임베딩은
                                     제공한다.                                                                  D1-07.

D3-07   P2   채널·임베드                  웹 위젯 임베드, Slack·Telegram·카카오 등 메신저 채널, 외부 앱용                           채널 어댑터 Addon(OpenClaw 패턴 참고). 위젯은 iframe+postMessage. API
                                     API.                                                                   키는 D9-03.




5.5 FR-D4 애드온 SDK·스캐폴드 — 템플릿·위저드·SDK·메타 스키마·시험·패키징·내보내기
ID      P    에이전트                    하는 일                                                                   구현 요지

D4-01   P0   에이전트 템플릿 9유형            app·service·rag·tool-proxy·reviewer·execution·hitl·memory·federation   v1 Board/RagAgent/ServiceAgent/ToolProxyAgent 승계 + 5유형 추가. 각 템
                                     유형별 완성 예제와 zip.                                                        플릿에 compose·agent.yaml 포함.

D4-02   P0   스캐폴드 위저드·CLI            UI 위저드와 plaza init CLI 로 이름·유형·도메인·LLM 요구를                             Copier 템플릿(재템플릿 update 지원). v1 /api/addon-agents/scaffold 승계.
                                     받아 zip 을 생성하고 바로 배포한다.

D4-03   P0   에이전트 SDK                BaseAgent, DB 헬퍼, 인증 의존성, LLM 클라이언트(D1-05), 이벤트                        python 패키지 agentplaza-sdk, TS 패키지 @agentplaza/ui(클라이언트·훅
                                     발행, MCP/A2A 자동 노출을 제공한다.                                               ·i18n·테마).

D4-04   P0   agent.yaml 스키마·검증기      메타(정체·버전                                                               v1 meta.json 상위 호환. 다국어 필드. A2A Agent Card·MCP server.json 생성
                                     ·capabilities·governance·protocols·llm·permissions·resources·ui·db)를   매핑.
                                     JSON Schema 로 정의·검증한다.

D4-05   P1   로컬 개발·계약 시험             make test(구조·문법·router·SQL·React export) + 로컬 실행 +                     MCP Inspector CLI, A2A 샘플 클라이언트, promptfoo 시나리오. 시험 결과는
                                     MCP/A2A 계약 시험.                                                         test/impl/<N>/ 규칙.

D4-06   P1   패키징·서명                  make publish 로 zip·checksums·SBOM·서명을 만든다. OCI 아                       cosign 키리스 또는 Ed25519 키. syft SBOM. ORAS 로 OCI 레지스트리 배포.
                                     티팩트 푸시 선택.

D4-07   P0   파생·독립 실행 내보내기           기존 에이전트를 새 이름으로 파생 export(출처 자동 명시)하고,                                 v1 F26/F27 승계. 번들 = agent.zip 규격 그대로(M1 독립 구동).
                                     compose·Dockerfile·.env 포함 독립 번들을 만든다.




5.6 FR-D5 패키지·레지스트리 — Zip 업로드·검증·서명·라이선스·디플로이·카탈로그
ID      P    에이전트                    하는 일                                                                   구현 요지

D5-01   P0   Zip 업로드                 단일·다중 zip 을 업로드한다. 진행 표시, 파일별 결과, 크기 상한                                v1 F4 승계. 스트리밍 업로드, 재시도. 상한 기본 100MB(설정).
                                     설정.

D5-02   P0   구조 검증 게이트               스키마·경로탐색 차단·파일 규칙·Python 문법·SQL 정적검사·금지                                _safe_extract 승계 + zip-slip·심볼릭 링크·크기 폭탄 방어. sqlglot 로 DDL 만
                                     API 검사.                                                                허용.

D5-03   P1   서명·SBOM·취약점 게이트         서명 검증, SBOM 생성·비교, 취약점 스캔(Critical 차단).                                cosign verify, syft/grype 또는 trivy. 마켓 퍼블리셔 키(D6-06)와 대조.

D5-04   P1   라이선스·정책 게이트             패키지 라이선스 등급(G1~G5)과 선언 권한(network·fs·secrets)을                         OPA/Rego 정책. G4(AGPL) 는 격리 컨테이너 전용 표시, G5 는 차단.
                                     조직 정책과 대조한다.

D5-05   P0   디플로이 모드                 v1 호환 in-process 핫 디플로이(importlib)와 v2 컨테이너 디플로이                       agent.yaml runtime.mode=inprocess|container. 컨테이너 모드가 기본. in-
                                     (compose)를 선택 실행한다.                                                    process 는 신뢰 퍼블리셔만.

D5-06   P0   카탈로그 DB·capability 인덱   등록 에이전트·버전·상태·capability 를 저장하고 semver 업그레이                            tbl_agents/tbl_agent_versions/tbl_capabilities. 라우터 제거는 컨테이너 모
             스                       드·롤백·활성/비활성·삭제를 관리한다.                                                  드에서 즉시.

D5-07   P0   프론트 통합 파이프라인            Addon frontend 를 콘솔에 끼운다. 런타임 iframe 기본, 빌드타임                          v1 재빌드 30초 경로 유지(선택). iframe+postMessage 규약(토큰·테마·로케
                                     통합·Module Federation 선택.                                               일). 네비 노출 규칙 is_active&&has_front.
5.7 FR-D6 마켓플레이스 — 스토어·설치 3경로·구매·퍼블리셔·업데이트
ID      P    에이전트                   하는 일                                                      구현 요지

D6-01   P0   스토어 UI                 검색·카테고리·상세(README·스크린샷·라이선스·권한·버전·퍼블                      콘솔 안 마켓 탭. 카드는 agent.yaml 에서 렌더. 신뢰 배지(서명·검증).
                                    리셔·평점).

D6-02   P0   설치 경로 A 다운로드·설치        마켓에서 zip 또는 OCI 아티팩트를 받아 D5 파이프라인을 자동 실                   원클릭. 요구 env 입력 폼(required_env). 실패 시 롤백.
                                    행하고 콘솔에 노출한다.

D6-03   P0   설치 경로 B 직접 설치          로컬 zip 업로드, Git URL, OCI 참조, 사설 미러에서 설치한다. 폐쇄             v1 ZIP 업로드 승계 + 소스 다양화. 미러는 D6-07.
                                    망 지원.

D6-04   P0   설치 경로 C 연동·연계          코드를 설치하지 않고 원격 A2A Agent Card 또는 MCP 서버 URL 을             agent_type=federation. 인증 정보는 D9-04. 헬스·계약 시험 후 노출.
                                    등록해 카탈로그에 편입한다.

D6-05   P1   구매·라이선스·엔타이틀먼          무료·유료 에이전트. 라이선스 키 발급·검증, 좌석·기간, 결제 어댑                    Ed25519 서명 라이선스 토큰(오프라인 검증). 결제는 Lago/Polar/Stripe 어
             트                      터, 영수증.                                                   댑터. 상거래 정산은 X12.

D6-06   P1   퍼블리셔 계정·릴리스            퍼블리셔 등록, 서명 키, 게시·심사·버전 릴리스, 다운로드 통계.                     심사 = D5 게이트 자동 + 관리자 승인. 키 회전. 철회(revoke).

D6-07   P1   업데이트·마켓 서버             업데이트 알림·자동 갱신·롤백. 마켓 서버는 셀프호스팅 가능하며                       레지스트리 API(서버 목록·버전·아티팩트). 오프라인 번들 export. 공식
                                    MCP registry server.json 과 호환한다.                          MCP 레지스트리 미러.




5.8 FR-D7 프로토콜 게이트웨이 — MCP·A2A·OpenAI 호환·AG-UI·ACP·정책
ID      P    에이전트                   하는 일                                                      구현 요지

D7-01   P0   에이전트별 MCP 서버           각 에이전트의 capability 를 MCP tools·resources·prompts 로 노출한    Streamable HTTP, 사양 2026-07-28(무상태, server/discover) + 2025-11-25 동
                                    다.                                                        시 광고. 경로 /mcp/{agent}. v1 포트 방식은 호환 옵션. 공식 python-sdk 또
                                                                                              는 FastMCP.

D7-02   P0   MCP 클라이언트·서버 등록        외부 MCP 서버(stdio·HTTP)를 등록하고 도구 카탈로그를 오케스트                 v1 router_mcp_config 승계. 도구 허용목록(D9-06). 공식 레지스트리 검색.
                                    레이터에 공급한다. OAuth 2.1.

D7-03   P0   A2A 서버                 Agent Card 공개, Task 생성·상태·스트리밍·푸시 알림, 인증 스킴.              v1 router_a2a(v0.x 스타일) → 공식 a2a-python SDK(v1.0.1 사양) 로 교체.
                                                                                              Card 는 agent.yaml 에서 생성, JWS 서명 필수.

D7-04   P0   A2A 클라이언트              원격 에이전트의 Card 를 읽고 Task 를 보내 결과·아티팩트를 받는                  D6-04 연동 경로의 실행부. 장기 Task 폴링·SSE. 오류·취소.
                                    다.

D7-05   P1   OpenAI 호환 노출·OpenAPI   에이전트를 /v1/chat/completions 로 노출하고, 기존 REST(OpenAPI)       Open WebUI·LibreChat 등 외부 클라이언트가 AgentPlaza 를 모델처럼 사
             변환                     를 MCP 도구로 자동 변환한다.                                        용. OpenAPI→MCP 는 게이트웨이 기능(fastapi_mcp 는 2025-08 정체로 비
                                                                                              권장). v1 openapi_to_mcp 승계.

D7-06   P1   AG-UI 이벤트·ACP 브리지      프론트↔에이전트 이벤트 스트림을 AG-UI 로 표준화하고, 코딩                       AG-UI spec 1.0 이벤트 34종(SUBAGENT_* 포함). ACP 어댑터(gemini --acp,
                                    CLI 는 ACP 로 연결한다.                                         claude-agent-acp, codex-acp).

D7-07   P1   게이트웨이 정책               인증(API key·JWT·OAuth)·RBAC·레이트리밋·감사·OTel 전파를              agentgateway(MCP+A2A+LLM 단일 데이터플레인). Mcp-Method·Mcp-Name
                                    MCP/A2A 트래픽에 일괄 적용한다.                                     헤더로 툴 단위 RBAC. 에이전트 코드는 정책을 모른다.




5.9 FR-D8 런타임·컴포즈 — Agent compose 골격·루트 include·라우팅·격리·GPU·업그레이드·에어갭
ID      P    에이전트                   하는 일                                                      구현 요지

D8-01   P0   에이전트 compose 골격        frontend·backend·db(·worker) 4서비스, healthcheck, labels,   compose.yaml 표준 + x-agentplaza 메타. standalone 프로파일이 M1.
                                    networks, volumes, secrets, profiles.

D8-02   P0   플랫폼 루트 compose         공유 인프라(postgres·redis·traefik·otel·gateway)와 설치된 에이전트     installed/*.compose.yaml 자동 생성. 이름 충돌은 프로젝트 접두어. 프로파
                                    compose 를 include 로 묶는다.                                  일 federated.

D8-03   P0   라우팅·TLS                Traefik 라벨로 에이전트를 호스트·경로로 자동 노출한다. 포트 노                   /a/{agent}/api, /a/{agent}/ui, /mcp/{agent}, /.well-known/agent-card.json 프록
                                    출 0. Let's Encrypt.                                       시. 사용자 pub-SSL-Cert-Manager 재사용.

D8-04   P0   격리·샌드박스                에이전트 네트워크 분리, 리소스 상한, read-only fs, docker.sock 금         agent.yaml permissions 를 compose 로 번역. execution 유형은 별 샌드박스
                                    지, 필요 시 gVisor 런타임.                                       (X05).

D8-05   P0   GPU·모델 자원              LLM Provider 만 GPU 를 예약하고 모델 볼륨을 공유한다. Apple              deploy.resources.reservations.devices. 모델 캐시 볼륨. Docker Model Runner
                                    Silicon 은 네이티브 브리지.                                       선택.

D8-06   P1   헬스·업그레이드·롤백·백업         헬스 기반 기동 순서, 이미지 태그 고정 업그레이드, 실패 시 롤백,                    depends_on service_healthy. 버전 pin. offen/docker-volume-backup 또는
                                    볼륨·DB 백업.                                                 restic.

D8-07   P1   오프라인·설치자               이미지 tar·모델 사전 배치·미러 레지스트리로 폐쇄망 설치. 설치                     v1 F28 승계. 사용자 pub-Server-Init·pub-wsa-for-sdd 셸 재사용.
                                    스크립트.
5.10 FR-D9 신원·거버넌스 — 인증·RBAC·서비스계정·시크릿·정책·가드레일·감사
ID       P    에이전트               하는 일                                                                      구현 요지

D9-01    P0   계정·SSO             로컬 계정(JWT) + OIDC SSO(Keycloak·Authentik). 최초 관리자 셋업.                     v1 JWT 승계. OIDC 는 선택 프로파일. 세션 만료·MFA(IdP).

D9-02    P0   역할 기반 권한           supervisor·admin·user + 에이전트 단위 권한, 하위권한만 제어 규                            v1 F31 승계. 권한 = 역할×에이전트×capability.
                                 칙.

D9-03    P0   서비스 계정·API 키       외부 MCP/A2A 클라이언트용 API 키→서비스 JWT, 에이전트 간 토                                 v1 F29 승계. 키 범위(에이전트·capability). 회전·철회.
                                 큰.

D9-04    P1   시크릿                .env 에서 OpenBao·SOPS·Infisical 로. required_env 주입, 회전.                    compose secrets. 로그 마스킹. 퍼블릭 LLM 키는 게이트웨이(D1-05)만 보유.

D9-05    P1   거버넌스 정책 엔진         data_classification·human_approval_required·audit_level 을 정책으             OPA. 등급별 허용 모델(D1-06)·도구·내보내기 제한.
                                 로 집행한다.

D9-06    P1   가드레일               프롬프트 인젭션 방어, PII 마스킹, 도구 허용목록, 출력 검토.                                     입력·출력 필터 미들웨어. reviewer(D2-05) 연계. 한국어 PII 패턴.

D9-07    P0   감사 원장              누가·어느 에이전트·어떤 도구·결과 해시를 불변 기록. 보존·개인                                      append-only 테이블 + 해시 체인. 프롬프트 원문은 등급별 저장.
                                 정보 최소화.




5.11 FR-D10 콘솔·관측 — 콘솔·셋업·OTel·LLM 관측·평가·데이터모델·알림
ID       P    에이전트               하는 일                                                                      구현 요지

D10-01   P0   플랫폼 콘솔             에이전트 관리(내장·Addon 목록, 토글, MCP 설정, 삭제, 추출), 설                               v1 AgentsPage/SettingsPage/UsersPage 승계. 에이전트 상태·헬스·버전 표
                                 정, 사용자, 프로필, 마켓 탭.                                                        시.

D10-02   P0   셋업 위저드·온보딩         최초 실행: 관리자 생성, LLM 연결(로컬/퍼블릭) 검사, 모델 pull, 기                              v1 SetupWizard·ollama_preflight 승계. 비차단 경고.
                                 본 에이전트 활성화.

D10-03   P0   OTel 트레이스·메트릭·로그   GenAI semconv 로 에이전트 span·토큰·비용·지연을 수집한다.                                 OTel Collector 공유 서비스. SDK 자동 계측(D4-03).

D10-04   P1   LLM 관측 UI          트레이스·프롬프트·세션·비용 대시보드.                                                     Opik 기본(Apache-2.0), Langfuse 선택. Grafana 인프라 대시보드.

D10-05   P1   평가·시험 표준           에이전트 회귀 시나리오, 품질 점수, 사용자 시험 표                                             promptfoo·deepeval. 마켓 게시 전 필수 시나리오. 사용자 wise-dev-std 규
                                 준(test/impl/<N>).                                                         칙.

D10-06   P0   데이터 모델·마이그레이션      공통 스키마                                                                    v1 sql/ 승계. 플랫폼 계약은 dbmate(순수 SQL·언어 무관), 개발 편의는
                                 (users·sessions·messages·agents·versions·capabilities·installs·licenses   alembic autogenerate. Addon DB 는 격리 3방식.
                                 ·audit). 멱등 마이그레이션. SQLite↔PG.

D10-07   P2   알림·상태              헬스 대시보드, 알림(Slack·Telegram·메일), 사용량 리포트.                                  uptime-kuma 선택. 이벤트 버스(P03) 구독.




5.12 FR-X 후순위·공백
요구사항 8개에 직접 명시되지 않았으나 인포그래픽 20 저장소를 성실히 수용하려면 필요한 항목. 모두 Addon 또는 연계로 구현되어
코어를 키우지 않는다.
ID       이름                            구현 요지                                                                                                               P

X01      비주얼 플로우 빌더 Addon              Langflow(MIT) 컨테이너. 플로우→Addon Agent 내보내기                                                                            P2

X02      이미지·비디오 생성 Addon              ComfyUI GPL-3.0 격리 컨테이너, API 호출. SD WebUI 는 대체                                                                      P2

X03      음성 Addon                      faster-whisper STT, sherpa-onnx/piper TTS                                                                           P2

X04      자동화 연계                        n8n Sustainable Use → 웹훅·MCP 연계만                                                                                    P2

X05      코드 실행 샌드박스 Agent              execution 유형. microsandbox/E2B/gVisor                                                                               P2

X06      브라우저 에이전트                     browser-use + Playwright                                                                                            P2

X07      RAG 엔진 연계                     RAGFlow Apache-2.0 컨테이너                                                                                             P2

X08      파인튠·로컬 학습                     Transformers·PyTorch. LLMForge PRD 참조                                                                               P2

X09      멀티테넌시                         조직·워크스페이스 격리(v1 out-of-scope 유지)                                                                                    P2

X10      쿠버네티스 배포                      kompose·Helm·kagent. compose 가 1차                                                                                   P2

X11      데스크톱·모바일 셸                    Tauri. 콘솔 PWA 우선                                                                                                    P2

X12      상거래 정산·세금                     마켓 결제 고도화. 법무 검토                                                                                                    P2
5.13 FR-P 플랫폼 공유 서비스
에이전트가 아니라 에이전트들이 함께 쓰는 인프라. 루트 compose 의 infra/ 에 산다. M1 에서는 없어도 된다(DP2).
ID     이름                        역할                                                                       M1 부재 시 강등

P01    리버스 프록시                   Traefik. 라벨 라우팅·TLS·미들웨어                                                 에이전트가 자체 포트 publish

P02    에이전트 레지스트리                D5-06 카탈로그 API. server.json·Agent Card 발행                                agent.yaml 로컬 파일만

P03    이벤트 버스                    Valkey Streams. 도구·승인·상태 이벤트                                             인메모리 큐

P04    공유 Postgres               플랫폼 스키마 + 선택 Addon 스키마. pgvector                                         에이전트 자체 db 컨테이너 또는 SQLite

P05    공유 Valkey                 세션·캐시·큐·이벤트 스트림. Redis 8 3중 라이선스 회피(BSD-3)                               인메모리 캐시

P06    OTel 컬렉터                  트레이스·메트릭·로그 수집·내보내기                                                      stdout 로그

P07    신원 제공자                    Keycloak(선택 프로파일). 로컬 JWT 기본                                             로컬 JWT

P08    시크릿 저장소                   OpenBao(선택). compose secrets 기본                                          compose secrets/.env

P09    마켓 서버                     D6-07. 셀프호스팅 레지스트리·아티팩트                                                  zip 직접 업로드만

P10    빌드 서비스                    zip→이미지 빌드(BuildKit), 프론트 통합 빌드                                          로컬 docker build

P11    작업 실행기                    장기 작업·스케줄. Temporal 선택                                                   인프로세스 asyncio

P12    plaza CLI                 init·test·publish·install·up·export                                      make 타겟




5.14 사용자 스토리 (대표 8)
ID    역할             스토리                                               수용 기준                                                관련 FR

US1   일반 사용자         인터넷이 끊긴 사무실에서도 사내 문서로 질문하고                        퍼블릭 API 차단 상태에서 Ollama 로 응답, 인용 포                    D1-01, D1-05, D3-06, D8-07
                     답을 받는다                                            함
US2   운영자            게시판 에이전트를 마켓에서 골라 5분 안에 쓴다                        설치→네비 노출 5분, 코드 편집 0                                 D6-02, D5-*, D8-02

US3   Addon 개발자      템플릿으로 재고 에이전트를 만들어 zip 으로 올린                      plaza init/test/publish 후 업로드 성                      D4-*, D5-01, D7-01
                     다                                                 공, MCP 도구로 보임

US4   보안 담당          confidential 문서는 퍼블릭 LLM 으로 나가지 않는다               정책 위반 요청은 게이트웨이가 거부하고 원장에                            D1-06, D9-05, D9-07
                                                                       남김
US5   외부 개발자         Cursor 에서 AgentPlaza 의 에이전트를 MCP 도구로              /mcp/{agent} 연결, x-api-key 인증, tools/list 성공         D7-01, D9-03
                     쓴다
US6   파트너            자사 ADK 에이전트를 코드 설치 없이 연동한다                        Agent Card URL 등록 → 계약 시험 통과 →                       D6-04, D7-04, D2-02
                                                                       Orchestrator 가 라우팅

US7   고객사            에이전트 하나만 받아 자기 서버에서 돌린다                           번들 압축 해제 → compose up → /health ok,                  D4-07, D8-01
                                                                       MCP·A2A 응답

US8   관리자            위험한 작업은 승인 후 실행된다                                 hitl_pending 카드 → 승인 → 재개, 미승인 만료                    D2-06, D3-03, D9-02
                                                                       시 취소
6. 비기능 요구사항
가장 위에 두는 것은 격리·독립 구동(NFR-I) 이다. 임의 코드가 든 Zip 을 받아 실행하는 플랫폼이므로, 격리가 깨지면 나머지 품질은
의미가 없다.

6.1 NFR-I 격리·독립 구동 (최상위)
ID        요구                                                                                           측정·검증

NFR-I1    모든 에이전트는 플랫폼 서비스 없이 compose --profile standalone up 으로 기동해 /health ok                        CI 가 70 항목 각각 M1 기동 시험
          를 낸다
NFR-I2    업로드 코드는 기본으로 별 컨테이너에서 실행. 플랫폼 프로세스(in-process)는 서명된 신뢰 퍼블리셔 + 관리                             runtime.mode 기본값 container. 정책 테스트
          자 승인 시에만
NFR-I3    에이전트 컨테이너는 docker.sock·host network·privileged 를 가질 수 없다(v1 network_mode:host·pid:host 는 폐   compose 린트 게이트가 차단
          기)

NFR-I4    에이전트 간 네트워크는 기본 차단. 허용은 agent.yaml permissions.network 선언 + 정책 승인                            네트워크별 격리 시험

NFR-I5    리소스 상한(cpu·memory·pids) 기본값 존재, 초과 시 OOM 격리로 다른 에이전트에 영향 없음                                  부하 시험

NFR-I6    에이전트 삭제 시 컨테이너·볼륨·라우트·카탈로그·MCP/A2A 노출이 60초 내 모두 제거된다(v1 '재시작 필요'                             삭제 후 스캔
          해소)




6.2 NFR-L LLM 공급
ID        요구                                                                                                   측정

NFR-L1    퍼블릭 API 장애 시 30초 내 로컬 모델로 폴백하고 사용자에게 강등 배지를 보인다                                                      장애 주입 시험

NFR-L2    로컬 전용 모드(퍼블릭 키 0개)에서 Assistant·Orchestrator·RAG 가 전부 동작한다                                            에어갭 시험(v1 F28 승계)

NFR-L3    confidential 등급 요청은 local:true 모델 외로 나가지 않는다                                                         정책 시험, 원장 검사

NFR-L4    게이트웨이 첫 토큰 지연 오버헤드 50ms 이하(p95, 로컬망)                                                                 벤치

NFR-L5    모델 카탈로그는 컨텍스트·도구호출·비전·라이선스·로컬 여부를 필수 필드로 가진다                                                         스키마 검증




6.3 NFR-P 프로토콜 적합성
ID        요구                                                                                                   측정

NFR-P1    MCP 서버는 11장에 기록한 현행 사양 버전의 initialize·tools/list·tools/call·Streamable HTTP 를 통과한다                   MCP Inspector CLI 계약 시험

NFR-P2    A2A Agent Card 는 사양 스키마를 통과하고 Task 상태 전이가 사양과 같다                                                     a2a-python 클라이언트 시험

NFR-P3    agent.yaml 에서 생성한 Card·server.json·OpenAPI 가 실제 엔드포인트와 일치한다                                          생성물 vs 런타임 diff 시험

NFR-P4    AG-UI 이벤트는 순서·타입이 표준 스키마를 따르며 클라이언트가 재연결 후 재개 가능                                                     이벤트 리플레이 시험




6.4 NFR-S 보안
ID        요구                                                                                                   측정

NFR-S1    Zip 은 zip-slip·심볼릭 링크·압축 폭탄·중첩 아카이브를 거부한다                                                            악성 샘플 코퍼스

NFR-S2    서명 없는 패키지는 '미검증' 배지, Critical 취약점 패키지는 설치 거부                                                         게이트 시험

NFR-S3    퍼블릭 LLM 키는 게이트웨이 컨테이너만 보유. 에이전트 env 에 원본 키 없음                                                        env 스캔

NFR-S4    모든 도구 호출은 원장(누가·에이전트·도구·인자 해시·결과 해시·시각)에 남는다                                                         샘플링 검사

NFR-S5    인증 없는 엔드포인트는 /health 와 /.well-known/agent-card.json 만                                                라우트 스캔

NFR-S6    프롬프트 인젝션 기본 필터 + 도구 허용목록. 우회 시 reviewer 게이트                                                          레드팀 세트
6.5 NFR-U 사용성·즉시 사용
ID       요구                                                            측정

NFR-U1   빈 서버에서 첫 대화까지 30분 이내(퍼블릭 키 보유 시), 로컬 모델 pull 제외               신규 운영자 측정

NFR-U2   마켓 설치 → 네비 노출 5분 이내(이미지 빌드 포함)                                타이머

NFR-U3   한국어 UI 기본, 영어 폴백. 모든 메타 필드 다국어(v1 F32 확장)                     i18n 키 커버리지 100%

NFR-U4   콘솔은 키보드·스크린리더 접근 가능(WCAG 2.1 AA 목표)                           axe 검사

NFR-U5   화면 없는 에이전트는 자동으로 어시스턴트 스코프 채팅 화면을 가진다(v1 규칙)                  UI 시험




6.6 NFR-O 운영·관측·이식성
ID       요구                                                            측정

NFR-O1   모든 에이전트 span 은 OTel GenAI 규약 속성을 가진다(11.5)                    컬렉터 검사

NFR-O2   compose 만으로 단일 호스트 운영. Kubernetes 는 kompose/Helm 변환으로 도달 가능   변환 시험

NFR-O3   Linux x86_64·arm64, macOS Apple Silicon(LLM 은 네이티브 브리지) 지원    3 플랫폼 CI

NFR-O4   업그레이드는 이미지 태그 고정 + 백업 후 실행, 실패 시 이전 태그로 롤백                    롤백 시험

NFR-O5   SQLite(개발·M1)↔PostgreSQL(운영) 동일 마이그레이션                        양쪽 CI




6.7 NFR-C 준법·라이선스
ID       요구                                                            측정

NFR-C1   G4 코드가 기본 이미지에 링크되지 않는다                                       SBOM 라이선스 스캔 CI

NFR-C2   설치·파생·연계 모든 산출물에 출처·라이선스 자동 기록(DP10)                          메타 검사

NFR-C3   개인정보(대화·파일)는 보존 기간·삭제권·등급을 가진다(개인정보보호법)                       정책 문서 + 삭제 시험

NFR-C4   마켓 유료 거래는 영수증·라이선스 증적을 남기고, 정산·세금은 X12 에서 별도 검토               법무 확인 항목
7. 아키텍처

7.1 계층
층               역할                                   주 에이전트                 정본 패턴
L0 표면           콘솔·채팅·위젯·채널·외부 클라이언트                 D3, D10-01             React 19 + AG-UI 이벤트, iframe 마운트

L1 신원·정책        로그인·RBAC·서비스 계정·시크릿·거버넌스             D9, P07, P08           로컬 JWT 기본 + Keycloak 선택 + OPA

L2 프로토콜 게이트웨이   MCP·A2A·OpenAI 호환·AG-UI·정책 미들웨어      D7, P01                Traefik + agentgateway 패턴

L3 오케스트레이션      의도·계획·라우팅·실행 패턴·게이트·상태               D2, P03, P11           LangGraph StateGraph + Redis Streams

L4 에이전트         Addon 70종 + 기본 2종. 각각 fe/be/db       D1~D10 항목              agent.zip 규격, FastAPI + React + SQLite/PG

L5 LLM 공급       로컬·퍼블릭·CLI 백엔드·게이트웨이·임베딩             D1                     LiteLLM/Bifrost + Ollama/vLLM + 공식 SDK

L6 패키지·마켓       업로드·검증·서명·카탈로그·스토어·구매                D4, D5, D6, P09, P10   cosign + syft/trivy + OCI/ORAS + registry API

L7 런타임          compose 골격·include·격리·GPU·업그레이드      D8                     Compose Spec include/profiles/healthcheck

L8 관측·데이터       OTel·LLM 관측·평가·데이터 모델·알림             D10, P04, P05, P06     OTel Collector + Opik + Postgres/pgvector




                                                 그림 2. 10영역 에이전트 스쿼드
7.2 LLM 공급 계층




                           그림 3. 로컬·퍼블릭·CLI 백엔드 → 통합 게이트웨이 → 모든 에이전트

게이트웨이는 OpenAI 호환 /v1 하나만 노출한다. Ollama 가 Anthropic 호환 API 도 제공하므로 Claude SDK 로 작성된 v1 코드는
base_url 만 바꿔 로컬로 돌릴 수 있다(11장 실측). CLI 에이전트 백엔드(D1-04)는 '모델'이 아니라 '작업 실행자'라서 게이트웨이를 거
치지 않고 Orchestrator 가 A2A 스타일 Task 로 위임하며, 작업 디렉터리는 샌드박스 볼륨이다.

7.3 디렉터리
AgentPlaza/
├── platform/
│   ├── compose.yaml            # include: infra/*.yaml, core/*.yaml, installed/*.compose.yaml
│   ├── infra/                  # traefik, postgres, redis, otel, agentgateway, keycloak(opt),
openbao(opt), market
│   ├── core/                   # orchestrator.compose.yaml, assistant.compose.yaml, llm-
provider.compose.yaml, console
│   ├── installed/              # 설치 시 자동 생성되는 {agent-id}.compose.yaml (git 미추적)
│   └── profiles/               # standalone, federated, airgap, gpu
├── agents/                     # 기본 2종 + 플랫폼 소속 에이전트 소스 (각각 agent.zip 규격 디렉터리)
│   ├── orchestrator/ {agent.yaml, backend/, database/, compose.yaml}
│   ├── assistant/     {agent.yaml, frontend/, backend/, database/, compose.yaml}
│   └── llm-provider/ {agent.yaml, backend/(gateway config), compose.yaml}
├── sdk/
│   ├── python/agentplaza_sdk/ # BaseAgent, db, auth deps, llm client, events, mcp/a2a auto-expose
│   └── ts/@agentplaza/ui/      # client, hooks, i18n, theme, postMessage bridge
├── templates/                  # 9유형 Copier 템플릿 (app, service, rag, tool-proxy, reviewer,
execution, hitl, memory, federation)
├── console/                    # 플랫폼 콘솔 프론트 (에이전트 관리·마켓·사용자·설정·셋업)
├── market/                     # 마켓 서버 (registry API, 아티팩트, 라이선스 발급)
├── cli/                        # plaza: init, test, publish, install, up, export, verify-coverage
├── db/migrations/              # 플랫폼 스키마 (dbmate, SQLite·PG 공용)
├── ops/                        # 설치 스크립트(pub-Server-Init 승계), 인증서(pub-SSL-Cert-Manager), 백업, 에
어갭 번들
└── test/                       # dev-env/, impl/<Nth>/ (wise-dev-std 규칙)
7.4 에이전트 공통 골격 (agent.zip 내부)




                                                             그림 4. agent.zip 규격과 등록 8단계
 부분                                필수                 내용                                                                                   v1 대응

 agent.yaml                        필수                 정체                                                                                   {Name}-meta.json
                                                      ·capabilities·governance·protocols·llm·permissions·resources·runtime·ui·db·license
                                                      ·publisher

 backend/                          필수(federation 유형   FastAPI 앱. SDK BaseAgent 상속. router export. Dockerfile                               {Name}-app.py
                                   제외)

 frontend/                         선택                 React 컴포넌트 또는 정적 빌드. 콘솔이 iframe 또는 MF 로 마운트                                          {Name}-front.tsx

 database/                         선택                 migrations/*.sql(멱등), seed/. engine: sqlite|postgres, isolation: own|shared-         {Name}-sql.sql
                                                      schema|file

 compose.yaml                      필수                 fe·be·db(·worker) 서비스, healthcheck, labels, networks,                                F27 standalone 생성물
                                                      profiles(standalone/federated)

 mcp/server.json · a2a/agent-      생성                 빌드 시 agent.yaml 에서 생성. 수정 금지                                                         -
 card.json

 LICENSE · README.md ·             필수                 라이선스·출처·변경 이력                                                                        F26 provenance
 CHANGELOG.md

 checksums.txt · signature.sig ·   publish 시 생성       무결성·서명·SBOM                                                                          -
 sbom.json




코어는 BaseAgent 의 handle(capability, input) -> output|stream 하나다. REST·MCP·A2A·AG-UI 네 어댑터는 SDK 가
agent.yaml 을 읽어 자동으로 붙인다(DP4). 에이전트 작성자는 어댑터 코드를 쓰지 않는다.
7.5 프로토콜 표면




                                               그림 8. 모든 에이전트가 여는 네 문과 호출자


7.6 실패와 강등
실패                              강등                                      사용자에게 보일 것
퍼블릭 LLM 장애·예산 초과                게이트웨이가 로컬 별칭으로 폴백                       '로컬 모델 응답' 배지

Orchestrator 부재(M1 Assistant)   단일 LLM 채팅 + 자기 도구만                      '라우팅 없음' 안내

레지스트리 miss                      general 폴백 + registry_miss 이벤트(v1)      후보 에이전트 제안

Reviewer 거부                     수정 요청 또는 차단, 원장 기록                      '검토에서 차단됨' 카드

HITL 만료                         Task canceled, 체크포인트 보존                 '승인 만료' 카드, 재요청 버튼

Addon 헬스 실패                     라우트·네비·도구에서 제거, 카탈로그 상태 unhealthy       '일시 중단' 배지

원격 A2A 에이전트 불응답                 Task failed, 재시도 정책, 대체 후보              '연계 에이전트 응답 없음'

GPU 없음                          CPU 추론 또는 퍼블릭 폴백                        성능 경고

IdP 장애                          로컬 비상 관리자 계정(사전 활성화 시)                  제한 모드
7.7 배포 토폴로지




                              그림 7. 루트 compose 가 include 로 인프라·코어·설치 에이전트를 묶는다

   단일 호스트(기본). 루트 compose 하나. Traefik 이 80/443 만 열고 나머지는 내부 네트워크. GPU 는 llm-provider 만.
   Apple Silicon 개발기. Docker 는 Metal 을 못 쓴다. Ollama 는 호스트 네이티브, 컨테이너는 host.docker.internal:11434 로 접속(v1
    OLLAMA_RUNTIME=mlx 승계).
   폐쇄망. 이미지 tar + 모델 파일 + 사설 OCI 레지스트리(zot) + 오프라인 마켓 번들. 퍼블릭 어댑터 비활성.
   분산(선택). LLM 공급 서버와 에이전트 서버를 분리. 게이트웨이 URL 만 바뀐다(DP3). Kubernetes 는 X10.
8. 에이전트 카탈로그
각 행은 독립 기동 단위다. 구현 시 디렉터리 agents/{id}/ 또는 마켓 패키지 {id}.zip. 참고 OSS 열은 9장 실측 표기(스타·라이선스)를 따
른다.

8.1 카탈로그 읽는 법
ID 는 5장 FR 과 같다. P 는 우선순위. '단독 실행'은 M1 명령. 참고 OSS 는 엔진 후보이지 필수 링크가 아니다(DP3·DP7). * 는 사용자 스
타 목록 포함.

8.2 AG-D1 LLM 공급
ID      에이전트                P    단독 실행(M1)                                     참고 OSS (실측)

D1-01   Ollama 로컬 런타임 어댑터   P0   cd agents/d1-01 && docker compose --profile   ollama/ollama * · 181,183★ · ggml-org/llama.cpp * · 128,619★
                                 standalone up

D1-02   고성능 로컬 서빙 엔진        P1   cd agents/d1-02 && docker compose --profile   vllm-project/vllm * · 92,055★ · sgl-project/sglang * · 36,116★ · ggml-org/llama.cpp * ·
                                 standalone up                                 128,619★

D1-03   퍼블릭 LLM API 어댑터     P0   cd agents/d1-03 && docker compose --profile   openai/openai-python * · 31,640★ · anthropics/anthropic-sdk-python · 3,905★ ·
                                 standalone up                                 googleapis/python-genai * · 3,981★

D1-04   CLI 에이전트 백엔드 브리지    P1   cd agents/d1-04 && docker compose --profile   anthropics/claude-agent-sdk-python · 8,124★ · anthropics/claude-code * · 145,936★ ·
                                 standalone up                                 openai/codex * · 124,973★

D1-05   통합 게이트웨이·라우터        P0   cd agents/d1-05 && docker compose --profile   BerriAI/litellm * · 59,036★ · maximhq/bifrost * · 8,147★ · Portkey-AI/gateway * ·
                                 standalone up                                 13,028★

D1-06   모델 카탈로그·데이터 등급 정책   P0   cd agents/d1-06 && docker compose --profile   QwenLM/Qwen3 · 27,637★ · deepseek-ai/DeepSeek-V3 * · 104,464★ ·
                                 standalone up                                 deepseek-ai/DeepSeek-R1 * · 91,980★

D1-07   임베딩·리랭크 서빙          P1   cd agents/d1-07 && docker compose --profile   huggingface/text-embeddings-inference · 5,052★ · michaelfeil/infinity · 2,942 ★ ·
                                 standalone up                                 ollama/ollama * · 181,183★




8.3 AG-D2 오케스트레이터
ID      에이전트                P    단독 실행(M1)                                     참고 OSS (실측)

D2-01   의도 분류·계획            P0   cd agents/d2-01 && docker compose --profile   langchain-ai/langgraph * · 41,863★ · pydantic/pydantic-ai * · 20,021★
                                 standalone up

D2-02   레지스트리 라우팅           P0   cd agents/d2-02 && docker compose --profile   a2aproject/A2A * · 25,828★ · modelcontextprotocol/registry · 7,260★
                                 standalone up

D2-03   실행 패턴 엔진            P0   cd agents/d2-03 && docker compose --profile   langchain-ai/langgraph * · 41,863★ · crewAIInc/crewAI * · 58,715★ · google/adk-python ·
                                 standalone up                                 21,568★

D2-04   도구 호출 실행기           P0   cd agents/d2-04 && docker compose --profile   modelcontextprotocol/python-sdk * · 24,325★ · a2aproject/a2a-python · 2,147★
                                 standalone up

D2-05   리뷰어 게이트             P1   cd agents/d2-05 && docker compose --profile   guardrails-ai/guardrails · 7,428★ · NVIDIA-NeMo/Guardrails * · 7,160★
                                 standalone up

D2-06   휴먼 승인 게이트           P0   cd agents/d2-06 && docker compose --profile   langchain-ai/langgraph * · 41,863★
                                 standalone up

D2-07   상태·내구성·합성           P1   cd agents/d2-07 && docker compose --profile   temporalio/temporal · 23,144★ · dbos-inc/dbos-transact-py · 1,578★ ·
                                 standalone up                                 hatchet-dev/hatchet · 7,959★




8.4 AG-D3 대화형 어시스턴트
ID      에이전트                P    단독 실행(M1)                                     참고 OSS (실측)

D3-01   채팅 UI·스트리밍          P0   cd agents/d3-01 && docker compose --profile   assistant-ui/assistant-ui · 12,194★ · danny-avila/LibreChat * · 44,255★ ·
                                 standalone up                                 CopilotKit/CopilotKit * · 37,403★

D3-02   세션·히스토리             P0   cd agents/d3-02 && docker compose --profile   open-webui/open-webui * · 152,425★ · danny-avila/LibreChat * · 44,255★
                                 standalone up

D3-03   도구 호출 UX·에이전트 스코프   P0   cd agents/d3-03 && docker compose --profile   CopilotKit/CopilotKit * · 37,403★ · ag-ui-protocol/ag-ui * · 15,934★
        채팅                            standalone up

D3-04   파일·멀티모달 입력               P1   cd agents/d3-04 && docker compose --profile   k2-fsa/sherpa-onnx · 14,834★ · SYSTRAN/faster-whisper · 25,450★ · openai/whisper ·
                                      standalone up                                 109,302★

D3-05   메모리·개인화                  P1   cd agents/d3-05 && docker compose --profile   mem0ai/mem0 * · 65,539★ · letta-ai/letta * · 24,783★ · getzep/graphiti * · 30,975★
                                      standalone up

D3-06   지식(RAG) 연결               P1   cd agents/d3-06 && docker compose --profile   infiniflow/ragflow * · 90,911★ · run-llama/llama_index * · 52,206★ ·
                                      standalone up                                 docling-project/docling * · 66,588★

D3-07   채널·임베드                   P2   cd agents/d3-07 && docker compose --profile   openclaw/openclaw * · 390,029★ · slackapi/bolt-python · 1,326★
                                      standalone up




8.5 AG-D4 애드온 SDK·스캐폴드
ID      에이전트                     P    단독 실행(M1)                                     참고 OSS (실측)

D4-01   에이전트 템플릿 9유형             P0   cd agents/d4-01 && docker compose --profile   WisemanLim/pub-MultiAIAgent-Template · 1★ · langchain-ai/new-langgraph-project ·
                                      standalone up                                 293★ · google/adk-samples * · 10,341★

D4-02   스캐폴드 위저드·CLI             P0   cd agents/d4-02 && docker compose --profile   copier-org/copier · 3,579★ · cookiecutter/cookiecutter · 25,091 ★
                                      standalone up

D4-03   에이전트 SDK                 P0   cd agents/d4-03 && docker compose --profile   fastapi/fastapi * · 102,408★ · PrefectHQ/fastmcp * · 27,717★ · a2aproject/a2a-python ·
                                      standalone up                                 2,147★

D4-04   agent.yaml 스키마·검증기       P0   cd agents/d4-04 && docker compose --profile   modelcontextprotocol/registry · 7,260★ · a2aproject/A2A * · 25,828★ ·
                                      standalone up                                 modelcontextprotocol/mcpb · 2,114★

D4-05   로컬 개발·계약 시험              P1   cd agents/d4-05 && docker compose --profile   modelcontextprotocol/inspector * · 10,904★ · promptfoo/promptfoo · 25,243★
                                      standalone up

D4-06   패키징·서명                   P1   cd agents/d4-06 && docker compose --profile   sigstore/cosign · 6,310★ · anchore/syft · 9,574★ · oras-project/oras · 2,433★
                                      standalone up

D4-07   파생·독립 실행 내보내기            P0   cd agents/d4-07 && docker compose --profile   WisemanLim/pub-MultiAIAgent-Template · 1★
                                      standalone up




8.6 AG-D5 패키지·레지스트리
ID      에이전트                     P    단독 실행(M1)                                     참고 OSS (실측)

D5-01   Zip 업로드                  P0   cd agents/d5-01 && docker compose --profile   WisemanLim/pub-MultiAIAgent-Template · 1★
                                      standalone up

D5-02   구조 검증 게이트                P0   cd agents/d5-02 && docker compose --profile   tobymao/sqlglot · 9,625★ · astral-sh/ruff · 49,676★
                                      standalone up

D5-03   서명·SBOM·취약점 게이트          P1   cd agents/d5-03 && docker compose --profile   sigstore/cosign · 6,310★ · aquasecurity/trivy · 37,969★ · anchore/grype · 12,900★
                                      standalone up

D5-04   라이선스·정책 게이트              P1   cd agents/d5-04 && docker compose --profile   open-policy-agent/opa · 12,245★
                                      standalone up

D5-05   디플로이 모드                  P0   cd agents/d5-05 && docker compose --profile   docker/compose · 38,178★ · WisemanLim/pub-MultiAIAgent-Template · 1★
                                      standalone up

D5-06   카탈로그 DB·capability 인덱스   P0   cd agents/d5-06 && docker compose --profile   modelcontextprotocol/registry · 7,260★
                                      standalone up

D5-07   프론트 통합 파이프라인             P0   cd agents/d5-07 && docker compose --profile   module-federation/core · 2,645★ · single-spa/single-spa · 13,877★
                                      standalone up




8.7 AG-D6 마켓플레이스
ID      에이전트                     P    단독 실행(M1)                                     참고 OSS (실측)

D6-01   스토어 UI                   P0   cd agents/d6-01 && docker compose --profile   Comfy-Org/ComfyUI-Manager · 16,179★ · anthropics/claude-code * · 145,936★
                                      standalone up

D6-02   설치 경로 A 다운로드·설치          P0   cd agents/d6-02 && docker compose --profile   oras-project/oras · 2,433★ · IceWhaleTech/CasaOS · 37,231★
                                      standalone up

D6-03   설치 경로 B 직접 설치            P0   cd agents/d6-03 && docker compose --profile   goharbor/harbor * · 29,401★ · project-zot/zot · 2,773★
                                      standalone up

D6-04   설치 경로 C 연동·연계            P0   cd agents/d6-04 && docker compose --profile   a2aproject/A2A * · 25,828★ · modelcontextprotocol/registry · 7,260★
                                       standalone up

D6-05   구매·라이선스·엔타이틀먼트            P1   cd agents/d6-05 && docker compose --profile   getlago/lago · 10,572★ · polarsource/polar * · 10,271★ · keygen-sh/keygen-api · 1,590★
                                       standalone up

D6-06   퍼블리셔 계정·릴리스               P1   cd agents/d6-06 && docker compose --profile   sigstore/cosign · 6,310★
                                       standalone up

D6-07   업데이트·마켓 서버                P1   cd agents/d6-07 && docker compose --profile   modelcontextprotocol/registry · 7,260★ · docker/mcp-registry · 554★
                                       standalone up




8.8 AG-D7 프로토콜 게이트웨이
ID      에이전트                      P    단독 실행(M1)                                     참고 OSS (실측)

D7-01   에이전트별 MCP 서버              P0   cd agents/d7-01 && docker compose --profile   modelcontextprotocol/python-sdk * · 24,325★ · PrefectHQ/fastmcp * · 27,717 ★ ·
                                       standalone up                                 modelcontextprotocol/inspector * · 10,904★

D7-02   MCP 클라이언트·서버 등록           P0   cd agents/d7-02 && docker compose --profile   modelcontextprotocol/python-sdk * · 24,325★ · modelcontextprotocol/registry · 7,260 ★ ·
                                       standalone up                                 docker/mcp-gateway · 1,571★

D7-03   A2A 서버                    P0   cd agents/d7-03 && docker compose --profile   a2aproject/a2a-python · 2,147★ · a2aproject/A2A * · 25,828★
                                       standalone up

D7-04   A2A 클라이언트                 P0   cd agents/d7-04 && docker compose --profile   a2aproject/a2a-python · 2,147★
                                       standalone up

D7-05   OpenAI 호환 노출·OpenAPI 변환   P1   cd agents/d7-05 && docker compose --profile   agentgateway/agentgateway · 4,900★ · BerriAI/litellm * · 59,036★
                                       standalone up

D7-06   AG-UI 이벤트·ACP 브리지         P1   cd agents/d7-06 && docker compose --profile   ag-ui-protocol/ag-ui * · 15,934★ · agentclientprotocol/agent-client-protocol · 4,273 ★ ·
                                       standalone up                                 agentclientprotocol/claude-agent-acp · 2,540★

D7-07   게이트웨이 정책                  P1   cd agents/d7-07 && docker compose --profile   agentgateway/agentgateway · 4,900★ · traefik/traefik · 64,888★
                                       standalone up




8.9 AG-D8 런타임·컴포즈
ID      에이전트                      P    단독 실행(M1)                                     참고 OSS (실측)

D8-01   에이전트 compose 골격           P0   cd agents/d8-01 && docker compose --profile   docker/compose · 38,178★ · compose-spec/compose-spec · 2,730★
                                       standalone up

D8-02   플랫폼 루트 compose            P0   cd agents/d8-02 && docker compose --profile   docker/compose · 38,178★
                                       standalone up

D8-03   라우팅·TLS                   P0   cd agents/d8-03 && docker compose --profile   traefik/traefik · 64,888★ · caddyserver/caddy * · 75,834★ · WisemanLim/pub-SSL-Cert-
                                       standalone up                                 Manager · 0★

D8-04   격리·샌드박스                   P0   cd agents/d8-04 && docker compose --profile   google/gvisor · 19,345★ · superradcompany/microsandbox * · 8,285★
                                       standalone up

D8-05   GPU·모델 자원                 P0   cd agents/d8-05 && docker compose --profile   ollama/ollama * · 181,183★ · docker/model-runner · 651★
                                       standalone up

D8-06   헬스·업그레이드·롤백·백업            P1   cd agents/d8-06 && docker compose --profile   offen/docker-volume-backup · 4,011★ · restic/restic · 36,105★ · containrrr/watchtower ·
                                       standalone up                                 24,650★

D8-07   오프라인·설치자                  P1   cd agents/d8-07 && docker compose --profile   WisemanLim/pub-Server-Init · 0★ · WisemanLim/pub-wsa-for-sdd · 0★ · project-zot/zot ·
                                       standalone up                                 2,773★




8.10 AG-D9 신원·거버넌스
ID      에이전트                      P    단독 실행(M1)                                     참고 OSS (실측)

D9-01   계정·SSO                    P0   cd agents/d9-01 && docker compose --profile   keycloak/keycloak * · 36,838★ · goauthentik/authentik · 25,604★ · zitadel/zitadel ·
                                       standalone up                                 15,044★

D9-02   역할 기반 권한                  P0   cd agents/d9-02 && docker compose --profile   apache/casbin · 20,395★
                                       standalone up

D9-03   서비스 계정·API 키              P0   cd agents/d9-03 && docker compose --profile   WisemanLim/pub-MultiAIAgent-Template · 1★
                                       standalone up

D9-04   시크릿                       P1   cd agents/d9-04 && docker compose --profile   openbao/openbao · 7,407★ · getsops/sops · 23,148★ · Infisical/infisical · 29,299★
                                       standalone up

D9-05   거버넌스 정책 엔진                P1   cd agents/d9-05 && docker compose --profile   open-policy-agent/opa · 12,245★ · microsoft/agent-governance-toolkit * · 6,282★
                                  standalone up

D9-06    가드레일               P1    cd agents/d9-06 && docker compose --profile    NVIDIA-NeMo/Guardrails * · 7,160★ · guardrails-ai/guardrails · 7,428★ · data-privacy-
                                  standalone up                                  stack/presidio · 10,919★

D9-07    감사 원장              P0    cd agents/d9-07 && docker compose --profile    langfuse/langfuse · 34,746★
                                  standalone up




8.11 AG-D10 콘솔·관측
ID       에이전트               P     단독 실행(M1)                                      참고 OSS (실측)

D10-01   플랫폼 콘솔             P0    cd agents/d10-01 && docker compose --profile   WisemanLim/pub-MultiAIAgent-Template · 1★
                                  standalone up

D10-02   셋업 위저드·온보딩         P0    cd agents/d10-02 && docker compose --profile   WisemanLim/pub-MultiAIAgent-Template · 1★
                                  standalone up

D10-03   OTel 트레이스·메트릭·로그   P0    cd agents/d10-03 && docker compose --profile   open-telemetry/opentelemetry-collector * · 7,565★ · open-telemetry/semantic-
                                  standalone up                                  conventions-genai · 370★ · traceloop/openllmetry · 7,438★

D10-04   LLM 관측 UI          P1    cd agents/d10-04 && docker compose --profile   comet-ml/opik * · 22,104★ · langfuse/langfuse · 34,746★ · grafana/grafana * · 76,792 ★
                                  standalone up

D10-05   평가·시험 표준           P1    cd agents/d10-05 && docker compose --profile   promptfoo/promptfoo · 25,243★ · confident-ai/deepeval * · 18,317★ · WisemanLim/pub-
                                  standalone up                                  wise-dev-std · 0★

D10-06   데이터 모델·마이그레이션      P0    cd agents/d10-06 && docker compose --profile   amacneil/dbmate · 7,391★ · pgvector/pgvector * · 23,046★ · valkey-io/valkey · 27,228★
                                  standalone up

D10-07   알림·상태              P2    cd agents/d10-07 && docker compose --profile   louislam/uptime-kuma · 91,498★ · prometheus/alertmanager · 8,613★
                                  standalone up




8.12 AG-X 후순위
ID       이름                      비고

X01      비주얼 플로우 빌더 Addon        Langflow(MIT) 컨테이너. 플로우→Addon Agent 내보내기
X02      이미지·비디오 생성 Addon        ComfyUI GPL-3.0 격리 컨테이너, API 호출. SD WebUI 는 대체
X03      음성 Addon                faster-whisper STT, sherpa-onnx/piper TTS
X04      자동화 연계                  n8n Sustainable Use → 웹훅·MCP 연계만
X05      코드 실행 샌드박스 Agent        execution 유형. microsandbox/E2B/gVisor
X06      브라우저 에이전트               browser-use + Playwright
X07      RAG 엔진 연계               RAGFlow Apache-2.0 컨테이너
X08      파인튠·로컬 학습               Transformers·PyTorch. LLMForge PRD 참조
X09      멀티테넌시                   조직·워크스페이스 격리(v1 out-of-scope 유지)
X10      쿠버네티스 배포                kompose·Helm·kagent. compose 가 1차
X11      데스크톱·모바일 셸              Tauri. 콘솔 PWA 우선
X12      상거래 정산·세금               마켓 결제 고도화. 법무 검토




8.13 AG-P 플랫폼 공유 서비스
ID       이름                 역할

P01      리버스 프록시            Traefik. 라벨 라우팅·TLS·미들웨어
P02      에이전트 레지스트리         D5-06 카탈로그 API. server.json·Agent Card 발행
P03      이벤트 버스             Valkey Streams. 도구·승인·상태 이벤트
P04      공유 Postgres        플랫폼 스키마 + 선택 Addon 스키마. pgvector
P05      공유 Valkey          세션·캐시·큐·이벤트 스트림. Redis 8 3중 라이선스 회피(BSD-3)
P06      OTel 컬렉터           트레이스·메트릭·로그 수집·내보내기
P07      신원 제공자             Keycloak(선택 프로파일). 로컬 JWT 기본
 P08     시크릿 저장소             OpenBao(선택). compose secrets 기본
 P09     마켓 서버               D6-07. 셀프호스팅 레지스트리·아티팩트
 P10     빌드 서비스              zip→이미지 빌드(BuildKit), 프론트 통합 빌드
 P11     작업 실행기              장기 작업·스케줄. Temporal 선택
 P12     plaza CLI           init·test·publish·install·up·export




8.14 수량과 v1 대비
도메인 70 + 후순위 12 + 플랫폼 12 = 94 종. v1 은 내장 2종(general/chat) + 템플릿 4종 + 플랫폼 기능 32개(F1~F32)를 한 FastAPI 프
로세스에 두었다. AgentPlaza 는 같은 기능을 70개 독립 단위로 나누되, 첫 릴리스(P0 41종)는 v1 이 이미 증명한 범위에서 시작한다.
 우선순위                항목 수   구성
 P0                  43     v1 승계 + 컨테이너 모드 + 마켓 설치 3경로 + MCP/A2A 정식 SDK
 P1                  25     게이트웨이 정책, 서명·SBOM, 구매, SSO, 관측 UI, 내구성
 P2                  2      채널, 알림
 X                   12     Addon·연계로만 구현
9. 기술 스택 — 실측 기반 선정
2026-09-18 GitHub REST API 로 361개 저장소를 실측했다(스타·라이선스·아카이브·최신 커밋·최신 릴리스). 선정 기준: (1) 저장소 주소
실측, (2) 기본값은 OSI 허용 라이선스(Apache-2.0·MIT·BSD·ISC·MPL·PostgreSQL), (3) GPL 은 별 컨테이너, (4)
G4(AGPL·SSPL·BUSL·SUL·Polyform·브랜딩 조건)는 연계만, (5) 아카이브·정체는 대체 명시, (6) 사용자 스타 목록 교차(*). 표의 수치는
repos.tsv 에서 렌더된다.

9.1 결정 요약
 영역                   1순위                                                     대체                                                 결정 근거

 로컬 LLM(개발·맥)         ollama/ollama * · 181,183★                              ggml-org/llama.cpp * · 128,619★                    OpenAI+Anthropic 호환 동시 제공, Metal, 모델 관리 내장

 로컬 LLM(GPU 운영)       vllm-project/vllm * · 92,055★                           sgl-project/sglang * · 36,116★                     처리량·구조화 출력·/v1/messages 네이티브

 임베딩·리랭크              huggingface/text-embeddings-inference · 5,052★          michaelfeil/infinity · 2,942★                      Metal 지원, 리랭크 포함

 LLM 게이트웨이            BerriAI/litellm * · 59,036★                             maximhq/bifrost * · 8,147★                         기능 폭·MCP·Anthropic 수신. enterprise/ 는 유료 → 경계 검증. 마찰 시
                                                                                                                                 Bifrost(전부 Apache-2.0) 승격

 Orchestrator 엔진      langchain-ai/langgraph * · 41,863★                      microsoft/agent-framework · 13,571★                그래프·체크포인터·interrupt(HITL). 라이브러리만(langgraph-api 는
                                                                                                                                 Elastic-2.0)

 Assistant 에이전트 SDK   openai/openai-agents-python * · 29,531★                 pydantic/pydantic-ai * · 20,021★                   핸드오프·가드레일·세션. pydantic-ai 는 durable_exec+ag_ui 통합

 워커·코딩 에이전트           langchain-ai/deepagents * · 29,534★                     anthropics/claude-agent-sdk-python · 8,124★        planner+subagent, 승인·편집·거부 1급

 내구성 엔진               LangGraph 체크포인터 → temporalio/temporal ·                 dbos-inc/dbos-transact-py · 1,578★ ·               전부 MIT. Inngest SSPL·Restate BUSL 회피
                      23,144★                                                 hatchet-dev/hatchet · 7,959★

 프론트(Assistant)       assistant-ui/assistant-ui · 12,194★                     danny-avila/LibreChat * · 44,255★                  헤드리스·MIT·react-ag-ui·도구 승인 UI 1급. 완제품 포크 금지

 백엔드                  fastapi/fastapi * · 102,408★                            honojs/hono * · 32,258★                            OpenAPI 자동생성 = 도구 카탈로그. v1 승계

 DB                   postgres/postgres * · 22,130★ + pgvector/pgvector * ·   sqlite/sqlite · 10,500★                            관계형+벡터+JSONB 단일 엔진. 격리는 스키마·역할
                      23,046★

 캐시·큐·이벤트             valkey-io/valkey · 27,228★                              -                                                  BSD-3. Redis 8 은 RSALv2/SSPLv1/AGPLv3 3중

 마이그레이션               amacneil/dbmate · 7,391★                                ariga/atlas · 8,729★(검증)                           순수 SQL·언어 무관. Python 개발은 alembic autogenerate 후 dbmate 형
                                                                                                                                 식
 MCP SDK              modelcontextprotocol/python-sdk * · 24,325★             PrefectHQ/fastmcp * · 27,717★                      사양 2026-07-28. fastapi_mcp 는 정체(비권장)

 A2A SDK              a2aproject/a2a-python · 2,147★                          google/adk-python · 21,568★                        v1.0.1. pydantic-ai to_a2a 제거됨

 프로토콜 게이트웨이           agentgateway/agentgateway · 4,900★                      IBM/mcp-context-forge · 4,489★                     MCP+A2A+LLM 단일 데이터플레인, Mcp-Method 헤더 RBAC

 리버스 프록시              traefik/traefik · 64,888★                               caddyserver/caddy * · 75,834★                      라벨 라우팅, exposedByDefault=false, ACME

 UI 인증 게이트            authelia/authelia · 29,006★                             oauth2-proxy/oauth2-proxy · 14,968★                forwardAuth. IdP 는 Keycloak

 IdP(SSO)             keycloak/keycloak * · 36,838★                           goauthentik/authentik · 25,604★                    Apache-2.0, Token Exchange(aud=agent:{id}). Zitadel 은 AGPL

 시크릿                  getsops/sops · 23,148★ + compose secrets                openbao/openbao · 7,407★                           HKDF 파생 + 암호화. Infisical 은 ee/ 분리

 패키지 배포               oras-project/oras · 2,433★ + project-zot/zot · 2,773★   goharbor/harbor * · 29,401★                        OCI 아티팩트 + referrers(서명·SBOM)

 서명·SBOM·스캔           sigstore/cosign · 6,310★ · anchore/syft · 9,574★ ·      anchore/grype · 12,900★ · snyk/agent-scan ·        keyless 서명, CycloneDX, Critical 차단, MCP 툴 포이즈닝 스캔
                      aquasecurity/trivy · 37,969★                            3,060★

 샌드박스                 google/gvisor · 19,345★                                 kata-containers/kata-containers · 8,742★ ·         runtime: runsc 한 줄. 신뢰등급 연동. Daytona 는 AGPL+중단
                                                                              firecracker-microvm/firecracker · 36,802★

 스캐폴드                 copier-org/copier · 3,579★                              cookiecutter/cookiecutter · 25,091★                update 재템플릿 지원. cookiecutter 2026-04 이후 정체

 관측 계약                open-telemetry/opentelemetry-collector * · 7,565★ +     traceloop/openllmetry · 7,438★                     OTLP 단일 계약. 백엔드 교체 가능
                      open-telemetry/semantic-conventions-genai · 370★

 관측 백엔드               comet-ml/opik * · 22,104★                               langfuse/langfuse · 34,746★ · SigNoz/signoz ·      Apache-2.0. Langfuse 코어 MIT(저작권 ClickHouse). Phoenix ELv2·Grafana
                                                                              32,120★                                            AGPL 은 내부 전용

 평가                   promptfoo/promptfoo · 25,243★ · confident-ai/deepeval   vibrantlabsai/ragas · 15,763★                      CI 레드팀 + pytest. ragas 는 2026-02 이후 정체
                      * · 18,317★

 가드레일                 NVIDIA-NeMo/Guardrails * · 7,160★                       guardrails-ai/guardrails · 7,428★                  Apache-2.0. llm-guard 아카이브

 메모리                  mem0ai/mem0 * · 65,539★                                 letta-ai/letta * · 24,783★ · getzep/graphiti * ·   Apache-2.0, pgvector 백엔드
                                                                              30,975★

 문서 파싱·RAG            docling-project/docling * · 66,588★ ·                   infiniflow/ragflow * · 90,911★(완제품 Addon)          MIT/Apache-2.0
                      run-llama/llama_index * · 52,206★

 음성                   k2-fsa/sherpa-onnx · 14,834★                            SYSTRAN/faster-whisper · 25,450★                   STT+TTS+VAD 통합, Apache-2.0. fish-speech 비상용, piper1-gpl GPL

 백업                   offen/docker-volume-backup · 4,011★ → restic/restic ·   -                                                  라벨 기반 정합성 백업 + 중복제거 암호화
                      36,105★

 이미지 갱신               renovatebot/renovate · 22,528★                          nicholas-fedor/watchtower · 4,461★                 PR 방식. containrrr/watchtower 아카이브
 상거래                                  killbill/killbill · 5,737★                                      getlago/lago · 10,572★(AGPL) · polarsource/polar      Apache-2.0. 라이선스 키는 Ed25519 자체 구현(keygen-api 는 FCL)
                                                                                                      * · 10,271★

 기능 플래그·엔타이틀먼트                        open-feature/spec · 1,258★ 인터페이스                                Unleash/unleash · 13,813★(AGPL)                       자체 구현 백엔드 권장




9.2 D1 LLM 공급
조사한 서버형 로컬 런타임 전부가 OpenAI /v1/chat/completions 를 구현한다(예외 0). 그리고
Ollama·llama.cpp·vLLM·SGLang·LMDeploy·LocalAI·exo·textgen·TensorRT-LLM 이 Anthropic /v1/messages 를 네이티브로 제공한다. 동기
는 하나다 — Claude Code·Claude Agent SDK 를 로컬 모델에 그대로 붙이기 위해서다. 따라서 v1 의 Anthropic SDK 코드는 base_url 만 바
꾸면 로컬에서 돈다.
 런타임 실측                                                                     OpenAI 호환                      Anthropic 호환                       포맷                  Apple Silicon     판정

 ollama/ollama * · 181,183★ · MIT                                           O                              O                                  GGUF                O                 개발·맥·경량 1순위

 ggml-org/llama.cpp * · 128,619★ · MIT                                      O(+/v1/responses,              O                                  GGUF                O                 저수준 제어. Ollama 기반
                                                                            /reranking)

 vllm-project/vllm * · 92,055★ · Apache-2.0                                 O                              O(/v1/messages,                    safetensors         X                 GPU 운영 1순위
                                                                                                           count_tokens)

 sgl-project/sglang * · 36,116★ · Apache-2.0                                O                              O(기본 활성)                           safetensors         X                 프리픽스 캐시. CUDA 13 요구

 mudler/LocalAI · 49,147★ · MIT                                             O                              O(3.10+)                           다중                  O                 올인원(텍스트·이미지·음성). 루트 compose
                                                                                                                                                                                    실존
 InternLM/lmdeploy · 8,079★ · Apache-2.0                                    O                              O                                  TurboMind           X                 대체

 NVIDIA/TensorRT-LLM · 14,641★ · Apache-2.0                                 O                              O                                  TRT 엔진              X                 NVIDIA 극한 최적화만

 huggingface/transformers * · 166,261★ · Apache-2.0                         O(transformers serve)          X                                  safetensors         O(MPS)            라이브러리. 인포그래픽 04

 ml-explore/mlx-lm * · 7,043★ · MIT                                         O                              X                                  MLX                 O(전용)             맥 네이티브 브리지 후보

 janhq/jan * · 44,516★ · Apache-2.0 계열 (Menlo Research,                     O                              [미확인]                              GGUF                O                 데스크톱 앱 중심
 LICENSE 본문 확인)

 mozilla-ai/llamafile * · 25,986★ · Apache-2.0                              O                              [미확인]                              GGUF                O                 구 Mozilla-Ocho 경로 이전. 단일 실행파일

 huggingface/text-generation-inference · 10,886★ · Apache-2.0 [아            O                              X                                  safetensors         X                 아카이브 — 채택 금지
 카이브]

 oobabooga/textgen · 47,683★ · AGPL-3.0                                     O                              O                                  다중                  O                 AGPL-3.0 — 채택 금지. 구 text-generation-
                                                                                                                                                                                    webui 이전

 exo-explore/exo * · 47,490★ · Apache-2.0                                   O                              O                                  MLX 등               O                 정체. 배제




 오픈 가중치 모델                                                         가중치 라이선스                                                                     상용                     AgentPlaza 카탈로그 기본값

 Qwen3 (QwenLM/Qwen3 · 27,637★)                                    Apache-2.0 (HF 모델 카드. 저장소 LICENSE 없음)                                        가능                     기본 범용·한국어

 DeepSeek-V3 (deepseek-ai/DeepSeek-V3 * ·                          코드 MIT / 가중치 DEEPSEEK LICENSE(상용 명시 허용)                                      가능(제한 승계)              허용
 104,464★)

 DeepSeek-V3.1 · R1 (deepseek-ai/DeepSeek-R1 * ·                   MIT(가중치 포함)                                                                  가능                     기본 추론. R1-Distill-Llama 는 Llama 승계 → 비권장
 91,980★)

 gpt-oss (openai/gpt-oss · 20,407★)                                Apache-2.0                                                                   가능                     허용(harmony 포맷 전제)

 Phi-4                                                             MIT (HF 배포, GitHub 저장소 없음)                                                   가능                     경량

 Gemma 3 (google-deepmind/gemma · 5,737★ 코                         Gemma Terms(약관 승계·원격 제한)                                                     조건부                    conditional → 기본 비활성
 드)

 Llama 4 (meta-llama/llama-models · 7,692★)                        Llama 4 Community(Built with Llama 표기, 파생 'Llama' 접두, MAU 7                  조건부                    conditional → 기본 비활성
                                                                   억)

 Mistral                                                           모델별 상이(Small 3.2 Apache-2.0 / Large 2411 MRL 비상용)                            모델별                    벤더가 아닌 모델 단위 추적

 EXAONE 4.0 (LG)                                                   EXAONE AI Model License 1.2 – NC                                             불가                     prohibited




규칙. 카탈로그 license 는 열거형, commercial_use: allowed|conditional|prohibited 는 별도 필수 필드.
conditional 은 관리자 승인 플래그로만 활성. verified_at 180일 경과 시 CI 경고(DeepSeek-V3→V3.1 에서 실제 MIT 로 바뀐 사례).
 퍼블릭·CLI 백엔드 실측                                                             헤드리스                    스트리밍 이벤트                              구조화 출력                  MCP 주입              ACP

 anthropics/claude-code * · 145,936★ · Anthropic Commercial                 claude -p               --output-format stream-json           --json-schema           --mcp-config        미확인(claude-agent-acp 어댑터)
 Terms (LICENSE.md, 소스 비공개)                                                                         (NDJSON)

 anthropics/claude-agent-sdk-python · 8,124★ · MIT                          SDK                     네이티브                                  O                       O + in-process      -
                                                                                                                                                                    MCP

 openai/codex * · 124,973★ · Apache-2.0                                 codex exec                --json (JSONL)                          --output-schema           O                     codex-acp 어댑터

 google-gemini/gemini-cli * · 107,051★ · Apache-2.0                     -p / non-TTY              --output-format                         O                         O                     O (gemini --acp)

 anomalyco/opencode * · 208,244★ · MIT                                  O                         ACP 이벤트                                 [미확인]                     O                     O 네이티브. 구 sst/opencode 이전.
                                                                                                                                                                                          opencode-ai/opencode 는 아카이브

 openclaw/openclaw * · 390,029★ · MIT (OpenClaw Foundation)             Gateway/CLI               Gateway 이벤트                             [미확인]                     O                     미확인

 agentclientprotocol/agent-client-protocol · 4,273★ · Apache-2.0        -                         -                                       -                         -                     프로토콜 v1. 원격 전송은 WIP → 1차
                                                                                                                                                                                          NDJSON 어댑터, 2차 ACP




 게이트웨이 실측                                               Anthropic           예산·가상키                캐시                가드레일            MCP                 compose 동봉            판정
                                                        수신
 BerriAI/litellm * · 59,036★ · MIT (enterprise/ 디렉      O                   O                     O                 O               O(광범위)              O(루트 +                1순위. enterprise/ 프로덕션 사용은 유료 — 공식 이
 터리 별도 라이선스)                                                                                                                                            hardened)             미지 포함 여부 [미확인] → 법무 확인

 maximhq/bifrost * · 8,147★ · Apache-2.0                O                   O(계층형)                O(semantic)       O               O                   O                     대체 1. 전부 Apache-2.0

 Portkey-AI/gateway * · 13,028★ · MIT                   O                   [미확인]                 O(semantic)       O(50+)          O                   O                     대체 2. 2026-05 이후 커밋 없음

 katanemo/plano * · 7,055★ · Apache-2.0                 O                   [미확인]                 [미확인]             O               O                   O                     구 archgw 이전. 의미기반 라우팅

 tensorzero/tensorzero * · 11,720★ · Apache-2.0         -                   -                     -                 -               -                   -                     아카이브(2026-06) 채택 금지
 [아카이브]

 theagentrouter/agent-router · 2,116★ · Apache-2.0      [미확인]               O                     [미확인]             [미확인]           O                   O                     구 Envoy AI Gateway. K8s 전제

 higress-group/higress · 9,400★ · Apache-2.0 ·          [미확인]               -                     -                 O               O                   -                     기존 API GW 운영 시
 Kong/kong · 44,148★




임베딩·리랭크: huggingface/text-embeddings-inference · 5,052★ · Apache-2.0 1순위, michaelfeil/infinity · 2,942★ · MIT 는 멀티모달
(CLIP·ColPali) 시. infiniflow/infinity · 4,708★ 는 리랭크 서버가 아니라 벡터 DB 다. 리랭크는 OpenAI 표준이 없어 내부 규격 POST
/v1/rerank(Cohere/Jina 계열 스키마)로 TEI /rerank 와 llama.cpp /reranking 을 흡수한다.


9.3 D2 오케스트레이션
 프레임워크 실측                                                     패턴                                            MCP              A2A                        HITL              내구성                           판정

 langchain-ai/langgraph * · 41,863★ · MIT                     graph·supervisor·handoff·fan-out·loop         △(adapters)      -                          O interrupt       O checkpoint sqlite/pg        Orchestrator 1순위. 라
                                                                                                                                                                                                        이브러리만(langgraph-
                                                                                                                                                                                                        api ELv2)

 microsoft/agent-framework · 13,571★ · MIT                    sequential·concurrent·handoff·group·gr        O                O(hosting)                 O                 O time-travel                 대체 1. AutoGen+SK 승계
                                                              aph

 google/adk-python · 21,568★ · Apache-2.0                     workflow·sequential/parallel/loop             O                O 서버+클라이언트                 O                 △ sessions                    A2A 상호운용 후보

 openai/openai-agents-python * · 29,531★ · MIT                handoff·agent-as-tool·guardrail               O                -                          O                 △ run_state                   Assistant 1순위

 pydantic/pydantic-ai * · 20,021★ · MIT                       graph·delegation·toolsets                     O                fasta2a 별도(to_a2a          O                 O                             Assistant 대체
                                                                                                                             제거)                                          durable_exec(temporal·
                                                                                                                                                                          dbos·prefect) +
                                                                                                                                                                          ui/ag_ui

 langchain-ai/deepagents * · 29,534★ · MIT                    planner+subagent                              O                -                          O 승인·편집·거         O(LangGraph)                  워커 1순위
                                                                                                                                                        부
 crewAIInc/crewAI * · 58,715★ · MIT                           sequential·hierarchical·Flows                 O                △                          △                 △                             역할 기반 어댑터(인포그
                                                                                                                                                                                                        래픽 06)

 agno-agi/agno * · 42,227★ · Apache-2.0                       팀·워크플로                                        O                O(A2A·AG-UI)               △                 O(Postgres)                   참조 아키텍처

 mastra-ai/mastra * · 28,147★ · Apache-2.0 (ee/ 별도 상          graph 워크플로·네트워크                               O                △                          O                 O storage                     TS 단일 스택 시(ee/ 주의)
 용)                                                                                                                                                     suspend/resum
                                                                                                                                                        e

 huggingface/smolagents · 29,376★ · Apache-2.0                CodeAgent 루프                                  O                -                          △                 -                             워커 대체

 letta-ai/letta * · 24,783★ · Apache-2.0                      스테이트풀                                         O                △                          △                 O                             장기 메모리(D3-05)

 2FastLabs/agent-squad * · 7,765★ · Apache-2.0                classifier 라우팅                                O                -                          -                 △                             구 awslabs 이전. 라우팅
                                                                                                                                                                                                        참고
 strands-agents/harness-sdk * · 7,342★ · Apache-2.0           multi-agent patterns                          O                -                          △                 O                             구 sdk-python 이전

 microsoft/autogen * · 61,035★ · CC-BY-4.0 (코드에 부             group chat·swarm                              O                -                          △                 △                             유지보수 모드 + CC-
 적합) · 유지보수 모드                                                                                                                                                                                          BY-4.0 채택 금지

 microsoft/semantic-kernel · 28,572★ · MIT                    플래너                                           O                O                          △                 △                             MAF 로 승계 고지

 FoundationAgents/MetaGPT * · 70,484★ · MIT                   SOP 파이프라인                                     △                -                          △                 △                             8개월 정체. 비권고
내구성 엔진 실측                                                                           라이선스 판정                                                   적합성
temporalio/temporal · 23,144★ · MIT                                                 MIT                                                       최적. 장기 실행·승인 대기·SLA

hatchet-dev/hatchet · 7,959★ · MIT                                                  MIT                                                       매우 적합

dbos-inc/dbos-transact-py · 1,578★ · MIT                                            MIT                                                       매우 적합(경량, Postgres 만)

PrefectHQ/prefect · 23,859★ · Apache-2.0                                            Apache-2.0                                                조건부

inngest/inngest · 5,842★ · SSPL-1.0 + Apache-2.0 Future License                     SSPL + Apache Future                                      라이선스 주의 → 회피

restatedev/restate · 4,438★ · BUSL-1.1 (내부 배포 허용, 공개 Restate 서                      BUSL-1.1(내부 배포 허용)                                        조건 확인 필요
비스 금지)

windmill-labs/windmill · 17,958★ · AGPL-3.0 + Apache-2.0 혼합 + EE 독                  AGPL 기본                                                   조건부
점
apache/airflow * · 46,885★ · Apache-2.0                                             Apache-2.0                                                부적합(배치 DAG 지향)




9.4 D3 어시스턴트 — 프론트·백엔드·DB·공통 서비스
프론트 실측                                                                 라이선스 판정                                            도구 승인 UI                  i18n ko       판정

assistant-ui/assistant-ui · 12,194★ · MIT                              MIT                                                O(makeAssistantToolUI)    우리 통제         1순위. react-ag-ui 패키지

danny-avila/LibreChat * · 44,255★ · MIT                                MIT                                                △                         O(44 로케일)     2순위 헤지. Mongo 의존 → Addon 격리 포장

CopilotKit/CopilotKit * · 37,403★ · MIT                                MIT                                                O                         -             AG-UI 주도. 런타임 동반

vercel/ai · 26,819★ · Apache-2.0 · vercel/chatbot * · 20,955★          Apache-2.0                                         -                         -             모델 추상화 SDK / 골격 레퍼런스(구 ai-chatbot 이전,
                                                                                                                                                                  2026-07 정체)

langchain-ai/agent-chat-ui * · 3,162★ · MIT                            MIT                                                O(인터럽트 승인)                -             레퍼런스

Chainlit/chainlit * · 12,457★ · Apache-2.0                             Apache-2.0                                         O                         -             Python 내부 도구용

open-webui/open-webui * · 152,425★ · Open WebUI License                Open WebUI License — 브랜딩 변경 시 30일 50               △                         O(65)         채택 보류. 기능 기준선·Pipelines 규격만 참고
(BSD-3 기반 + 브랜딩 조건)                                                    사용자 상한

lobehub/lobehub · 82,576★ · LobeHub Community License                  LobeHub Community License                          △                         O             구 lobe-chat 이전. 불채택
(Apache-2.0 기반 + 추가 조건)

Mintplex-Labs/anything-llm * · 66,156★ · MIT                           MIT                                                △                         -             워크스페이스=에이전트 격리 모델 참고

khoj-ai/khoj * · 37,399★ · AGPL-3.0                                    AGPL-3.0                                           -                         -             불채택

mckaywrigley/chatbot-ui · 33,352★ · MIT                                MIT                                                -                         -             2024-06 정체

nlkitai/nlux · 1,380★ · MPL-2.0 + AI 학습·코드번역 제한 조항                     MPL 변형                                             -                         -             구 nlux-ai 이전. 정체
(비OSI 변형)




마이크로프론트 실측                                                                                 판정
iframe + postMessage                                                                       기본. 격리·이종 스택·크래시 차단. 규약 v1 12종 메시지(ready/auth/context/resize/navigate/notify/modal/telemetry/error)

module-federation/core · 2,645★ · MIT                                                      선택. 1st-party·React 동일 메이저·iframe 폴백 구현 시만

lit/lit · 21,825★ · BSD-3-Clause                                                           보조. 배지·미니 위젯

single-spa/single-spa · 13,877★ · MIT · umijs/qiankun · 16,686★                            불채택(정체·불완전 격리)

withastro/astro · 62,655★ · MIT                                                            불채택(문제 영역 불일치)




백엔드·서빙 실측                                                                                  판정

fastapi/fastapi * · 102,408★ · MIT                                                         1순위. OpenAPI = 도구 카탈로그. sse-starlette

honojs/hono * · 32,258★ · MIT                                                              경량 TS Addon(streamSSE 내장)

nestjs/nest · 76,683★ · MIT                                                                대규모 Node Addon

langchain-ai/langserve · 2,329★ · LangServe License (독자, 비OSI) [아카이브] [아                   아카이브 + 독자 LangServe License — 사용 금지
카이브]

langgraph-api (PyPI, langgraph-cli[inmem])                                                 Elastic-2.0 — MIT 저장소에 소스 없음. langgraph dev·Platform 미의존. langgraph + checkpoint-postgres 만 임포트

Kludex/starlette · 12,619★ · BSD-3-Clause                                                  구 encode/starlette 이전(1.6.0)

celery/celery · 28,898★ · BSD-3-Clause · taskiq · BullMQ                                   큐. Python 은 taskiq(MIT)+valkey, Node 는 BullMQ




DB·저장 실측                                                                                           라이선스 판정                                              역할

postgres/postgres * · 22,130★ · PostgreSQL License + pgvector/pgvector * · 23,046 ★ ·              PostgreSQL License                                   1순위 관계형+벡터
PostgreSQL License

sqlite/sqlite · 10,500★ · Public Domain · asg017/sqlite-vec · 8,115★                               Public Domain / Apache-2.0(pre-1.0)                  개발·M1·소형 Addon
 valkey-io/valkey · 27,228★ · BSD-3-Clause                                                              BSD-3                                                   캐시·큐·스트림

 redis/redis · 76,398★ · RSALv2 OR SSPLv1 OR AGPLv3 (8.0+, 3중) / 7.2 이하 BSD-3                           RSALv2/SSPLv1/AGPLv3 3중(8.0+)                           회피

 qdrant/qdrant * · 34,650★ · Apache-2.0 · lancedb/lancedb · 11,451★                                     Apache-2.0                                              벡터 수억 건 초과 시 분리 / 임베디드

 weaviate/weaviate · 16,819★ · BSD-3-Clause (wl/ 디렉터리만 Weaviate License) ·                              BSD-3(wl/ 제외) / Apache-2.0                              대체
 milvus-io/milvus * · 46,153★ · chroma-core/chroma * · 29,320★

 supabase/supabase * · 109,931★ · Apache-2.0                                                            Apache-2.0                                              스키마·역할·RLS 격리 패턴 참조(도입 아님)

 amacneil/dbmate · 7,391★ · MIT · golang-migrate/migrate · 18,929★                                      MIT                                                     플랫폼 마이그레이션 계약 / 대체

 ariga/atlas · 8,729★ · Apache-2.0 · sqlalchemy/alembic · 4,400★ · drizzle-team/drizzle-orm * ·         Apache-2.0 / MIT / Apache-2.0                           드리프트 검증 / Python·TS 개발 편의(prisma 는 구 prisma/prisma 이
 35,803★ · prisma/orm · 47,618★                                                                                                                                 전)




 공통 서비스 실측                                                                                                                   판정
 keycloak/keycloak * · 36,838★ · Apache-2.0                                                                                  IdP 1순위. Token Exchange

 goauthentik/authentik · 25,604★ · MIT (authentik/enterprise/ 별도, website/ CC) · ory/kratos · 13,880★ · better-              대체. authentik enterprise/ 별도. Zitadel 은 AGPL
 auth/better-auth · 29,992★ · supertokens/supertokens-core · 15,312★

 mem0ai/mem0 * · 65,539★ · Apache-2.0 · letta-ai/letta * · 24,783★ · getzep/graphiti * · 30,975★ ·                           메모리. 전부 Apache-2.0
 topoteretes/cognee * · 30,794★

 docling-project/docling * · 66,588★ · MIT · run-llama/llama_index * · 52,206 ★ · deepset-ai/haystack · 26,534 ★ ·           문서 파싱·RAG 라이브러리
 Unstructured-IO/unstructured · 15,445★

 comet-ml/opik * · 22,104★ · Apache-2.0 · langfuse/langfuse · 34,746★ · SigNoz/signoz · 32,120★ · openlit/openlit            관측 백엔드. Phoenix(ELv2)·Grafana/Loki/Tempo(AGPL)는 내부 전용
 · 2,770★

 promptfoo/promptfoo · 25,243★ · MIT · confident-ai/deepeval * · 18,317★ · vibrantlabsai/ragas · 15,763 ★                    평가. ragas 는 구 explodinggradients 이전·정체

 NVIDIA-NeMo/Guardrails * · 7,160★ · Apache-2.0 (SPDX 헤더) · guardrails-ai/guardrails · 7,428★ · data-privacy-                가드레일·PII. NeMo 는 구 NVIDIA/NeMo-Guardrails 이전. protectai/llm-guard 아카이브
 stack/presidio · 10,919★

 k2-fsa/sherpa-onnx · 14,834★ · Apache-2.0 · SYSTRAN/faster-whisper · 25,450★ · idiap/coqui-ai-TTS · 2,321 ★                 음성. coqui-ai/TTS 사망→idiap 계승(MPL-2.0). rhasspy/piper 아카이브→OHF-Voice/piper1-gpl(GPL). fish-
                                                                                                                             speech 비상용




9.5 D4·D5·D6 패키징·레지스트리·마켓
Zip + 루트 매니페스트 패턴이 사실상 표준이다(Dify .difypkg, MCPB .mcpb, WordPress, Grafana). 매니페스트는 신원·실행·권한 3계층으
로 수렴한다. 마켓 서버가 오픈소스인 사례는 드물다 — ClawHub(MIT)와 MCP Registry(Apache 계열)가 유일한 본격 사례다.
 플러그인 규격 선례 실측                                                배포 포맷                    매니페스트                                 권한 선언                       서명                     마켓 서버       채택
                                                                                                                                                                                OSS

 langgenius/dify-plugin-daemon · 459★ · Apache-2.0            .difypkg(zip)            manifest.yaml                         resource.permission         RSA-4096 zip comment   X           권한 선언 구조 참고

 modelcontextprotocol/mcpb · 2,114★ · MIT → Apache-2.0        .mcpb(zip)               manifest.json                         user_config(+sensitive)     X.509 체인               -           user_config 스키마 차용. 구
 전환 진행 중                                                                                                                                                                                    anthropics/mcpb 이전

 modelcontextprotocol/registry · 7,260★ · MIT →               npm·pypi·oci·mcpb        server.json(2025-12-11)               environmentVariables.isSe   네임스페이스 소유권             O           그대로 채택(oci 1급)
 Apache-2.0 전환 진행 중                                                                                                          cret

 openclaw/clawhub · 9,422★ · MIT                              .tgz                     CLAW.md(YAML+MD)                      agent.tools, requires.env   SHA-256 사전 제시 +        O(MIT)      유료 마켓 서버 참조. 발행 거부 10
                                                                                                                                                         자동 감사                              사유 = 검증 체크리스트

 anthropics/claude-code * · 145,936★ · Anthropic              git 저장소                  .claude-plugin/plugin.json +          경로 제약                       ref+sha 핀              불필요(정적)     무료·사내 카탈로그 = git + JSON
 Commercial Terms (LICENSE.md, 소스 비공개) 플러그인 ·                                          marketplace.json
 anthropics/claude-plugins-official * · 36,447★

 google-gemini/gemini-cli * · 107,051★ · Apache-2.0 확장        git/로컬                   gemini-extension.json                 envVar allowlist,           --ref 고정               X           참고
                                                                                                                             excludeTools

 Comfy-Org/ComfyUI-Manager · 16,179★ · GPL-3.0                git/zip                  pyproject [tool.comfy]                ruff 정적 검사만                 X                      정적 카탈로      채널 카탈로그 참고. 구 ltdrdata 이
                                                                                                                                                                                그           전. GPL-3.0

 n8n-io/n8n * · 205,085★ · Sustainable Use License (.ee 파     npm                      package.json n8n                      verified/unverified         npm                    X           신뢰 등급 개념만
 일은 Enterprise) 커뮤니티 노드

 open-webui/pipelines * · 2,435★ · MIT                        파일 드롭                    docstring                             없음                          없음                     -           불채택(격리 부재)

 hacs/integration · 7,719★ · MIT · WordPress ·                zip                      hacs.json / plugin.json+MANIFEST      -                           PGP(Grafana)           정적          zip 업로드 UX·rootUrls 개념
 grafana/plugin-tools · 89★

 backstage/backstage · 34,433★ · Apache-2.0                   npm 빌드타임                 package.json                          -                           npm                    -           부정적 선례(클릭 설치 불가)




 배포·서명·샌드박스·상거래 실측                                                                                                                    판정

 oras-project/oras · 2,433★ · Apache-2.0 · project-zot/zot · 2,773★ · goharbor/harbor * · 29,401★ · distribution/distribution ·       OCI 아티팩트 배포. zot 은 폐쇄망 미러
 10,614★

 sigstore/cosign · 6,310★ · Apache-2.0 · slsa-framework/slsa-verifier · 344 ★ · in-toto/attestation · 373 ★                           keyless 서명·증명
 anchore/syft · 9,574★ · Apache-2.0 · anchore/grype · 12,900★ · aquasecurity/trivy · 37,969★                                    SBOM(CycloneDX)·취약점·라이선스 스캔

 copier-org/copier · 3,579★ · MIT · cookiecutter/cookiecutter · 25,091★                                                         스캐폴드. copier 만 update 지원

 google/gvisor · 19,345★ · Apache-2.0 · kata-containers/kata-containers · 8,742★ · firecracker-microvm/firecracker ·            격리. gVisor 는 runtime: runsc 한 줄. microsandbox 는 구 경로 이전. E2B 는 코드 실행 특화
 36,802★ · superradcompany/microsandbox * · 8,285★ · e2b-dev/E2B * · 13,864★

 daytonaio/daytona * · 71,721★ · AGPL-3.0 · 2026-06 유지보수 중단 선언 (SPDX none)                                                      2026-06 유지보수 중단 + AGPL — 비권장

 bytecodealliance/wasmtime * · 18,643★ · Apache-2.0 · wasmCloud/wasmCloud · 2,437★                                              장기 옵션(풀스택 에이전트에는 제약)

 killbill/killbill · 5,737★ · Apache-2.0 · getlago/lago · 10,572★ · polarsource/polar * · 10,271 ★                              청구. Kill Bill Apache-2.0 1순위, Lago AGPL 분리 연동, Polar MoR

 keygen-sh/keygen-api · 1,590★ · FCL-1.0-ALv2 (Fair Core License, 비OSI)                                                         FCL-1.0-ALv2(비OSI) → 설계만 참고, Ed25519 토큰 자체 구현

 open-feature/spec · 1,258★ · Apache-2.0 · Unleash/unleash · 13,813★                                                            엔타이틀먼트 인터페이스 / AGPL 백엔드(자체 구현 권장)




9.6 D7 프로토콜
11장에 상세. 요지: MCP 사양 2026-07-28 + python-sdk/FastMCP, A2A v1.0.1 + a2a-python, AG-UI 1.0, ACP(Agent Client Protocol) 선택,
agentgateway 단일 데이터플레인, OTel GenAI semconv(별도 저장소 이관).

9.7 D8 런타임·compose·운영
 실측                                                                                              판정
 docker/compose · 38,178★ · Apache-2.0                                                           v5 계열(릴리스 v5.5.1 (2026-09-03)). v5.0.0: Compose 를 SDK 로 공식 사용 가능, 빌더는 Bake 위임, OCI/Git 원격 리소스. 최소 요구
                                                                                                 >= 5.0. '컴포즈 v2' 표기 금지

 compose-spec/compose-spec · 2,730★ · Apache-2.0                                                 include(이름 충돌 시 병합 없이 경고 → 접두어 강제), profiles(다른 프로파일 depends_on 은 에러), depends_on.condition,
                                                                                                 develop.watch, models(v2.38.0+), provider(v2.36.0+), secrets, GPU devices, start_interval

 docker/model-runner · 651★ · Apache-2.0                                                         compose models: 최상위 요소의 실행기(OCI 모델 아티팩트). 선택 경로

 docker/mcp-gateway · 1,571★ · MIT                                                               Docker MCP Toolkit. examples/minimal-compose 존재. 로컬 개발 중심

 containers/podman-compose · 6,217★ · GPL-2.0 · containerd/nerdctl · 10,383★                     호환성 Tier: include·profiles·service_healthy·secrets 지원, models·provider·develop·GPU 미지원(podman). nerdctl 은
                                                                                                 deploy.resources·secrets.external 미구현. CI 는 Docker Engine 고정

 abiosoft/colima * · 30,860★ · MIT · podman-desktop/podman-desktop · 8,020 ★ ·                   Docker Desktop 유료 기준(직원 250명 이상 또는 연매출 1,000만 달러 이상) 회피 경로. Docker Engine/compose CLI 는 무관 — 문서
 rancher-sandbox/rancher-desktop · 7,353★                                                        에 구분 명시

 coollabsio/coolify · 61,962★ · Apache-2.0                                                       차용 자유(Apache-2.0). 템플릿에 ports 없음 + 헬스체크 정형화(5s/20s/10). 마켓 CI 게이트 원형

 IceWhaleTech/CasaOS · 37,231★ · Apache-2.0 · runtipi/runtipi · 9,670★ ·                         앱스토어 = compose + x- 메타 + 아이콘. CasaOS x-casaos 다국어 맵, Runtipi form_fields(random 등) = 즉시 사용 UX. Umbrel 은
 getumbrel/umbrel · 11,974★                                                                      PolyForm Noncommercial → 구조만. runtipi GPL-3.0

 portainer/portainer · 38,520★ · Zlib · louislam/dockge · 24,376★ · moghtech/komodo ·            관리 UI 참고. 콘솔은 자체
 12,326★

 traefik/traefik · 64,888★ · MIT                                                                 v3. exposedByDefault=false + constraints=Label + traefik.docker.network. traefik.* 는 커스텀 constraint 키로 못 씀 → agentplaza.* 네
                                                                                                 임스페이스
 caddyserver/caddy * · 75,834★ · Apache-2.0 · nginx-proxy/nginx-proxy · 19,913★                  대체

 authelia/authelia · 29,006★ · Apache-2.0 · oauth2-proxy/oauth2-proxy · 14,968★ ·                UI 경로 forwardAuth. MCP/A2A 는 agentgateway
 pomerium/pomerium · 5,009★

 getsops/sops · 23,148★ · MPL-2.0 · openbao/openbao · 7,407★ · Infisical/infisical ·             시크릿. sops+compose secrets 기본, OpenBao 선택, Infisical ee/ 분리
 29,299★

 offen/docker-volume-backup · 4,011★ · MPL-2.0 · restic/restic · 36,105★                         stop-during-backup 라벨로 정합성 백업 → restic. 복원 시험 분기 1회

 renovatebot/renovate · 22,528★ · AGPL-3.0 · containrrr/watchtower · 24,650★ ·                   PR 방식 갱신. containrrr 는 아카이브('no longer maintained'), nicholas-fedor 가 후속. 런타임 자동 갱신 기본 off
 nicholas-fedor/watchtower · 4,461★

 open-telemetry/opentelemetry-collector * · 7,565★ · Apache-2.0 · SigNoz/signoz ·                OTLP 단일 계약. SigNoz(MIT 코어) 인프라 관측, Grafana 스택은 AGPL(내부 전용)
 32,120★ · prometheus/prometheus * · 66,109★ · grafana/grafana * · 76,792★

 louislam/uptime-kuma · 91,498★ · MIT · willfarrell/docker-autoheal · 1,999★                     가용성 대시보드 + unhealthy 자동 재시작(라벨 화이트리스트, stateless 만)

 kubernetes/kompose · 10,623★ · Apache-2.0 · helm/helm * · 30,251★ ·                             K8s 는 X10. kompose 는 CI 린터. Helm 은 v4.3.0 (2026-09-09) 세대(Helm 3 전제 금지). kagent(Apache-2.0)는 K8s 에이전트 운영
 kagent-dev/kagent * · 3,752★

 hashicorp/nomad · 16,956★ · BUSL-1.1 (Licensor IBM, 경쟁 호스팅 금지)                                  BUSL, Licensor IBM — 비권고




9.8 플랫폼형 참조(인포그래픽·검색·조사)
 플랫폼 실측                                                                       라이선스 판정                                                AgentPlaza 에서                                             compose 경로

 langflow-ai/langflow * · 154,959★ · MIT                                      MIT                                                    X01 Addon(통째 포장)                                          [미확인]

 infiniflow/ragflow * · 90,911★ · Apache-2.0                                  Apache-2.0                                             X07 Addon                                                 docker/docker-compose.yml(+4
                                                                                                                                                                                               변형)

 rowboatlabs/rowboat * · 17,888★ · Apache-2.0                                 Apache-2.0                                             참조                                                        루트 없음
 bytedance/deer-flow * · 82,612★ · MIT                                     MIT                                                        참조(딥리서치)                                                  docker/docker-compose.yaml

 coze-dev/coze-studio · 21,604★ · Apache-2.0                               Apache-2.0                                                 OpenAPI 플러그인 등록 참조                                        docker/docker-compose.yml

 simstudioai/sim * · 29,660★ · Apache-2.0                                  Apache-2.0                                                 참조(docker-compose.ollama.yml 보유)                          루트 3종. sim-studio/sim 은
                                                                                                                                                                                                404

 paperclipai/paperclip * · 80,953★ · MIT                                   MIT                                                        에이전트 조직 운영 개념 참조(격리 compose 보유)                           docker/

 OpenHands/OpenHands * · 88,354★ · MIT                                     MIT                                                        코딩 에이전트 참조. 구 All-Hands-AI 이전                             루트 없음

 kagent-dev/kagent * · 3,752★ · Apache-2.0                                 Apache-2.0                                                 X10                                                       Helm

 activepieces/activepieces * · 24,531★ · MIT (packages/ee/ 별도 상용)          MIT + ee/                                                  자동화 대체(n8n 대신)                                            루트 3종

 langgenius/dify * · 156,215★ · Apache-2.0 변형 (멀티테넌트·로고                    수정 Apache(멀티테넌트 금지, 로고 제거 금지)                              규격 참고·연계만                                                 docker/docker-compose.yaml
 제거 금지 추가 조건)

 n8n-io/n8n * · 205,085★ · Sustainable Use License (.ee 파일은                Sustainable Use                                            연계만(X04)                                                  -
 Enterprise)

 Significant-Gravitas/AutoGPT * · 187,421★ · Polyform Shield               MIT + autogpt_platform Polyform Shield                     패턴 참고                                                     루트 없음
 (autogpt_platform/) + MIT (그 외)

 kortix-ai/suna * · 20,220★ · Elastic-2.0 (관리형 서비스 제공 금지)                  Elastic-2.0                                                사내 전용만. 불채택                                               -

 FlowiseAI/Flowise * · 55,467★ · Apache-2.0 (enterprise/ 별도) [아카           Apache-2.0 + enterprise/                                   아카이브(2026-08-13) 불채택                                      -
 이브 2026-08-13] [아카이브]

 openclaw/openclaw * · 390,029★ · MIT (OpenClaw Foundation)                MIT                                                        채널 어댑터·ClawHub 마켓 선례·CLI 백엔드                              -

 TransformerOptimus/SuperAGI · 17,683★ · MIT · HKUDS/AutoAgent *           MIT                                                        유지보수 중단. 비권고                                              -
 · 9,793★




9.9 아카이브·이전·정체 총람
 구분                                저장소                                                                                                                                            조치
 아카이브                              huggingface/text-generation-inference, tensorzero/tensorzero(2026-06), mistralai/mistral-inference, opencode-ai/opencode,                      채택 금지. 대체 명시
                                   FlowiseAI/Flowise(2026-08-13), langchain-ai/langserve, protectai/llm-guard, rhasspy/piper, containrrr/watchtower, agntcy/acp-spec·acp-sdk,
                                   docker/model-cards

 유지보수 중단 선언                        microsoft/autogen(유지보수 모드), daytonaio/daytona(2026-06 비공개 이전), coqui-ai/TTS(2024-02), AUTOMATIC1111/stable-diffusion-                          채택 금지
                                   webui(2024-07), mckaywrigley/chatbot-ui(2024-06), agi-inc/agent-protocol(2025-04)

 이전(리다이렉트)                         comfyanonymous/ComfyUI→Comfy-Org/ComfyUI · anthropics/mcpb→modelcontextprotocol/mcpb · casbin/casbin →apache/casbin ·                          현행 full_name 으로 기록
                                   microsandbox→superradcompany · sst/opencode→anomalyco/opencode · Mozilla-Ocho/llamafile→mozilla-ai · text-generation-
                                   webui→oobabooga/textgen · katanemo/archgw→plano · zed-industries/agent-client-protocol →agentclientprotocol ·
                                   lobe-chat→lobehub/lobehub · vercel/ai-chatbot→vercel/chatbot · nlux-ai→nlkitai · encode/starlette →Kludex · prisma/prisma →prisma/orm ·
                                   explodinggradients/ragas→vibrantlabsai · NVIDIA/NeMo-Guardrails→NVIDIA-NeMo/Guardrails · strands-agents/sdk-python →harness-sdk ·
                                   awslabs/agent-squad→2FastLabs · All-Hands-AI→OpenHands/OpenHands · invariantlabs-ai/mcp-scan →snyk/agent-scan · block/goose →aaif-
                                   goose · semantic-conventions GenAI→semantic-conventions-genai · ltdrdata/ComfyUI-Manager →Comfy-Org

 정체(관찰)                            Portkey-AI/gateway(2026-05), michaelfeil/infinity(2026-03), exo(2026-08), vibrantlabsai/ragas(2026-02), single-spa(2025-06), faster-           분기별 재확인, 대체안 유지
                                   whisper(2025-11), open-webui/pipelines(2025-08), tadata-org/fastapi_mcp(2025-08), lasso-security/mcp-gateway(2026-01),
                                   cookiecutter(2026-04), drizzle-orm(2026-07), vercel/chatbot(2026-07), FoundationAgents/MetaGPT(2026-01)

 존재하지 않음                           sim-studio/sim(→simstudioai/sim), Comfy-Org/comfy-registry, microsoft/phi-4(HF 만), openai/apps-sdk-examples(→openai-apps-sdk-                  표기 정정
                                   examples), LG EXAONE GitHub(HF 만)




9.10 라이선스 5등급
 등급                                   SPDX·조건                                                           AgentPlaza 기본 이미지                               예

 G1 허용                                Apache-2.0, MIT, BSD, ISC                                         링크·내장 가능                                        Ollama, llama.cpp, LangGraph, CrewAI, LiteLLM, FastMCP, A2A SDK,
                                                                                                                                                        Traefik, Keycloak

 G2 파일 카피레프트                          MPL-2.0                                                           파일 단위 고지. 내장 가능                                 OpenBao, sops 일부

 G3 프로세스 카피레프트                        GPL-2.0/3.0, LGPL                                                 별 컨테이너. 링크 금지                                   ComfyUI, piper1-gpl

 G4 네트워크·소스공개형 제                      AGPL-3.0, SSPL, BUSL, Sustainable Use, Polyform Shield,           연계(M2)만. 포크·내장·재판매 금지                           SD WebUI, n8n, AutoGPT platform, Dify, Open WebUI, Inngest, Restate
 한                                    Open WebUI License, Dify 추가조건

 G5 확인 부족·비OSS                        NONE, NOASSERTION, 상용 약관                                          기본 제외. 재확인 전 사용 금지                              검색 상위 다수, Claude Code CLI 본체(약관), 상용 API




오픈코어(ee/·enterprise/ 디렉터리 별도 라이선스) 저장소 — LiteLLM, Infisical, authentik, Langfuse, SigNoz, supertokens, mastra,
activepieces, Flowise, weaviate(wl/) — 는 G1 로 분류하되 해당 디렉터리를 이미지에서 제외하는 빌드 검사를 둔다. 공식 이미지에 포함
되는지는 저장소별로 [미확인] 이므로 SBOM 스캔이 최종 판정이다.
9.11 사용자 저장소 재사용
저장소 실측                                                     AgentPlaza 역할                                                                개조 지점

WisemanLim/pub-MultiAIAgent-Template · 1★ · LICENSE 파일 없   v1 기준선. Orchestrator·Assistant·Addon flat zip·per-agent MCP·A2A·standalone   agent.yaml 도입(meta.json 자동 변환), 컨테이너 모드,
음 (사용자 본인 저장소)                                             export                                                                       network_mode:host·docker.sock 제거, a2a-python SDK, 공식 MCP 사양
                                                                                                                                        갱신
WisemanLim/pub-wsa-for-sdd · 0★ · LICENSE 파일 없음 (사용자       배포 셸의 직접 원형. 다중 repo 수집·역할 인식 compose 생성·서비스명 접두                             ports→traefik 라벨, healthcheck 주입, x-agentplaza 주입, 루트 include
본인 저장소) · WisemanLim/wsa4sdd-samples · 0★                  충돌 방지·[NOT SET]/[PENDING]/[DONE] 상태 모델                                       갱신, 83KB 셸 회귀 시험 골격

WisemanLim/pub-Server-Init · 0★ · LICENSE 파일 없음 (사용자 본     0단계 호스트 프로비저닝(멱등, 6개 배포판)                                                    'Compose v2(plugin)' → v5 판정, plaza-shared 네트워크, GPU 툴킷
인 저장소)

WisemanLim/pub-SSL-Cert-Manager · 0★ · LICENSE 파일 없음 (사    폐쇄망 전용 TLS 경로 profiles:[offline-tls]. 기본은 Traefik ACME                       9개월 정체 재검증
용자 본인 저장소)

WisemanLim/pub-wise-dev-std · 0★ · LICENSE 파일 없음 (사용자      개발 표준·스캐폴딩 엔진(.claude-plugin/marketplace.json + profiles/*.yaml —            /scaffold 에 agentplaza-agent 템플릿 추가
본인 저장소)                                                    마켓과 동일 멘탈 모델)

WisemanLim/pub-wise-vibe · 1★ · MIT                        제출 Agent 공급망 심사 파이프라인(review_source)                                         마켓 심사 단계 연결




선결 과제. 6개 중 5개에 LICENSE 파일이 없다(SPDX none). 고객 전달 자산·마켓 게시 전에 명시가 필요하다.
10. 독립 구동, 연계, 즉시 사용
사용자가 에이전트를 골라 등록하면 바로 쓸 수 있어야 하고, 같은 산출물이 혼자서도 돌아야 한다. 이를 agent.yaml 과 compose.yaml
두 파일이 보장한다.

10.1 세 모드 계약
 항목           M1 독립                                 M2 연계                                 M3 즉시 사용
 실행 전제        agent.zip + Docker                    플랫폼 루트 compose 또는 원격 URL              콘솔 계정 + 마켓 접근(또는 오프라인 번들)
 명령           docker compose --profile              plaza install ./x.zip 또는 plaza link   콘솔 '설치' 버튼
              standalone up -d                      <card-url>

 DB           자체 db 컨테이너 또는 SQLite 파일               자체 db 또는 공유 Postgres 스키마              정책 기본값(자체 db)
 포트           자체 publish (env PORT)                 publish 없음. Traefik 경로                동일

 LLM          env LLM_BASE_URL (게이트웨이 또는 Ollama 직   플랫폼 게이트웨이 별칭                          동일
              접)
 노출           REST·MCP·A2A 자체                       게이트웨이 경유 + 카탈로그 + Orchestrator 라우팅    + 콘솔 네비·Assistant 도구
 도입           분                                     시간                                    분
 되돌리기         compose down -v                       plaza uninstall (60초 내 흔적 제거)         콘솔 '삭제'




10.2 agent.yaml 규격
v1 meta.json 을 상위 호환한다(3.5). 아래는 게시판 에이전트 예시 전문이다.
apiVersion: agentplaza/v1
kind: Agent
metadata:
  id: board                              # 소문자·하이픈. 카탈로그·compose 접두어·라우트 키
  name: Board
  displayName: { ko: "게시판", en: "Board" }
  description: { ko: "게시글·댓글 CRUD 앱", en: "CRUD board with comments" }
  version: 1.2.0                         # semver
  publisher: { id: wise, name: "Wise", url: "https://github.com/WisemanLim", keyId: "cosign:…" }
  license: MIT
  provenance:                            # 파생 시 자동 기록 (v1 F26)
    baseAgent: null
spec:
  type: app                              # app|service|rag|tool-proxy|reviewer|execution|hitl|memory|
federation
  platform: { min: "2.0.0" }
  capabilities:
    - verb: manage
      domain: app.board
      description: { ko: "게시물 생성·조회·수정·삭제" }
      inputSchema: { $ref: "schemas/manage.in.json" }
      outputSchema: { $ref: "schemas/manage.out.json" }
      qos: { maxLatencyMs: 5000, supportsAsync: false, supportsStreaming: false }
  governance:
    dataClassification: internal         # public|internal|confidential
    humanApprovalRequired: false
    auditLevel: standard                 # minimal|standard|full
  protocols:
    rest: { path: /api, openapi: true }
    mcp:   { enabled: true, transport: streamable-http, path: /mcp }
    a2a:   { enabled: true, cardPath: /.well-known/agent-card.json, streaming: true,
pushNotifications: false }
    agui: { enabled: true }
    openaiCompat: { enabled: false }
  llm:
    required: true
    alias: plaza/chat                    # 게이트웨이 별칭. 공급자 비의존 (DP3)
    localOk: true
   minContext: 8000
   features: [tool_call]
 env:
   required: []
   optional: [BOARD_PAGE_SIZE]
   secretRefs: []                       # 시크릿 이름만. 값은 D9-04
 permissions:
   network: { egress: [] }              # 빈 배열 = 외부 차단. 예: ["api.example.com:443"]
   fs: { readOnlyRoot: true, writable: [/data] }
   docker: false                        # 항상 false 여야 게이트 통과 (NFR-I3)
 resources: { cpu: "500m", memory: "512Mi", pids: 256 }
 runtime:
   mode: container                      # container(기본) | inprocess(신뢰 퍼블리셔만)
   healthcheck: { path: /health, intervalSec: 10 }
 ui:
   hasFrontend: true
   mount: iframe                        # iframe(기본) | module-federation | none
   route: /addon/board
   navVisible: true                     # 규칙: isActive && hasFrontend
 db:
   engine: [sqlite, postgres]
   isolation: own                       # own | shared-schema | file
   migrations: database/migrations
 dependencies: []                       # 비어야 M1 (DP2). 선택 의존은 optionalServices
 optionalServices: [postgres, redis, otel]
 tests:
   - given: "standalone up"
     then: "GET /health 200, tools/list 에 manage 포함, agent-card.json skills[0].id == manage"



spec.dependencies 가 비어 있어야 DP2 가 성립한다. permissions.docker: false 와 runtime.mode: container
가 기본값이며 게이트가 강제한다(NFR-I2·I3).

10.3 compose.yaml 규격
에이전트 하나의 compose 전문. standalone 프로파일이 M1, federated 프로파일이 M2 다. 루트 compose 는 이 파일을 include 하고 프로
젝트명·네트워크를 덧씌운다.
name: plaza-board
x-agentplaza:                              # 확장 필드. 플랫폼이 읽고 Docker 는 무시
  agent: board
  version: 1.2.0
  manifest: ./agent.yaml
services:
  board-be:
    build: ./backend
    image: ${PLAZA_REGISTRY:-local}/agent-board-be:1.2.0
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql://board:board@board-db:5432/board}
      LLM_BASE_URL: ${LLM_BASE_URL:-http://llm-gateway:4000/v1}
      LLM_ALIAS: plaza/chat
      AGENT_BASE_URL: ${AGENT_BASE_URL:-http://localhost:8001}
      OTEL_EXPORTER_OTLP_ENDPOINT: ${OTEL_EXPORTER_OTLP_ENDPOINT:-}
    secrets: []
    read_only: true
    tmpfs: [/tmp]
    volumes: [board-data:/data]
    networks: [board-internal, plaza-shared]
    deploy: { resources: { limits: { cpus: "0.5", memory: 512M, pids: 256 } } }
    healthcheck: { test: ["CMD", "curl", "-fsS", "http://localhost:8000/health"], interval: 10s,
timeout: 3s, retries: 6, start_period: 20s }
    depends_on: { board-db: { condition: service_healthy } }
    labels:
      agentplaza.agent: board
      traefik.enable: "true"
      traefik.http.routers.board-api.rule: PathPrefix(`/a/board/api`) || PathPrefix(`/mcp/board`)
      traefik.http.routers.board-api.middlewares: plaza-auth@file
      traefik.http.services.board-api.loadbalancer.server.port: "8000"
    profiles: [standalone, federated]
  board-fe:
    build: ./frontend
    image: ${PLAZA_REGISTRY:-local}/agent-board-fe:1.2.0
    networks: [plaza-shared]
    labels:
      traefik.enable: "true"
      traefik.http.routers.board-ui.rule: PathPrefix(`/a/board/ui`)
      traefik.http.services.board-ui.loadbalancer.server.port: "80"
    profiles: [standalone, federated]
  board-db:
    image: postgres:17-alpine
    environment: { POSTGRES_USER: board, POSTGRES_PASSWORD: board, POSTGRES_DB: board }
    volumes: [board-pg:/var/lib/postgresql/data, ./database/migrations:/docker-entrypoint-
initdb.d:ro]
    networks: [board-internal]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U board"], interval: 5s, timeout: 3s, retries:
5 }
    profiles: [standalone, federated]      # isolation: shared-schema 이면 이 서비스가 생략되고
DATABASE_URL 만 주입
  board-standalone-proxy:                  # M1 전용. 플랫폼 Traefik 이 없을 때 자체 포트 publish
    image: traefik:v3
    command: ["--providers.docker=true", "--providers.docker.exposedbydefault=false", "--
entrypoints.web.address=:80"]
    ports: ["${PORT:-8001}:80"]
    volumes: ["/var/run/docker.sock:/var/run/docker.sock:ro"]   # 프록시 컨테이너만 허용. 에이전트 컨테이너는 금
지
    networks: [plaza-shared]
    profiles: [standalone]
networks:
  board-internal: {}
  plaza-shared: { external: ${PLAZA_SHARED_EXTERNAL:-false}, name: plaza-shared }
volumes:
  board-data: {}
  board-pg: {}



루트 compose 는 include: - path: installed/board.compose.yaml                                     project_directory:
installed/board      env_file: installed/board.env 로 흡수하고, PLAZA_SHARED_EXTERNAL=true 로 공유 네트
워크에 붙인다. standalone 프로파일 서비스는 include 시 켜지지 않는다.

10.4 등록 8단계
 단계    이름               하는 일                                                                                     실패 시
 1     업로드·수집           zip 수신(단일·다중), Git/OCI/URL 가져오기, 임시 격리 디렉터리                                              거부

 2     구조 검증            agent.yaml JSON Schema, zip-slip·링크·크기, 파일 규칙, Python 문법(ruff), SQL DDL 만(sqlglot), 금지   거부 + 사유 목록
                        API(docker.sock·subprocess 정책)

 3     서명·SBOM·취약점      cosign verify(퍼블리셔 키), syft SBOM, trivy/grype — Critical 차단, High 경고                     거부 또는 '미검증' 배지

 4     라이선스·정책          SBOM 라이선스 → G1~G5, permissions 선언 vs 조직 정책(OPA). G4 는 격리 표시, G5 차단                       거부 또는 격리 전용

 5     빌드               BuildKit 이미지 빌드(태그 = id:version), 프론트 정적 빌드, server.json·agent-card.json 생성              롤백(이미지 삭제)

 6     등록               카탈로그·버전·capability 인덱스 INSERT, installed/{id}.compose.yaml 생성, 라이선스 키 검증(유료)             롤백

 7     기동·헬스            compose up federated, service_healthy 대기, 계약 시험(tools/list·Card)                         롤백(down -v) + 상태 failed

 8     노출               Traefik 라우트 활성, 콘솔 네비, Assistant 도구 목록 갱신, MCP/A2A 게이트웨이 등록, registry 공개                 -




경로 C(연동·연계)는 6단계부터 시작한다. 원격 Card/URL 을 읽어 capability 를 만들고 계약 시험(7)을 거쳐 노출(8)한다. v1 in-process 호
환 모드는 2·4 통과 후 5 를 건너뛰고 importlib 로 적재하되, 신뢰 퍼블리셔 서명이 있어야 한다.

10.5 카탈로그 소스 다형 필드와 신뢰 등급
세 경로를 하나의 source 필드로 표현한다(Claude Code marketplace.json 패턴). 서명·감사 결과가 신뢰 등급을 정하고, 신뢰 등급이
런타임 격리 강도를 정한다(13.2).
{ "id": "com.wise/board", "version": "1.2.0",
  "source": { "type": "oci",        "ref": "reg.plaza.local/agents/board:1.2.0", "digest": "sha256:…"
} }
{ "source": { "type": "zip-url",    "url": "https://…/board-1.2.0.zip", "sha256": "…" } }
{ "source": { "type": "git-subdir", "url": "https://github.com/wise/agents.git", "path": "board",
"ref": "v1.2.0", "sha": "30287f5e…" } }
{ "source": { "type": "remote-a2a", "card_url": "https://invoice.acme.com/.well-known/agent-
card.json" } }
{ "source": { "type": "remote-mcp", "url": "https://mcp.acme.com/http", "transport": "streamable-
http" } }



무료·사내 카탈로그는 서버 없이 git 저장소 + marketplace.json(정적)으로, 유료 카탈로그만 API 서버(ClawHub 참조)로 이원화한다. 설
치 시 x-agentplaza.form_fields(text·password·random·select·boolean, Runtipi 패턴)가 required_env 입력 폼을 만들고, random
은 HKDF 로 파생해 sops 로 암호화한다.

10.6 v1 → AgentPlaza 마이그레이션
 단계           내용                                                                                                          후방 호환
 v1.x(현행)     flat zip, {Name}-meta.json, importlib 핫 디플로이                                                                -

 v2.0         agent.yaml 도입. meta.json 자동 변환(agent_type→spec.type, capabilities, governance, required_env→env.required,   양방향
              min_platform_version→platform.min). 디렉터리 zip 허용, flat zip 은 경고와 함께 지원

 v2.1         checksums.txt 필수, 서명 선택(미서명 = community 등급 + 강한 격리). 컨테이너 모드 기본                                             유지

 v2.2         compose.yaml 필수. v1 F27 export-standalone 생성기를 패키지 빌드 도구로 전환                                                flat zip 은 플랫폼이 compose 자동 생성

 v3.0         flat zip 종료. OCI 아티팩트 배포, 공개 마켓은 cosign 서명 필수, 3경로 전면 가동                                                    renames/migrated_to 로 이전



plaza init    --template <app|service|rag|tool-proxy|reviewer|execution|hitl|memory|federation>                                                      #
copier
plaza update                        # 템플릿 갱신 반영(copier update)
plaza validate [--strict]           # 스키마 + 정적검사 + coherence(선언 vs 실제)
plaza pack   [--out board-1.2.0.zip]
plaza sign   --keyless | --key k.pem
plaza verify board-1.2.0.zip
plaza publish --registry reg.plaza.local [--dry-run]
plaza install ./board-1.2.0.zip | oci://… | https://…zip | git+https://…#board@v1.2.0
plaza link    https://…/.well-known/agent-card.json | mcp://…
plaza up | down | export --standalone <id>
plaza verify-coverage




10.7 프로파일
 프로파일               켜는 것                                                                                   용도
 standalone         에이전트 자신 + 자체 db + standalone-proxy                                                     M1. 개발·납품
 federated          루트 compose: infra + core + installed/*                                                 M2/M3 기본
 local-only         federated − 퍼블릭 어댑터 + Ollama 필수                                                        프라이버시·에어갭 전 단계
 airgap             local-only + zot 미러 + 오프라인 마켓 번들 + 모델 사전 배치                                            폐쇄망

 gpu                llm-provider 에 devices 예약 + vLLM 선택                                                    GPU 서버
 sso                federated + keycloak + oauth2 미들웨어                                                     조직 도입




10.8 누락 검증 CI (verify_coverage)
data.py 의 ITEMS 키 집합 == agents/*/agent.yaml metadata.id 집합 == FR-D ID 집합 == 카탈로그 시드. 하나라도 어긋나면 빌드 실패.
인포그래픽 20 저장소 각각이 3.1 의 귀속 ID 를 갖는지, 요구사항 (1)~(8) 이 3.6 추적표에서 빈 칸 없는지도 같은 스크립트가 검사한
다. M1 기동 시험(NFR-I1)은 70 항목을 매트릭스로 돌린다.
plaza verify-coverage --items data.py --agents agents/ --frs docs/PRD.md --infographic 20
plaza test --standalone --all     # 70 x (compose up → /health → tools/list → agent-card) 매트릭스
11. 표준 프로토콜 — 현행 사양 실측과 반영
요구 (7) 'MCP·A2A 등 표준 프로토콜을 통한 연계'는 사양 버전을 고정해 두면 실패한다. 2026-09-18 사양 저장소를 실측한 결과 두 프
로토콜 모두 2026년에 비호환 개정을 거쳤다. 이 장은 실측 버전·변경 요지·AgentPlaza 반영을 적는다. 수치는 모두 2026-09-18 GitHub
API 값이다.

11.1 요약
 축                         실측 결론(2026-09-18)                                                                                AgentPlaza 반영

 MCP 최신 사양                 2026-07-28 (직전 2025-11-25, 2025-06-18). 사양 저장소 docs/specification/ 에 6개 버전 디렉                    Addon 은 SDK 추상화 뒤에서 2025-11-25 와 2026-07-28 을 동시 광고. 버전
                           터리                                                                                               협상은 게이트웨이(D7-07)

 MCP 2026-07-28 성격         파괴적 재설계: Mcp-Session-Id 제거, initialize 핸드셰이크 제거(무상태), server/discover 필수,                        MCP 서버 컨테이너를 stateless 로 수평 확장. 헬스는 ping 대신
                           subscriptions/listen, Tasks 를 확장(io.modelcontextprotocol/tasks)으로 분리, MRTR, SSE 재개 제거,           server/discover. 장기 작업은 A2A Task
                           Roots·Sampling·Logging 폐기 예고

 MCP 라이선스                  조직 전체 MIT → Apache-2.0 전환 중. spdx NOASSERTION 은 혼합 문구 때문                                         고지 이중 표기

 MCP 레지스트리                 registry.modelcontextprotocol.io 가동. server.json 스키마 2025-12-11, API /v0.1/servers,              마켓 서버(D6-07)가 이 API 와 호환. 공식 레지스트리 증분 미러
                           Go+PostgreSQL 셀프호스팅

 A2A 최신 사양                 v1.0.1 (2026-05-28). v1.0.0 2026-03-12. specification/a2a.proto 가 모든 바인딩의 규범 정본.                 v0.3 예제·블로그 인용 금지. Agent Card protocolVersion 확인 후 분기
                           Linux Foundation 산하, TSC 8개사

 Agent Card 경로             /.well-known/agent-card.json (RFC 8615). JWS 서명(signatures) + RFC 8785 정규화                       v1 router_a2a 경로와 동일. 서명 필수화

 게이트웨이                     agentgateway/agentgateway · 4,900★ · Apache-2.0 — MCP+A2A+LLM 3축을 한 데이터플레인으                      D7-07 기본 엔진
                           로 처리하는 유일한 후보
 관측                        OTel GenAI 규약이 open-telemetry/semantic-conventions-genai 로 이관(2026-05-05 생성, 릴리스                 D10-03. 속성 정규화 계층으로 이름 변경 대비
                           태그 없음, Development). MCP 전용 semconv(mcp.md) 보유




11.2 MCP 2026-07-28 변경 요지와 대응
 #      변경                                                                                      SEP              AgentPlaza 대응

 1      프로토콜 수준 세션 제거(Mcp-Session-Id 삭제). 상태는 서버가 발행한 handle 을 툴                                2567             sticky session 불필요. L7 로드밸런싱
        인자로
 2      initialize/initialized 제거. 모든 요청 _meta 에                                                2575             SDK 클라이언트가 자동 처리. 불일치 시 UnsupportedProtocolVersionError 처리
        protocolVersion·clientCapabilities·clientInfo

 3      server/discover RPC 필수. 지원 버전·capability·identity 광고                                    2575             카탈로그 갱신 = discover → tools/list. 헬스체크도 discover

 4      GET SSE·resources/subscribe 를 subscriptions/listen 단일 스트림으로                             2575             프록시가 GET 을 특별 취급하지 않음

 5      ping·logging/setLevel·roots/list_changed 제거                                             2575             로그 레벨은 _meta.logLevel, 로깅은 OTel

 6      Tasks 를 코어에서 확장 io.modelcontextprotocol/tasks 로 분리(tasks/get 폴링,                        2663             장기 작업은 A2A Task 우선, MCP Tasks 확장은 차선
        tasks/update)

 7      MRTR: 서버→클라 역방향 요청 대신 resultType=input_required + 재시도                                   2322             Orchestrator 도구 실행기(D2-04)에 MRTR 루프

 8      모든 결과에 resultType(complete|input_required) 필수                                           2322             구버전 서버 생략 시 complete 간주

 9      Streamable HTTP SSE 재개·재전송(Last-Event-ID) 제거                                            2575             끊기면 새 request id 로 재발행

 m1     OTel trace context 를 _meta(traceparent·tracestate·baggage)로 전파                          414              게이트웨이가 주입·전파(D10-03)

 m2     CacheableResult(ttlMs·cacheScope) 필수 — tools/list 등                                     2549             게이트웨이 공유 캐시(public 만)

 m3     POST 에 Mcp-Method·Mcp-Name 헤더 요구                                                        2243             본문 파싱 없이 툴 단위 RBAC·레이트리밋(D7-07)

 d1     Roots·Sampling·Logging 폐기 예고(12개월 창)                                                    2577             신규 구현 금지

 d2     OAuth DCR 폐기 → CIMD(Client ID Metadata Documents) 권장                                    -                D7-02 클라이언트 등록은 CIMD




2025-06-18 세대에서 도입된 Streamable HTTP·OAuth 2.1·Elicitation·Tool output schema 는 이미 안정화되었다. 2026-07-28 의 쟁점은 그
위의 무상태화·세션 제거·Tasks 분리·MRTR 다. MCP 보안 문서(security_best_practices, 2026-07-28)의 11개 항목은 Confused
Deputy·Token Passthrough·SSRF·State Handle Hijacking 등이며 Tool Poisoning 은 별도 항목이 아니다 → 플랫폼 자체 통제(D5-02 정적
검사 + tools/list 해시 핀닝 + snyk/agent-scan)로 보완한다.
11.3 MCP SDK·레지스트리·게이트웨이 실측
저장소                                                                          실측                                                         판정
modelcontextprotocol/modelcontextprotocol · 9,241★ · MIT → Apache-2.0        사양. 릴리스 2026-07-28 (2026-07-28)                            정본
전환 진행 중 (문서 CC-BY-4.0)

modelcontextprotocol/python-sdk * · 24,325★ · MIT                            릴리스 v2.2.0 (2026-09-07)                                    Addon SDK 기반(1순위)

modelcontextprotocol/typescript-sdk · 13,420★ · MIT → Apache-2.0 전환          커밋 2026-09-16                                              콘솔·MCP 클라이언트
진행 중
modelcontextprotocol/go-sdk · 5,116★ · MIT → Apache-2.0 전환 진행 중              릴리스 v1.8.0 (2026-09-14)                                    게이트웨이 확장 시

PrefectHQ/fastmcp * · 27,717★ · Apache-2.0                                   릴리스 v4.0.5 (2026-09-17)                                    Python 서버 데코레이터. SDK 대체 후보

tadata-org/fastapi_mcp * · 12,008★ · MIT                                     커밋 2025-08-10                                              비권장(2025-08 이후 무커밋). OpenAPI→MCP 는 게이트웨이 기
                                                                                                                                        능으로 대체
modelcontextprotocol/registry · 7,260★ · MIT → Apache-2.0 전환 진행 중            server.json 2025-12-11, /v0.1/servers                      마켓 서버 호환 대상

modelcontextprotocol/inspector * · 10,904★ · LICENSE 파일 없음                   LICENSE 파일 없음 [미확인]                                        계약 시험 CLI(개발 도구로만)
(README 확인 필요)

docker/mcp-gateway · 1,571★ · MIT                                            Docker MCP Toolkit                                         로컬 개발 중심. 참고

agentgateway/agentgateway · 4,900★ · Apache-2.0                              릴리스 v1.5.0 (2026-08-27)                                    D7-07 기본

IBM/mcp-context-forge · 4,489★ · Apache-2.0                                  MCP 중심 게이트웨이·레지스트리                                         대체 후보. A2A 지원 [미확인]

lasso-security/mcp-gateway · 388★ · MIT                                      커밋 2026-01-22                                              정체. 비권장

snyk/agent-scan · 3,060★ · Apache-2.0                                        구 invariantlabs-ai/mcp-scan (이전)                           등록 게이트 3단계 스캐너




11.4 A2A v1.0.1 핵심 모델과 대응
요소                         v1.0.1 실측                                                                                              AgentPlaza 대응

정본                         specification/a2a.proto (package lf.a2a.v1). JSON-RPC·HTTP+JSON·gRPC 3바인딩 등가성 명세                       SDK a2a-python 사용, 손코딩 금지(v1 router_a2a 교체)

Agent Card                 /.well-known/agent-card.json. supportedInterfaces[{url, protocolBinding, protocolVersion, tenant}],    agent.yaml 에서 생성(D4-04). signatures 필수. interfaces[0]=JSONRPC
                           capabilities{streaming, pushNotifications, extendedAgentCard, extensions[]}, securitySchemes(OpenAPI
                           동형: APIKey·HTTP·OAuth2(Device Code·PKCE)·OIDC·mTLS), skills[], signatures[](JWS)

Task                       상태 9종(종단 4·중단 2: INPUT_REQUIRED, AUTH_REQUIRED 등). UUID 단일 ID. canceled 철자.                            HITL(D2-06)은 INPUT_REQUIRED 로 표현. tasks 테이블(12.1)
                           SCREAMING_SNAKE_CASE enum

RPC 11종                    SendMessage, SendStreamingMessage(stream), GetTask, ListTasks(신설), CancelTask, SubscribeToTask,        D7-03 서버·D7-04 클라이언트 전부 구현. Push 는 P1
                           PushNotificationConfig CRUD 4, GetExtendedAgentCard

Part                       평탄화: text/raw/url/data + media_type. kind 판별자 제거                                                       AG-UI 이벤트로 변환(12.5)

Extensions                 AgentExtension{uri, required, params}. Data-only/Profile/Method/State Machine                          사내 감사추적 확장 1개(required:true) — D9-07

미디어타입                      application/a2a+json 선호(v1.0.1)                                                                        게이트웨이 Content-Type 규칙

멀티테넌시                      gRPC scope/tenant 필드                                                                                   X09 대비 필드 예약




A2A SDK                                                                      실측                                                                 판정

a2aproject/A2A * · 25,828★ · Apache-2.0                                      릴리스 v1.0.1 (2026-05-28)                                            사양

a2aproject/a2a-python · 2,147★ · Apache-2.0                                  릴리스 v1.1.4 (2026-09-08)                                            1순위 (PyPI a2a-sdk)

a2aproject/a2a-js · 621★ · Apache-2.0                                        릴리스 v1.1.0 (2026-08-26)                                            콘솔·TS SDK

a2aproject/a2a-samples · 1,769★ · Apache-2.0                                 다중 프레임워크 샘플 + extensions/                                          계약 시험 참조

a2aproject/a2a-inspector · 490★ · Apache-2.0                                 디버깅 UI                                                             개발 도구

google/adk-python · 21,568★ · Apache-2.0                                     src/google/adk/a2a/ 일급 지원                                          D2-03 어댑터 후보

microsoft/agent-framework · 13,571★ · MIT                                    python/packages/a2a·hosting-a2a                                    .NET 스택 시

pydantic/pydantic-ai * · 20,021★ · MIT                                       Agent.to_a2a() 제거, fasta2a 별도 패키지                                  to_a2a 의존 금지

langchain-ai/langgraph * · 41,863★ · MIT                                     코어 A2A 미지원(샘플만)                                                    D7-03 이 SDK 로 감싼다




11.5 그 밖의 표준
표준                                  실측                                                                                                       AgentPlaza 채택

ACP (Agent Client Protocol, Zed)    agentclientprotocol/agent-client-protocol · 4,273★ · Apache-2.0 — 구 zed-industries 경로에서 전용 org 로         D1-04 CLI 백엔드 브리지 + D7-06. 개발자 IDE 채널은 P2
                                    이전. 프로토콜 v1(schema v1.22.0), JSON-RPC over stdio. Gemini CLI 네이티브, claude-agent-acp·codex-
                                  acp 어댑터, Copilot CLI 프리뷰

 AG-UI (CopilotKit)               ag-ui-protocol/ag-ui * · 15,934★ · MIT — spec 1.0, 이벤트 34종(README 의 16종은 구식), 전송 무관,                D3-01·D7-06 프론트 이벤트 표준(12.5)
                                  conformance 스위트, integrations/a2a 포함

 AGNTCY                           oasf(스키마 분류체계)·slim(전송 substrate)·dir 은 현역, acp-spec·acp-sdk 는 2025-05/06 아카이브.                     불채택. 문서에서 'ACP' 는 항상 Agent Client Protocol 로 풀어
                                  Zed ACP 와 이름만 같음                                                                                    쓴다

 ANP                              agent-network-protocol/AgentNetworkProtocol — did:wba 분산 신원, 공개 웹 규모                                불채택(모니터링)

 agent-protocol                   agi-inc/agent-protocol (구 AI-Engineer-Foundation) — 2025-04 이후 무커밋                                  종료. 불채택

 AAIF·AGENTS.md                   aaif org 2025-11-14 생성, goose·AGENTS.md 이관 확인, MCP 이관 흔적 없음. agentsmd/agents.md                     D4 개발 표준에 AGENTS.md 채택(v1 이미 보유)

 OpenAI Apps SDK                  openai/openai-apps-sdk-examples (요청 표기 apps-sdk-examples 는 404)                                     ChatGPT 배포 시 선택

 OTel GenAI semconv               open-telemetry/semantic-conventions-genai · 370★ · Apache-2.0 — gen_ai.operation.name 에             D10-03 필수. mcp.*.session.duration 메트릭은 세션 제거로 의
                                  invoke_agent·execute_tool·invoke_workflow·plan + 메모리 연산 8종. mcp.md 전용 규약(컨텍스트를                      미 상실 → 알람 금지
                                  params._meta 에 주입)

 OpenLLMetry / OpenInference      traceloop/openllmetry · 7,438★ · Apache-2.0 (opentelemetry-instrumentation-mcp 보유) /                부트스트랩은 OpenLLMetry, Phoenix 평가 시 OpenInference
                                  Arize-ai/openinference · 1,224★ · Apache-2.0




11.6 프로토콜 비교와 경쟁 관계
 축                       MCP                                           A2A                                           ACP                              AG-UI
 목적                      에이전트↔도구                                       에이전트↔에이전트                                     에디터↔코딩 에이전트                      에이전트↔UI
 현행                      2026-07-28                                    v1.0.1                                        protocol 1                       spec 1.0
 전송                      stdio, Streamable HTTP                        JSONRPC·gRPC·HTTP+JSON                        stdio JSON-RPC                   무관(SSE·WS)
 인증                      OAuth 2.1, PRM, CIMD                          OpenAPI Security Scheme                       에이전트별                            미규정

 장기 작업                   확장(tasks)                                     코어 Task + Push                                세션                               Run/Step
 발견                      server/discover + Registry                    Agent Card + 큐레이션                             ACP Registry                     없음

 라이선스                    MIT→Apache-2.0                                Apache-2.0                                    Apache-2.0                       MIT
 채택                      필수                                            필수                                            선택(P2)                           권장(P1)




네 표준은 축이 달라 보완재다. 실제 경쟁은 세 쌍: MCP Tasks 확장 ↔ A2A Task(장기 작업 → A2A 우세), MCP Apps(ext-apps) ↔ OpenAI
Apps SDK(대화 내 위젯), OTel GenAI ↔ OpenInference ↔ OpenLLMetry(규약은 OTel, 구현은 OpenLLMetry).

11.7 Orchestrator 의 MCP·A2A 결정 규칙
 조건                                                                                        경로
 단일 함수, 30초 미만, 멱등                                                                         MCP tools/call

 구조화 결과 1건                                                                                 MCP (outputSchema + structuredContent)

 다단계 목표, 수 분 이상                                                                            A2A SendMessage → Task

 중간 승인·추가 입력                                                                               A2A INPUT_REQUIRED (HITL 게이트)
 비동기 완료 통지                                                                                 A2A Push Notification

 상대가 MCP 만 지원 + 장기 실행                                                                      MCP + io.modelcontextprotocol/tasks 확장(차선)

 상대가 REST/OpenAI 호환만                                                                       게이트웨이가 MCP 툴로 래핑(D7-05). Orchestrator 는 모른다




11.8 외부 에이전트 등록 게이트(경로 C)
등록 요청(Card URL 또는 MCP URL)
  → ① server.json / agent-card.json 스키마 검증
  → ② Agent Card JWS 서명 검증(A2A) / 네임스페이스 소유권 검증(MCP: DNS·HTTP·OIDC)
  → ③ snyk/agent-scan (tool poisoning, 과다 권한)
  → ④ mcp inspector --cli 스모크 (server/discover, tools/list) / a2a-inspector
  → ⑤ tools/list 전체 해시 핀닝 → 카탈로그 저장 (rug-pull 방어)
  → ⑥ 게이트웨이 정책 생성 (RBAC scope, rate limit, egress allowlist)
  → 승인 → 8단계 중 6~8
11.9 미확인 항목
   modelcontextprotocol/inspector 의 LICENSE(API 반환 없음), typescript-sdk 코어 패키지 버전, 각 SDK 와 2026-07-28 의 정확한 대응.
   MCP 공식 레지스트리 GA 선언 여부, server.json 2025-12-11 이후 스키마 존재 여부, MCP 의 AAIF 이관 계획.
   IBM/mcp-context-forge 의 A2A 지원, OpenInference 의 MCP 전용 규약, mcp.*.session.duration 메트릭의 향후 처리.
12. 데이터 모델과 API

12.1 플랫폼 스키마 (요지)
users(id, email, role[supervisor|admin|user], is_active, locale, created_at)                                                            -- v1 tbl_users
승계
sessions(id, user_id, title, agent_scope, created_at, archived_at)                          -- 대화 세
션
messages(id, session_id, role, content_jsonb, tool_calls_jsonb, tokens_in, tokens_out, model_alias,
created_at)
agents(id, name, type, version, publisher_id, license, status[registered|healthy|unhealthy|disabled],
runtime_mode, manifest_jsonb)
agent_versions(agent_id, version, image_digest, sbom_ref, signature_ok, license_grade, installed_at,
installed_by)
capabilities(agent_id, verb, domain, input_schema, output_schema, qos_jsonb)                -- v1
tbl_addon_agent_capabilities 승계
installs(id, agent_id, source[market|zip|git|oci|link], source_ref, env_jsonb(비밀 제외), compose_path,
created_at)
remote_agents(id, kind[a2a|mcp], url, card_jsonb, auth_ref, last_contract_test_at, status) -- 경로 C
llm_models(alias, provider, model_id, local, context, tool_call, vision, license, cost_in, cost_out,
enabled)
llm_usage(id, ts, alias, agent_id, user_id, tokens_in, tokens_out, cost, fallback_from)
approvals(id, task_id, capability, requester_id, approver_id, status[pending|approved|rejected|
expired], expires_at)
tasks(id, session_id, agent_id, a2a_task_id, state, checkpoint_ref, created_at, ended_at)    -- 오케스
트레이션·A2A
market_listings(id, agent_id, price, currency, license_model[free|seat|term], publisher_id, rating,
downloads)
licenses(id, listing_id, user_or_org, token(Ed25519), seats, valid_until, revoked)
publishers(id, name, key_id, verified, created_at)
audit_events(id, ts, actor, agent_id, action, resource, args_hash, result_hash, prev_hash) --
append-only, 해시 체인
settings(key, value_jsonb)                                                                  -- v1
tbl_settings 승계



프롬프트·응답 원문은 messages 에만, auditLevel=full 에서만 원장에 해시가 아닌 원문 참조를 둔다. 퍼블릭 LLM 키·시크릿 값은 어느
테이블에도 저장하지 않는다(D9-04).

12.2 Addon DB 격리 3방식
 방식                               agent.yaml db.isolation   장점                                               단점                               권장

 전용 DB 컨테이너                       own                       완전 격리, M1 과 동일, 라이선스·백업 단위                       컨테이너 수 증가                        기본값
                                                            일치
 공유 Postgres 스키마                  shared-schema             자원 절약, 플랫폼 백업 한 번                                스키마 충돌·권한 관리, M1 시 별도 경로         소형 에이전트 다수

 SQLite 파일                        file                      가장 단순, 개발·M1                                     동시성 제한                           app 유형 소규모




v1 은 addon SQL 을 플랫폼 DB 에 직접 실행했다(PG→SQLite 자동 변환). AgentPlaza 는 own 을 기본으로 바꾸고, shared-schema 는
plaza_{agent_id} 스키마와 전용 role 로 제한한다.


12.3 플랫폼 REST (요지)
 메서드           경로                                                목적                                                                v1 대응

 POST          /api/chat/stream                                  Assistant 채팅. AG-UI SSE. body: message, session_id, agent_scope   POST /api/agent/chat/stream

 GET/POST      /api/sessions                                     세션 목록·생성                                                          신규

 GET           /api/agents                                       카탈로그(내장·설치·원격), 상태·버전                                             GET /api/addon-agents/

 POST          /api/agents/upload                                zip 업로드(다중) → 8단계 잡 ID                                            POST /api/addon-agents/upload

 POST          /api/agents/scaffold                              위저드 → zip 생성(또는 바로 설치)                                            POST /api/addon-agents/scaffold
 POST                    /api/agents/link                                                원격 A2A Card / MCP URL 등록(경로 C)                     신규

 GET                     /api/agents/{id}/install-status                                 8단계 진행·실패 사유                                       신규

 PATCH                   /api/agents/{id}                                                활성·비활성·설정(모델 별칭·프롬프트·설명)                           PATCH toggle + agent_config

 DELETE                  /api/agents/{id}                                                삭제(60초 내 흔적 제거)                                    DELETE

 POST                    /api/agents/{id}/export                                         파생 zip                                             F26

 POST                    /api/agents/{id}/export-standalone                              M1 번들(agent.zip)                                   F27

 GET                     /api/market/listings                                            마켓 검색·상세                                           신규

 POST                    /api/market/install/{listing}                                   경로 A 설치(라이선스 키 포함)                                 신규

 GET/POST                /api/llm/models                                                 모델 카탈로그·별칭·정책                                      settings 일부

 GET                     /api/approvals · POST /api/approvals/{id}/approve               HITL                                               F25

 GET                     /api/audit                                                      권한 있는 원장 질의                                        신규

 GET                     /health                                                         인증 없음                                              동일




12.4 에이전트 표면 (모든 에이전트 동일)
 표면                                   경로                                                                                  인증
 REST                                 /a/{id}/api/… (OpenAPI /a/{id}/api/openapi.json)                                    JWT 또는 서비스 API 키

 MCP                                  /mcp/{id} (Streamable HTTP; v1 호환 포트 모드 선택)                                         x-api-key → 서비스 JWT(v1 F29) 또는 OAuth 2.1

 A2A                                  /a/{id}/.well-known/agent-card.json, /a/{id}/a2a/…                                  Card 는 공개, Task 는 인증

 AG-UI                                /a/{id}/api/agui (SSE)                                                              JWT

 OpenAI 호환                            /v1/chat/completions (model = plaza/agent/{id})                                     API 키

 UI                                   /a/{id}/ui/ (콘솔 iframe 마운트 /addon/{id})                                             쿠키 세션(HttpOnly) + postMessage 토큰 전달




12.5 AG-UI 이벤트 매핑
 v1 SSE 이벤트                                              AG-UI 이벤트(표준)                                                    비고

 delta(text)                                             TEXT_MESSAGE_START / CONTENT / END                               토큰 스트리밍

 tool_start / tool_end                                   TOOL_CALL_START / ARGS / END + TOOL_CALL_RESULT                  MCP 도구 호출

 registry_miss                                           CUSTOM(name=registry_miss)                                       후보 제안

 hitl_pending                                            CUSTOM(name=approval_required) + STATE_SNAPSHOT                  승인 카드

 reviewer 결과                                             CUSTOM(name=review)                                              차단 시 RUN_ERROR

 (없음)                                                    RUN_STARTED / RUN_FINISHED / STEP_STARTED / STEP_FINISHED        그래프 단계




이벤트 타입 이름은 11.4 에서 실측한 AG-UI 사양을 따른다. 사양 미확정 항목은 CUSTOM 으로 감싼다.

12.6 관측 속성
OpenTelemetry GenAI 규약(11.5). 필수 속성: gen_ai.system(provider), gen_ai.request.model, gen_ai.usage.input_tokens/output_tokens,
gen_ai.agent.id(=agent id), gen_ai.tool.name, plaza.session_id, plaza.capability, plaza.fallback_from. 프롬프트 원문은 기본 미수집(opt-
in).
13. 보안, 법적, 윤리

13.1 위협 모델 — 임의 코드가 든 Zip 을 받는 플랫폼
    위협                              경로                                   통제(FR/NFR)

    악성 Addon 코드                     zip 업로드·마켓 다운로드                      컨테이너 모드 기본(DP5), 신뢰등급별 gVisor(D8-04), egress 기본 차단, docker.sock·host network 금지(NFR-I3), 정적
                                                                         검사(D5-02), 서명·SBOM·취약점(D5-03)

    공급망 변조                          마켓 아티팩트 교체, 원격 에이전트 조용한 동            cosign 서명 검증, 다이제스트 고정, tools/list 해시 핀닝(rug-pull 방어), Agent Card JWS 검증, 재검증 주기
                                    작 변경
    MCP 툴 포이즈닝·Confused             외부 MCP 서버 등록, 도구 설명 주입               snyk/agent-scan, 도구 허용목록(D9-06), 토큰 패스스루 금지(게이트웨이 토큰 교환 RFC 8693), egress allowlist,
    Deputy·Token Passthrough·SSRF                                        MCP 보안 문서 11항목 체크

    프롬프트 인젭션·간접 인젭션                 사용자 입력, RAG 문서, 도구 결과                입력·출력 필터, reviewer 게이트(D2-05), 도구 결과를 데이터로 취급, HITL(D2-06)

    데이터 유출(퍼블릭 LLM)                 confidential 문서가 API 로 전송            프라이버시 등급 L0~L3 헤더를 게이트웨이가 검증, 헤더 없으면 L2 기본, L2+ 퍼블릭 403(D1-06·D9-05)

    권한 상승                           user 가 admin 기능·다른 에이전트 DB 접근        RBAC(D9-02), 에이전트별 DB role(NOSUPERUSER·CONNECTION LIMIT·statement_timeout), aud=agent:{id} 단명 JWT

    시크릿 노출                          env 파일, 로그, Addon 코드                 compose secrets, 퍼블릭 키는 게이트웨이만 보유(NFR-S3), 로그 마스킹, ${ENV_VAR} 미해결 강제(ClawHub 규칙)

    iframe 공격                       Addon 프론트가 콘솔 조작                     에이전트별 서브도메인, CSP frame-ancestors, sandbox, postMessage origin 화이트리스트, targetOrigin 명시
    가용성                             폭주 에이전트, 무한 루프                       리소스 상한(pids 포함), 타임아웃·재시도 상한, circuit breaker, autoheal(stateless 만)

    라이선스 위반                         G4 코드 내장, 오픈코어 ee/ 포함                SBOM 라이선스 스캔 CI(NFR-C1), ee/ 제외 빌드 검사, 등급 게이트(D5-04)




13.2 신뢰 등급과 격리 연동
    등급                      조건                                  런타임                                  네트워크                                     in-process 허용

    official                플랫폼 서명 + 심사                         runc                                 정책상 필요한 egress                           가능(관리자 승인)

    partner                 검증 퍼블리셔 서명                          runc + 강화 seccomp                    egress allowlist                         불가

    community               미서명 또는 직접 업로드 zip                   gVisor(runsc) 또는 Kata                egress 기본 차단                             불가

    external                경로 C 원격 에이전트                        컨테이너 없음                              egress allowlist + 데이터 반출 통제             -




감사 결과(audit status × risk level)가 격리 강도를 결정한다. risk=High 면 자동으로 runsc + egress deny. 이것이 v1(모든 Addon 이 플랫
폼 프로세스에서 실행)과의 가장 큰 차이다.

13.3 오픈소스 라이선스
9.10 등급을 빌드 게이트로 강제한다. 특히 다음 결정은 본 PRD 가 고정한다.
         langgraph-api(Elastic-2.0)·LangGraph Platform 미의존. MIT 라이브러리(langgraph, checkpoint-postgres)만 자체 FastAPI 안에서
          실행한다.
         Open WebUI 코드 미포크. 브랜딩 조항(변경 시 30일 50 사용자 상한)이 제품화와 충돌. 기능 기준선·Pipelines 규격만 참고.
         Dify·n8n·Suna·AutoGPT platform 은 연계(M2)만. 멀티테넌트 금지·재판매 제한·관리형 서비스 금지·경쟁 제품 금지 조항.
         Redis 8 대신 Valkey. RSALv2/SSPLv1/AGPLv3 3중 라이선스 회피.
         LiteLLM enterprise/ 경계. 프로덕션 사용은 유료 구독. 공식 이미지 포함 여부 [미확인] → 법무 확인 전까지 Bifrost 병행.
         오픈 가중치 모델은 모델 단위 추적. DeepSeek-V3 원본(가중치 별도 라이선스)과 V3.1(MIT)이 다르고, Mistral 은 같은 벤더 안에서
          Apache-2.0 과 MRL 이 공존한다. Llama 4 는 'Built with Llama' 표기 의무.
         MCP 라이선스 이중 표기. MIT→Apache-2.0 전환 중이라 고지를 둘 다 적는다.
         사용자 저장소 5개에 LICENSE 부여. 마켓 게시·고객 전달 전 필수.
13.4 개인정보·데이터
대화·파일·메모리는 개인정보를 담는다. 개인정보보호법상 처리 목적·보관 기간·파기·열람·삭제권을 설치 시 고지하고 정책으로 강제
한다. 감사 원장은 프롬프트 원문 대신 해시를 기본으로 하고, auditLevel=full 에서만 원문 참조를 둔다. 비프로덕션 환경에 실데이터
반입 금지(사용자 COMPLIANCE.md 규칙 승계). 국제 고객이 있으면 GDPR 데이터 처리 계약과 퍼블릭 LLM 제공자의 학습 미사용 조건
을 확인한다. 가정: 구체 조항 적용은 배포 전 법무 확인.
근거: 정보통신망법 §47(ISMS), 개인정보보호법 §32-2(유출 통지), ISMS-P, CSAP(공공 판매 시). NIST AI RMF 1.0, OWASP GenAI LLM Top
10 2026 및 ASI01~10(선행 AegisMesh PRD 참조).

13.5 마켓·상거래
   유료 에이전트 판매는 전자상거래법·부가가치세 신고 대상이 될 수 있다. 결제·정산·세금은 X12 에서 별도 검토하고, 첫 릴리스
    는 라이선스 키 발급·검증과 영수증 증적까지만 한다.
   라이선스 키 클라이언트 검증은 우회 가능하다. 근본 강제는 서버 측 엔타이틀먼트 — 플랫폼이 LLM 프록시·시크릿 주입을 라이
    선스 유효 시에만 수행한다.
   퍼블리셔 심사는 자동 게이트 + 관리자 승인. 철회(revoke)는 즉시 카탈로그 비공개 + 설치본 경고.

13.6 윤리·오용
   에이전트가 실행하는 도구는 실제 부작용을 낸다. human_approval_required 는 메타 선언이고 게이트가 집행하며 UI 우회를 막
    는다(DP8).
   CLI 에이전트 백엔드(Claude Code 등)는 파일·셸 권한을 가진다. 작업 디렉터리 샌드박스, --allowedTools 최소화, 승인 정책을 기본
    으로 한다.
   마켓에서 이중 용도 에이전트(스크래핑·자동 대량 발송 등)는 카테고리 심사 기준을 둔다. 스텔스·감시 기능은 게시 금지.
   모델 출력의 편향·오정보는 reviewer 게이트와 평가(D10-05) 시나리오로 상시 측정한다.

13.7 알려진 실패 모드
   v1 방식 in-process 핫 디플로이를 편의상 기본으로 되돌리기 — 금지(NFR-I2).
   Agent Card 를 손으로 편집 — 금지(DP4). 생성물만.
   A2A v0.3 예제를 복사 — 와이어 비호환. v1.0.1 SDK 만.
   MCP initialize 를 기대하는 구클라이언트 — server/discover 로 두 버전 광고.
   퍼블릭 폴백이 프라이버시 등급을 무시 — 게이트웨이가 403.
   include 이름 충돌 — 접두어 강제 CI 게이트. 5개 초과 시 M2 독립 프로젝트 방식.
14. 원천 검증 — 인포그래픽·검색·v1 의 주장 검토
네 원천의 항목을 그대로 믿지 않고 2026-09-18 실측과 대조했다. 판정: 일치 / 변경(사실이 바뀜) / 부정확 / 공백(원천에 없어 추가) /
해석 주의.

14.1 인포그래픽 20 저장소 검증
 #        항목                                                 판정              근거·조치

 01       OpenClaw = 개인 AI 어시스턴트/게이트웨                        일치 + 보강         390,029★ MIT(OpenClaw Foundation). ClawHub(MIT)가 유일한 오픈소스 에이전트 마켓 서버 → D6 참조 모델로 승격
          이
 02       Langflow = 비주얼 빌더                                  일치              MIT. X01 Addon

 03       TensorFlow                                         해석 주의           현 스택에서 비중 낮음. X08 선택

 04       Transformers                                       일치 + 보강         transformers serve 가 OpenAI 호환 서버 제공(Anthropic 미지원)

 05       AutoGPT = 자율 에이전트 플랫폼                              변경              autogpt_platform/ 은 Polyform Shield(경쟁 제품 금지). 루트 MIT. 내장 불가

 06       CrewAI = 멀티에이전트 프레임워크                              일치              MIT. Flows 이벤트 기반 추가. 어댑터 후보

 07       n8n                                                변경              Sustainable Use License, .ee 파일 별도. 연계만(X04). 대체 activepieces(MIT+ee)

 08       ComfyUI                                            변경(경로)          comfyanonymous → Comfy-Org/ComfyUI 이전. GPL-3.0 격리 컨테이너

 09       Ollama = 로컬 LLM 런타임                                일치 + 보강         Anthropic /v1/messages 호환 API 제공 → v1 Claude SDK 코드 base_url 전환 가능

 10       Whisper                                            일치              MIT 모델. 서빙은 sherpa-onnx/faster-whisper

 11       Stable Diffusion WebUI                             변경              2024-07-27 이후 커밋 없음 + AGPL. 제외, ComfyUI 로 대체

 12       llama.cpp                                          일치 + 보강         llama-server 가 OpenAI(+/v1/responses)·Anthropic·/reranking 제공. 릴리스 태그 체계 2종(bNNNN·vX.Y) 병존

 13       RAGFlow                                            일치              Apache-2.0. docker/docker-compose.yml(+4변형). X07

 14       LangChain                                          일치 + 주의         MIT. LangGraph 서버(langgraph-api)는 Elastic-2.0 — 라이브러리만 사용

 15       Claude Code                                        해석 주의           저장소는 배포·이슈·플러그인용, LICENSE.md 는 Anthropic Commercial Terms. 헤드리스 -p + Agent SDK(MIT)로 백엔드화.
                                                                             플러그인 marketplace.json 은 카탈로그 규격 선례

 16       PyTorch                                            일치              BSD-3. 간접

 17       Dify                                               변경              수정 Apache-2.0: 멀티테넌트 금지·로고 제거 금지. .difypkg 규격 참고, 연계만

 18       DeepSeek-V3                                        해석 주의           원본 가중치는 DEEPSEEK LICENSE(상용 허용, 제한 승계). V3.1·R1 은 MIT. 모델 단위 라이선스 추적

 19       Gemini CLI                                         일치 + 보강         Apache-2.0, 107,051★. ACP 네이티브(gemini --acp). gemini-extension.json 규격

 20       Open WebUI                                         변경              Open WebUI License 브랜딩 조항(변경 시 50 사용자 상한). 코드 미포크, 기준선·Pipelines 규격만




요약. 20개 중 그대로 내장 가능 6, Addon 격리 4, 연계만 4, 규격·패턴 참고 5, 제외 1(SD WebUI). 라이선스 변경·조건 발견 6건
(05·07·11·17·20 + 14 의 서버). 경로 이전 1건(08).

14.2 GitHub 검색 결과 검증
 주장·기대                                                             판정                근거

 검색 상위가 멀티 에이전트 플랫폼 후보를 준다                                         부정확               총 2,256건 중 상위 20 의 절반 이상이 Jupyter 튜토리얼. 1위 1,064★. 플랫폼 백본 후보 0

 squad·ai-dispatch·AgentBridge·ijfw·multi-ai-collaboration         공백 → 반영           '여러 AI CLI 를 묶는 협업 도구'라는 공통 패턴 → D1-04 CLI 백엔드 브리지 정식화

 lyraios = MCP 에이전트 OS                                             해석 주의             2025-03 정체. 개념만 D7

 Aether-desktop-orchestrator                                       부정확               index.html 만 있는 배포 랜딩 저장소, 라이선스 없음. 제외

 라이선스 없는 저장소 3건(kaymen99·AgentBridge·Aether)                       조치                코드 차용 금지(G5)

 snowdreamtech/template AGENTS.md 단일 진실                            일치                v1 이 이미 AGENTS.md 보유. D4 표준




14.3 v1 템플릿 주장 검증
 v1 주장(README·PRD.md)                                             판정               AgentPlaza 조치

 A2A Protocol v1.0 엔드포인트(F12)                                     변경               router_a2a 는 v0.x 스타일(status 문자열, kind 판별). v1.0.1 은 SCREAMING_SNAKE enum·UUID·kind 제거·JWS 서명.
                                                                                   a2a-python SDK 로 교체

 Per-agent MCP 프록시 포트 20000–59999(F12)                            해석 주의            포트 방식은 MCP 무상태화(2026-07-28)로 불필요. 경로 /mcp/{id} + 게이트웨이. 포트 모드는 호환 옵션
 MCP JSON-RPC 2.0(standalone)                                변경          2026-07-28 은 initialize 제거·server/discover 필수·Mcp-Method 헤더. 두 버전 동시 광고

 prod compose network_mode: host + pid: host + docker.sock   부정확(보안)     NFR-I3 위반. Traefik 라벨 라우팅 + 접두 네트워크로 교체. docker.sock 은 프록시·빌드 서비스만
 마운트
 Addon SQL 을 플랫폼 DB 에 직접 실행(PG→SQLite 변환)                    변경          db.isolation own 기본, shared-schema 는 전용 role

 importlib 핫 디플로이 = 즉시 사용                                    해석 주의       속도는 장점, 격리는 단점. 컨테이너 모드 기본 + 신뢰 퍼블리셔 in-process 옵션

 Ollama 폴백은 tool_use 미지원 텍스트만(F3)                            변경          Ollama 는 현재 OpenAI 호환 도구 호출·구조화 출력 지원. 게이트웨이가 도구 호출 유지

 오프라인 실행 보장(F28)                                             일치          승계. airgap 프로파일

 Claude 기본 모델 sonnet/haiku                                   해석 주의       게이트웨이 별칭으로 추상화(DP3). 실제 모델은 카탈로그

 Out of Scope: SSO·멀티테넌시·마켓                                  변경          SSO·마켓은 범위 안. 멀티테넌시는 X09




14.4 표준 사양 가정 검증
 가정                                                          판정        실측
 MCP 최신은 2025-06-18 또는 2025-11-25                            변경        2026-07-28(파괴적 재설계). 12개월 폐기 창 정책 도입

 A2A 는 v0.3 또는 v1.0                                          변경        v1.0.1(2026-05-28). a2a.proto 정본, LF 산하

 Agent Card 경로 agent.json                                    변경        agent-card.json

 OTel GenAI 규약은 semantic-conventions 본체                      변경        semantic-conventions-genai 별도 저장소(2026-05-05, Development)

 AAIF 2025-12 설립, MCP 이관                                     부정확       org 생성 2025-11-14. goose·AGENTS.md 이관, MCP 이관 흔적 없음

 ACP = AGNTCY Agent Connect Protocol                         해석 주의     AGNTCY ACP 는 아카이브. 본 문서의 ACP 는 Zed Agent Client Protocol

 pydantic-ai Agent.to_a2a()                                  변경        제거됨(fasta2a 별도)

 compose 최신은 v2.x                                            변경        v5(v5.5.1 (2026-09-03)). models·provider 요소 존재

 Redis 는 BSD                                                 변경        8.0+ 3중 라이선스. Valkey

 tensorzero 현역                                               변경        2026-06 아카이브




14.5 누락 검증
요구사항 (1)~(8) → 도메인 추적표(3.6)에 빈 칸 없음. 인포그래픽 20 → 귀속 ID 20/20. 검색 상위 14 → 판정 14/14. v1 F1~F32 → 처
리 표 18행에 전수 매핑. 항목 70 = FR-D 70 = 카탈로그 70. 후순위 12, 플랫폼 12. CI 스크립트 verify-coverage 가 같은 검사를 자동화한
다(10.6).
15. 지표, 로드맵, 리스크

15.1 성공 지표
지표                                            기준선(가정)                            목표                                    측정

M1 독립 기동 성공률(70 항목)                           v1: 내장 2 + 템플릿 4                   100% /health ok                       CI 매트릭스(NFR-I1)
마켓 설치 → 네비 노출                                 v1 zip: 30초(front 재빌드)             5분 이내(이미지 빌드 포함)                      타이머(NFR-U2)
빈 서버 → 첫 대화                                   없음                                 30분 이내                                신규 운영자 측정(NFR-U1)
퍼블릭 장애 시 로컬 폴백                                v1: 텍스트만                           30초 내, 도구 호출 유지                       장애 주입(NFR-L1)
프라이버시 등급 위반                                   없음                                 0                                     게이트웨이 403 로그 + 원장

MCP·A2A 계약 시험 통과                              v1: v0.x 스타일                       2026-07-28 · v1.0.1 100%              inspector·a2a 클라이언트

G4 코드 기본 이미지 링크                               미측정                                0                                     SBOM 라이선스 CI

Agent Card·server.json 과 런타임 불일치              v1: 손코딩                            0                                     생성물 diff 시험(NFR-P3)
감사 누락 도구 호출                                   없음                                 0                                     원장 샘플링

한국어 UI 키 커버리지                                 v1: ko/en                          100%                                  i18n 린트




15.2 단계
단계                       기간(가정)               산출                                                                                                           P

S0 골격                    2주                   agent.yaml 스키마·검증기, compose 골격, 루트 include, verify-coverage CI, LICENSE 부여                                   P0

S1 v1 이식                 4주                   Orchestrator·Assistant 를 agent.zip 규격 컨테이너로. 게이트웨이(LiteLLM/Bifrost) + Ollama + 퍼블릭 어댑터. 셋업 위저드               P0

S2 패키지·레지스트리             4주                   8단계 파이프라인(1·2·5~8), 컨테이너 디플로이, v1 flat zip 호환 변환, 카탈로그·capability 인덱스, iframe 마운트                            P0

S3 프로토콜 정식화              3주                   MCP 2026-07-28 SDK, a2a-python v1.0.1, Agent Card 서명, agentgateway 정책, AG-UI 이벤트                             P0

S4 마켓 3경로                4주                   스토어 UI, 다운로드·설치(OCI/zip), 직접 설치(Git/URL), 연동·연계(Card/MCP URL + 등록 게이트)                                       P0

S5 신뢰·격리                 3주                   서명·SBOM·취약점 게이트, 라이선스 등급, gVisor 연동, 시크릿(sops), OIDC                                                         P1

S6 관측·평가·내구성             3주                   OTel GenAI, Opik, promptfoo 게이트, Temporal 선택, 백업·롤백                                                          P1

S7 구매·퍼블리셔               3주                   라이선스 토큰(Ed25519), 엔타이틀먼트, Kill Bill 어댑터, 퍼블리셔 심사·철회                                                          P1

S8 Addon 확장              연속                   X01~X07 Addon(Langflow·ComfyUI·음성·RAGFlow·샌드박스·브라우저), 채널, 알림                                                 P2




합계 P0 약 17주(가정). v1 이 이미 증명한 범위(S1·S2 절반)는 이식이지 신규 개발이 아니다.

15.3 리스크
ID         위험                                                                           완화

R1         MCP 사양 파괴적 개정 재발(2025-11-25→2026-07-28 에서 세션·핸드셰이크·Tasks                     버전 협상을 게이트웨이에 집중, Addon 은 SDK 뒤. 사양 릴리스 watch
           전부 변경)

R2         A2A v0.3 자료 오염(예제·블로그 대량)                                                    v1.0.1 proto 만 정본. 인용 금지 규칙

R3         LiteLLM enterprise/ 라이선스 경계                                                  법무 확인. Bifrost 병행 PoC

R4         langgraph-api ELv2 오용                                                        CI 에서 패키지 금지 목록(langgraph-api, langgraph-runtime-inmem)

R5         임의 코드 실행(직접 업로드 zip)                                                         컨테이너 기본 + gVisor + egress deny + 관리자 권한

R6         include 이름 충돌·프로젝트 단일화 한계                                                    접두어 CI 게이트. 5개 초과 시 M2 독립 프로젝트 전환

R7         OTel GenAI semconv 미성숙(Development, 릴리스 없음)                                  속성 정규화 계층 분리

R8         오픈코어 ee/ 코드가 공식 이미지에 포함                                                      SBOM 스캔 + ee/ 제외 빌드 검사

R9         모델 라이선스 변경·조건(Llama 4 표기, Gemma 원격 제한, EXAONE NC)                            commercial_use 필드, conditional 기본 비활성, verified_at 180일 경고

R10        Apple Silicon GPU 미지원(Docker Metal 불가)                                       호스트 네이티브 Ollama 브리지 문서화(v1 mlx 경로 승계)

R11        Docker Desktop 유료 기준으로 기업 도입 마찰                                              Docker Engine/compose CLI 는 무관 — 문서 구분. colima·Podman Desktop 경로

R12        유료 마켓의 결제·세금 법규                                                              X12 분리, 첫 릴리스는 라이선스 증적까지

R13        사용자 저장소 LICENSE 부재                                                           S0 에서 부여
    R14       정체 저장소 의존(Portkey·infinity·ragas·fastapi_mcp·cookiecutter)   1순위에서 제외, 분기별 재확인




15.4 다음 결정
         게이트웨이를 LiteLLM(기능 폭)으로 갈지 Bifrost(전부 Apache-2.0)로 갈지 — 법무 답변에 종속.
         Assistant 에이전트 SDK 를 openai-agents-python 으로 고정할지 pydantic-ai(durable_exec·ag_ui 통합)로 갈지.
         Addon 프론트 통합의 Module Federation 허용 범위(1st-party 만 vs 전면 iframe).
         MCP 포트 모드(v1 호환)를 얼마나 오래 유지할지 — 외부 클라이언트 현황에 종속.
         Temporal 도입 시점 — LangGraph 체크포인터로 버티는 상한(승인 대기 일수·SLA).
         무료·사내 카탈로그(git+JSON)와 유료 마켓 서버(ClawHub 참조)의 이원화 시점.
이 결정은 /recommend 스택 추천 단계에서 확정한다. 본 PRD 는 라이선스 등급, 세 모드, agent.zip 규격, 표준 프로토콜 버전, 격리
원칙을 고정한다.
16. 참조 프로젝트 분석 (v2)
v2 는 사용자 로컬의 멀티 에이전트 프로젝트 11종을 소스 수준으로 분석해 Addon-Agent 후보군을 도출한다. 이 프로젝트들은 모두
v1 기준선(pub-MultiAIAgent-Template)과 같은 골격(Orchestrator + AI Assistant + Addon 핫디플로이 + MCP/A2A)을 공유하므로, 각 프로
젝트의 도메인 에이전트·라우터 기능·마켓 자산이 AgentPlaza 의 agent.zip 후보로 그대로 정규화된다.

16.1 참조 프로젝트 11종
 약칭                       경로(로컬)                               도메인                 업종                 한 줄 정의                                                 v2 기여

 MultiAIAgent-Template    eden-MultiAIAgent/MultiAIAgent-      platform            J 정보통신             v1 기준선. Orchestrator + Assistant + flat zip 핫          AgentPlaza 코어 원형(1장). 5부 골격·9유형
                          Template                                                                    디플로이 + per-agent MCP + A2A +                           meta.json
                                                                                                      standalone export

 SeCuardian               wise-SeCuardian/SeCuardian           security            J 정보통신             보안 Multi-AI Agent 템플릿(Orchestrator +                   보안 도메인 에이전트·behavior-
                                                                                                      Assistant + 인증·설정·MCP·A2A·Registry +                   noti·ShellAgent 템플릿
                                                                                                      Addon 핫디플로이)

 SeCuardian-Basic         wise-SeCuardian/SeCuardian-Basic     security            J 정보통신             보안 코어 런타임 배포판(코어는 하나, 보안                               Basic(코어) vs Marketplace(자산) 분리 패턴 =
                                                                                                      Agent 는 마켓에서). Basic/Marketplace 분리 모                  AgentPlaza Basic/Store 이원화 근거
                                                                                                      델
 SeCuardian-Marketplace   wise-SeCuardian/SeCuardian-          security+platform   J 정보통신             보안 마켓 플랫폼.                                             마켓 데이터모델·자산 카탈로그(marketplace-
                          Marketplace                                                                 Marketplace·Workflow·RAG·Playground·Guardrai           assets)·워크플로 DAG·가드레일 24도메인·자
                                                                                                      ls 내장 + 보안 자산 30여 종 카탈로그                               산 blob·설치 상태머신

 SecuFTPL                 wise-SeCuardian/SecuFTPL             llmops              J 정보통신             보안 LLM 파인튜닝 파이프라인(데이터셋 구                               LLMOps·파인튜닝 파이프라인 에이전트군
                                                                                                      축→다중 베이스 파인튜닝→평가→피드백                                   (X08 구체화)
                                                                                                      루프→야간 재튜닝·재배포)

 MAS-Basic                eden-MultiAIAgent/MAS-Basic          platform            J 정보통신             Template 준용 기본판 런타임(코어는 하나,                            manifest v2 스키마
                                                                                                      Agent 는 MAS-Marketplace 에서). manifest v2               (schema_version·compat.topologies·pricing·req
                                                                                                      스키마 공유                                                 uires) = agent.yaml 확장 근거

 MAS-Marketplace          eden-MultiAIAgent/MAS-Marketplace    platform            O 공공행정+전업          기업·정부/지자체용 AI 에이전트 마켓. 조직                              마켓 3축(조직·카테고리·등급)·배치
                                                                                   종                  (테넌트)·계층형 카테고리·등급별 노출·도입                               (deploy_scope)·도구정책·컬렉션(도메인
                                                                                                      (배치)·리뷰·게시자·서명                                         팩)·Ed25519 서명·다운로드 무결성

 DOPQ-MultiAIAgent        eden-project/DOPQ-MultiAIAgent       manufacturing       C 제조               제조 SME 수요예측·주문·계획·품질(DOPQ) 폐                           제조 업종 에이전트(수요예측·주문자동화·생
                                                                                                      쇄루프 플랫폼                                                산계획·품질·실적학습)

 HRAgent-MultiAIAgent     eden-project/HRAgent-MultiAIAgent    hr                  M 전문·과학기술          채용 자동화 HR SaaS(공고 작성→서류 분석                             인사·채용 업종 에이전트 + PII·채용절차 준법
                                                                                                      →스크리닝→면접 질문 생성)

 SmartHaccp-MultiAgent    eden-project/SmartHaccp-MultiAgent   food-safety         C 제조(식품)           HACCP 전산화 17개 도메인 + 도메인 에이전                            식품안전 업종 에이전트 8종 + CCP 모니터링·
                                                                                                      트 8종                                                   교정·시정·PDCA
                                                                                                      (advisor·alert·calibration·corrective·field·monitori
                                                                                                      ng·pdca·record)

 MAA-Bonded-Areas         eden-project/MAA-Bonded-Areas        logistics-customs   H 운수·창고            보세 구역 자동 수입·처리 관리(문서·환율·외                              물류·통관 업종 에이전트 + 수입신고·환율·외
                                                                                                      자비율·신고 자동화)                                            자비율·문서 OCR




라이선스 파일은 대부분 [확인 필요] 다(v1 사용자 저장소와 동일 이슈). 고객 전달·마켓 게시 전에 명시가 필요하다(부록 F, 13.3).

16.2 세 갈래 계열
 계열                       프로젝트                                                                                      AgentPlaza 대응

 코어·마켓 플랫폼                MultiAIAgent-Template, MAS-Basic, MAS-Marketplace, SeCuardian, SeCuardian-Basic,          Basic(코어) vs Marketplace(자산 카탈로그) 분리 = AgentPlaza 의 코
                          SeCuardian-Marketplace                                                                    어/스토어 이원화 근거. 마켓 데이터 모델·배치·서명·리뷰를 D5·D6 에
                                                                                                                    반영(16.4)
 도메인 특화                   DOPQ(제조)·HRAgent(인사)·SmartHaccp(식품안전)·Bonded(물류·통관)                                       각 도메인 에이전트·라우터 기능을 업종별 Addon-Agent 후보로(17·18
                                                                                                                    장). 같은 골격이라 zip 규격으로 정규화 가능

 LLMOps 파이프라인             SecuFTPL                                                                                  데이터셋·파인튜닝·평가·재배포 단계를 LLMOps 도메인 Addon-Agent 후
                                                                                                                    보로. v1 의 X08(파인튠)을 구체화




16.3 인벤토리 방법
프로젝트별로 README·PRD·AGENTS.md·app/agents/*.py(클래스·시스템 프롬프트·도구)·app/routers/*.py(엔드포인
트)·addon-agents/_templates·sql/*/01_init.sql(도메인 테이블)·front/src/pages·docker-compose·marketplace-assets 를 읽어 에이전트·기능
단위를 후보로 추출했다. 공통 템플릿(Board·UserManager·RagAgent·ServiceAgent·ToolProxyAgent·ShellAgent·McpServer)은 한 번만 집계
했다. 각 후보에 업무·업종·도메인 3축, 독립 구동 등급(H/M/L), zip 구성(fe·be·db·meta), 근거 경로를 기록했다(candidates.tsv → 18장).
추출 결과 요약은 17.5, 전수표는 18장이다. 확인 못한 기능은 [미확인] 으로 두고 추측하지 않았다.

16.4 마켓플레이스 설계 준용 (SeCMP · MAS)
두 마켓 프로젝트가 이미 구현·시험한 데이터 모델과 흐름을 AgentPlaza D5·D6 의 정본으로 삼는다. 새로 발명하지 않는다.
 테이블·엔티티                                        역할                                                                                                   출처

 marketplace_assets                             카탈로그 자산(key·version·category·display·description·checksum·signature·status)                          SeCMP

 marketplace_asset_blobs                        사용자 등록 ZIP BLOB(key@version 당 1개)                                                                    SeCMP

 marketplace_installs                           설치 이력(단일 활성 버전·force·해제 시 흔적 정리)                                                                     SeCMP

 tbl_category                                   계층형 카테고리(parent_id·slug·sort_order)                                                                  MAS

 agent_categories                               에이전트↔카테고리 N:M 매핑                                                                                     MAS

 orgs / org_groups / org_members                조직(테넌트)·부서·구성원 — 배치 대상 단위                                                                            MAS

 adoptions                                      도입=배치(deploy_scope org|group|user·nav_group·accepted_permissions·tool_policy·pinned_version)         MAS

 collections / collection_items                 도메인 팩(설치 순서대로 일괄 도입)                                                                                 MAS

 publishers                                     게시자(slug·is_verified·통계). 업로드 시 자동 생성                                                                MAS

 agent_versions                                 버전 이력(checksum·signature·approval_status·released_by)                                                MAS

 reviews / review_votes                         리뷰(도입자만·평점 분포·업보트·게시자 답글·숨김)                                                                         MAS

 tbl_download_log                               다운로드 이력(분당 30회 제한·감사·download_count)                                                                 MAS

 marketplace_host_catalog                       host(레지스트리 서버) 공개 카탈로그 API(ping·catalog·download)                                                    SeCMP




 마켓 설계 요소                           SeCMP / MAS 실측                                                                                         AgentPlaza 반영

 카테고리 체계                            MAS tbl_category 계층형(제조업>식품, 경영지원>HR), slug·parent_id·sort_order. SeCMP                                업무·업종·도메인 3축(17.1~17.3). 카테고리는 slug 계층
                                    marketplace-assets/{security,utilities,builtin,addon}                                                  + agent_categories N:M

 자산 저장                              SeCMP: 시드는 marketplace-assets/{cat}/{key}.zip, 사용자 등록은 DB BLOB(marketplace_asset_blobs), 설치는 addon-    D5-06 카탈로그 + D6-03. AgentPlaza 는 OCI 아티팩트 기본,
                                    agents/deployed/{key}                                                                                  BLOB·파일 병행

 설치·해제                              단일 활성 버전, force 중복 확인, 해제 시 테이블 DROP·deployed 삭제·MCP 중지·web 재빌드까지 완전 정리                                D5-05·NFR-I6(60초 내 흔적 제거). SeCMP 상태머신 그대로

 도입=배치                              MAS: adoption 이 아니라 deployment. deploy_scope(org|group|                                                D6-05 + D9-02. tool_policy 는 게이트웨이 강제(11.7)
                                    user)·nav_group·accepted_permissions·tool_policy(allow/deny, deny 우선)·pinned_version

 조직·등급                              MAS 3등급(supervisor 플랫폼/admin 조직/user), 노출 정책(allowed_org_types: government 전용 등), org_groups(부         D9-01·D9-02. 멀티테넌시는 X09(선택)
                                    서)

 컬렉션(도메인 팩)                         MAS collections — 설치 순서대로 일괄 도입(hr-pack 등)                                                             업종별 스타터 팩(17.6). 도메인 후보를 묶어 원클릭 도입

 게시자·리뷰·통계                          MAS publishers(업로드 시 자동 생성, supervisor 인증)·reviews(도입자만·평점 분포·업보트·답글·숨                                 D6-06. Ed25519 서명은 v1 결정 유지
                                    김)·download_log(분당 30회·감사)

 카탈로그 v2 메타                         MAS manifest v2: schema_version·compat.topologies[T1~T6]·compat.hardware·pricing(표시                    agent.yaml 확장(17.4). v1 4필드 meta.json 상위 호환
                                    만)·requires(core·agents)·tags·role·example_prompts·data_sources·screenshots·readme

 워크플로·RAG·가드레일·플레이그                 SeCMP 내장 5종: workflow(DAG 8노드·webhook·Dify DSL import·풀스크린 빌더)·rag(BM25+dense                          D2·D3·D6·D9 의 참조 구현. 후보 카탈로그의 공통 도메인
 라운드                                RRF·pgvector·Qdrant)·guardrails(24도메인 규칙·regex+LLM classifier)·playground(A/B)·marketplace             (18.2)

 host 레지스트리                         SeCMP marketplace-host API(ping·catalog·download, ZIP SHA256). 외부 SeCuardian 이 원격 설치                   D6-07 마켓 서버 + 경로 C 연동. MCP registry server.json 호
                                                                                                                                           환




16.5 배치 토폴로지 (compat.topologies)
MAS manifest v2 의 compat.topologies(T1~T6)를 그대로 채택한다. 각 Addon-Agent 는 agent.yaml 에 지원 토폴로지를 선언하고, 설치 시
플랫폼이 호환성을 검사한다.
 코드                 토폴로지                                  설명
 T1                 Cloud-API                             퍼블릭 LLM API 만. GPU 불필요. 최소 자원

 T2                 온프렘 GPU                               로컬 LLM(vLLM 등) + GPU. 프라이버시

 T3                 Apple Silicon                         맥 네이티브 Ollama/MLX 브리지. 개발·소규모

 T4                 Cloud(전체)                             클라우드 컨테이너 배포. 퍼블릭+로컬 혼합

 T5                 Hybrid                                로컬 LLM + 퍼블릭 폴백. 등급별 라우팅
T6   Kubernetes   K8s + Helm. 다중 노드·HA(X10 선택)
17. Addon-Agent 후보 카탈로그 — 분류 체계 (v2)
참조 프로젝트 11종에서 도출한 Addon-Agent 후보를 업무·업종·도메인 3축으로 분류한다. 모든 후보는 v1 의 agent.zip 규격
(agent.yaml + frontend/ + backend/ + database/ + compose.yaml)을 따르며, docker compose --profile standalone up 으
로 홀로 구동(M1)되고, 마켓에서 골라 즉시 사용(M3)되며, 표준 프로토콜(MCP·A2A)로 연계(M2)된다.

17.1 분류 축 1 — 업무(기능)
에이전트가 무엇을 하는가. 카테고리 slug 의 1차 축이며 카탈로그 필터의 기본 파셋이다.
 ID     업무                       포함 기능

 W01    대화·어시스턴트                 채팅·세션·도구 UX·멀티모달·메모리·채널

 W02    오케스트레이션                  의도·계획·라우팅·실행 패턴·게이트·상태

 W03    지식·RAG                   문서 수집·청킹·임베딩·하이브리드 검색·인용

 W04    워크플로·자동화                 DAG 빌더·노드·트리거·HITL·스케줄

 W05    플레이그라운드·평가               프롬프트·모델·RAG 실험·A/B·비용·품질

 W06    가드레일·준법                  PII·인젝션 필터·도메인 규칙·정책·증거 수집

 W07    보안 운영(SOC·탐지·대응)         SIEM·IDS·런타임 탐지·SOAR·위협 인텔

 W08    취약점·공급망                  CVE·API·CI/CD·이미지·악성코드·시크릿 스캔

 W09    신원·접근·권한                 IAM·PAM·mTLS·네트워크 정책·AD 점검

 W10    관측·모니터링                  OTel·메트릭·로그·헬스·대시보드·MTTD/MTTR

 W11    AI/에이전트 보안               위협모델·레드팀·평가 게이트·에이전트 설정 감사

 W12    모델·LLMOps                데이터셋·파인튜닝·양자화·평가·서빙·재배포

 W13    인사·채용(HR)                공고·서류·스크리닝·면접·온보딩

 W14    생산·수요·품질(제조)             수요예측·주문·생산계획·품질검사·실적학습

 W15    식품안전(HACCP)              CCP 모니터링·교정·시정조치·기록·PDCA·현장점검

 W16    물류·통관                    수입신고·환율·외자비율·재고·입출고·문서 OCR

 W17    문서·데이터 처리                OCR·추출·분류·변환·요약

 W18    플랫폼·마켓                   카탈로그·등록·심사·배치·구매·게시자·리뷰

 W19    공통 유틸                    게시판·사용자 관리·셸·프록시·대시보드·트래픽




17.2 분류 축 2 — 업종(KSIC 대분류)
누구를 위한 에이전트인가. 전업종 공통과 업종 특화를 가른다. MAS 노출 정책(allowed_org_types)과 결합해 조직 유형별 카탈로그를
구성한다.
 KSIC        업종              AgentPlaza 관련
 전업종         -               업종 무관 공통 에이전트(대화·RAG·워크플로·게시판·사용자)

 J           정보통신            SW·SaaS·보안·플랫폼·LLMOps

 C           제조              생산·품질·수요예측(DOPQ)·식품안전(HACCP)

 H           운수·창고           물류·보세·통관(Bonded)

 O           공공행정            정부·지자체 도입, 컴플라이언스·증거

 K           금융              신용정보·가드레일 금융 도메인

 M           전문·과학기술         인사서비스(HR)·컨설팅

 G           도소매             재고·주문·POS 연계




17.3 분류 축 3 — 도메인(생태계)
어느 기술·업무 생태계에 속하는가. 참조 프로젝트 계열과 대체로 1:1 이며, 18장 전수표의 장 구분이 된다.
 도메인                   이름                    업무 매핑·계열

 common                공통                    W01·W03·W04·W05·W19. 어느 업종에나 설치

 security              보안                    W07·W08·W09·W10·W11. SeCuardian 계열

 llmops                LLMOps                W12. SecuFTPL 계열

 governance            거버넌스·준법               W06. ISMS-P·개인정보·감사

 platform              플랫폼                   W02·W18. 코어·마켓

 hr                    인사                    W13. HRAgent 계열

 manufacturing         제조                    W14. DOPQ 계열

 food-safety           식품안전                  W15. SmartHaccp 계열

 logistics-customs     물류·통관                 W16. Bonded 계열

 docintel              문서지능                  W17. OCR·추출




17.4 카테고리 slug 체계
MAS tbl_category(계층형 slug·parent_id) 를 그대로 채택한다. 루트는 업종, 2단계는 업무, 태그로 도메인·토폴로지를 보조 표기한다.
에이전트↔카테고리는 N:M(agent_categories).
# 카탈로그 카테고리 트리 (예시 — MAS tbl_category 준용)
전업종(common)
├─ 대화·어시스턴트       common-assistant                              # W01
├─ 지식·RAG           common-rag                                    # W03
├─ 워크플로·자동화       common-workflow                               # W04
├─ 플레이그라운드·평가     common-playground                             # W05
└─ 공통 유틸           common-utility                                # W19 (Board·UserManager·ShellAgent…)
정보통신(J)
├─ 보안운영          ict-security-soc                               # W07    도메인=security
├─ 취약점·공급망       ict-security-vuln                              # W08
├─ 신원·접근         ict-security-iam                               # W09
├─ 관측·모니터링       ict-observability                              # W10
├─ AI·에이전트 보안    ict-ai-security                                # W11
├─ 거버넌스·준법       ict-governance                                 # W06   도메인=governance
├─ 모델·LLMOps       ict-llmops                                     # W12   도메인=llmops
└─ 플랫폼·마켓         ict-platform                                   # W02·W18 도메인=platform
제조(C)
├─ 생산·수요·품질      mfg-dopq                                       # W14    도메인=manufacturing
└─ 식품안전(HACCP)     mfg-food-haccp                                # W15    도메인=food-safety
운수·창고(H)
└─ 물류·통관         logi-customs                                   # W16    도메인=logistics-customs
전문·과학기술(M)
└─ 인사·채용         hr-recruiting                                  # W13    도메인=hr
공공행정(O)
└─ (전업종·거버넌스 재사용 + 노출정책 government)

# agent.yaml 매핑
metadata.categories: [ict-security-soc]                           # slug 목록 (N:M)
metadata.tags: [security, T2, T5, siem]                           # 도메인·토폴로지·자유 태그
spec.industry: J                                                  # KSIC 축
spec.work: W07                                                    # 업무 축




17.5 독립 구동(Zip) 규격 — 도메인 Addon-Agent
도메인 에이전트도 공통 규격을 따른다(10.2·10.3). 참조 프로젝트의 도메인 에이전트는 대개 plaza DB·인증에 결합돼 있어, 독립 구동
등급(standalone)을 H/M/L 로 표기하고 L 인 경우 독립 구동을 위한 대체(목 데이터·CSV 업로드·수동 입력·외부 어댑터)를 명시한다.
 결합 요인                              독립 구동 시 대체                                       예
 플랫폼 공유 DB(Postgres)                db.isolation=own 전용 컨테이너 또는 sqlite               게시판·HR·품질 테이블

 플랫폼 인증(JWT/RBAC)                   standalone 프로파일에서 로컬 관리자 계정 + 서비스 API 키          모든 에이전트

 퍼블릭 LLM 키                          env LLM_BASE_URL 로 로컬 Ollama 직결                  대화·요약·분류

 외부 시스템(ERP·MES·UNI-PASS·환율 API·이   어댑터 인터페이스 + 목/CSV 업로드/수동 입력 폴백                   DOPQ 주문·Bonded 신고·HACCP 센서
 메일·센서)

 선행 에이전트(requires.agents)               compose depends_on 또는 컬렉션(도메인 팩)으로 함께 설치                            compliance-isms → 모니터 에이전트들

 GPU                                    compat.gpu=optional, CPU 폴백 또는 퍼블릭 LLM                              파인튜닝·임베딩




등급 정의: H 외부 의존 없음, 코어만으로 M1 가능 / M 외부 어댑터를 목·업로드로 대체하면 M1 가능 / L 외부 시스템·데이터가 사실상
필수, M1 은 데모 한정.

17.6 후보 수량과 도메인 분포
 도메인                              후보 수           독립 구동                           출처 프로젝트
 플랫폼 (platform)                   73             H 31 · M 13 · L 29              DOPQ-MultiAIAgent, HRAgent-MultiAIAgent, MAS-Basic, MAS-Mark

 제조 (manufacturing)               38             H 7 · M 19 · L 12               DOPQ-MultiAIAgent, DOPQ-MultiAIAgent, HRAgent-MultiAIAgent,

 공통 (common)                      11             H7·M3·L1                        DOPQ-MultiAIAgent, MAA-Bonded-Areas, MAS-Basic, SeCuardian,

 인사 (hr)                          31             H 12 · M 10 · L 9               HRAgent-MultiAIAgent, HRAgent-MultiAIAgent, MAS-Basic, MAS-B

 식품안전 (food-safety)               32             H 8 · M 16 · L 8                MAS-Basic, SmartHaccp-MultiAgent

 거버넌스·준법 (governance)             24             H 12 · M 9 · L 3                MAA-Bonded-Areas, MAA-Bonded-Areas, MAS-Basic, MAS-Basic, MA

 물류·통관 (logistics-customs)        24             H 21 · M 2 · L 0                MAA-Bonded-Areas, MAA-Bonded-Areas, MAS-Basic

 보안 (security)                    43             H 15 · M 27 · L 1               MAS-Basic, MAS-Marketplace, SeCuardian, SeCuardian, SeCuardi

 문서지능 (docintel)                  3              H3·M0·L0                        MAS-Basic

 LLMOps (llmops)                  24             H 9 · M 15 · L 0                SeCuardian, SeCuardian-Marketplace, SecuFTPL




총 후보 303종(공통 템플릿 포함). 도메인 10개. 18장에 도메인별 전수표를 싣는다. 공통(common) 도메인은 어느 업종에나 설치되고,
나머지는 업종·계열별 스타터 팩(컬렉션)으로 묶어 원클릭 도입한다.

17.7 업종별 스타터 팩 (컬렉션)
MAS 컬렉션(설치 순서대로 일괄 도입)을 업종 팩으로 구성한다. 팩 하나 = 그 업종을 바로 쓰게 하는 최소 에이전트 묶음.
 팩 slug                      대상                               구성(요지)

 pack-common                 전업종 기본                           assistant + orchestrator + RAG + 게시판 + 사용자관리

 pack-security               J 보안팀                            SOC·취약점·IAM·관측·AI보안 핵심 + 가드레일 + ISMS 증거

 pack-llmops                 J LLM 운영                         데이터셋 + 파인튜닝 + 평가 + 서빙 + 재배포

 pack-manufacturing          C 제조                             수요예측 + 주문 + 생산계획 + 품질 + 실적학습

 pack-food-haccp             C 식품                             CCP 모니터링 + 교정 + 시정조치 + 기록 + PDCA + 알림 + 자문

 pack-logistics              H 물류·통관                          문서 OCR + 수입신고 + 환율 + 외자비율 + 재고·입출고

 pack-hr                     M 인사                             공고작성 + 서류분석 + 스크리닝 + 면접질문 + 온보딩

 pack-govtech                O 공공                             pack-common + 거버넌스·가드레일(공공 도메인) + 노출정책 government




팩은 requires.agents 로 설치 순서를 정하고, deploy_scope(org|group|user)로 배치 범위를 정한다. 각 팩은 지원 토폴로지(T1~T6)를 함
께 표기한다.
18. 카테고리별 세부 Agent 배치 (v2)
17장 분류에 따라 참조 프로젝트 11종에서 도출한 Addon-Agent 후보를 도메인별로 전수 배치한다. 각 행은 독립 구동(Zip) 후보 하나
다. 열: 키 / 이름 / 유형 / 업무·업종 / 독립 구동 등급 / zip 구성 / 출처. capabilities·근거 경로는 candidates.tsv 에 보존한다.

18.1 읽는 법
 열                     뜻
 agent_key             카탈로그 키(소문자). agent.zip 의 metadata.id 후보
 유형                    agent_type(app·service·rag·tool-proxy·reviewer·execution·hitl·memory·federation·llm-provider)

 업무/업종                 17.1 업무(요지) / 17.2 KSIC
 독립                    H 코어만으로 M1 / M 어댑터 목·업로드로 M1 / L 외부 시스템 사실상 필수

 zip                   fe·be·db·meta 중 필요한 구성
 출처                    도출 근거 참조 프로젝트




18.2 공통 (common) — 11종
 키                           이름                                       유형                   업무/업종                 독립    zip              출처

 board                       게시판 (Board)                              app                  플랫폼공통/전업종             M     `fe;be;db;meta   DOPQ-MultiAIAgent, MAS-Basic, SeCuardian,
                                                                                                                                        SmartHaccp-MultiAgent

 usermanager                 사용자 관리 (UserManager)                     app                  플랫폼공통/전업종             M     `fe;be;db;meta   DOPQ-MultiAIAgent, MAA-Bonded-Areas, MAS-Basic,
                                                                                                                                        SeCuardian

 example                     예시 도메인 에이전트(스텁)                          app                  AI대화/J                H     be               MAA-Bonded-Areas

 mcpserver                   MCP 서버 카드 템플릿                            tool-proxy           외부 MCP 서버 게           L     meta             MAS-Basic
                                                                                           시/J

 mailtriage                  메일 트리아지 (MailTriage)                     app                  커뮤니케이션·고객             H     be,db,meta       MAS-Basic
                                                                                           대응/전업종

 translator                  번역 (Translator)                          service              커뮤니케이션·고객             M     be,meta          MAS-Basic
                                                                                           대응/전업종

 kbconnector                 지식베이스 커넥터 (KBConnector)                  rag                  사내 지식검색/J             H     be,db,meta       MAS-Basic

 RagAgent                    RAG/Knowledge Agent                      rag                  RAG지식/전업종             H     `be;db;meta      SeCuardian

 ServiceAgent                서비스 Agent                                service              (범용 골격)/전업종           H     `be;meta         SeCuardian

 ToolProxyAgent              Tool Proxy Agent                         tool-proxy           시스템연동/전업종             H     `be;meta         SeCuardian

 ShellAgent                  셸 진단 (ShellAgent)                        shell                인프라운영/전업종             H     fe;be;meta       SeCuardian-Marketplace




18.3 플랫폼 (platform) — 73종
 키                           이름                                       유형                   업무/업종                 독립    zip              출처

 orchestrator                오케스트레이터                                  federation           플랫폼공통/J               L     be               DOPQ-MultiAIAgent, MAA-Bonded-Areas, SmartHaccp-
                                                                                                                                        MultiAgent

 chat                        AI 어시스턴트 (ExampleAgent)                  app                  플랫폼공통/J               L     fe;be;db         DOPQ-MultiAIAgent, HRAgent-MultiAIAgent, MAS-Basic,
                                                                                                                                        MAS-Marketplace, SeCuardian

 general                     Orchestrator                             federation           플랫폼공통/J               L     be;db            HRAgent-MultiAIAgent, MAS-Basic, MAS-Marketplace,
                                                                                                                                        SeCuardian

 router.auth                 인증·2FA                                   service              사용자·권한/J              M     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.users                사용자 관리                                   service              사용자·권한/J              M     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.settings             시스템 설정                                   service              설정관리/J                H     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.agent                AI 어시스턴트 채팅                              service              AI대화/J                L     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.agent-config         에이전트 관리                                  service              에이전트관리/J              L     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.addon-agents         애드온 에이전트 배포                              service              애드온배포/J               L     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.mcp                  MCP 노출                                   tool-proxy           MCP노출/J               L     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.mcp-configs          MCP 설정                                   tool-proxy           MCP노출/J               L     fe,be,db         MAA-Bonded-Areas, SmartHaccp-MultiAgent

 router.setup                Setup Wizard                             service              초기설정(Setup            L     fe,be,db         MAA-Bonded-Areas
                                                                         Wizard)/J

router.a2a                 A2A 프로토콜                         federation   A2A연동/J         L   fe,be,db        MAA-Bonded-Areas

router.agent-registry      외부 에이전트 레지스트리                    federation   외부에이전트등록/J      L   fe,be,db        MAA-Bonded-Areas

pipeline.keyword_ruleset   정적 키워드 룰셋                        service      AI대화/J          M   be              MAA-Bonded-Areas

marketplace_client         Marketplace 설치 클라이언트             tool-proxy   에이전트 도입·설       M   fe,be           MAS-Basic
                                                                         치/J

addon_agent                Addon 핫디플로이                      other        Addon 수명주기/J    H   fe,be           MAS-Basic

addon_sdk                  Addon 공개 SDK                     other        Addon 개발 계약/J   H   be              MAS-Basic, SeCuardian-Basic

addon_blobs                Addon 오브젝트 스토리지                  other        파일 저장·배포/J      H   be,db           MAS-Basic

addon_jobs                 Addon 백그라운드 작업·스케줄               execution    비동기 작업 실행/J     M   be,db           MAS-Basic

connectors                 외부 엔진 커넥터                        tool-proxy   외부 AI 엔진 연동/J   L   be              MAS-Basic

vector_store               Addon 벡터스토어                      memory       임베딩 검색/J        H   be,db           MAS-Basic

runtime_profile            런타임 프로파일 수집·보고                   other        배치 호환성 판정/J     H   be              MAS-Basic

mcp_proxy                  MCP 프록시·JSON-RPC 서버              tool-proxy   외부 도구 연동/J      H   fe,be,db        MAS-Basic, MAS-Marketplace

a2a                        A2A 프로토콜 v1.0                    federation   에이전트 간 연동/J     H   be              MAS-Basic, MAS-Marketplace, SeCuardian

auth_rbac                  인증·RBAC(3등급)·TOTP·Setup          other        계정·권한/전업종       H   fe,be,db        MAS-Basic, MAS-Marketplace

issuecore                  이슈 관리 코어 (IssueCore)             app          IT 이슈·릴리즈 관     H   be,meta         MAS-Basic
                                                                         리/J

rageval                    RAG 회귀 평가 (RagEval)              rag          AI 품질 회귀평가/J    H   be,db,meta      MAS-Basic

org_tenancy                조직(테넌트) 관리                       service      조직·테넌트 관리/O     H   fe,be,db        MAS-Marketplace

category                   계층형 카테고리                         service      카탈로그 분류/전업      H   fe,be,db        MAS-Marketplace
                                                                         종
catalog                    에이전트 카탈로그·탐색·비교                  service      에이전트 탐색/전업      H   fe,be           MAS-Marketplace
                                                                         종
adoption                   도입(설치)·배치·도구정책                   service      에이전트 도입·배       H   fe,be,db        MAS-Marketplace
                                                                         포/전업종

trial                      도입 전 시험(평가 도입)                   service      도입 전 평가/전업종     M   fe,be,db        MAS-Marketplace

collection                 컬렉션(도메인 팩)                       service      묶음 도입/전업종       H   fe,be,db        MAS-Marketplace

publish_review             에이전트 등록·심사·게시                    reviewer     게시·심사/J         H   fe,be,db        MAS-Marketplace

distribution               패키지 배포(다운로드 API)                 service      패키지 유통/J        H   be,db           MAS-Marketplace

publisher                  게시자 관리·토큰                        service      게시자 워크플로/J      H   fe,be,db        MAS-Marketplace

review                     리뷰·평점·신고                         service      신뢰·커뮤니티/전업      H   fe,be,db        MAS-Marketplace
                                                                         종
compat_check               배치 호환성 판정                        reviewer     배치 적합성/전업종      H   fe,be,db        MAS-Marketplace

public_catalog             공개 카탈로그·llms.txt                 federation   외부 에이전트 연       H   be              MAS-Marketplace
                                                                         동/J

usermanager_deployed       사용자 관리 (배포본)                     app          공통 예제(사용자관      H   fe,be,db        MultiAIAgent-Template
                                                                         리)/전업종

deployed/board             게시판 (배포본)                        app          게시판/전업종         M   fe;be;db;meta   SeCuardian

deployed/ragagent          RAG/Knowledge Agent (배포본)        rag          RAG지식/전업종       M   be;db;meta      SeCuardian

auth                       인증·2FA                           other        사용자관리/전업종       L   fe;be;db        SeCuardian

users                      사용자 관리                           other        사용자관리/전업종       L   fe;be;db        SeCuardian

setup                      Setup Wizard                     other        설치/초기화/전업종      L   fe;be;db        SeCuardian

settings                   시스템 설정                           other        플랫폼설정/전업종       L   fe;be;db        SeCuardian

agent-config               에이전트 설정 관리                       other        에이전트거버넌         L   fe;be;db        SeCuardian
                                                                         스/전업종

addon-agents               ADDON 에이전트 허브                    other        에이전트배포/전업       L   fe;be;db        SeCuardian
                                                                         종
agent-registry             Agent Registry v2                other        에이전트거버넌         L   be;db           SeCuardian
                                                                         스/전업종

mcp                        MCP 서버/프록시                       other        시스템연동/전업종       M   be              SeCuardian

mcp-configs                MCP Proxy 설정                     other        시스템연동/전업종       L   fe;be;db        SeCuardian

chat-history               대화이력·피드백                         other        사용자경험/전업종       L   fe;be;db        SeCuardian

suggestions                운영자 건의                           other        고객피드백/전업종       H   fe;be;db        SeCuardian

standalone-export          Standalone 번들 export             other        에이전트배포/전업       M   be              SeCuardian
                                                                         종
core-agents                코어 에이전트 2종 (Orchestrator·AI 어시   other        AI오케스트레이션/J     L   fe;be;db        SeCuardian-Basic
                           스턴트)
core-routers-14          코어 라우터 14종                      other        플랫폼운영/전업종     L    fe;be;db        SeCuardian-Basic

templates-6              스캐폴딩 템플릿 6종                     other        (범용 골격)/전업종   H    fe;be;db;meta   SeCuardian-Basic

addon_manifest           매니페스트 v2 파서·검증                  other        자산메타관리/전업     L    be;meta         SeCuardian-Basic
                                                                      종
addon_deps               의존성 자동 설치                       other        자산배포/전업종      M    be;db           SeCuardian-Basic

marketplace-client-v2    마켓플레이스 설치 파이프라인 v2              other        에이전트배포/전업     L    fe;be;db        SeCuardian-Basic
                                                                      종
rbac-4tier               RBAC 4단계                        other        사용자관리/전업종     L    fe;be;db        SeCuardian-Basic

deploy-topology          배치 토폴로지 프로파일 4종                 other        인프라운영/전업종     H    be              SeCuardian-Basic

marketplace              마켓플레이스                          service      에이전트마켓/전업     L    fe;be;db;meta   SeCuardian-Marketplace
                                                                      종
workflow                 워크플로우                           service      업무자동화/전업종     M    fe;be;db;meta   SeCuardian-Marketplace

templates-5-common       공통 개발 템플릿 5종                    other        (범용 골격)/전업종   H    fe;be;db;meta   SeCuardian-Marketplace

server-shell             셸 진단 (ShellAgent)               service      인프라운영/전업종     H    fe;be;meta      SeCuardian-Marketplace

marketplace-host         레지스트리 호스트 API                   other        에이전트마켓/전업     H    be;meta         SeCuardian-Marketplace
                                                                      종
marketplace-remote       원격 레지스트리 클라이언트                  other        에이전트마켓/전업     M    fe;be;db        SeCuardian-Marketplace
                                                                      종
tenancy                  멀티테넌시 격리 레벨                     other        조직/테넌트관리/전    L    db              SeCuardian-Marketplace
                                                                      업종
asset-lifecycle          자산 등록·삭제·시드 라이프사이클              other        자산관리/전업종      L    fe;be;db        SeCuardian-Marketplace

supervisor-ui            Supervisor UI·CLI               service      운영도구/전업종      H    be;db           SecuFTPL

front-wizard             파이프라인 위저드 프론트                   service      운영도구/전업종      H    fe;be           SecuFTPL




18.4 보안 (security) — 43종
키                        이름                              유형           업무/업종         독립   zip             출처

output_filters           출력 마스킹 훅                        reviewer     응답 후처리·마스     H    be              MAS-Basic
                                                                      킹/전업종

package_verify           패키지 서명 검증                       reviewer     패키지 무결성/J     M    be              MAS-Basic

piiguard                 PII 가드 (PiiGuard)               reviewer     보안·개인정보 보     M    be,meta         MAS-Basic
                                                                      호/전업종

signing                  패키지 서명·키 관리                     service      패키지 무결성·신     H    fe,be,db        MAS-Marketplace
                                                                      뢰/J

vasca-cve                VASCA CVE Scanner               service      취약점관리/전업종     M    be;meta         SeCuardian

cilium-netpol            Cilium Network Policy           service      보안운영/J        M    be;meta         SeCuardian

teler-ids                teler HTTP IDS                  service      보안운영/전업종      M    be;meta         SeCuardian

shuffle-soar             Shuffle SOAR                    execution    보안운영/전업종      M    be;meta         SeCuardian

neosync-dlp              Neosync DLP                     service      개인정보보호/전업     M    be;meta         SeCuardian
                                                                      종
teleport-pam             Teleport PAM                    service      계정관리/전업종      M    be;meta         SeCuardian

velociraptor-dfir        Velociraptor DFIR               service      침해사고대응/전업     M    be;meta         SeCuardian
                                                                      종
ai-redteam               AI Red Team ⚠️
                                      Isolated           execution    AI보안/J        M    be;meta         SeCuardian

behavior-noti            BehaviorNotiService C++         service      보안운영/전업종      M    be;meta         SeCuardian

agentic-soc              Agentic SOC Platform            federation   보안운영/전업종      M    be;meta         SeCuardian

deployed/behavior-noti   BehaviorNotiService C++ (배포본)   service      보안운영/전업종      M    be;meta         SeCuardian

vault-monitor            Vault Secrets 모니터               service      시크릿관리/전업종     M    be;meta         SeCuardian, SeCuardian-Marketplace

keycloak-monitor         Keycloak IAM 모니터                service      계정관리/전업종      M    be;meta         SeCuardian, SeCuardian-Marketplace

logto-monitor            Logto IAM 모니터                   service      계정관리/J        M    be;meta         SeCuardian, SeCuardian-Marketplace

harbor-monitor           Harbor 레지스트리 모니터                service      공급망보안/J       M    be              SeCuardian

falco-receiver           Falco 런타임 이벤트 수신기               service      보안운영/J        M    be;meta         SeCuardian, SeCuardian-Marketplace

hardening                Linux 서버 하드닝 관리                 service      보안운영/전업종      H    be              SeCuardian

caddy-proxy              Caddy Proxy Monitor             service      인프라운영/전업종     H    be;meta         SeCuardian, SeCuardian-Marketplace

crowdsec                 CrowdSec 위협 탐지 모니터              service      보안운영/전업종      M    be              SeCuardian

wazuh                    Wazuh SIEM 모니터                  service      보안운영/전업종      M    be              SeCuardian

istio                    Istio 서비스 메시 모니터                service      인프라운영/J       L    be              SeCuardian
wireproxy                    WireProxy ZTNA 모니터                 service      네트워크보안/전업     H    be              SeCuardian
                                                                             종
truffle-scan                 TruffleHog Secret Scan Receiver    execution    공급망보안/전업종     H    be;meta         SeCuardian-Marketplace

security-13-ported           보안 내장 13종 이식 자산                    other        보안운영/전업종      M    be;meta         SeCuardian-Marketplace

harbor-scanner               Harbor 레지스트리 스캐너                   service      공급망보안/J       M    be;meta         SeCuardian-Marketplace

hardening-auditor            Linux 하드닝 감사자                      service      보안운영/전업종      M    be;meta         SeCuardian-Marketplace

crowdsec-monitor             CrowdSec 위협 탐지 모니터                 service      보안운영/전업종      M    be;meta         SeCuardian-Marketplace

istio-mtls                   Istio mTLS 모니터                     service      인프라운영/J       H    be;meta         SeCuardian-Marketplace

wireproxy-ztna               WireProxy ZTNA 모니터                 service      네트워크보안/전업     H    be;meta         SeCuardian-Marketplace
                                                                             종
wazuh-siem                   Wazuh SIEM 모니터                     service      보안운영/전업종      M    be;meta         SeCuardian-Marketplace

agentic-threat-model         에이전틱 위협 모델러                        service      AI보안/J        H    be;meta         SeCuardian-Marketplace

attack-surface-recon         공격표면 정찰                            service      취약점관리/전업종     M    be;meta         SeCuardian-Marketplace

api-vuln-scan                API 취약점 스캐너                        service      취약점관리/전업종     H    be;meta         SeCuardian-Marketplace

cicd-security-scan           CI/CD 보안 스캐너                       service      DevSecOps/J   H    be;meta         SeCuardian-Marketplace

ad-security-scan             AD 보안 점검                           service      계정관리/전업종      M    be;meta         SeCuardian-Marketplace

malware-hunt                 악성코드 헌팅                            service      공급망보안/전업종     H    be;meta         SeCuardian-Marketplace

soc-intel-fusion             SOC 인텔 융합                          service      위협인텔리전스/전     H    be;meta         SeCuardian-Marketplace
                                                                             업종
VASCA_worker                 VASCA Worker (CVE 스캐너)             execution    보안운영/전업종      H    meta            SeCuardian-Marketplace

BehaviorNotiService_worker   BehaviorNotiService Worker (C++)   execution    보안운영/전업종      H    meta            SeCuardian-Marketplace




18.5 LLMOps (llmops) — 24종
키                            이름                                 유형           업무/업종         독립   zip             출처

otel-collector               OpenTelemetry Collector            tool-proxy   모니터링/전업종      H    be;meta         SeCuardian

ai-eval-gate                 AI Security Eval Gate ⚠️           service      AI거버넌스/J      H    be;meta         SeCuardian

observability                Observability 스택 모니터               service      모니터링/전업종      M    be              SeCuardian

llm-ops                      LLM 라우팅·미터링                        other        LLMOps/전업종    M    fe;be;db        SeCuardian

rag                          RAG                                rag          RAG지식/전업종     M    fe;be;db;meta   SeCuardian-Marketplace

playground                   플레이그라운드                            service      LLMOps/전업종    M    fe;be;db;meta   SeCuardian-Marketplace

ai-traffic-monitor           AI 트래픽 모니터                         service      모니터링/전업종      M    be;meta         SeCuardian-Marketplace

grafana-dashboard            Grafana Dashboard RAG Agent        rag          모니터링/전업종      M    be;db;meta      SeCuardian-Marketplace

observability-monitor        Observability 모니터                  service      모니터링/전업종      H    be;meta         SeCuardian-Marketplace

model-registry               모델 레지스트리·카탈로그                      service      모델관리/전업종      M    be;db           SecuFTPL

model-download               모델 다운로드 워커                         service      모델관리/전업종      M    be;db           SecuFTPL

collect                      데이터 수집(3채널)                        service      데이터수집/전업종     H    be;db           SecuFTPL

dedup                        중복 제거                              service      데이터정제/전업종     H    be;db           SecuFTPL

formats                      포맷 어댑터                             service      데이터가공/전업종     H    be;db           SecuFTPL

review-queue                 검수 큐(3단계 그룹핑)                      service      데이터검수/전업종     M    be;db           SecuFTPL

augment                      데이터 증강                             service      데이터증강/전업종     M    be;db           SecuFTPL

rag-synth                    RAG 코퍼스 합성                         service      RAG지식/전업종     M    be;db           SecuFTPL

tuning-job                   튜닝 잡 오케스트레이션                       service      모델학습/전업종      M    be;db           SecuFTPL

trainer                      학습 워커(QLoRA)                       service      모델학습/전업종      M    be;db           SecuFTPL

job-monitor                  잡 리소스 모니터링·큐잉                      service      모니터링/전업종      M    be;db           SecuFTPL

evaluate                     평가 러너·리더보드                         service      모델평가/전업종      M    be;db           SecuFTPL

export-runtime               다중 런타임 export                      service      모델배포/전업종      H    be;db           SecuFTPL

feedback-loop                Agent 환류 루프                        service      사용자피드백/전업     H    be;db           SecuFTPL
                                                                             종
pipeline-runner              원스톱 파이프라인 오케스트레이션                  service      파이프라인자동       H    be;db           SecuFTPL
                                                                             화/전업종
18.6 거버넌스·준법 (governance) — 24종
키                           이름                            유형           업무/업종        독립   zip             출처

router.check-list           도입 사전점검 체크리스트                 service      사전점검/J       H    fe,be,db        SmartHaccp-MultiAgent

bondedregkb                 규제 지식베이스 (BondedRegKB)        app          규제지식/O       H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic

bonded.regkb_search         규제 KB 검색(RAG-lite)            rag          규제지식/O       H    fe,be,db,meta   MAA-Bonded-Areas

tool_policy                 런타임 도구 정책 강제                  reviewer     도구 거버넌스/J    M    be              MAS-Basic

audit                       감사 로그                         other        감사·증적/J      H    be,db           MAS-Basic

vouchermatch                전표-증빙 매칭 (VoucherMatch)       app          재무·회계 증빙/K   M    be,meta         MAS-Basic

lawadvisor                  법령 어드바이저 (LawAdvisor)         tool-proxy   법령 조사·준법/M   L    be,meta         MAS-Basic

lawmcp                      법제처 MCP 서버 (korean-law-mcp)   tool-proxy   법령 조사·준법/M   L    meta            MAS-Basic

visibility                  등급별 노출 정책                     reviewer     노출 거버넌스/O    H    fe,be,db        MAS-Marketplace

badges                      배지(Featured·Validated)        reviewer     품질 신호/전업종    H    fe,be           MAS-Marketplace

dashboard_kpi               운영 대시보드·KPI                   other        운영 모니터링/J    H    fe,be           MAS-Marketplace

audit_gov                   감사 로그·거버넌스                    other        감사·증적/O      H    fe,be,db        MAS-Marketplace

isms-p-evidence             ISMS-P Evidence Collector     service      컴플라이언스/전업    L    be;meta         SeCuardian
                                                                       종
guardrails                  가드레일(Reviewer/HITL/룰셋)        other        AI거버넌스/전업종   M    fe;be;db;meta   SeCuardian, SeCuardian-Marketplace

addon_validator             ZIP 정적 보안 검증(scan_zip)        reviewer     자산심사/전업종     M    be;db           SeCuardian-Basic

addon-matrix-bench          전 자산 설치 매트릭스 벤치               reviewer     품질보증/전업종     M    be;meta         SeCuardian-Basic

compliance-isms             ISMS-P 컴플라이언스 증거 수집           service      컴플라이언스/전업    H    be;meta         SeCuardian-Marketplace
                                                                       종
governance-hitl             거버넌스 — HITL 승인 게이트            other        AI거버넌스/전업종   M    be;db           SeCuardian-Marketplace

governance-owasp            거버넌스 — OWASP LLM Top10 스코어카   other        AI거버넌스/전업종   M    be              SeCuardian-Marketplace
                            드
signature-gpg               자산 서명 검증(GPG/mTLS)            other        공급망보안/전업종    M    be              SeCuardian-Marketplace

gate-sanitize               정제 게이트·가명화                    service      개인정보보호/전업    H    be;db           SecuFTPL
                                                                       종
dataset-export              데이터셋 내보내기·manifest            service      데이터유통/전업종    H    be;db           SecuFTPL

decontam                    평가셋 오염 검사(13-gram)            service      품질관리/전업종     H    be;db           SecuFTPL

batch-gate                  야간 배치·배포 게이트                  service      운영자동화/전업종    M    be;db           SecuFTPL




18.7 인사 (hr) — 31종
키                           이름                            유형           업무/업종        독립   zip             출처

hrassistant                 HR 어시스턴트 (관리용)                app          플랫폼공통/M      L    be;db;meta      HRAgent-MultiAIAgent, MAS-Basic

workspace                   워크스페이스                        app          조직·권한관리/M    L    fe;be;meta      HRAgent-MultiAIAgent, MAS-Basic

jobs                        공고 관리                         app          채용공고/M       L    fe;be;meta      HRAgent-MultiAIAgent, MAS-Basic

applicants                  지원자 관리                        app          서류분석/M       L    fe;be;meta      HRAgent-MultiAIAgent, MAS-Basic

pricing                     가격 정책                         app          과금·플랜/M      L    fe;be;meta      HRAgent-MultiAIAgent, MAS-Basic

hrassistantv2               HR 어시스턴트 (HRAssistantV2)      app          플랫폼공통/M      L    fe;be;db;meta   HRAgent-MultiAIAgent

ws.core                     워크스페이스 생성·조회·삭제               service      조직·권한관리/J    H    fe;be;db        HRAgent-MultiAIAgent

ws.invite_code              초대 코드 발급·참여                   service      조직·권한관리/J    H    fe;be;db        HRAgent-MultiAIAgent

ws.invite_email             이메일 초대                        service      조직·권한관리/J    H    fe;be;db        HRAgent-MultiAIAgent

ws.members                  구성원 관리                        service      조직·권한관리/J    H    fe;be;db        HRAgent-MultiAIAgent

ws.roles                    커스텀 권한(RBAC)                  service      조직·권한관리/J    H    fe;be;db        HRAgent-MultiAIAgent

jobs.crud                   공고 CRUD·검색·상태토글               service      채용공고/N       M    fe;be;db        HRAgent-MultiAIAgent

jobs.weights                스크리닝 가중치 설정                   service      스크리닝/N       M    fe;be;db        HRAgent-MultiAIAgent

jobs.ai_draft               AI 공고 초안 생성                   service      채용공고/N       H    fe;be;db        HRAgent-MultiAIAgent

applicants.crud             지원자 등록·목록·삭제                  service      서류분석/M       M    fe;be;db        HRAgent-MultiAIAgent

applicants.upload           서류 업로드                        service      서류분석/M       M    fe;be;db        HRAgent-MultiAIAgent

applicants.resume_extract   이력서 구조화 추출                    service      서류분석/M       M    fe;be;db        HRAgent-MultiAIAgent

applicants.cover_analysis   자소서 분석·JD 매칭률                 service      서류분석/M       M    fe;be;db        HRAgent-MultiAIAgent

applicants.plagiarism       표절 검사                         service      서류분석/M       H    fe;be;db        HRAgent-MultiAIAgent

applicants.certificate      증명서 추출·검증                     service      서류분석/M       M    fe;be;db        HRAgent-MultiAIAgent
applicants.review            추출 데이터 수정·검토 완료          hitl         서류분석/M      M    fe;be;db        HRAgent-MultiAIAgent

screening.run                AI 스크리닝(평가)              reviewer     스크리닝/M      H    fe;be;db        HRAgent-MultiAIAgent

screening.questions          면접 질문 생성·저장              service      면접/M        H    fe;be;db        HRAgent-MultiAIAgent

screening.print              면접 질문지 인쇄 출력             service      면접/M        H    fe;be;db        HRAgent-MultiAIAgent

ops.dashboard                HR 운영 대시보드               service      운영대시보드/J    L    fe;be;db        HRAgent-MultiAIAgent

ops.audit                    감사 로그                    service      감사·컴플라이언    M    fe;be;db        HRAgent-MultiAIAgent
                                                                   스/J

ops.platform_accounts        채용플랫폼 계정 연동              tool-proxy   외부채널연동/N    L    fe;be;db        HRAgent-MultiAIAgent

ops.platform_uploads         공고·지원자 플랫폼 업로드           tool-proxy   외부채널연동/N    L    fe;be;db        HRAgent-MultiAIAgent

pricing.plans                가격 정책 조회                 service      과금·플랜/J     M    fe;be;db        HRAgent-MultiAIAgent

hrcore                       HR 코어 (HRCore)           app          인사·채용/N     H    be,db,meta      MAS-Basic

resumeextract                이력서 추출 (ResumeExtract)   app          인사·채용/N     H    be,db,meta      MAS-Basic




18.8 제조 (manufacturing) — 38종
키                            이름                       유형           업무/업종       독립   zip             출처

dopq.search_items            DOPQ 품목검색 도구             service      기준정보관리/C    M    be              DOPQ-MultiAIAgent

dopq.get_order_status        DOPQ 주문현황 도구             service      주문관리/C      M    be              DOPQ-MultiAIAgent

dopq.get_inventory_balance   DOPQ 재고잔고 도구             service      재고·추적성/C    M    be              DOPQ-MultiAIAgent

dopq.get_production_status   DOPQ 생산현황 도구             service      생산계획/C      M    be              DOPQ-MultiAIAgent

dopq.get_defect_summary      DOPQ 불량집계 도구             service      품질관리/C      M    be              DOPQ-MultiAIAgent

dopq.trace_lot               DOPQ LOT추적 도구            service      재고·추적성/C    M    be              DOPQ-MultiAIAgent

master                       기준정보                     app          기준정보관리/C    M    fe;be;db;meta   DOPQ-MultiAIAgent, MAS-Basic

orders                       판매주문                     app          주문관리/C      M    fe;be;db;meta   DOPQ-MultiAIAgent, MAS-Basic

inventory                    재고/LOT                   app          재고·추적성/C    L    fe;be;db;meta   DOPQ-MultiAIAgent, MAS-Basic

production                   생산실행                     app          생산계획/C      L    fe;be;db;meta   DOPQ-MultiAIAgent, MAS-Basic

dashboard                    대시보드                     app          운영대시보드/C    L    fe,be,db,meta   DOPQ-MultiAIAgent, HRAgent-MultiAIAgent, MAS-Basic,
                                                                                                    SeCuardian-Marketplace

forecast                     풀무원 수요예측                 app          수요예측/C      H    fe;be;db;meta   DOPQ-MultiAIAgent, MAS-Basic

master.items                 품목 마스터 관리                service      기준정보관리/C    M    fe;be;db        DOPQ-MultiAIAgent

master.partners              거래처·공급사·창고·작업장           service      기준정보관리/C    M    fe;be;db        DOPQ-MultiAIAgent

master.codes                 불량코드·단위계                 service      품질관리/C      M    fe;be;db        DOPQ-MultiAIAgent

master.bom                   BOM revision 관리          service      기준정보관리/C    M    fe;be;db        DOPQ-MultiAIAgent

master.routing               라우팅 revision 관리          service      생산계획/C      M    fe;be;db        DOPQ-MultiAIAgent

master.inspection_spec       검사기준 revision 관리         service      품질관리/C      L    fe;be;db        DOPQ-MultiAIAgent

orders.entry                 판매주문 등록·조회               service      주문관리/C      M    fe;be;db        DOPQ-MultiAIAgent

orders.status                주문 상태 전이 규칙              service      주문관리/C      M    fe;be;db        DOPQ-MultiAIAgent

inventory.txn                재고 수불 규칙                 service      재고·추적성/C    M    fe;be;db        DOPQ-MultiAIAgent

inventory.lot_hold           LOT 보류/해제(격리)            service      품질관리/C      M    fe;be;db        DOPQ-MultiAIAgent

inventory.genealogy          LOT genealogy 추적         service      재고·추적성/C    M    fe;be;db        DOPQ-MultiAIAgent

production.work_order        생산오더 발행                  service      생산계획/C      L    fe;be;db        DOPQ-MultiAIAgent

production.result            작업실적·불량 수집               service      품질관리/C      L    fe;be;db        DOPQ-MultiAIAgent

production.complete          생산완료·LOT 결선              service      재고·추적성/C    L    fe;be;db        DOPQ-MultiAIAgent

production.downtime          정지시간(비가동) 기록             service      생산계획/C      M    fe;be;db        DOPQ-MultiAIAgent

dashboard.summary            운영 KPI 집계                service      운영대시보드/C    L    fe;be;db        DOPQ-MultiAIAgent

dashboard.defects            불량코드별 집계                 service      품질관리/C      L    fe;be;db        DOPQ-MultiAIAgent

dashboard.due_orders         납기 임박 주문 라인              service      주문관리/C      L    fe;be;db        DOPQ-MultiAIAgent

forecast.load_data           수요예측 데이터 적재              execution    수요예측/C      H    be;db           DOPQ-MultiAIAgent

forecast.train               수요예측 모델 학습               execution    수요예측/C      H    be;db           DOPQ-MultiAIAgent

forecast.inference           수요예측 추론(D8~D14)          execution    수요예측/C      H    be;db           DOPQ-MultiAIAgent

router.employees             직원 명부                    service      인사/직원관리/C   H    fe,be,db        SmartHaccp-MultiAgent

router.notifiers             알림 설정                    service      알림설정/C      L    fe,be,db        SmartHaccp-MultiAgent
router.code-master                  코드 관리                   service     코드관리/C         H    fe,be,db        SmartHaccp-MultiAgent

router.dashboard                    대시보드                    service     대시보드/C         L    fe,be,db        SmartHaccp-MultiAgent

employees.bulk-import               직원 일괄 적재 파이프라인          service     인사/직원관리/C      H    be,db           SmartHaccp-MultiAgent




18.9 식품안전 (food-safety) — 32종
키                                   이름                      유형          업무/업종          독립   zip             출처

monitoring                          CCP 모니터링 에이전트           app         CCP모니터링/C      M    be              SmartHaccp-MultiAgent

alert                               이탈 알림 에이전트              app         알림/C           M    be              SmartHaccp-MultiAgent

corrective                          개선 조치 에이전트              app         시정조치/C         M    be              SmartHaccp-MultiAgent

record                              기록 관리 에이전트              app         기록관리/C         H    be              SmartHaccp-MultiAgent

calibration                         검교정 에이전트                app         교정/C           H    be              SmartHaccp-MultiAgent

pdca                                PDCA 평가 에이전트            app         PDCA/C         L    be              SmartHaccp-MultiAgent

field                               현장 출입·위생 에이전트           app         현장점검/C         M    be              SmartHaccp-MultiAgent

advisor                             HACCP 자문 에이전트           app         자문/C           H    be              SmartHaccp-MultiAgent

alert.acknowledge_alert             알림 확인 처리 도구             execution   알림/C           M    be              SmartHaccp-MultiAgent

corrective.create_corrective_acti   개선조치 생성 도구              execution   시정조치/C         M    be              SmartHaccp-MultiAgent
on

corrective.complete_corrective_     개선조치 완결 도구              execution   시정조치/C         M    be              SmartHaccp-MultiAgent
action

router.templates                    문서 템플릿                  service     기록관리/C         H    fe,be,db        SmartHaccp-MultiAgent

router.records                      기록 관리                   service     기록관리/C         H    fe,be,db        SmartHaccp-MultiAgent

router.monitoring                   CCP 모니터링                service     CCP모니터링/C      M    fe,be,db        SmartHaccp-MultiAgent

router.alerts                       이탈 알림                   service     알림/C           M    fe,be,db        SmartHaccp-MultiAgent

router.corrective-actions           개선 조치                   service     시정조치/C         M    fe,be,db        SmartHaccp-MultiAgent

router.calibration                  검교정                     service     교정/C           H    fe,be,db        SmartHaccp-MultiAgent

router.pdca                         PDCA                    service     PDCA/C         M    fe,be,db        SmartHaccp-MultiAgent

router.entry-log                    현장 출입                   service     현장점검/C         M    fe,be,db        SmartHaccp-MultiAgent

router.hygiene-log                  위생 점검                   service     현장점검/C         M    fe,be,db        SmartHaccp-MultiAgent

qr-management                       QR 관리                   app         QR발급/C         H    fe              SmartHaccp-MultiAgent

payment-process                     결재 프로세스 관리              hitl        기록관리/C         M    fe              SmartHaccp-MultiAgent

labelcheck                          식품 표시 검증 (LabelCheck)   app         식품표시 규제검       M    be,meta         MAS-Basic
                                                                        증/C

haccpadvisor                        HACCP 어드바이저             service     식품안전 HACCP 운   M    be,meta         MAS-Basic
                                                                        영/C

haccpalert                          HACCP 이탈 알림             service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C

haccpcalibration                    HACCP 계측기 검교정           service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C

haccpcore                           HACCP 코어                app         식품안전 HACCP 운   H    fe,be,db,meta   MAS-Basic
                                                                        영/C

haccpcorrective                     HACCP 개선 조치             service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C

haccpfield                          HACCP 출입·위생             service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C

haccpmonitoring                     HACCP CCP 모니터링          service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C

haccppdca                           HACCP PDCA 평가           service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C

haccprecord                         HACCP 문서·기록             service     식품안전 HACCP 운   L    be,meta         MAS-Basic
                                                                        영/C




18.10 물류·통관 (logistics-customs) — 24종
키                                   이름                      유형          업무/업종          독립   zip             출처

bondeddococr                        문서 인식 (BondedDocOCR)    app         문서OCR/H        M    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic
    bondedruleengine              정합성 검증 (BondedRuleEngine)    app       정합성검증/H    H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic

    bondedfxengine                환율·외자비율 (BondedFXEngine)     app       환율/H       H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic

    bondeddeclaration             수입신고 (BondedDeclaration)     app       수입신고/O     H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic

    bondedintegrationgateway      연동 게이트웨이                     app       입출고/H      H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic
                                  (BondedIntegrationGateway)

    bondedfxcompliance            외환 컴플라이언스                    app       외환컴플라이언    H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic
                                  (BondedFXCompliance)                   스/O

    bondedselfreport              자진신고 전환 (BondedSelfReport)   app       자진신고/O     H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic

    bondedfxsimulation            환율·공급망 시뮬레이션                 app       시뮬레이션/H    H    fe,be,db,meta   MAA-Bonded-Areas, MAS-Basic
                                  (BondedFXSimulation)

    bonded.doc_upload             문서 업로드·텍스트 추출                service   문서OCR/H    H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.doc_review_queue       OCR 검토 큐·확정                  hitl      문서OCR/H    H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.fx_rates               환율 등록·조회                     service   환율/H       H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.fx_ratio_calc          외자비율 계산                      service   외자비율/H     H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.validation             정합성 검증                       service   정합성검증/H    H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.mixed_use              혼용승인 강제                      hitl      혼용승인/H     H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.declaration_draft      신고서 초안 생성                    service   수입신고/O     H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.declaration_approval   신고 승인 워크플로우(SLA)             hitl      수입신고/O     H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.inout_events           입출고 이벤트 수신                   service   입출고/H      H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.inventory              재고 관리                        service   재고/H       [    fe,be,db,meta   MAA-Bonded-Areas

    bonded.audit_report           감사 리포트                       service   감사리포트/O    H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.fx_tx_eval             외환거래 평가·과태료 산정               service   외환컴플라이언    H    fe,be,db,meta   MAA-Bonded-Areas
                                                                         스/O

    bonded.exposure               우발부채 정량 추정                   service   우발부채추정/O   H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.selfreport_workflow    자진신고 HITL 워크플로우              hitl      자진신고/O     H    fe,be,db,meta   MAA-Bonded-Areas

    bonded.fx_simulate            환율·공급망 What-if               service   시뮬레이션/H    H    fe,be,db,meta   MAA-Bonded-Areas

    pipeline.ocr_vision           스캔 PDF 로컬 비전 OCR 파이프라인       service   문서OCR/H    M    be              MAA-Bonded-Areas




18.11 문서지능 (docintel) — 3종
    키                             이름                           유형        업무/업종      독립   zip             출처

    dockb                         문서 지식베이스 (DocKB)             rag       문서처리·지식검   H    be,db,meta      MAS-Basic
                                                                         색/J

    hybridrag                     하이브리드 RAG (HybridRAG)        rag       문서처리·지식검   H    be,db,meta      MAS-Basic
                                                                         색/J

    receiptcheck                  영수증 검증 (ReceiptCheck)        rag       문서처리·지식검   H    be,db,meta      MAS-Basic
                                                                         색/J




18.12 종합
총 303종. 이 목록은 후보군이며, 첫 릴리스 우선순위는 15장 로드맵(S8 Addon 확장)과 17.7 스타터 팩을 따른다. 모든 후보는 등록 8
단계(10.4)와 누락 검증 CI(10.8)를 거쳐 카탈로그에 편입된다.

18.99 후보 도출 원칙과 한계
        같은 골격이라 정규화가 쉽다. 11종 모두 v1 템플릿 골격을 공유해, 도메인 에이전트·라우터 기능을 agent.zip 규격으로 옮기는
         비용이 낮다.
        공통 템플릿은 한 번만. Board·UserManager·RagAgent·ServiceAgent·ToolProxyAgent·ShellAgent·McpServer 는 common 도메인에 한
         번만 싣고, 프로젝트별 중복은 제거했다.
        독립 구동 L 은 데모 한정. 외부 시스템(ERP·MES·UNI-PASS·환율 API·센서)이 필수인 후보는 목·업로드 폴백을 붙여야 M1 이 성립
         한다(17.5).
        라이선스 확인 필요. 참조 프로젝트 대부분 LICENSE 파일 [미확인]. 마켓 게시 전 부여(부록 F).
        후보는 요구가 아니다. 본 장은 '무엇을 Addon 으로 만들 수 있는가'의 목록이다. 구현 우선순위·범위는 별도 결정(15.4)한다.
부록 A. 용어
용어                뜻
Addon Agent       agent.zip 으로 포장된 독립 에이전트. frontend/backend/database/agent.yaml/compose.yaml
agent.yaml        에이전트 정본 메타. v1 meta.json 상위 호환. Card·server.json·OpenAPI 생성 원천
M1/M2/M3          독립 / 연계 / 즉시 사용
경로 A/B/C          마켓 다운로드·설치 / 직접 설치(zip·Git·OCI·URL) / 연동·연계(원격 Card·MCP URL)
G1~G5             라이선스 허용 등급(9.10)
E/A/L/R/X         인포그래픽 저장소 결합 방식: 기본 엔진/Addon 컨테이너/연계만/패턴 참고/제외
MCP               Model Context Protocol. 에이전트↔도구. 현행 2026-07-28
A2A               Agent2Agent. 에이전트↔에이전트. 현행 v1.0.1. Agent Card = /.well-known/agent-card.json
ACP               본 문서에서는 항상 Agent Client Protocol(Zed). AGNTCY Agent Connect Protocol(아카이브)과 무관
AG-UI             Agent-User Interaction Protocol. 에이전트→UI 이벤트 스트림 spec 1.0
MRTR              MCP Multi Round-Trip Requests. resultType=input_required + 재시도
server/discover   MCP 2026-07-28 필수 RPC. initialize 대체
프라이버시 등급 L0~L3    public / internal / confidential / regulated. 게이트웨이가 모델 허용 범위 결정
신뢰 등급             official / partner / community / external. 격리 강도 결정
오픈코어              코어 허용 라이선스 + ee/·enterprise/ 별도 상용(LiteLLM, Langfuse, authentik 등)
v1                WisemanLim/pub-MultiAIAgent-Template 구현(2026-07-30)
부록 B. 출처 총람

B.1 원천·검색·사용자
   인포그래픽 「20 AI GitHub Repos」 — 원 게시자·URL 미확인. 요약 보고서 20AI-GitHub-Repos/Summary-Repos.docx(2026-09-15) 로 전
    사.
   https://github.com/search?q=Multi-ai+Agent&type=repositories (REST API 2026-09-18, 300건)
   https://github.com/WisemanLim?tab=repositories · https://github.com/WisemanLim?tab=stars
   https://github.com/WisemanLim/pub-MultiAIAgent-Template (README.md · PRD.md · addon-agents/README.md ·
    standalone/README.md · docker-compose.yml · app/routers/router_a2a.py 실독)

B.2 표준 사양
   MCP: https://github.com/modelcontextprotocol/modelcontextprotocol — docs/specification/2026-07-28 (changelog, deprecated,
    basic/patterns/mrtr, server/discover, security_best_practices), schema/2026-07-28. 릴리스 2026-07-28.
   MCP Registry: https://github.com/modelcontextprotocol/registry — server.json 스키마 2025-12-11, API /v0.1/servers.
    https://registry.modelcontextprotocol.io
   MCPB: https://github.com/modelcontextprotocol/mcpb (구 anthropics/mcpb) — manifest.json, user_config
   A2A: https://github.com/a2aproject/A2A — specification/a2a.proto (package lf.a2a.v1), docs/topics/agent-discovery.md, extensions.md,
    GOVERNANCE.md. 릴리스 v1.0.1 2026-05-28. https://a2a-protocol.org
   ACP: https://github.com/agentclientprotocol/agent-client-protocol — docs/protocol/v1, schema-v1.22.0. https://agentclientprotocol.com
   AG-UI: https://github.com/ag-ui-protocol/ag-ui — spec/1.0/schema.json, integrations/
   OTel GenAI: https://github.com/open-telemetry/semantic-conventions-genai — docs/gen-ai/{gen-ai-agent-spans.md, mcp.md},
    model/gen-ai/registry.yaml
   Compose Spec: https://github.com/compose-spec/compose-spec — spec.md, include, profiles, models.md, provider. docker/compose 릴
    리스 v5.5.1 및 v5.0.0 노트
   Claude Code 헤드리스·플러그인: https://code.claude.com/docs/en/headless, plugins, plugin-marketplaces.
    https://github.com/anthropics/claude-plugins-official
   Docker Desktop 라이선스: https://docs.docker.com/subscription/desktop-license
   모델 라이선스: deepseek-ai/DeepSeek-V3 LICENSE-MODEL, HF deepseek-ai/DeepSeek-V3.1·R1, HF Qwen/Qwen3-235B-A22B,
    openai/gpt-oss, ai.google.dev/gemma/terms, meta-llama/llama-models models/llama4/LICENSE, HF mistralai/*, HF microsoft/phi-4, HF
    LGAI-EXAONE/EXAONE-4.0-32B

B.3 법령·프레임워크
   정보통신망법, 개인정보보호법, ISMS-P, CSAP(사용자 COMPLIANCE.md 근거 승계). NIST AI RMF 1.0. OWASP GenAI LLM Top 10
    2026(2026-08-04) 및 ASI01~10. RFC 8615(well-known), RFC 8785(JCS), RFC 8693(token exchange), RFC 9728(PRM), RFC 8628(Device
    Code).

B.4 선행 내부 문서
   AgentNexus_PRD(2026-09-16), AgentStackHub_PRD(2026-09-15), AegisMesh_PRD·AgentSentry_PRD, LLMForge_PRD(2026-09-17) —
    경계는 2.5. 양식 참조 문서는 출처가 아님.
B.5 실측 저장소 전수
361개. 2026-09-18 GitHub REST API. * 사용자 스타, A 아카이브. 라이선스는 LICENSE 판독 결과 우선(40자 절단).
 저장소                                           ★       라이선스                         커밋           A

 2FastLabs/agent-squad *                       7765    Apache-2.0                   2026-07-29


 a2aproject/A2A *                              25828   Apache-2.0                   2026-09-16


 a2aproject/a2a-dotnet                         263     Apache-2.0                   2026-09-16


 a2aproject/a2a-go                             467     Apache-2.0                   2026-09-07


 a2aproject/a2a-inspector                      490     Apache-2.0                   2026-08-08


 a2aproject/a2a-java                           493     Apache-2.0                   2026-09-17


 a2aproject/a2a-js                             621     Apache-2.0                   2026-09-17


 a2aproject/a2a-python                         2147    Apache-2.0                   2026-09-15


 a2aproject/a2a-samples                        1769    Apache-2.0                   2026-08-04


 aaif-goose/goose *                            54406   Apache-2.0                   2026-09-18


 aaif/aaif-landscape                           56      NONE (LICENSE 확인 필요)         2026-08-18


 abiosoft/colima *                             30860   MIT                          2026-09-15


 activepieces/activepieces *                   24531   MIT (packages/ee/ 별도 상용)     2026-09-17


 ag-ui-protocol/ag-ui *                        15934   MIT                          2026-09-17


 agent-network-protocol/AgentNetworkProtocol   1432    Apache-2.0                   2026-09-10


 agent-tools-org/ai-dispatch                   12      MIT                          2026-09-15


 agentclientprotocol/agent-client-protocol     4273    Apache-2.0                   2026-09-18


 agentclientprotocol/claude-agent-acp          2540    Apache-2.0                   2026-09-17


 agentclientprotocol/codex-acp                 387     Apache-2.0 (LICENSE 본문 확인)   2026-09-17


 agentclientprotocol/java-sdk                  68      Apache-2.0                   2026-08-28


 agentclientprotocol/kotlin-sdk                93      Apache-2.0                   2026-09-17


 agentclientprotocol/python-sdk                324     Apache-2.0                   2026-09-11


 agentclientprotocol/registry                  394     Apache-2.0                   2026-09-18


 agentclientprotocol/rust-sdk                  204     Apache-2.0                   2026-09-14


 agentclientprotocol/typescript-sdk            254     Apache-2.0                   2026-09-14


 agentgateway/agentgateway                     4900    Apache-2.0                   2026-09-17


 agentsmd/agents.md *                          24438   MIT                          2026-09-10


 agi-inc/agent-protocol                        1455    MIT                          2025-04-08


 agno-agi/agno *                               42227   Apache-2.0                   2026-09-17


 agntcy/acp-sdk                                88      Apache-2.0                   2025-06-16   A

 agntcy/acp-spec                               168     Apache-2.0                   2025-05-23   A

 agntcy/dir                                    189     Apache-2.0                   2026-09-16


 agntcy/oasf                                   334     Apache-2.0                   2026-09-08


 agntcy/slim                                   218     Apache-2.0                   2026-09-17


 AIAnytime/Multi-Agents-System-from-Scratch    72      MIT                          2024-11-13
amacneil/dbmate                          7391     MIT                                       2026-09-17


anchore/grype                            12900    Apache-2.0                                2026-09-18


anchore/syft                             9574     Apache-2.0                                2026-09-18


anomalyco/opencode *                     208244   MIT                                       2026-09-18


anthropics/anthropic-sdk-python          3905     MIT                                       2026-09-15


anthropics/claude-agent-sdk-python       8124     MIT                                       2026-09-18


anthropics/claude-code *                 145936   Anthropic Commercial Terms (LICENSE.md,   2026-09-18


anthropics/claude-plugins-official *     36447    Apache-2.0                                2026-09-17


anthropics/skills *                      176932   LICENSE 파일 없음 (저장소 SPDX none)             2026-09-10


apache/airflow *                         46885    Apache-2.0                                2026-09-18


apache/casbin                            20395    Apache-2.0                                2026-09-11


aquasecurity/trivy                       37969    Apache-2.0                                2026-09-17


ariga/atlas                              8729     Apache-2.0                                2026-09-04


Arize-ai/openinference                   1224     Apache-2.0                                2026-09-17


Arize-ai/phoenix *                       11525    Elastic-2.0 (ELv2, 관리형 제공 금지)             2026-09-18


asg017/sqlite-vec                        8115     Apache-2.0                                2026-05-18


assistant-ui/assistant-ui                12194    MIT                                       2026-09-18


astral-sh/ruff                           49676    MIT                                       2026-09-18


astral-sh/uv *                           89941    Apache-2.0                                2026-09-18


authelia/authelia                        29006    Apache-2.0                                2026-09-17


AUTOMATIC1111/stable-diffusion-webui *   164996   AGPL-3.0                                  2024-07-27


backstage/backstage                      34433    Apache-2.0                                2026-09-17


BerriAI/litellm *                        59036    MIT (enterprise/ 디렉터리 별도 라이선스)            2026-09-18


better-auth/better-auth                  29992    MIT                                       2026-09-17


bytecodealliance/wasmtime *              18643    Apache-2.0                                2026-09-17


bytedance/deer-flow *                    82612    MIT                                       2026-09-18


caddyserver/caddy *                      75834    Apache-2.0                                2026-09-17


camel-ai/camel                           17740    Apache-2.0                                2026-09-07


celery/celery                            28898    BSD-3-Clause                              2026-09-17


Chainlit/chainlit *                      12457    Apache-2.0                                2026-08-26


ChatGPTNextWeb/NextChat                  88778    MIT                                       2026-08-11


chroma-core/chroma *                     29320    Apache-2.0                                2026-09-16


comet-ml/opik *                          22104    Apache-2.0                                2026-09-17


Comfy-Org/comfy-cli                      973      GPL-3.0                                   2026-09-17


Comfy-Org/ComfyUI *                      133706   GPL-3.0                                   2026-09-18


Comfy-Org/ComfyUI-Manager                16179    GPL-3.0                                   2026-09-15


compose-spec/compose-spec                2730     Apache-2.0                                2026-09-17
confident-ai/deepeval *           18317    Apache-2.0                                 2026-09-16


containerd/nerdctl                10383    Apache-2.0                                 2026-09-17


containers/podman-compose         6217     GPL-2.0                                    2026-08-11


containrrr/watchtower             24650    Apache-2.0                                 2025-12-17   A

cookiecutter/cookiecutter         25091    BSD-3-Clause                               2026-03-04


coollabsio/coolify                61962    Apache-2.0                                 2026-09-17


copier-org/copier                 3579     MIT                                        2026-09-07


CopilotKit/CopilotKit *           37403    MIT                                        2026-09-18


coqui-ai/TTS                      46023    MPL-2.0                                    2024-02-10


coze-dev/coze-studio              21604    Apache-2.0                                 2026-07-29


crewAIInc/crewAI *                58715    MIT                                        2026-09-17


dankefox/multi-ai-collaboration   20       AGPL-3.0                                   2026-08-16


danny-avila/LibreChat *           44255    MIT                                        2026-09-17


data-privacy-stack/presidio       10919    MIT                                        2026-09-16


daytonaio/daytona *               71721    AGPL-3.0 · 2026-06 유지보수 중단 선언 (SPDX none   2026-06-25


dbos-inc/dbos-transact-py         1578     MIT                                        2026-09-17


deepseek-ai/DeepSeek-R1 *         91980    MIT                                        2025-04-09


deepseek-ai/DeepSeek-V3 *         104464   MIT                                        2025-08-28


deepset-ai/haystack               26534    Apache-2.0                                 2026-09-17


distribution/distribution         10614    Apache-2.0                                 2026-08-31


docker/compose                    38178    Apache-2.0                                 2026-09-17


docker/mcp-gateway                1571     MIT                                        2026-09-16


docker/mcp-registry               554      MIT                                        2026-09-16


docker/model-runner               651      Apache-2.0                                 2026-08-20


docling-project/docling *         66588    MIT                                        2026-09-17


drizzle-team/drizzle-orm *        35803    Apache-2.0                                 2026-07-23


duckdb/duckdb *                   41472    MIT                                        2026-09-17


e2b-dev/E2B *                     13864    Apache-2.0                                 2026-09-17


electric-sql/electric             10362    Apache-2.0                                 2026-09-09


exo-explore/exo *                 47490    Apache-2.0                                 2026-08-25


fastapi/fastapi *                 102408   MIT                                        2026-09-01


feiyun0112/AgentBridge            28       LICENSE 파일 없음                              2026-03-24


FerroxLabs/ijfw                   210      MIT                                        2026-07-11


firecracker-microvm/firecracker   36802    Apache-2.0                                 2026-09-17


fishaudio/fish-speech *           32729    Fish Audio Research License (사내 사용도 상용 정   2026-09-16


FlowiseAI/Flowise *               55467    Apache-2.0 (enterprise/ 별도) [아카이브 2026-0   2026-08-13   A

FoundationAgents/MetaGPT *        70484    MIT                                        2026-01-21


GalaxyLLMCI/lyraios               137      Apache-2.0                                 2025-03-18
getlago/lago                            10572    AGPL-3.0                                   2026-09-17


getsops/sops                            23148    MPL-2.0                                    2026-09-18


getumbrel/umbrel                        11974    PolyForm Noncommercial (상용 차용 불가, 구조만 참고   2026-09-17


getzep/graphiti *                       30975    Apache-2.0                                 2026-09-17


ggml-org/llama.cpp *                    128619   MIT                                        2026-09-17


ggml-org/whisper.cpp                    53739    MIT                                        2026-09-18


gin-gonic/gin *                         89232    MIT                                        2026-09-16


goauthentik/authentik                   25604    MIT (authentik/enterprise/ 별도, website/    2026-09-18


goharbor/harbor *                       29401    Apache-2.0                                 2026-09-17


golang-migrate/migrate                  18929    MIT                                        2026-09-09


google-deepmind/gemma                   5737     Apache-2.0                                 2026-09-16


google-gemini/gemini-cli *              107051   Apache-2.0                                 2026-09-18


google/adk-python                       21568    Apache-2.0                                 2026-09-18


google/adk-samples *                    10341    Apache-2.0                                 2026-09-17


google/gvisor                           19345    Apache-2.0                                 2026-09-18


googleapis/python-genai *               3981     Apache-2.0                                 2026-09-18


gradio-app/gradio *                     43565    Apache-2.0                                 2026-09-18


grafana/grafana *                       76792    AGPL-3.0                                   2026-09-18


grafana/loki *                          28908    AGPL-3.0                                   2026-09-18


grafana/plugin-tools                    89       Apache-2.0                                 2026-09-17


grafana/tempo *                         5478     AGPL-3.0                                   2026-09-17


guardrails-ai/guardrails                7428     Apache-2.0                                 2026-08-26


hacs/integration                        7719     MIT                                        2026-09-05


hashicorp/nomad                         16956    BUSL-1.1 (Licensor IBM, 경쟁 호스팅 금지)         2026-09-16


hatchet-dev/hatchet                     7959     MIT                                        2026-09-15


helm/helm *                             30251    Apache-2.0                                 2026-09-17


higress-group/higress                   9400     Apache-2.0                                 2026-09-10


HKUDS/AutoAgent *                       9793     MIT                                        2025-10-16


honojs/hono *                           32258    MIT                                        2026-09-15


huggingface/chat-ui                     10953    Apache-2.0                                 2026-09-17


huggingface/smolagents                  29376    Apache-2.0                                 2026-08-22


huggingface/text-embeddings-inference   5052     Apache-2.0                                 2026-09-17


huggingface/text-generation-inference   10886    Apache-2.0                                 2026-03-21   A

huggingface/transformers *              166261   Apache-2.0                                 2026-09-18


IBM/mcp-context-forge                   4489     Apache-2.0                                 2026-09-17


IceWhaleTech/CasaOS                     37231    Apache-2.0                                 2025-08-06


idiap/coqui-ai-TTS                      2321     MPL-2.0                                    2026-06-10
in-toto/attestation                        373      Apache-2.0 (LICENSE 본문 확인)                 2026-09-14


infiniflow/infinity                        4708     Apache-2.0                                 2026-09-09


infiniflow/ragflow *                       90911    Apache-2.0                                 2026-09-18


Infisical/infisical                        29299    MIT (ee/ 디렉터리 별도)                          2026-09-18


inngest/inngest                            5842     SSPL-1.0 + Apache-2.0 Future License       2026-09-17


InternLM/lmdeploy                          8079     Apache-2.0                                 2026-09-17


janhq/jan *                                44516    Apache-2.0 계열 (Menlo Research, LICENSE 본   2026-09-18


k2-fsa/sherpa-onnx                         14834    Apache-2.0                                 2026-09-17


kagent-dev/kagent *                        3752     Apache-2.0                                 2026-09-17


kata-containers/kata-containers            8742     Apache-2.0                                 2026-09-17


katanemo/plano *                           7055     Apache-2.0                                 2026-08-19


kaymen99/langgraph-email-automation        274      NONE (LICENSE 확인 필요)                       2025-02-13


keycloak/keycloak *                        36838    Apache-2.0                                 2026-09-17


keygen-sh/keygen-api                       1590     FCL-1.0-ALv2 (Fair Core License, 비OSI)     2026-09-10


khoj-ai/khoj *                             37399    AGPL-3.0                                   2026-08-02


killbill/killbill                          5737     Apache-2.0                                 2026-08-20


Kludex/starlette                           12619    BSD-3-Clause                               2026-09-12


Kong/kong                                  44148    Apache-2.0                                 2026-09-03


kortix-ai/suna *                           20220    Elastic-2.0 (관리형 서비스 제공 금지)                2026-09-18


ksm26/Multi-AI-Agent-Systems-with-crewAI   168      NONE (LICENSE 확인 필요)                       2024-06-11


kubernetes/kompose                         10623    Apache-2.0                                 2026-06-15


kvcache-ai/ktransformers                   19523    Apache-2.0                                 2026-09-17


kyegomez/swarms                            7177     Apache-2.0                                 2026-09-17


labstack/echo                              32708    MIT                                        2026-09-16


lainXXX/multi-ai-chat-skill                37       MIT                                        2026-09-17


lancedb/lancedb                            11451    Apache-2.0                                 2026-09-17


langchain-ai/agent-chat-ui *               3162     MIT                                        2026-09-14


langchain-ai/deepagents *                  29534    MIT                                        2026-09-18


langchain-ai/langchain *                   146562   MIT                                        2026-09-18


langchain-ai/langgraph *                   41863    MIT                                        2026-09-18


langchain-ai/langserve                     2329     LangServe License (독자, 비OSI) [아카이브]        2026-05-05   A

langchain-ai/new-langgraph-project         293      MIT                                        2026-08-21


langflow-ai/langflow *                     154959   MIT                                        2026-09-16


langfuse/langfuse                          34746    MIT (ee/ 별도) · 저작권자 ClickHouse, Inc.       2026-09-17


langgenius/dify *                          156215   Apache-2.0 변형 (멀티테넌트·로고 제거 금지 추가 조건)       2026-09-18


langgenius/dify-plugin-daemon              459      Apache-2.0                                 2026-09-11


langgenius/dify-plugins                    553      LICENSE 파일 없음 (플러그인별 상이)                   2026-09-18
lasso-security/mcp-gateway                  388     MIT                                        2026-01-22


letta-ai/letta *                            24783   Apache-2.0                                 2026-09-10


lit/lit                                     21825   BSD-3-Clause                               2026-09-14


litestar-org/litestar                       8470    MIT                                        2026-09-17


lobehub/lobehub                             82576   LobeHub Community License (Apache-2.0 기반   2026-09-18


louislam/dockge                             24376   MIT                                        2026-04-19


louislam/uptime-kuma                        91498   MIT                                        2026-09-17


mastra-ai/mastra *                          28147   Apache-2.0 (ee/ 별도 상용)                     2026-09-18


maximhq/bifrost *                           8147    Apache-2.0                                 2026-09-17


mckaywrigley/chatbot-ui                     33352   MIT                                        2024-06-22


mco-org/squad                               816     MIT                                        2026-05-26


mem0ai/mem0 *                               65539   Apache-2.0                                 2026-09-18


meta-llama/llama-models                     7692    Llama Community License (모델별)              2025-10-10


metaskills/experts                          1064    MIT                                        2024-09-09


michaelfeil/infinity                        2942    MIT                                        2026-03-24


microsoft/agent-framework                   13571   MIT                                        2026-09-18


microsoft/agent-governance-toolkit *        6282    MIT                                        2026-09-17


microsoft/autogen *                         61035   CC-BY-4.0 (코드에 부적합) · 유지보수 모드              2026-04-06


microsoft/mcp-gateway                       840     MIT                                        2026-08-25


microsoft/PhiCookBook                       3878    MIT                                        2026-08-26


microsoft/semantic-kernel                   28572   MIT                                        2026-09-11


milvus-io/milvus *                          46153   Apache-2.0                                 2026-09-18


Mintplex-Labs/anything-llm *                66156   MIT                                        2026-09-17


mistralai/mistral-common                    946     Apache-2.0                                 2026-09-17


mistralai/mistral-inference                 10825   Apache-2.0                                 2026-06-16   A

ml-explore/mlx-examples *                   8954    MIT                                        2026-04-06


ml-explore/mlx-lm *                         7043    MIT                                        2026-09-17


modelcontextprotocol/csharp-sdk             4532    MIT → Apache-2.0 전환 진행 중                   2026-09-13


modelcontextprotocol/ext-apps               2849    MIT → Apache-2.0 전환 진행 중                   2026-09-09


modelcontextprotocol/ext-auth               164     MIT                                        2026-06-18


modelcontextprotocol/ext-skills             601     Apache-2.0                                 2026-09-16


modelcontextprotocol/ext-tasks              46      Apache-2.0                                 2026-09-04


modelcontextprotocol/go-sdk                 5116    MIT → Apache-2.0 전환 진행 중                   2026-09-17


modelcontextprotocol/inspector *            10904   LICENSE 파일 없음 (README 확인 필요)               2026-09-16


modelcontextprotocol/java-sdk               3698    MIT                                        2026-09-17


modelcontextprotocol/mcpb                   2114    MIT → Apache-2.0 전환 진행 중                   2026-04-22


modelcontextprotocol/modelcontextprotocol   9241    MIT → Apache-2.0 전환 진행 중 (문서 CC-BY-4.0)    2026-09-16
modelcontextprotocol/python-sdk *             24325    MIT                                        2026-09-16


modelcontextprotocol/registry                 7260     MIT → Apache-2.0 전환 진행 중                   2026-09-16


modelcontextprotocol/rust-sdk                 3937     MIT → Apache-2.0 전환 진행 중                   2026-09-15


modelcontextprotocol/servers *                90426    MIT → Apache-2.0 전환 진행 중                   2026-09-03


modelcontextprotocol/typescript-sdk           13420    MIT → Apache-2.0 전환 진행 중                   2026-09-16


module-federation/core                        2645     MIT                                        2026-09-16


moghtech/komodo                               12326    GPL-3.0                                    2026-09-01


mozilla-ai/any-llm                            2198     Apache-2.0                                 2026-09-17


mozilla-ai/llamafile *                        25986    Apache-2.0                                 2026-09-16


mudler/LocalAI                                49147    MIT                                        2026-09-17


n8n-io/n8n *                                  205085   Sustainable Use License (.ee 파일은 Enterpr   2026-09-18


nestjs/nest                                   76683    MIT                                        2026-09-17


nginx-proxy/nginx-proxy                       19913    MIT                                        2026-08-26


nicholas-fedor/watchtower                     4461     Apache-2.0                                 2026-09-18


nlkitai/nlux                                  1380     MPL-2.0 + AI 학습·코드번역 제한 조항 (비OSI 변형)       2025-11-25


NVIDIA-NeMo/Guardrails *                      7160     Apache-2.0 (SPDX 헤더)                       2026-09-17


NVIDIA/TensorRT-LLM                           14641    Apache-2.0                                 2026-09-18


oauth2-proxy/oauth2-proxy                     14968    MIT                                        2026-09-13


offen/docker-volume-backup                    4011     MPL-2.0                                    2026-09-15


OHF-Voice/piper1-gpl *                        5609     GPL-3.0                                    2026-09-17


ollama/ollama *                               181183   MIT                                        2026-09-17


oobabooga/textgen                             47683    AGPL-3.0                                   2026-08-17


open-feature/spec                             1258     Apache-2.0                                 2026-09-15


open-policy-agent/opa                         12245    Apache-2.0                                 2026-09-17


open-telemetry/opentelemetry-collector *      7565     Apache-2.0                                 2026-09-17


open-telemetry/opentelemetry-python-contrib   1095     Apache-2.0                                 2026-09-17


open-telemetry/semantic-conventions           651      Apache-2.0                                 2026-09-16


open-telemetry/semantic-conventions-genai     370      Apache-2.0                                 2026-09-16


open-webui/mcpo *                             4378     MIT                                        2026-02-27


open-webui/open-webui *                       152425   Open WebUI License (BSD-3 기반 + 브랜딩 조건)     2026-09-04


open-webui/pipelines *                        2435     MIT                                        2025-08-18


openai/codex *                                124973   Apache-2.0                                 2026-09-18


openai/gpt-oss                                20407    Apache-2.0                                 2026-07-24


openai/harmony *                              4502     Apache-2.0                                 2026-04-08


openai/openai-agents-python *                 29531    MIT                                        2026-09-17


openai/openai-apps-sdk-examples               2338     MIT                                        2026-04-15


openai/openai-python *                        31640    Apache-2.0                                 2026-09-18
openai/whisper                                   109302   MIT                                        2026-08-31


openbao/openbao                                  7407     MPL-2.0                                    2026-09-17


openclaw/clawhub                                 9422     MIT                                        2026-09-17


openclaw/openclaw *                              390029   MIT (OpenClaw Foundation)                  2026-09-18


opencode-ai/opencode                             13751    MIT                                        2025-09-18   A

OpenHands/OpenHands *                            88354    MIT                                        2026-09-17


openlit/openlit                                  2770     Apache-2.0                                 2026-09-17


oras-project/oras                                2433     Apache-2.0                                 2026-09-15


ory/hydra                                        17547    Apache-2.0                                 2026-07-29


ory/kratos                                       13880    Apache-2.0                                 2026-07-29


OvidijusParsiunas/deep-chat                      3714     MIT                                        2026-09-17


paperclipai/paperclip *                          80953    MIT                                        2026-09-18


pgvector/pgvector *                              23046    PostgreSQL License                         2026-09-08


pingwu/maca                                      8        MIT                                        2026-01-26


pnganga813-commits/Aether-desktop-orchestrator   85       NONE (LICENSE 확인 필요)                       2026-09-18


podman-desktop/podman-desktop                    8020     Apache-2.0                                 2026-09-18


polarsource/polar *                              10271    Apache-2.0                                 2026-09-17


pomerium/pomerium                                5009     Apache-2.0                                 2026-09-17


portainer/portainer                              38520    Zlib                                       2026-09-18


Portkey-AI/gateway *                             13028    MIT                                        2026-05-25


postgres/postgres *                              22130    PostgreSQL License                         2026-09-18


PrefectHQ/fastmcp *                              27717    Apache-2.0                                 2026-09-17


PrefectHQ/fastmcp-ts                             65       Apache-2.0 (LICENSE 본문 확인)                 2026-09-11


PrefectHQ/prefect                                23859    Apache-2.0                                 2026-09-17


prisma/orm                                       47618    Apache-2.0                                 2026-09-17


project-zot/zot                                  2773     Apache-2.0                                 2026-09-17


prometheus/alertmanager                          8613     Apache-2.0                                 2026-09-17


prometheus/prometheus *                          66109    Apache-2.0                                 2026-09-17


promptfoo/promptfoo                              25243    MIT                                        2026-09-18


protectai/llm-guard                              3207     MIT                                        2026-07-08   A

pydantic/pydantic-ai *                           20021    MIT                                        2026-09-18


python-arq/arq                                   3014     MIT                                        2026-04-16


pytorch/pytorch                                  103076   BSD-3-Clause (LICENSE 파일 판독)               2026-09-18


qdrant/qdrant *                                  34650    Apache-2.0                                 2026-09-03


QwenLM/Qwen3                                     27637    저장소 LICENSE 파일 없음 (모델 카드 Apache-2.0 은 HF   2026-01-09


QwenLM/Qwen3-Coder *                             16839    저장소 LICENSE 파일 없음 (HF 모델 카드 확인 필요)         2026-03-24


rancher-sandbox/rancher-desktop                  7353     Apache-2.0                                 2026-09-17


redis/redis                                      76398    RSALv2 OR SSPLv1 OR AGPLv3 (8.0+, 3중) /    2026-09-17
renovatebot/renovate             22528    AGPL-3.0                                   2026-09-18


restatedev/restate               4438     BUSL-1.1 (내부 배포 허용, 공개 Restate 서비스 금지)     2026-09-17


restic/restic                    36105    BSD-2-Clause                               2026-08-29


rhasspy/piper                    11284    MIT                                        2025-08-26   A

rowboatlabs/rowboat *            17888    Apache-2.0                                 2026-09-17


run-llama/llama_index *          52206    MIT                                        2026-09-17


runtipi/runtipi                  9670     GPL-3.0                                    2026-09-12


sgl-project/sglang *             36116    Apache-2.0                                 2026-09-18


Significant-Gravitas/AutoGPT *   187421   Polyform Shield (autogpt_platform/) + MI   2026-09-04


SigNoz/signoz                    32120    MIT (ee/·cmd/enterprise/ 별도)               2026-09-18


sigstore/cosign                  6310     Apache-2.0                                 2026-09-15


simonw/llm                       12525    Apache-2.0                                 2026-09-08


simstudioai/sim *                29660    Apache-2.0                                 2026-09-18


single-spa/single-spa            13877    MIT                                        2025-06-19


slackapi/bolt-python             1326     MIT                                        2026-09-08


slsa-framework/slsa-verifier     344      Apache-2.0                                 2026-08-07


smapiot/piral                    1930     MIT                                        2026-09-09


snowdreamtech/template           15       MIT                                        2026-09-12


snyk/agent-scan                  3060     Apache-2.0                                 2026-09-17


sparckles/Robyn                  7406     BSD-2-Clause                               2026-08-09


sqlalchemy/alembic               4400     MIT                                        2026-09-11


sqlalchemy/sqlalchemy            12164    MIT                                        2026-09-15


sqlite/sqlite                    10500    Public Domain                              2026-09-17


strands-agents/harness-sdk *     7342     Apache-2.0                                 2026-09-17


streamlit/streamlit *            45778    Apache-2.0                                 2026-09-18


supabase/supabase *              109931   Apache-2.0                                 2026-09-18


superradcompany/microsandbox *   8285     Apache-2.0                                 2026-09-17


supertokens/supertokens-core     15312    Apache-2.0 (ee/ 별도)                        2026-09-04


SYSTRAN/faster-whisper           25450    MIT                                        2025-11-19


tadata-org/fastapi_mcp *         12008    MIT                                        2025-08-10


taskforcesh/bullmq               9413     MIT                                        2026-09-18


taskiq-python/taskiq             2335     MIT                                        2026-09-17


temporalio/temporal              23144    MIT                                        2026-09-18


tensorflow/tensorflow            200160   Apache-2.0                                 2026-09-18


tensorzero/tensorzero *          11720    Apache-2.0                                 2026-06-04   A

theagentrouter/agent-router      2116     Apache-2.0                                 2026-09-17


tobymao/sqlglot                  9625     MIT                                        2026-09-18


tokio-rs/axum                    27170    MIT                                        2026-09-15
topoteretes/cognee *                   30794   Apache-2.0                                 2026-09-09


traceloop/openllmetry                  7438    Apache-2.0                                 2026-09-17


traefik/traefik                        64888   MIT                                        2026-09-14


TransformerOptimus/SuperAGI            17683   MIT                                        2025-01-22


umijs/qiankun                          16686   MIT                                        2026-09-17


Unleash/unleash                        13813   AGPL-3.0                                   2026-09-18


Unstructured-IO/unstructured           15445   Apache-2.0                                 2026-09-15


valkey-io/valkey                       27228   BSD-3-Clause                               2026-09-17


vercel/ai                              26819   Apache-2.0                                 2026-09-17


vercel/chatbot *                       20955   Apache-2.0                                 2026-07-08


verdaccio/verdaccio                    17886   MIT                                        2026-09-10


vibrantlabsai/ragas                    15763   Apache-2.0                                 2026-02-24


vishalmysore/Tools4AI                  190     MIT                                        2026-07-28


vllm-project/vllm *                    92055   Apache-2.0                                 2026-09-18


wasmCloud/wasmCloud                    2437    Apache-2.0                                 2026-09-17


weaviate/weaviate                      16819   BSD-3-Clause (wl/ 디렉터리만 Weaviate License   2026-09-17


willfarrell/docker-autoheal            1999    MIT                                        2025-09-09


windmill-labs/windmill                 17958   AGPL-3.0 + Apache-2.0 혼합 + EE 독점           2026-09-17


WisemanLim/pub-MultiAIAgent-Template   1       LICENSE 파일 없음 (사용자 본인 저장소)                 2026-07-30


WisemanLim/pub-Server-Init             0       LICENSE 파일 없음 (사용자 본인 저장소)                 2026-06-30


WisemanLim/pub-SSL-Cert-Manager        0       LICENSE 파일 없음 (사용자 본인 저장소)                 2025-12-08


WisemanLim/pub-wise-dev-std            0       LICENSE 파일 없음 (사용자 본인 저장소)                 2026-08-28


WisemanLim/pub-wise-vibe               1       MIT                                        2026-03-14


WisemanLim/pub-wsa-for-sdd             0       LICENSE 파일 없음 (사용자 본인 저장소)                 2026-06-13


WisemanLim/wsa4sdd-samples             0       LICENSE 파일 없음 (사용자 본인 저장소)                 2026-06-13


withastro/astro                        62655   MIT                                        2026-09-18


zitadel/zitadel                        15044   AGPL-3.0                                   2026-09-17
부록 C. 사용자 즐겨찾기 교차
스타 목록 5,665건과 실측 집합 361건의 교집합 120건. 본문 * 표기와 동일. 사용자 저장소 6개는 별도(9.11).
저장소                                    ★        라이선스
2FastLabs/agent-squad                  7765     Apache-2.0

a2aproject/A2A                         25828    Apache-2.0

aaif-goose/goose                       54406    Apache-2.0

abiosoft/colima                        30860    MIT

activepieces/activepieces              24531    MIT (packages/ee/ 별도 상용)

ag-ui-protocol/ag-ui                   15934    MIT

agentsmd/agents.md                     24438    MIT

agno-agi/agno                          42227    Apache-2.0

anomalyco/opencode                     208244   MIT

anthropics/claude-code                 145936   Anthropic Commercial Terms (LICENSE.md, 소스 비

anthropics/claude-plugins-official     36447    Apache-2.0

anthropics/skills                      176932   LICENSE 파일 없음 (저장소 SPDX none)

apache/airflow                         46885    Apache-2.0

Arize-ai/phoenix                       11525    Elastic-2.0 (ELv2, 관리형 제공 금지)

astral-sh/uv                           89941    Apache-2.0

AUTOMATIC1111/stable-diffusion-webui   164996   AGPL-3.0

BerriAI/litellm                        59036    MIT (enterprise/ 디렉터리 별도 라이선스)

bytecodealliance/wasmtime              18643    Apache-2.0

bytedance/deer-flow                    82612    MIT

caddyserver/caddy                      75834    Apache-2.0

Chainlit/chainlit                      12457    Apache-2.0

chroma-core/chroma                     29320    Apache-2.0

comet-ml/opik                          22104    Apache-2.0

Comfy-Org/ComfyUI                      133706   GPL-3.0

confident-ai/deepeval                  18317    Apache-2.0

CopilotKit/CopilotKit                  37403    MIT

crewAIInc/crewAI                       58715    MIT

danny-avila/LibreChat                  44255    MIT

daytonaio/daytona                      71721    AGPL-3.0 · 2026-06 유지보수 중단 선언 (SPDX none)

deepseek-ai/DeepSeek-R1                91980    MIT

deepseek-ai/DeepSeek-V3                104464   MIT

docling-project/docling                66588    MIT

drizzle-team/drizzle-orm               35803    Apache-2.0

duckdb/duckdb                          41472    MIT

e2b-dev/E2B                            13864    Apache-2.0

exo-explore/exo                        47490    Apache-2.0

fastapi/fastapi                        102408   MIT

fishaudio/fish-speech                  32729    Fish Audio Research License (사내 사용도 상용 정의 —

FlowiseAI/Flowise                      55467    Apache-2.0 (enterprise/ 별도) [아카이브 2026-08-13

FoundationAgents/MetaGPT               70484    MIT

getzep/graphiti                        30975    Apache-2.0

ggml-org/llama.cpp                     128619   MIT

gin-gonic/gin                          89232    MIT

goharbor/harbor                        29401    Apache-2.0

google-gemini/gemini-cli               107051   Apache-2.0

google/adk-samples                     10341    Apache-2.0

googleapis/python-genai                3981     Apache-2.0
gradio-app/gradio                        43565    Apache-2.0

grafana/grafana                          76792    AGPL-3.0

grafana/loki                             28908    AGPL-3.0

grafana/tempo                            5478     AGPL-3.0

helm/helm                                30251    Apache-2.0

HKUDS/AutoAgent                          9793     MIT

honojs/hono                              32258    MIT

huggingface/transformers                 166261   Apache-2.0

infiniflow/ragflow                       90911    Apache-2.0

janhq/jan                                44516    Apache-2.0 계열 (Menlo Research, LICENSE 본문 확인

kagent-dev/kagent                        3752     Apache-2.0

katanemo/plano                           7055     Apache-2.0

keycloak/keycloak                        36838    Apache-2.0

khoj-ai/khoj                             37399    AGPL-3.0

kortix-ai/suna                           20220    Elastic-2.0 (관리형 서비스 제공 금지)

langchain-ai/agent-chat-ui               3162     MIT

langchain-ai/deepagents                  29534    MIT

langchain-ai/langchain                   146562   MIT

langchain-ai/langgraph                   41863    MIT

langflow-ai/langflow                     154959   MIT

langgenius/dify                          156215   Apache-2.0 변형 (멀티테넌트·로고 제거 금지 추가 조건)

letta-ai/letta                           24783    Apache-2.0

mastra-ai/mastra                         28147    Apache-2.0 (ee/ 별도 상용)

maximhq/bifrost                          8147     Apache-2.0

mem0ai/mem0                              65539    Apache-2.0

microsoft/agent-governance-toolkit       6282     MIT

microsoft/autogen                        61035    CC-BY-4.0 (코드에 부적합) · 유지보수 모드

milvus-io/milvus                         46153    Apache-2.0

Mintplex-Labs/anything-llm               66156    MIT

ml-explore/mlx-examples                  8954     MIT

ml-explore/mlx-lm                        7043     MIT

modelcontextprotocol/inspector           10904    LICENSE 파일 없음 (README 확인 필요)

modelcontextprotocol/python-sdk          24325    MIT

modelcontextprotocol/servers             90426    MIT → Apache-2.0 전환 진행 중

mozilla-ai/llamafile                     25986    Apache-2.0

n8n-io/n8n                               205085   Sustainable Use License (.ee 파일은 Enterprise)

NVIDIA-NeMo/Guardrails                   7160     Apache-2.0 (SPDX 헤더)

OHF-Voice/piper1-gpl                     5609     GPL-3.0

ollama/ollama                            181183   MIT

open-telemetry/opentelemetry-collector   7565     Apache-2.0

open-webui/mcpo                          4378     MIT

open-webui/open-webui                    152425   Open WebUI License (BSD-3 기반 + 브랜딩 조건)

open-webui/pipelines                     2435     MIT

openai/codex                             124973   Apache-2.0

openai/harmony                           4502     Apache-2.0

openai/openai-agents-python              29531    MIT

openai/openai-python                     31640    Apache-2.0

openclaw/openclaw                        390029   MIT (OpenClaw Foundation)

OpenHands/OpenHands                      88354    MIT

paperclipai/paperclip                    80953    MIT

pgvector/pgvector                        23046    PostgreSQL License

polarsource/polar                        10271    Apache-2.0

Portkey-AI/gateway                       13028    MIT
postgres/postgres              22130    PostgreSQL License

PrefectHQ/fastmcp              27717    Apache-2.0

prometheus/prometheus          66109    Apache-2.0

pydantic/pydantic-ai           20021    MIT

qdrant/qdrant                  34650    Apache-2.0

QwenLM/Qwen3-Coder             16839    저장소 LICENSE 파일 없음 (HF 모델 카드 확인 필요)

rowboatlabs/rowboat            17888    Apache-2.0

run-llama/llama_index          52206    MIT

sgl-project/sglang             36116    Apache-2.0

Significant-Gravitas/AutoGPT   187421   Polyform Shield (autogpt_platform/) + MIT (그

simstudioai/sim                29660    Apache-2.0

strands-agents/harness-sdk     7342     Apache-2.0

streamlit/streamlit            45778    Apache-2.0

supabase/supabase              109931   Apache-2.0

superradcompany/microsandbox   8285     Apache-2.0

tadata-org/fastapi_mcp         12008    MIT

tensorzero/tensorzero          11720    Apache-2.0

topoteretes/cognee             30794    Apache-2.0

vercel/chatbot                 20955    Apache-2.0

vllm-project/vllm              92055    Apache-2.0
부록 D. 이미지·그림 출처
그림     내용                            원천                             복제 여부
—      인포그래픽 「20 AI GitHub Repos」    사용자 제시(이전 세션). 본 세션 첨부 파일 없음   삽입하지 않음. 요약 보고서 20행만 전사(3.1)
—      GitHub 검색 결과 페이지              사용자 제시 URL                     삽입하지 않음. 저장소 목록만 전사(3.3)
—      v1 템플릿 화면(MultiAIAgent.gif)   사용자 저장소                        삽입하지 않음. 기능만 전사(3.4)

그림 1   AgentPlaza 개요                 요구사항 (1)~(8) + 3장              자체

그림 2   10영역                          본 문서 기능 분해                     자체

그림 3   LLM 공급 계층                     9.2 실측 + LLM 조사                자체

그림 4   agent.zip·등록 8단계              10.2·10.4                      자체(Dify·MCPB·ClawHub·Claude Code 규격 참고, 도식 비복
                                                                    제)

그림 5   운용 3모드                        4.3                            자체

그림 6   마켓 3경로                        D6                             자체

그림 7   compose 토폴로지                  10.3 + Compose Spec include    자체(CasaOS·Umbrel·Runtipi·Coolify 구조 참고, 코드 비복제)

그림 8   프로토콜 표면                       11장                            자체

그림 9   인포그래픽 20 결합 방식                3.1 판정                         자체(카드 격자는 원본 레이아웃과 무관)
부록 E. 한계
   첨부 인포그래픽 파일이 본 세션에 전달되지 않아 요약 보고서의 20개 목록·분류·라이선스를 전사 원천으로 삼았다. 원본 이미
    지의 부제·장식 문구는 검증하지 못했다.
   검색 300건 중 상위 60건을 판독하고 14건을 표에 실었다. 전체 실측은 아니다.
   실측 347개 저장소 중 LICENSE 판독으로 보정한 75건 외에도 오픈코어 디렉터리가 공식 이미지에 포함되는지는 [미확인].
   MCP inspector·typescript-sdk 패키지 버전, MCP 레지스트리 GA 여부, MCP 의 AAIF 이관, IBM/mcp-context-forge 의 A2A 지원, compose
    OCI/Git 원격 리소스 문법, kompose 커버리지, podman GPU(CDI) 는 [미확인].
   LiteLLM 공식 이미지의 enterprise/ 포함 여부, Jan·llamafile·ktransformers 의 Anthropic 호환, Codex·Claude Code·OpenClaw 의 ACP 네
    이티브 지원은 [미확인].
   기간·지연·비용 수치는 가정이다. 구현 후 실측으로 교체한다.
   법령 조항 적용 여부는 법무 검토가 필요하다.
   양식만 기존 내부 PRD 를 따랐고 그 내용은 출처가 아니다.
부록 F. v1 → v2 변경 이력
v1(2026-09-18)은 요구사항 (1)~(8)을 도메인 70항목으로 분해한 플랫폼 PRD 였다. v2(2026-09-18)는 사용자 로컬 참조 프로젝트 11종
을 분석해 독립 구동(Zip) Addon-Agent 후보군을 업무·업종·도메인 3축으로 분류·배치했다. v1 본문(1~15장·부록 A~E)은 변경 없이 유
지한다.
 구분             v1                             v2 추가·변경

 장 구성           1~15장 + 부록 A~E                 16·17·18장 + 부록 F 추가. 1.4 문서구성·표지 갱신

 16장            -                              참조 프로젝트 11종 인벤토리, 세 갈래 계열, 마켓 설계 준용(SeCMP·MAS 데이터모델·배치·서명·리뷰), 토폴로지 T1~T6

 17장            -                              분류 3축(업무 W01~W19·업종 KSIC·도메인 10), 카테고리 slug 체계, 독립 구동 규격·등급, 후보 수량·분포, 업종별 스타
                                               터 팩 8종

 18장            -                              도메인별 후보 전수표(candidates.tsv)

 데이터            data.py + repos.tsv            data_v2.py + candidates.tsv 추가. build_all 이 자동 병합

 부제·표지          …PRD                           …PRD (v2), 작성일 v2 표기, 참조 프로젝트 원천 추가

 산출물 이동         -                              v1 산출물을 old/ 로 이동: old/AgentPlaza_PRD.v1.docx·.pdf·AgentPlaza_assets.v1/




이동 규칙(사용자 지시). 이전 버전은 old/ 이하로 이동한다. old/AgentPlaza_PRD.v1.{docx,pdf} 와 old/AgentPlaza_assets.v1/ 에 v1 스냅숏
을 보존했다. 현행 AgentPlaza_PRD.{docx,pdf} 가 v2 다.
부록 G. 참조 프로젝트 출처
모두 사용자 로컬 저장소(2026-09-18 소스 실독). 원격 저장소·라이선스는 [확인 필요].
 약칭                       로컬 경로                                                           라이선스 파일
 MultiAIAgent-Template    /Users/wise/Developer/eden-MultiAIAgent/MultiAIAgent-Template   없음

 SeCuardian               /Users/wise/Developer/wise-SeCuardian/SeCuardian                확인 필요

 SeCuardian-Basic         /Users/wise/Developer/wise-SeCuardian/SeCuardian-Basic          확인 필요

 SeCuardian-Marketplace   /Users/wise/Developer/wise-SeCuardian/SeCuardian-Marketplace    확인 필요

 SecuFTPL                 /Users/wise/Developer/wise-SeCuardian/SecuFTPL                  확인 필요

 MAS-Basic                /Users/wise/Developer/eden-MultiAIAgent/MAS-Basic               확인 필요

 MAS-Marketplace          /Users/wise/Developer/eden-MultiAIAgent/MAS-Marketplace         확인 필요

 DOPQ-MultiAIAgent        /Users/wise/Developer/eden-project/DOPQ-MultiAIAgent            확인 필요

 HRAgent-MultiAIAgent     /Users/wise/Developer/eden-project/HRAgent-MultiAIAgent         확인 필요

 SmartHaccp-MultiAgent    /Users/wise/Developer/eden-project/SmartHaccp-MultiAgent        확인 필요

 MAA-Bonded-Areas         /Users/wise/Developer/eden-project/MAA-Bonded-Areas             확인 필요




분석은 general-purpose 4개 병렬(SeCuardian 4종·MAS 3종·DOPQ+HR·SmartHaccp+Bonded)로 수행했고, 후보는 candidates.tsv 로 집계
했다. 마켓 설계는 SeCuardian-Marketplace(marketplace-assets 30여 종·데이터모델 15표)와 MAS-Marketplace(manifest v2·카테고리·배치·
리뷰·서명)를 준용했다.
