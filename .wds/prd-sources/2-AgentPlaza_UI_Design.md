       UI DESIGN DOCUMENT · 화면설계서




       AgentPlaza 화면설계서
       로컬·퍼블릭 LLM 통합 Multi-Agent 플랫폼 — 설치 위저드 / 콘솔(대시보드·어시스턴트·마켓플레이스·에이전트 관리·워크플로·지식·거버넌스
       ·LLM·관측·조직·설정) / Addon 화면 규약



       기준 문서 AgentPlaza_PRD.docx v2 (2026-09-18, FR-D 70 · FR-X 12 · FR-P 12 = 94항 · Addon 후보 303종)
       화면 수 80 (페이지 49 · 모달/위저드 18 · 탭 10 · 공통 규약 3) · 14 그룹
       버전 v1.0 · 작성일 2026-09-19 · 작성 AgentPlaza PRD 팀




       저장 위치: wise-Analysis-Repos/Need-to-be-organized-into-PRD/AgentPlaza_UI_Design.pptx (자산: AgentPlaza_UI_assets/pptx/ · 참조 구현 역문서화: AgentPlaza_UI_assets/research/)



AgentPlaza 화면설계서 · v1.0 · 표지                                                                                                                                              1
문서 정보 · 개정 이력
화면설계서(UI Design Document) 관리 정보와 History


문서명                 AgentPlaza 화면설계서(UI Design Document)                                         버전       일자            작성자                변경 내용                       해당 페이지

                                                                                                                                           초판. PRD v2 전 항목 기준 화면 80종
                    AgentPlaza — 로컬 LLM·퍼블릭 AI·Orchestrator/Assistant·Addon                      v1.0     2026-09-19    AgentPlaza PRD 팀                               전체
시스템                                                                                                                                        설계
                    마켓플레이스·MCP/A2A·compose 독립 구동

                    AgentPlaza_PRD.docx v2 (2026-09-18) · FR-D 70 / FR-X 12 / FR-P 12 · 16~18장
기준 문서
                    참조 프로젝트·3축 분류·Addon 후보

                    설치 위저드 → 로그인 → 대시보드 → AI 어시스턴트 → 마켓플레이스(도입 경로 A/B/C)
범위                  → 에이전트 관리(스캐폴드·ZIP·8단계 설치·MCP/A2A) → 워크플로·지식·플레이그라운드
                    → 거버넌스·LLM·조직·설정 → 관측·감사·운영 → Addon 화면 규약

                    웹 콘솔(React) · Addon 은 별 오리진 iframe + postMessage · plaza CLI 는 화면 동등         표기 규칙
플랫폼                                                                                              • 화면 ID: SCR-<그룹 A~N><2자리>. 그룹 = A 인증·설치 · B 메인·대시보드 · C AI 어시스턴트 · D 에이전트 관리 ·
                    명령 표기
                                                                                                 E 마켓플레이스 · F 워크플로 · G 지식(RAG) · H 플레이그라운드·평가 · I 가드레일·거버넌스 · J LLM·모델 · K 조직·
                    공공 SW 산출물 표준(CBD 가이드 D2 사용자 인터페이스 설계서: 구조도→목록→상세,                            사용자·권한 · L 설정·프로필 · M 관측·감사·운영 · N Addon 화면 규약
템플릿 근거              입출력 항목 속성) + 국내 스토리보드 관행(화면 ID·번호주석·Description 표) + 국제 UI                   • 구현 시 하위 변형은 접미로 파생: -Mnn 모달 · -Tnn 탭 · -Cnn 조건 변형 · -Enn 오류 변형. 폐기 ID 재사용 금지
                    Spec(상태·메시지·접근성·추적성) — 부록 F                                                  • 와이어프레임의 ①②③ 번호 = 우측 기능 설명 표의 No
                    SeCuardian-Marketplace · MAS-Marketplace · SeCuardian-Basic · MAS-Basic ·    • '연계' 열의 D1-01 / X01 / P01 은 PRD 5장 항목 ID, SCR-… 은 이동·호출 화면, MSG-… 은 부록 B 메시지,
참조 구현               MultiAIAgent-Template(addon-agents) · DOPQ/HR/SmartHaccp/MAA 도메인 Addon       ST-… 은 상태 규약
                    — 소스 역문서화(research/)                                                         • 색은 의미로만 쓰고 텍스트를 병기한다(색만으로 정보 전달 금지)
                    python-pptx 생성(AgentPlaza_UI_assets/pptx/build_ui.py). 와이어프레임은 편집 가능한        • [미확인] 은 PRD 와 동일하게 미검증 항목 표시
작성 도구
                    네이티브 도형

                    빌드 시 PRD 94항 ↔ 화면 ID 커버리지 assert(부록 C RTM) · 화면 ID 순서·누락 assert ·
검증
                    콜아웃 수 = 기능표 행 수




AgentPlaza 화면설계서 · v1.0 · 문서 정보                                                                                                                                                    2
목차
PART 1 앞부속 → PART 2 화면별 설계(14그룹) → PART 3 부록


   PART 1 개요·구조                                PART 2 화면별 설계
    1. 시스템 개요·운용 모드(M1/M2/M3)                   1. A. 인증·설치 (4)
    2. 화면 ID 명명 규칙·문서 표기                        2. B. 메인·대시보드 (4)
    3. 메뉴 구조도(IA) ① 사용 영역                       3. C. AI 어시스턴트 (7)
                                                4. D. 에이전트 관리 (13)
    4. 메뉴 구조도(IA) ② 관리 영역·Addon
                                                5. E. 마켓플레이스 (13)
    5. 화면 목록(80)                                6. F. 워크플로 (5)
    6. 권한(역할) × 화면 매트릭스                         7. G. 지식(RAG) (3)
    7. 화면 흐름도 ①~⑤                               8. H. 플레이그라운드·평가 (3)
    8. 공통 UI 가이드 — 레이아웃·토큰·컴포넌트                 9. I. 가드레일·거버넌스 (5)
    9. 공통 UI 가이드 — 상태·메시지·유효성·오류코드              10. J. LLM·모델 (7)
                                                11. K. 조직·사용자·권한 (6)
                                                12. L. 설정·프로필 (2)
                                                13. M. 관측·감사·운영 (6)
                                                14. N. Addon 화면 규약 (2)


                                               PART 3 부록
                                                A. 모달·위저드 카탈로그
                                                B. 메시지 정의(MSG-001~020)·서버 오류 ↔ 화면 처리
                                                C. 요구사항 추적표(RTM) PRD 94 ↔ 화면
                                                D. 비화면(백엔드·프로토콜) 요구의 표출 위치
                                                E. 참조 구현 결함 → 설계 변경 총람
                                                F. 참고 자료·템플릿 출처·한계




AgentPlaza 화면설계서 · v1.0 · 목차                                                           3
       PART 1


       개요 · 구조
       시스템 개요 · 명명 규칙 · IA · 화면 목록 · 권한 매트릭스 · 화면 흐름도 · 공통 UI 가이드




AgentPlaza 화면설계서 · v1.0 · 개요 · 구조                                   4
1. 시스템 개요 · 운용 모드
PRD 4장 — 코어 콘솔 + 기본 에이전트 둘(Orchestrator·Assistant) + Addon 에이전트(agent.zip). 세 운용 모드가 같은 콘솔을 쓴다


                                                                                                  핵심 설계 원칙(PRD DP1~DP10 중 화면에 직접 영향)
운용 모드                  설명                                화면에 미치는 영향                               • DP1 코어/스토어 이원화 → 콘솔(코어) 와 마켓(자산) 화면 분리, Addon 은 iframe 격리(N01)
                                                                                                  • DP2 agent.zip = frontend/backend/database/meta → 업로드(D04)·설치 진행(D05) 이 8단계
                                                                                                  게이트를 그대로 보인다
                       docker compose 한 벌로 플랫폼+로컬 LLM.   설치 위저드(A02) 로컬 경로만으로 완료 · 에어갭            • DP3 로컬 우선·등급 정책 → 모델 카탈로그(J01) 의 L0~L3 등급, 외부 전송 사전 차단(MSG-010)
M1 독립(Standalone)                                                                                 • DP4 생성물 일치 → 스캐폴드(D03)·추출(D08) 의 산출물이 설치 가능한 ZIP
                       폐쇄망                               번들(M06) · 오프라인 배너(ST-08)
                                                                                                  • DP5 표준 프로토콜 → 에이전트별 MCP(D06)·A2A/OpenAI 호환(D07)
                                                         원격 등록(D11) · 공급자 키(J02) ·                • DP6 관찰 가능 → 도구 호출·승인·리뷰 카드가 대화(C01) 에 인라인, 트레이스(M02) 링크
                       외부 MCP/A2A 에이전트·퍼블릭 LLM·SSO                                                • DP8 사람 개입 → 승인함(I04) 이 1급 화면, 만료·감사 연결
M2 연계(Federated)                                         SSO(A03·K05) · 데이터 등급 차단
                       연동                                                                         • DP9 독립 구동 → Standalone 내보내기(D08) · 런타임(M04)
                                                         (J04·MSG-010)
                                                                                                  • 참조 구현(SeCuardian/MAS 마켓) 의 검증된 구조는 유지하고 결함은 교정(부록 E)
                                                         카탈로그(E01) · 도입 위저드(E04) · 구매·라이선스
M3 즉시 사용(Hosted 마켓)    마켓 서버에서 다운로드·설치·구매
                                                         (E12) · 레지스트리(E13)
                                                                                                  역할 체계: supervisor(플랫폼 운영) > admin(조직 관리) > user(사용). 관리 메뉴 = supervisor|admin.
                                                                                                  라우트 역할 가드 + 서버 403 2중화.

에이전트 도입 경로              화면                           요지


A 다운로드·설치               E01 → E03 → E04 → D05        마켓에서 agent.zip 받아 8단계 게이트 후 컨테이너 기동


B 직접 설치                 D04 → D05                    ZIP 업로드(fe/be/db/meta) · 스캐폴드(D03) 로 생성


                                                     MCP 서버·A2A Agent Card·OpenAPI 를 external 로
C 연동·연계                 D11 → D06/D07
                                                     등록(설치 없음)




AgentPlaza 화면설계서 · v1.0 · PART 1 · 시스템 개요                                                                                                                                          5
2. 화면 ID 명명 규칙 · 문서 표기
국내 관행(구분_카테고리_순번, 팝업 접미사) 과 PRD ID 체계(D/X/P) 를 결합



구분                     규칙                                              예                   화면별 슬라이드 구성          내용


화면 ID                  SCR-<그룹 A~N><2자리>                               SCR-E03                                  시스템 · 화면 ID · 화면 유형 / 화면명 · 화면 경로(라우트) · 접근 권한 / 우선순위
                                                                                           상단 메타 표
                                                                                                                (P0~P2) · PRD 추적 · 작성일/버전

모달/위저드(구현 파생)          <화면>-M<2자리> · 위저드 단계는 -Snn                      SCR-D02-M01
                                                                                           설명                   화면 목적·핵심 동작 2~3문장 + 참조 구현 대비 변경 요지

탭/조건/오류 변형             <화면>-T<nn> · -C<nn>(권한·상태 변형) · -E<nn>(오류 표시)   SCR-E03-C02
                                                                                                                편집 가능한 도형. ①②③ 번호 마킹. 콘솔 셸(좌측 네비 12 + 설치된 Addon 섹션·상단
                                                                                           좌측 와이어프레임
                       A 인증·설치 B 메인 C 어시스턴트 D 에이전트 E 마켓 F 워크플로                                                  바) 은 공통
그룹 코드                  G 지식 H 플레이그라운드 I 거버넌스 J LLM K 조직 L 설정 M -
                       관측·운영 N Addon
                                                                                           우측 기능 설명 표           No · 구성요소 · 유형 · 기능 설명/동작(검증·상태·전이) · 연계(PRD ID·화면·메시지)
번호 체계                  01 목록/메인 · 02 상세/생성 · 이후 보조. 폐기 ID 재사용 금지       SCR-D01~D13

                                                                                           하단                   관련 PRD 항목 전체 · 푸터(문서·버전·그룹·페이지)
요구사항 연계                PRD 5장 D<도메인>-<번호> · X<번호>(공백) · P<번호>(플랫폼)     D6-02 · X01 · P09


                       CMP-nn 컴포넌트 · ST-nn 상태 · MSG-nnn 메시지 · FL-nn 흐름                     노트                   상태별 표현(ST)·메시지(MSG)·참조 구현 대비 변경(발표자 노트)
공통 규약 ID                                                               MSG-012
                       · OUT-nn 출력물


버전                     문서 v<major>.<minor>, 화면별 변경은 개정 이력에 페이지 기재 v1.0                     유형(Type) 어휘
                                                                                           버튼 · 버튼(위험) · 입력 · 선택(드롭다운) · 라디오 · 체크박스 · 토글 · 목록 · 표 · 카드 · 에이전트 카드 · 도구
                                                                                           카드 · 승인 카드 · 드롭영역 · 배지 · 상태 · 칩 · 탭 · 네비 · 배너 · 안내 · 코드 · 차트 · 진행 · 트리 · 드로어 ·
                                                                                           iframe · 컨테이너 · 규칙 · 대화 버블 · 스테퍼




AgentPlaza 화면설계서 · v1.0 · PART 1 · 명명 규칙                                                                                                                                    6
3. 메뉴 구조도(IA) ① — 사용 영역
좌측 네비 앞 6항목. 괄호 = 화면 ID. 사용자(user) 는 이 영역 + 내 프로필



           대시보드                            AI 어시스턴트                       마켓플레이스                         에이전트 관리                             워크플로           지식(RAG)


홈 대시보드 (B02)                       대화 (C01)                       카탈로그 (E01)                    목록 (D01) → 상세·설정 (D02)           목록 (F01)           컬렉션 (G01)



알림 센터 (B03)                        세션·히스토리 (C02)                  카테고리 3축 (E02)                 스캐폴드 (D03) · ZIP 업로드 (D04)       빌더 (F02)           문서·인덱싱 (G02)



온보딩 체크리스트 (B04)                    파일·멀티모달 (C03)                  자산 상세 (E03)                   설치 진행 8단계 (D05)                  실행 이력 (F03)        검색 시험 (G03)



                                   메모리·맞춤지침 (C04)                 도입 위저드 (E04) · 직접/연동 (E05)    MCP (D06) · 프로토콜 (D07)           트리거 (F04)



                                   스코프 채팅 /a/{agent}/chat (C05)   게시 (E06) · 퍼블리셔 (E07)         추출·Standalone (D08) · 워커 (D09)   DSL 반입 (F05)



                                   지식 연결 (C06)                    리뷰 (E08) · 버전·호환 (E09)        디플로이 모드 (D10)



                                   채널·임베드 (C07)                   컬렉션 (E10) · 설치됨 (E11)         원격 등록 (D11) · 정책 (D12)



                                                                  구매·라이선스 (E12) · 레지스트리 (E13)   capability 인덱스 (D13)




진입: 설치 위저드(A02) 는 supervisor 미존재 시 강제 이동 → 로그인(A01)/SSO(A03) → 대시보드(B02). 전역 레이아웃(B01) 은 전 화면 공통. 비밀번호(A04)·프로필(L02) 은 우상단 계정 메뉴.




AgentPlaza 화면설계서 · v1.0 · PART 1 · IA ①                                                                                                                               7
4. 메뉴 구조도(IA) ② — 관리 영역 · Addon
좌측 네비 뒤 6항목 + 설치된 Addon 섹션(동적). admin+ 노출, [S] = supervisor 전용



        플레이그라운드                              거버넌스                  LLM·모델                  관측·운영                     사용자·조직                  설정 · Addon


프롬프트·모델 실험 (H01)                   가드레일 도메인 (I01)        모델 카탈로그 (J01)            관측 대시보드 (M01)           사용자 (K01)                 시스템 설정 (L01)



A/B 비교·비용 (H02)                    판정 로그·시험 (I02)        공급자·키 (J02)              LLM 트레이스·세션 (M02)       조직·그룹·구성원 (K02)           내 프로필 (L02)



평가 시나리오·회귀 (H03)                   정책·데이터 등급 (I03) [S]   로컬 런타임·모델 준비 (J03)       감사 원장 (M03) [감사자·S]     역할·권한 매트릭스 (K03)          채널 (C07) · 레지스트리 (E13)



                                   승인함 HITL (I04) ← 배지   라우팅·폴백 정책 (J04) [S]      런타임·컨테이너 (M04) [S]      서비스 계정·API 키 (K04)        — 설치된 Addon —



                                   리뷰어 게이트 (I05) [S]     사용량·비용 (J05)             백업·업그레이드·롤백 (M05) [S]   SSO·IdP (K05) [S]         /a/{agent}/ui 마운트 (N01)



                                                         임베딩·리랭크 (J06)            오프라인·에어갭 번들 (M06) [S]   시크릿 (K06) [S]             Addon 화면 템플릿 규약 (N02)



                                                         CLI 에이전트 백엔드 (J07) [S]




Addon 노출 조건: isActive && hasFrontend 인 Addon 만 좌측 '설치된 Addon' 에 나타난다. 화면 없는 Addon 은 스코프 채팅(C05) 로 사용. 역할에 없는 메뉴는 렌더하지 않되 라우트 역할 가드로도 차단(2중화).




AgentPlaza 화면설계서 · v1.0 · PART 1 · IA ②                                                                                                                       8
5. 화면 목록 (1~21 / 80)
화면ID · 화면명 · 그룹 · 유형 · 라우트 · 권한 · 우선순위 · PRD 추적(요약)


화면 ID         화면명                           그룹         유형              라우트                      권한            P    PRD 추적(요약)

SCR-A01       로그인                           인증·설치      페이지(전체화면)       /login                   비로그인          P0   D9-01

SCR-A02       최초 설치 위저드                     인증·설치      위저드(5단계·전체화면)   /setup                   비로그인(최초 1회)   P0   D10-02 D1-01 D1-03 D1-05 …

SCR-A03       SSO 연결·콜백                     인증·설치      페이지(전체화면)       /auth/sso                비로그인          P1   D9-01

SCR-A04       비밀번호 변경·임시 비밀번호               인증·설치      모달(2종)          /profile/password · 모달   본인·admin      P0   D9-02

SCR-B01       전역 레이아웃(셸)                    메인·대시보드    공통 규약(레이아웃)     (모든 화면)                  로그인           P0   D10-01

SCR-B02       홈 대시보드                        메인·대시보드    페이지             /dashboard               로그인           P0   D10-01 D10-07 D8-06

                                                       페이지(우측 드로어 겸
SCR-B03       알림 센터                         메인·대시보드                    /notifications           로그인           P2   D10-07
                                                       용)

SCR-B04       전역 검색                         메인·대시보드    모달(커맨드 팔레트)     (상단바 팔레트)                로그인           P1   D10-01

SCR-C01       채팅(AI 어시스턴트)                  AI 어시스턴트   페이지             /chat                    로그인           P0   D3-01 D3-03 D2-06

SCR-C02       세션 목록·히스토리                    AI 어시스턴트   탭·패널            /chat (좌측 패널)            로그인           P0   D3-02

SCR-C03       파일·멀티모달 입력                    AI 어시스턴트   모달(인라인 첨부 패널)   /chat (첨부)               로그인           P1   D3-04

SCR-C04       메모리·맞춤지침                      AI 어시스턴트   페이지             /profile/memory          본인            P1   D3-05

SCR-C05       에이전트 스코프 채팅(폴백)               AI 어시스턴트   페이지             /a/{agent}/chat          로그인+권한        P0   D3-03

                                                       탭·패널(드롭다운 +
SCR-C06       지식(RAG) 연결 패널                 AI 어시스턴트                   /chat (지식 선택)            로그인           P1   D3-06
                                                       드로어)

SCR-C07       채널·임베드 설정                     AI 어시스턴트   페이지             /settings/channels       admin         P2   D3-07

                                                                                                로그인(관리 기능은
SCR-D01       에이전트 목록                       에이전트 관리    페이지             /agents                                P0   D5-06 D10-01
                                                                                                admin+)

SCR-D02       에이전트 상세·설정                    에이전트 관리    페이지             /agents/{key}            admin+        P0   D5-06 D1-06 D9-02

SCR-D03       새 Agent 만들기 — 스캐폴드            에이전트 관리    위저드(모달 5단계)     /agents (모달 탭1)          admin+        P0   D4-01 D4-02

SCR-D04       새 Agent 만들기 — ZIP 업로드         에이전트 관리    모달              /agents (모달 탭2)          admin+        P0   D5-01 D5-02

SCR-D05       설치·등록 진행(8단계)                 에이전트 관리    페이지             /agents/{key}/install    admin+        P0   D5-02 D5-03 D5-04 D5-05 …

SCR-D06       MCP 노출 설정·가이드                 에이전트 관리    모달              /agents/{key}/mcp (모달)   admin+        P0   D7-01 D7-02




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 목록                                                                                                        9
5. 화면 목록 (22~42 / 80)
화면ID · 화면명 · 그룹 · 유형 · 라우트 · 권한 · 우선순위 · PRD 추적(요약)


화면 ID         화면명                           그룹        유형             라우트                         권한            P    PRD 추적(요약)

SCR-D07       A2A 카드·프로토콜 표면                에이전트 관리   탭(에이전트 상세)     /agents/{key}/protocols     admin+        P1   D7-03 D7-05 D7-06

SCR-D08       추출(파생·Standalone 번들)          에이전트 관리   모달             /agents/{key}/export (모달)   admin+        P0   D4-07

SCR-D09       Worker·설치 가이드                 에이전트 관리   모달             /agents/{key}/guide (모달)    로그인           P1   D4-05 D8-01

SCR-D10       삭제·해제 확인                      에이전트 관리   모달(확인 다이얼로그)   (확인 다이얼로그)                  admin+        P0   D5-05 D5-06

SCR-D11       원격 에이전트 등록(연동·연계)             에이전트 관리   위저드(5단계)       /agents/link                admin+        P0   D6-04 D7-02 D7-04

SCR-D12       도구 정책·권한                      에이전트 관리   탭(에이전트 상세)     /agents/{key}/policy        admin+        P1   D9-02 D9-05

SCR-D13       capability·라우팅 인덱스            에이전트 관리   페이지            /agents/capabilities        admin+        P1   D2-02 D5-06

SCR-E01       마켓 홈(카탈로그)                    마켓플레이스    페이지            /market                     로그인           P0   D6-01

SCR-E02       카테고리 브라우즈(3축)                 마켓플레이스    페이지            /market/categories          로그인           P0   D6-01

SCR-E03       자산 상세                         마켓플레이스    페이지            /market/{key}               로그인           P0   D6-01 D5-03 D5-04

SCR-E04       설치(도입=배치) 위저드                 마켓플레이스    위저드            /market/{key}/adopt         admin+        P0   D6-02 D6-05 D9-02

SCR-E05       직접 설치(Zip·Git·OCI·URL)        마켓플레이스    모달             /market/install-direct      admin+        P0   D6-03

SCR-E06       자산 등록(게시)                     마켓플레이스    위저드            /market/publish             admin+·퍼블리셔   P1   D6-06 D4-06

SCR-E07       퍼블리셔 관리                       마켓플레이스    페이지            /market/publishers          supervisor    P1   D6-06

SCR-E08       리뷰·평점                         마켓플레이스    탭              /market/{key} (탭)           도입자           P1   D6-01

SCR-E09       비교(Compare)                   마켓플레이스    모달             /market/compare             로그인           P2   D6-01

SCR-E10       컬렉션(업종 스타터 팩)                 마켓플레이스    페이지            /market/collections         로그인           P1   D6-02 D6-01

SCR-E11       설치됨·업데이트 관리                   마켓플레이스    페이지            /market/installed           admin+        P0   D6-07 D8-06

SCR-E12       구매·라이선스                       마켓플레이스    위저드(모달)        /market/{key}/purchase      admin+        P1   D6-05

SCR-E13       원격 레지스트리 연결                   마켓플레이스    페이지            /settings/registries        supervisor    P1   D6-07

SCR-F01       워크플로 목록                       워크플로      페이지            /workflow                   admin+·빌더     P1   D2-03 X01




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 목록                                                                                                10
5. 화면 목록 (43~63 / 80)
화면ID · 화면명 · 그룹 · 유형 · 라우트 · 권한 · 우선순위 · PRD 추적(요약)


화면 ID         화면명                           그룹           유형              라우트                       권한             P    PRD 추적(요약)

SCR-F02       워크플로 빌더                       워크플로         페이지(전체화면 3분할)   /workflow/builder/{id}    admin+·빌더      P1   D2-03 X01

SCR-F03       실행 이력·노드 런                    워크플로         페이지             /workflow/{id}/runs       admin+·빌더      P1   D2-07

SCR-F04       트리거 설정                        워크플로         모달              /workflow/{id}/triggers   admin+         P1   D2-03

SCR-F05       DSL 반입                        워크플로         모달              /workflow/import          admin+         P2   X01

SCR-G01       지식 컬렉션 목록                     지식(RAG)      페이지             /rag                      로그인            P1   D3-06 X07

SCR-G02       문서 업로드·인덱싱                    지식(RAG)      페이지             /rag/{id}/documents       지식 담당          P1   D3-06 D1-07

SCR-G03       검색 시험·인용 확인                   지식(RAG)      탭(컬렉션 상세)       /rag/{id}/search          로그인            P1   D3-06

SCR-H01       플레이그라운드                       플레이그라운드·평가   페이지             /playground               개발자·admin      P1   D10-05

SCR-H02       A/B 비교·비용                     플레이그라운드·평가   탭(플레이그라운드)      /playground/compare       개발자·admin      P1   D10-04 D10-05

SCR-H03       평가 시나리오·회귀                    플레이그라운드·평가   페이지             /eval                     QA·admin       P1   D10-05

SCR-I01       가드레일 도메인 카탈로그                 가드레일·거버넌스    페이지             /guardrails               컴플라이언스·admin   P1   D9-06

SCR-I02       판정 로그·시험                      가드레일·거버넌스    탭               /guardrails/decisions     컴플라이언스·admin   P1   D9-06 D9-07

SCR-I03       정책·데이터 등급                     가드레일·거버넌스    페이지             /governance/policy        supervisor     P1   D9-05 D1-06

SCR-I04       승인 대기함(HITL)                  가드레일·거버넌스    페이지             /approvals                승인자            P0   D2-06

SCR-I05       리뷰어 게이트 설정                    가드레일·거버넌스    탭               /governance/reviewer      admin+         P1   D2-05

SCR-J01       모델 카탈로그                       LLM·모델       페이지             /llm/models               admin+         P0   D1-06

SCR-J02       공급자 연결·키                      LLM·모델       페이지             /llm/providers            admin+         P0   D1-03 D9-04

SCR-J03       로컬 런타임·모델 준비                  LLM·모델       페이지             /llm/local                admin+         P0   D1-01 D1-02 D8-05

SCR-J04       라우팅·폴백 정책                     LLM·모델       페이지             /llm/routing              supervisor     P0   D1-05 D1-06

SCR-J05       사용량·비용                        LLM·모델       페이지             /llm/usage                admin+         P1   D10-04

SCR-J06       임베딩·리랭크 설정                    LLM·모델       탭               /llm/embeddings           admin+         P1   D1-07




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 목록                                                                                                   11
5. 화면 목록 (64~80 / 80)
화면ID · 화면명 · 그룹 · 유형 · 라우트 · 권한 · 우선순위 · PRD 추적(요약)


화면 ID         화면명                           그룹            유형      라우트                     권한                    P    PRD 추적(요약)

SCR-J07       CLI 에이전트 백엔드                  LLM·모델        페이지     /llm/cli-agents         supervisor            P1   D1-04

SCR-K01       사용자 관리                        조직·사용자·권한     페이지     /users                  admin+                P0   D9-02

SCR-K02       조직·그룹·구성원                     조직·사용자·권한     페이지     /orgs                   supervisor·조직 admin   P1   X09 D6-05

SCR-K03       역할·권한 매트릭스                    조직·사용자·권한     페이지     /settings/roles         supervisor            P1   D9-02

SCR-K04       서비스 계정·API 키                  조직·사용자·권한     페이지     /settings/api-keys      admin+                P0   D9-03

SCR-K05       SSO·IdP 설정                    조직·사용자·권한     페이지     /settings/sso           supervisor            P1   D9-01

SCR-K06       시크릿 관리                        조직·사용자·권한     페이지     /settings/secrets       supervisor            P1   D9-04

SCR-L01       시스템 설정                        설정·프로필        페이지     /settings               admin+                P0   D10-01 D10-06

SCR-L02       내 프로필                         설정·프로필        페이지     /profile                본인                    P0   D3-05 D9-01

SCR-M01       관측 대시보드                       관측·감사·운영      페이지     /observability          운영자·admin             P0   D10-03

SCR-M02       LLM 트레이스·세션                   관측·감사·운영      페이지     /observability/traces   운영자·개발자               P1   D10-04

SCR-M03       감사 원장                         관측·감사·운영      페이지     /audit                  감사자·supervisor        P0   D9-07

SCR-M04       런타임·컨테이너 상태                   관측·감사·운영      페이지     /runtime                운영자                   P1   D8-01 D8-02 D8-06

SCR-M05       백업·업그레이드·롤백                   관측·감사·운영      페이지     /runtime/maintenance    supervisor            P1   D8-06

SCR-M06       오프라인·에어갭 번들                   관측·감사·운영      페이지     /runtime/airgap         supervisor            P2   D8-07

SCR-N01       Addon 화면 마운트 규약               Addon 화면 규약   공통 규약   /a/{agent}/ui           권한 상속                 P0   D5-07 D3-03

SCR-N02       Addon 화면 템플릿(목록·폼·상세)         Addon 화면 규약   공통 규약   (Addon 내부)              Addon 정의              P0   D4-01 D4-03




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 목록                                                                                                 12
6. 권한(역할) × 화면 매트릭스
PRD 13장·2.4. O 전체 · 조회 읽기 전용 · — 메뉴 미노출 + 라우트 가드 차단. 라우트 가드와 서버 인가 2중


네비 그룹                                        포함 화면                                       user                 admin                   supervisor

대시보드 · AI 어시스턴트                              B02·B03 · C01~C07                           O                    O                       O

마켓플레이스(조회·도입)                                E01·E02·E03·E04·E10·E12                     조회                   조회+설치                   전체

마켓 관리(게시·퍼블리셔·설치됨·레지스트리)                     E06·E07·E11·E13                             —                    일부(E11)                 O

에이전트 관리                                      D01~D13                                     —                    O                       O

워크플로 · 플레이그라운드                               F01~F05 · H01~H03                           —                    O                       O

지식(RAG)                                      G01~G03                                     조회                   O                       O

거버넌스(가드레일·판정·승인함)                            I01·I02·I04                                 승인자만 I04             O                       O

거버넌스(정책·리뷰어)                                 I03·I05                                     —                    —                       O

LLM·모델                                       J01·J02·J03·J05·J06                         —                    O                       O

LLM 정책·CLI 백엔드                               J04·J07                                     —                    —                       O

관측·운영                                        M01·M02·M04                                 —                    O                       O

감사·유지보수·에어갭                                  M03·M05·M06                                 —                    조회(M03)                 O

사용자·조직 · 보안 설정                               K01·K02·K03 · K04·K05·K06                   —                    O · 일부(K04)             O

설정 · 내 프로필                                   L01·C07·E13 · L02·C04·A04                   —·O                  O                       O

설치된 Addon 섹션                                 N01(동적)                                     설치·권한에 따름            동일                      동일



UI 규칙: 권한 없는 액션은 숨기지 않고 비활성 + 툴팁('admin 권한 필요', MSG-006). 페이지 단위는 403 안내 + 대시보드 링크. 401 은 토큰 제거 → 로그인(MSG-019) + 원래 경로 복귀. 조직 admin 과 플랫폼 supervisor 를 구분
(K02·K03).




AgentPlaza 화면설계서 · v1.0 · PART 1 · 권한 매트릭스                                                                                                                  13
7-① 최초 설치 → 첫 대화 (FL-01)
PRD 10.1 셋업 시나리오. NFR-U1 30분 내 첫 대화, NFR-L2 로컬만으로 완료 가능

                                                             없음                                                           검증 ✓                         준비 완료




       시작(컨테이너 기동)                          supervisor 존재?          A02 설치 위저드 1/5 관리자           A02 2/5 LLM 연결(로컬·퍼블릭)          A02 3/5 모델 준비(pull)           A02 4/5 기본 에이전트·정책




                                                    있음
                                                                                          예




                                             A01 로그인                       SSO?                        A03 SSO 콜백                                                A02 5/5 요약·완료


                                                                                                        자동 로그인
                                                                           세션
                                                    로컬 계정
                                                             첫 방문                        대화 시작                            스트리밍




                                            B02 대시보드                 B04 온보딩 체크리스트                 C01 AI 어시스턴트 첫 대화                 완료(첫 응답)




분기: 퍼블릭 LLM 키 검증 실패(MSG-017) 는 단계 복귀. 로컬 모델 pull 은 백그라운드 이동 허용(알림 통지). 참조 구현 SetupWizard 는 뒤로가기·i18n·다크모드가 없고 키를 .env 로 받았다 → 본 설계는 위저드 안에서 입력·검증.




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 흐름도                                                                                                                                           14
7-② 마켓 도입 — 경로 A 다운로드·설치 / B 직접 / C 연동 (FL-02·03)
PRD 11.6 8단계 등록 파이프라인. NFR-U2 설치 5분, 실패 시 단계별 사유

                                                           3축 필터                         카드 클릭                                                     예




            시작                              E01 카탈로그                   E02 카테고리 3축                     E03 자산 상세                     유료?                  E12 구매·라이선스


                                                                                                                                                 라이선스 ✓
                                                                                                                           아니오


                                                                            C              B                                A




                                        D11 원격 등록(C)                  D04 ZIP 업로드(B)                     도입 경로                   E04 도입 위저드(A)



                                                                                                        매니페스트 ✓
                                                 핸드셰이크                                                                                  확인
                                                                                         아니오




                                      external 등록(설치 없음)           실패 사유·재업로드(MSG-007)                  게이트 통과?                  D05 설치 진행 8단계


                                                                                                                           예



                                                                                                                           활성




                                                                           완료                    네비 Addon 섹션 갱신(MSG-014)           D02 상세·설정




8단계: 업로드 → 구조 검증 → 서명·SBOM·취약점 → 라이선스·정책 → 이미지 빌드 → DB 마이그레이션 → 프런트 통합 → 헬스. 서명 미검증 자산은 경고 배너 + 동의(MSG-008). 참조 구현 AdoptWizard 는 단일 스크롤 폼이라 호환
경고를 무시할 수 있었다 → 단계형.




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 흐름도                                                                                                                               15
7-③ Addon 개발 → 시험 → 게시 (FL-04)
PRD D4·D6-06. DP4 스캐폴드 산출물 = 설치 가능한 agent.zip

                                                                                 선택                                                      시험




            시작                         D03 스캐폴드 위저드             템플릿 9유형                agent.zip 다운로드(OUT-05)         로컬 개발(plaza dev)             D09 워커·계약 시험


                                                                                               업로드



                                                                                 설치                             평가                       PASS




                                            D04 ZIP 업로드         D05 설치 진행                  D01 목록(초안)                   H03 평가·회귀               D06 MCP · D07 프로토콜 확인


                                                                                                게시
                                                                   파생


                                                                                 필요             불요              승인                       공개




                                        E06 게시(릴리스)            I05 리뷰어 심사?                 심사 대기(ST-07)              E07 퍼블리셔 릴리스 관리                 카탈로그 노출




                                     D08 파생·Standalone 추출




게시 시 서명(Ed25519)·SBOM 첨부, 매니페스트 v2(compat.topologies T1~T6 · requires · pricing 표시). 파생 ZIP 은 출처를 자동 기록. 참조 구현은 Addon 프런트를 빌드타임 glob 으로 통합해 재빌드가 필요했다 → iframe 런타임
마운트(N01).




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 흐름도                                                                                                                               16
7-④ 대화 중 도구 호출 · 리뷰 게이트 · HITL 승인 (FL-05)
PRD DP6·DP8 · AG-UI 이벤트. 승인은 승인함(I04) 에 쌓이고 만료 시 취소

                                                                                                                                          예




         사용자 메시지                       의도 분류·계획(카드)            에이전트 라우팅                  도구 호출 카드(C01)                   승인 필요?                승인 카드 인라인(MSG-012)


                                                                                                            아니오

                                                                                                                                                          대기
                                                                                                             승인                          승인자




                                                                                          도구 실행·결과 카드                   승인/거부/만료                  I04 승인함(배지 +1)




                                                                                재시도

                                                                                예·수정                         통과                          기록




                                                             리뷰 카드(수정 요청)                   리뷰어 게이트?                        만료
                                                                                                                      최종 응답 스트리밍                  M03 감사 원장 기록




                                                                                               완료                 만료 → 재요청 버튼(MSG-013)




참조 구현은 백엔드가 intent/agent_start/hitl_pending/review_gate 이벤트를 내지만 프론트가 delta/done/error 만 처리해 도구 호출 UI 가 없었다 → AG-UI 이벤트 전부 렌더(CMP-15·16). 승인 대기 중 입력창 비활성, 승인함 배지
증가.




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 흐름도                                                                                                                           17
7-⑤ LLM 라우팅·폴백 (FL-06) · 조직 도입 (FL-07)
PRD D1-05·D1-06 데이터 등급 L0~L3 · 17장 스타터 팩 배치

                                                         L0~L3                                                 예




       요청(대화·워크플로)                          데이터 등급 판정            J04 라우팅 정책 적용               외부 전송 허용?                 퍼블릭 LLM(J02 키)                로컬 런타임(J03)


                                                                                                                                           폴백
                                                                                                                           로컬 별칭
                                                                                                  아니오
                                                                                                                                         저하 표기




                                                                                         사전 차단 배너(MSG-010)               실패·지연 30초?                저하 배지(MSG-011)




                                                                                                              배치                         일괄 설치




       K02 조직·그룹 생성                         K05 SSO 연결           E13 레지스트리 설정              I03 정책·데이터 등급             E10 스타터 팩(컬렉션) 도입            부분 실패 요약(MSG-018)




                                                                                                                       J05 사용량·비용 확인                     완료




NFR-L1: 퍼블릭 실패·30초 지연 시 로컬 폴백 + 응답 버블 하단 저하 배지 + 감사 기록. 조직 도입은 deploy_scope(org|group|user)·tool_policy·pinned_version 을 도입 위저드(E04) 에서 지정. 실패 건만 재시도.




AgentPlaza 화면설계서 · v1.0 · PART 1 · 화면 흐름도                                                                                                                             18
8. 공통 UI 가이드 — 레이아웃 · 디자인 토큰 · 컴포넌트
PRD 13장·참조 구현 AppLayout(SeCMP·MAS) 의 시각 언어를 토큰으로 일반화. 폐쇄망 전제 → 웹폰트·CDN 로컬 번들(UP8)


토큰                                 라이트                           다크                  용도                     컴포넌트 샘플(CMP-01~16)


--color-primary                    #3F51E5                       #7C8CFF             주 버튼·활성 네비·링크·선택                       게시판                                   설치됨                                재고 관리                             healthy
                                                                                                                 ◈                                                                      ◈
                                                                                                                            v1.2.0 · 공통·W05                                                          v0.9.1 · 제조·MCP

--color-primary-soft               #EEF0FD                       #23264A             선택 메뉴 배경·official 배지
                                                                                                             사내 게시판·댓글·첨부. 에이전트 카드(CMP-05)                                            원격 MCP 서버 연동(경로 C). 점선 = external


                                                                 #0F1220 /
--color-bg / card / border         #F6F7FB / #FFFFFF / #D9DCE5                       페이지·카드·구분선
                                                                 #181B2E / #2A2E48                                    official                                          ↓ 1.2k              external                                    ↓ - · ₩ 구독



--color-text / sub                 #222222 / #666B7A             #E6E8F2 / #9AA0B4   본문·보조

                                                                                     정상·설치됨 / 저하·미검증·                Primary                  Secondary            Danger                   official                   partner     community
                                   #2F9E44 / #E8A317 /
--ok / warn / danger / muted                                     명도 +10%             대기 / 오류·차단·삭제 /
                                   #C92A2A / #868E96
                                                                                     비활성
                                                                                                            입력(label 위)                                    선택
                                   #EEF0FD·#3F51E5 /
--trust
                                   #E6F7F4·#0C8599 /
official/partner/community/exter                                 -                   신뢰등급 배지(텍스트 병기)
                                   #FFF4E0·#7A4E00 /                                                         값                                             L2 내부                                 ▾                       토글 ON
nal
                                   #F1ECFF·#7048E8
                                   12px 카드 · 6px 버튼·입력 · 999px
--radius / shadow                                                -
                                   배지 / 0 1px 2px + 0 4px 12px
                                                                                                              healthy / 설치됨                          저하 / 대기·심사                          unhealthy / 차단                          비활성
                                   Pretendard·Noto Sans KR
--font / --space                   14/12/15/18/24px · 등폭 13px · -                    tabular-nums, 로컬 번들
                                   4pt 그리드                                                                   도구 호출 ·                           완료           승인 요청 · 외부 전송                   대기                     리뷰 게이트              재시도
레이아웃(2.2)                                                                                                    inventory.query
                                                                                                             args {sku} → 3건 · 1.2s                         만료 09:50 · 승인함 ↗                                       수정 요청 1건
• 셸 = 좌측 네비 240px(접기 64px, 상태 기억) + 상단바 64px 고정 + 본문 최대 1152px 좌측 정렬(중앙 정렬
금지)
• 반응형: ≥1280 4열 · ≥1024 3열 · ≥768 2열 · <768 1열(네비 오버레이 드로어, 표는 카드형)
• 전체화면 예외: 로그인(A01)·설치 위저드(A02)·워크플로 빌더(F02). 대화(C01) 는 높이 100%
• Addon 화면(N01) 은 별 오리진 iframe, 높이는 resize 메시지. 토스트·모달·네비는 코어가 소유


                                                                                                                 1       업로드                     2    검증                    3    빌드                         4     헬스




                                                                                                            진행·사용량 바(CMP-10): 85% 황 · 95% 적 · 남은 단계 텍스트 병기




AgentPlaza 화면설계서 · v1.0 · PART 1 · 공통 UI 가이드                                                                                                                                                                                                         19
9. 공통 UI 가이드 — 상태 · 메시지 · 유효성 · 서버 오류 처리
2.6 상태 ST-01~08 · 17장 검증 규칙. 화면별 설계에서는 이 규칙을 반복 기술하지 않는다


상태                   발생                     화면 표현                                                  유효성 검사                               규칙 → 메시지

                                            스켈레톤(목록·카드) 또는 인라인 스피너(버튼). 300ms 이하면
ST-01 로딩             데이터 요청 중                                                                      에이전트 키·slug                          ^[a-z][a-z0-9-]{1,40}$ · 예약어·내장 키 충돌 금지 → MSG-004/005(대체 이름 제안)
                                            표시하지 않음

ST-02 빈 상태           결과 0건                  원인별 문구(최초 생성 유도 / 검색 조건 완화 / 필터 초기화)                   semver / URL / 포트                    x.y.z(-pre) · https 필수(내부 http 는 경고) · 1024~65535 → MSG-004


ST-03 오류             요청 실패                  인라인 오류 + 재시도 버튼. 5xx 는 추적 ID 표기                        비밀번호 / API 키                         8~128·문자군 2종·최근 3개 금지 / 1~256·저장 후 마스킹·검증 필수 → MSG-017


ST-04 권한 없음          역할·정책 미충족              동작 버튼 비활성 + 사유 툴팁. 페이지 단위는 403 안내 화면                   파일(zip / 문서)                         .zip ≤100MB 10개 경로 안전 / pdf·docx·xlsx·md·txt·html ≤50MB → MSG-004/007


ST-05 부분 실패          다건 처리 중 일부 실패          성공/실패 건수 요약 + 실패 목록 상세                                 태그 / cron                            ^[a-z0-9][a-z0-9-]{0,29}$ 최대 10 / 5필드 + 다음 실행 미리보기

                     기능은 되나 품질·경로가
ST-06 저하(Degraded)                          배지로 표기(로컬 모델 폴백·캐시 응답·미검증 자산)                          프롬프트 입력                              ≤8,000자 · IME 조합 중 전송 불가
                     낮아짐

ST-07 대기·승인 필요       HITL·심사 대기             대기 배지 + 승인함 링크 + 만료 시각                                 권한 동의 / 라이선스 키                       permissions[] 전부 체크(422 → 단계 복귀) / 공개키 검증·대상·버전·만료·호스트 → MSG-017


ST-08 오프라인           외부 연결 불가               오프라인 배너 + 사용 가능한 로컬 기능 안내
                                                                                                   HTTP·코드                                      화면 처리


규칙                    내용
                                                                                                   400 / 422                                    상단 요약 + 필드 인라인 / 해당 단계·필드로 복귀


토스트                   성공 3초 · 오류 수동 닫기 · 우상단 스택(코어 소유, Addon 은 notify 메시지)                                                                      토큰 제거 → 로그인(MSG-019, next 보존) / MSG-006 비활성+툴팁, 페이지면 403
                                                                                                   401 / 403
                                                                                                                                                화면

                      삭제·해제 danger + 영향 범위 · 409 덮어쓰기 info · 정책 변경 warning · 외부 전송 warning · 미저장
확인 다이얼로그                                                                                           404 / 429                                    빈 상태(ST-02)·'삭제된 항목' / 남은 시간 + 버튼 비활성
                      이탈 neutral

                                                                                                   409 duplicate · builtin_conflict ·           파랑 확인 → force / 거부 + 이름 변경 안내 / 버전 교체 확인 (참조 구현 3패턴 →
긴 작업                  즉시 진행 카드(CMP-10) · 화면 이탈 허용 · 재진입 시 복원 · 완료는 알림(B03)
                                                                                                   install_conflict                             통일)

                      ko 기본·en 폴백. 키 이름 노출 금지(빌드 검사). 데이터 다국어는 {ko,en} 사전형. IME 조합 중 Enter         5xx / 네트워크                                   재시도 + 추적 ID / 오프라인 배너(ST-08)
다국어
                      무시




AgentPlaza 화면설계서 · v1.0 · PART 1 · 공통 UI 가이드                                                                                                                                                                    20
       PART 2


       화면별 설계
       80 화면 · 14 그룹 — 상단 메타 표 · 좌측 와이어프레임(①②③) · 우측 기능 설명 표 · 하단 관련 PRD 항목




AgentPlaza 화면설계서 · v1.0 · 화면별 설계                                              21
시스템          AgentPlaza                              화면 ID                 SCR-A01                                 화면 유형               페이지(전체화면)
화면명          로그인                                     화면 경로                 /login                                  접근 권한               비로그인
우선순위         P0                                      PRD 추적                D9-01                                   작성일 / 버전            2026-09-19 / v1.0

로컬 계정 또는 SSO 로 플랫폼에 진입한다. 셸 없는 전체화면 중앙 카드(max 400px)이며 진입 시 설치 상태를 먼저 확인해 supervisor 가 없으면 /setup 으로 강제 이동한다. 자격증명 오류는 아이디·비밀번호를 구분하지 않는 동일 문구로 계정
열거를 막는다.


                                                                                         1                    No   구성요소        유형             기능 설명 / 동작                           연계
                                                                                             언어 ko ▾   ☾ 테마

                                                                                                                               드롭다운·          ko|en, light|dark. 로그인 전에도 동작, 선택은
                                                                                                              1    언어·테마                                                           SCR-B01
                                                                                                                               토글             localStorage
                                 2
                                                                                                                               로고·            시스템 설정(SCR-L01) 값. 화이트라벨 시 교체,
                                                     ▣ AgentPlaza                                             2    브랜딩
                                                                                                                               텍스트            하드코딩 금지
                                                                                                                                                                             SCR-L01


                                                        멀티 에이전트 플랫폼
                                                                                                              3    아이디         input text     2~64자 필수. 자동완성 username              D9-01

                                     아이디
                                                                                                                               input
                                                                                                              4    비밀번호                       8~128자 필수. 표시/숨김 토글(aria-pressed)    D9-01
                                     3                                                                                         password
                                         admin
                                                                                                                                              체크 시 리프레시 토큰 장기 보관(정책 허용
                                                                                                              5    로그인 상태 유지   checkbox                                            D9-01
                                                                                                                                              시만 노출)
                                     비밀번호

                                     4                                                                                         button         ③④ 비면 disabled. 제출 중 loading·중복 제출
                                                                                                              6    로그인                                                           SCR-B02
                                         ••••••••                                    👁                                         primary        차단. 2FA 요구 시 6자리 코드 단계로 카드 교체

                                                                                                                               button         SSO 설정(SCR-K05) 활성 시만 렌더 → IdP
                                                                                                              7    SSO 로그인                                                         SCR-A03
                                     5                                                                                         secondary      리다이렉트
                                            로그인 상태 유지
                                                                                                                                              role=alert. 5회 실패 시 잠금·남은 시간. 세션
                                     6                                                                        8    오류 메시지      inline alert                                        MSG-019
                                                                                                                                              만료 진입은 MSG-019 배너
                                                             로그인
                                                                                                              9    환경·버전       text small     서버 값 표시. prod 에서는 환경 배지 숨김           -
                                                      ───── 또는 ─────

                                     7
                                                    조직 계정으로 로그인 (SSO)


                                                       비밀번호를 잊으셨나요?


                                     8
                                         ⚠ 아이디 또는 비밀번호가 올바르지 않습니다




                                 9                       환경 dev · v2.0.0




관련 요구사항(PRD): D9-01


AgentPlaza 화면설계서 · v1.0 · A. 인증·설치                                                                                                                                                           22
시스템                      AgentPlaza                                    화면 ID                 SCR-A02                                                                            화면 유형                 위저드(5단계·전체화면)
화면명                      최초 설치 위저드                                     화면 경로                 /setup                                                                             접근 권한                 비로그인(최초 1회)
우선순위                     P0                                            PRD 추적                D10-02 D1-01 D1-03 D1-05 D1-06                                                     작성일 / 버전              2026-09-19 / v1.0

관리자 생성 → LLM 연결 → 모델 준비 → 기본 에이전트 활성 → 완료의 5단계로, 빈 서버에서 첫 대화까지 30분 내 도달(NFR-U1)을 책임진다. 진행 상태는 서버에 저장되어 새로고침·재접속 시 이어서 진행하며, 완료 상태면 /login 으로 보낸다.
모델 pull 실패는 비차단 경고로 처리한다.


                                                                                                                                                                           No   구성요소         유형           기능 설명 / 동작                               연계
   AgentPlaza · 설치 위저드                                                                                                                                       언어 ko ▾   ☾

                                                                                                                                                                                                          5단계. 완료 단계는 클릭 이동, 미래 단계 비활
                                                                                                                                                                           1    단계 인디케이터     stepper                                               D10-02
   1                                                                                                                                                                                                      성. 전 단계 i18n·다크모드
           1       관리자                     2      LLM 연결               3       모델 준비                      4    기본 에이전트                 5          완료
                                                                                                                                                                           2    오류 배너        alert        서버 detail 우선 표시, 현재 단계 유지                -


       2                                                                                                                                                                        관리자 계정(1단    input·chec   아이디·이름·비밀번호(강도)·조직명 + 2FA 선
                                                                                                                                                                           3                                                                       D9-01 D9-02
               ⚠ 오류 배너 — 서버 detail 우선, 현재 단계 유지                                                                                                                                 계)           kbox         택. supervisor 고정

       3                                                                                                                                                                                                  local|public|hybrid. 로컬 감지 성공 시 local,
                                                                                                                                                                           4    LLM 방식       radio                                                 D1-01
               단계 1 · 관리자 ✓ 완료                             단계 2 · LLM 연결 (현재)                                      단계 3 · 모델 준비                                                                           실패 시 public 기본

               아이디 / 이름                                                                                           8
                                                           4                                                                                                                                 input +      GET /api/llm/local/detect. 실패 시 맥 네이티브
                                                                  로컬 런타임 사용                                           모델                   상태          진행                  5    로컬 런타임 URL                                                         D1-03
                                                                                                                                                                                             연결 시험        브리지 안내
                admin / 관리자                                                      감지됨 Ollama 0.34 ✓                    qwen3:8b             pull        62%
                                                                                                                                                                                             select +     검증 버튼 → MSG-016/017. 키는 마스킹
               비밀번호(8~128 · 강도 표시)                         5                                                                                                               6    퍼블릭 공급자·키                                                          D9-04
                                                                                                                      nomic-embed          대기          -                                     password     저장
                                                               http://host.docker…:11434 [시험]
                •••••••• (강도 보통)                                                                                                                                                프라이버시 기본                  L0~L3. 하이브리드 폴백 정책 초기값(SCR-
                                                                                                                                                                           7                 select                                                D1-05
                                                           6                                                       실패해도 계속 진행(비차단)                                              등급                        J04)
               조직명(브랜딩 기본값)                                       퍼블릭 API 사용
                                                                                                                                                                                             표+           권장 세트 pull(SSE 진행). 실패는 비차
                                                               Anthropic   ▾           ••••• [검증]                  단계 4 · 기본 에이전트                                          8    모델 준비 목록                                                           D1-06
                ACME                                                                                                                                                                         진행바          단, '나중에' 허용
                                                                                                                  9
                                                                  둘 다(하이브리드)                                          ✓    Orchestrator (필수)                                                 checkbox     Orchestrator·Assistant 해제 불가, 스타터 팩은
                                                                                                                                                                           9    기본 에이전트·완료                                                         SCR-A01
                   2단계 인증 설정 (QR + 6자리)                    프라이버시 기본 등급                                                                                                                       + button     설치 잡. 완료 → /login
                                                                                                                      ✓    AI Assistant (필수)
               supervisor 역할 고정 · 건너뛰면 프로필에서 설정
                                                           7
                                                               L1 (L0~L3)                             ▾
                                                                                                                           스타터 팩 pack-common
                                                           키는 마스킹 저장(D9-04) · 미검증이면 다음 비활성                         팩은 백그라운드 설치 잡




       진행 상태는 서버(current_step)에 저장 — 새로고침·재접속 시 이어서 진행

                                                                                                          이전                 건너뛰기                      다음 →




관련 요구사항(PRD): D10-02 D1-01 D1-03 D1-05 D1-06


AgentPlaza 화면설계서 · v1.0 · A. 인증·설치                                                                                                                                                                                                                               23
시스템          AgentPlaza                                    화면 ID             SCR-A03                   화면 유형                 페이지(전체화면)
화면명          SSO 연결·콜백                                     화면 경로             /auth/sso                 접근 권한                 비로그인
우선순위         P1                                            PRD 추적            D9-01                     작성일 / 버전              2026-09-19 / v1.0

OIDC(Keycloak 등) 인증 후 콜백을 처리해 세션을 수립한다. 인가 코드·state 검증 → 토큰 교환 → 사용자 매핑 → 복귀 경로 이동의 4단계를 표시하고, 3초를 넘기면 오류·재시도 안내를 띄운다. 로컬 계정 로그인 링크는 비상 경로로 항상 노출한다.



                                                                                                  No   구성요소        유형           기능 설명 / 동작                       연계


                                                                                                                   spinner +    콜백 처리 중 표시. 3초 초과 시 오류·재시도
                                                                                                  1    진행 표시                                                     -
                                                                                                                   text         안내 노출

                                                                                                                                코드·state 수신 → 토큰 교환 → 사용자 매핑 →
                                                                                                  2    처리 단계       상태 목록                                         D9-01
                                                                                                                                세션 수립
                          1
                                                    ◌ 조직 계정으로 로그인 중…                                                            신규 사용자 자동 생성 미허용 정책이면 '승인
                                                                                                  3    매핑 대기 안내    경고 배너                                         SCR-K01
                                                                                                                                대기' 안내

                                                        IdP 에서 돌아오면 자동으로 이동합니다.
                                                                                                                   alert +      state 불일치 / 토큰 교환 실패 / 사용자 매핑
                                                                                                  4    오류·재시도                                                    -
                                                                                                                   button       실패 사유 구분
                              2
                                      인가 코드·state 수신                                                                            항상 표시(비상 경로). IdP 장애 시 강등 경로
                                                                                                  5    로컬 로그인 링크   link                                          SCR-A01
                                                                                                                                안내
                                      토큰 교환(code → id_token)


                                      사용자 매핑(신규는 정책에 따라)


                                      세션 수립 · 복귀 경로 이동




                              3

                                  ⏳ 매핑 대기 — 관리자 승인 후 이용할 수 있습니다

                              4
                                  ⚠ SSO 오류: state 불일치                                     다시 시도


                                           5
                                                               로컬 계정으로 로그인 ›




                                                    IdP 장애 시 로컬 비상 계정 경로 안내(PRD 7.6 강등)




관련 요구사항(PRD): D9-01


AgentPlaza 화면설계서 · v1.0 · A. 인증·설치                                                                                                                                         24
시스템           AgentPlaza                               화면 ID    SCR-A04                                                  화면 유형                  모달(2종)
화면명           비밀번호 변경·임시 비밀번호                          화면 경로    /profile/password · 모달                                   접근 권한                  본인·admin
우선순위          P0                                       PRD 추적   D9-02                                                    작성일 / 버전               2026-09-19 / v1.0

본인 변경(현재·새·확인)과 관리자 초기화(임시 비밀번호 1회 노출) 두 모달을 정의한다. 본인 변경 성공 시 MSG-001 과 함께 다른 세션 만료를 안내하고, 관리자 초기화 대상자는 다음 로그인에서 변경이 강제된다. 대상은 하위 권한만 허용
(supervisor>admin>user).


                                                                                                                    No   구성요소          유형          기능 설명 / 동작                                연계


                                                                                                                                       input       본인 변경 시만 필수. 서버 검증 실패는 인라인
                                                                                                                    1    현재 비밀번호                                                             D9-02
                                                                                                                                       password    오류

                                                                                                                                       input
                                                                                                                    2    새 비밀번호        password    8~128자·정책(문자군) 검증. 강도 막대 표시               D9-02
       비밀번호 변경 (본인)                                    ✕
                                                                임시 비밀번호 발급 (관리자)                                ✕                      + 강도

                                                                                                                                       input
                                                                                                                    3    새 비밀번호 확인                 ②와 불일치 시 인라인 오류                           D9-02
                                                                                                                                       password
                                                                대상 사용자 hong@acme.com 의 임시 비밀번호가 발급되었습니다.
       현재 비밀번호
                                                                                                                                       button      PUT /api/auth/password → MSG-001 + 다른
                                                                                                                    4    변경                                                                  SCR-A01
       1                                                                                                                               primary     세션 만료 안내
           ••••••••
                                                                                                                                       read-only   POST /api/users/{id}/reset-password 결과.
                                                                5                                                   5    임시 비밀번호                                                             SCR-K01
                                                                                                                                       + 복사        마스킹 없이 1회만 노출
       새 비밀번호
                                                                    Xk9#dR2tQz                             복사
                                                                                                                                       경고 +        MSG-020. 닫기 전 확인 다이얼로그. 대상자는
       2                                                                                                            6    1회 노출 경고·확인                                                         MSG-020
                                                                                                                                       button      다음 로그인 시 변경 강제
           ••••••••••

                                          강도 보통                 6

                                                                    ⚠ 이 화면을 닫으면 다시 볼 수 없습니다(MSG-020).
       새 비밀번호 확인                                                    닫기 전 확인 다이얼로그 표시.

       3
           ••••••••••
                                                                대상 사용자는 다음 로그인 시 비밀번호 변경이 강제됩니다.

       정책(길이 8~128 · 문자군) 미충족 시 인라인 오류.
       확인값 불일치 시 오류.




                                                  4
                               취소                 변경                                                       확인




관련 요구사항(PRD): D9-02


AgentPlaza 화면설계서 · v1.0 · A. 인증·설치                                                                                                                                                                     25
시스템               AgentPlaza                 화면 ID          SCR-B01                                                               화면 유형                     공통 규약(레이아웃)
화면명               전역 레이아웃(셸)                 화면 경로          (모든 화면)                                                               접근 권한                     로그인
우선순위              P0                         PRD 추적         D10-01                                                                작성일 / 버전                  2026-09-19 / v1.0

상단바·좌측 네비·본문·토스트 영역의 공통 골격과 테마·언어 전환을 제공한다. 고정 메뉴 12개 아래에 설치된 Addon 섹션이 동적으로 붙고(isActive && hasFrontend), 역할별로 메뉴를 미렌더하며 라우트 가드로 직접 진입도 막는다. 401 은
/login?next=…&expired=1 로, 403 은 토스트 또는 안내 화면으로 처리한다.

 1                          2                                                   4            5                     6
                                            3                                                                                No   구성요소           유형            기능 설명 / 동작                                 연계
     ▣   AgentPlaza             🔍 검색 (⌘K)        dev                              🔔3          ko ▾             ☾        JD

 7                                                                                                                                               button +      접기 상태 localStorage. <768px 은 오버레이
     ▪ 대시보드                 대시보드 › 페이지 경로                                                                                    1    네비 토글·로고                                                                D10-01
                                                                                                                                                 link          드로어
                        9
     ▫ AI 어시스턴트
                            페이지 제목                                                                   주요 동작         보조                            input(팔레
                            페이지 설명(부제)                                                                                       2    전역 검색                        ⌘K/Ctrl+K 로 커맨드 팔레트 열기                     SCR-B04
                                                                                                                                                 트)
     ▫ 마켓플레이스

                                                                                                                             3    환경 배지          badge         local|dev|staging|prod. prod 에서는 숨김        -
     ▫ 에이전트 관리

                                                                                                                                                 icon +
     ▫ 워크플로                                                                                                                  4    알림                           승인·설치·헬스 합산 카운트. 클릭 → 드로어                  SCR-B03
                                                                                                                                                 count

     ▫ 지식(RAG)                                                                                                                                   select +      ko|en, light|dark|system. 즉시 반영 + 프로필
                                                                                                                             5    언어·테마                                                                   D10-01
                                                                                                                                                 toggle        저장, Addon 에 postMessage 전파
     ▫ 플레이그라운드

                                                                                                                             6    사용자 메뉴         dropdown      이름·역할·조직 / 내 프로필 / 로그아웃                    SCR-L03
     ▫ 거버넌스 ●2

                                            본문 컨테이너 — .page 규약(최대폭 1152px · 좌측 정렬 · 패딩)                                                                        역할별 노출(3.2 표). 미허용 메뉴 미렌더 +
     ▫ LLM·모델
                                                 역할 가드: 미허용 라우트는 403 안내 화면
                                                                                                                             7    고정 메뉴          nav list                                                 D10-01
                                                                                                                                                               라우트 역할 가드

     ▫ 관측·운영                                                                                                                                     nav           GET /api/agents?installed=1. nav_group 별
                                                                                                                             8    설치된 Addon 섹션                                                            SCR-D01
                                                                                                                                                 list(동적)      정렬, 헬스 이상 배지
     ▫ 사용자·조직
                                                                                                                                                 레이아웃          제목·설명·동작(primary 1개 원칙) 포털 주입,
                                                                                                                             9    헤더·본문·토스트                                                               -
     ▫ 설정                                                                                                                                        영역            본문 .page 규약, 토스트 최대 3


 8   설치된 Addon


     ▸ 게시판


     ▸ HR 채용



                                                                              ✓ 저장되었습니다
                                                                              토스트 스택 최대 3 · aria-live=polite
                                                                              오류 토스트는 자동 소멸 없음




     [‹ 접기]




관련 요구사항(PRD): D10-01


AgentPlaza 화면설계서 · v1.0 · B. 메인·대시보드                                                                                                                                                                                26
시스템              AgentPlaza                                         화면 ID              SCR-B02                                                                             화면 유형               페이지
화면명              홈 대시보드                                             화면 경로              /dashboard                                                                          접근 권한               로그인
우선순위             P0                                                 PRD 추적             D10-01 D10-07 D8-06                                                                 작성일 / 버전            2026-09-19 / v1.0

플랫폼 상태·에이전트 요약·설치 진행·알림·빠른 링크를 한 화면에 모은다. GET /api/dashboard?days= 한 번으로 채우고 탭이 활성일 때만 30초 폴링한다. scope(플랫폼/조직)는 서버가 역할로 판정하며, 각 타일·항목은 담당 화면으로 이동한다.



                                                                                                                                                                      No   구성요소       유형          기능 설명 / 동작                        연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                                dev                                            🔔3          ko ▾           ☾             JD

                                                                                                                                                                                      stat card   헬스·에이전트·대화(7일)·승인 대기·토큰/비용·
    ▪ 대시보드                대시보드                                                                                                                                        1    상태 요약 타일                                                 D10-01
                                                                                                                                                                                      ×6          업데이트. 클릭 → 해당 화면
                                                                                                                          2
    ▫ AI 어시스턴트
                          대시보드                                                                                                   새로고침                기간 7일   ▾                        select +    기간 7일 기본. 수동 새로고침 + 탭 활성 시 30
                                                                                                                                                                      2    기간·새로고침                                                  -
                                                                                                                                                                                      button      초 폴링
                         1
    ▫ 마켓플레이스
                              헬스                     에이전트               대화(7일)                 승인 대기                          토큰·비용                  업데이트
                                                                                                                                                                                      progress    설치·모델 pull·인덱싱·백업 잡 진행률. 클릭 → 잡
                                                                                                                                                                      3    진행 중 작업                                                  SCR-D05
                                                                                                                                                                                      list        상세
    ▫ 에이전트 관리                 ● 정상                   12 활성              1,204                  2                              1.2M / ₩…              3 가능
                                                                                                                                                                                      list(최근     심각도 아이콘 + 텍스트. 더보기 → 알림 센터·
    ▫ 워크플로                                                                                                                                                            4    알림·헬스 이상                                                 D10-07
                                                                                                                                                                                      5)          런타임 헬스
                         3                                                                 4
    ▫ 지식(RAG)                 진행 중 작업                                                              알림·헬스 이상 (최근 5)                                                                    grouped
                                                                                                                                                                      5    에이전트 요약                nav_group·도메인별 수와 unhealthy 수     SCR-D01
                                                                                                                                                                                      counts
                              board 설치 — 5/8 빌드                                                        퍼블릭 LLM 폴백 발생 2회
    ▫ 플레이그라운드
                                                                                                                                                                                      list(최근
                                                                                                                                                                      6    최근 활동                  감사 원장 요약. 더보기 → 감사 로그             SCR-M03
    ▫ 거버넌스
                                                                                                       rag-be unhealthy                                                               10)
                              qwen3:8b pull

                                                                                                                                                                                      button                                        SCR-C01 SCR-
    ▫ LLM·모델                  클릭 → 설치 상세(SCR-D05) · 모델(SCR-J02)                                    더보기 → SCR-B03 / SCR-M01                                            7    빠른 링크                  역할별. user 는 새 대화·마켓만 노출
                                                                                                                                                                                      group                                         E01

    ▫ 관측·운영                                                                                                                                                                           chart +     다운로드·설치 top5·일별 추이. supervisor=
                         5                                                                 6                                                                          8    유통·감사 통계                                                 D8-06
                              에이전트 요약(그룹별 수·헬스)                                                    최근 활동(감사 요약 10건)                                                                   table       플랫폼, admin=조직 scope
    ▫ 사용자·조직
                              공통 4 · 보안 3 · HR 2 · 플랫폼 3                                           14:23 admin 이 board 1.2.0 설치
                              unhealthy 1 → SCR-D01                                                13:50 hong 이 승인 '메일 발송' 처리
    ▫ 설정                                                                                           더보기 → SCR-M03



    설치된 Addon


    ▸ 게시판                                      7
                          빠른 링크                            새 대화              마켓 둘러보기                      Agent 만들기                       승인함
    ▸ HR 채용

                         8
                              유통·감사 통계 (supervisor=플랫폼 / admin=조직 scope)

                               board                       hrcore                rag                         secops                       mail         다운로드·설치 top5



    [‹ 접기]




관련 요구사항(PRD): D10-01 D10-07 D8-06


AgentPlaza 화면설계서 · v1.0 · B. 메인·대시보드                                                                                                                                                                                                               27
시스템             AgentPlaza                             화면 ID             SCR-B03                                                             화면 유형                페이지(우측 드로어 겸용)
화면명             알림 센터                                  화면 경로             /notifications                                                      접근 권한                로그인
우선순위            P2                                     PRD 추적            D10-07                                                              작성일 / 버전             2026-09-19 / v1.0

헬스·설치·승인·업데이트 알림을 시간순으로 확인한다. 상단바 벨을 누르면 우측 드로어로, /notifications 로 들어오면 전체 페이지로 같은 목록을 보여 준다. 항목을 열면 읽음 처리 후 대상 화면으로 이동한다.



                                                                                                                                        No   구성요소       유형            기능 설명 / 동작                              연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                       dev                                 🔔3   ko ▾    ☾                    JD

                                                                                                                                                                      POST /api/notifications/read-all → 상단바 배지
   ▫ 대시보드                알림                                                                                                             1    모두 읽음      button                                                  SCR-B01
                                                                                                                                                                      0
                                                                                                  1
   ▫ AI 어시스턴트
                         알림 센터                                                                        모두 읽음       필터 전체        ▾                        chips +
                                                                                                                                        2    유형 필터                    승인·설치·헬스·업데이트·보안. 기본 전체                 D10-07
                                                                                                                                                        select
   ▫ 마켓플레이스             2
                                 전체      승인                설치             헬스              업데이트           보안
                                                                                                                                                                      유형·제목·시각·액션. GET /api/notifications?
                                                                                                                                        3    알림 항목      list item                                             D10-07
                                                                                                                                                                      unread=
   ▫ 에이전트 관리
                        3
                                 승인 요청        '메일 발송' 승인 필요                                                        5분 전
   ▫ 워크플로                    4                                                                                                          4    미읽음 표시     dot + 배경      미읽음은 점 + 강조 배경. 클릭 시 PATCH read         -
                                              클릭 시 읽음 처리(PATCH read) 후 대상 화면으로 이동
                                                                                                                  5
                                                                                                                           승인함 ›
   ▫ 지식(RAG)                                                                                                                                                          승인함·런타임 헬스·에이전트 상세 등 대상
                                                                                                                                        5    조치 버튼      link button                                           SCR-I03 SCR-M01
                                                                                                                                                                      화면으로 이동
   ▫ 플레이그라운드                     설치 완료        board 1.2.0 설치가 끝났습니다                                               1시간 전
                                                                                                                                                        empty +
                                                                                                                                        6    빈 상태·페이징                 '새 알림이 없습니다'. 목록은 커서 페이징                -
   ▫ 거버넌스                                     클릭 시 읽음 처리(PATCH read) 후 대상 화면으로 이동                                          에이전트 ›
                                                                                                                                                        button


   ▫ LLM·모델
                                 헬스           rag-be unhealthy                                                    2시간 전

   ▫ 관측·운영
                                              클릭 시 읽음 처리(PATCH read) 후 대상 화면으로 이동                                          런타임 ›

   ▫ 사용자·조직

                                 업데이트         hrcore 1.3.0 사용 가능                                                      어제
   ▫ 설정

                                              클릭 시 읽음 처리(PATCH read) 후 대상 화면으로 이동                                          설치됨 ›
   설치된 Addon


   ▸ 게시판                 더보기(커서 페이징)


   ▸ HR 채용
                        6


                                                                      새 알림이 없습니다




   [‹ 접기]




관련 요구사항(PRD): D10-07


AgentPlaza 화면설계서 · v1.0 · B. 메인·대시보드                                                                                                                                                                                      28
시스템          AgentPlaza                                          화면 ID        SCR-B04                       화면 유형              모달(커맨드 팔레트)
화면명          전역 검색                                               화면 경로        (상단바 팔레트)                     접근 권한              로그인
우선순위         P1                                                  PRD 추적       D10-01                        작성일 / 버전           2026-09-19 / v1.0

에이전트·마켓 자산·문서·설정을 한 입력창에서 찾는다. ⌘K/Ctrl+K 로 열리며 300ms 디바운스로 GET /api/search?q= 를 호출하고, 유형별로 그룹지어 최대 5건씩 보여 준다. 권한이 없는 항목은 결과에서 제외한다.



                                                                                                       No   구성요소       유형         기능 설명 / 동작                           연계


                                                                                                                                  ≤100자. 300ms 디바운스, IME 조합 중에는
                                                                                                       1    검색 입력      input                                           D10-01
                                                                                                                                  검색하지 않음


                    전역 검색 (⌘K / Ctrl+K)                                                           ✕
                                                                                                       2    에이전트 결과    list(그룹)   설치 상태 배지 포함. Enter → 에이전트 상세         SCR-D02


                                                                                                            마켓·문서·설정
                   1                                                                                   3               list(그룹)   유형별 최대 5건. 권한 있는 항목만 렌더              SCR-E02
                                                                                                            결과
                       🔍 board                                                                Esc 닫기
                                                                                                                                  ↑↓ 이동 · Enter 열기 · Tab 유형 전환 · Esc
                                                                                                       4    키보드 안내     text                                            -
                                                                                                                                  닫기
                                            2
                       에이전트                        게시판 (board) · 설치됨                      → SCR-D02    5    빈 상태       empty      '결과가 없습니다' + 마켓플레이스 검색 링크            SCR-E01



                       마켓 자산                       Board 1.2.0 · common 도메인               → SCR-E02



                                            3
                       문서                          게시판 사용 가이드                                   →-




                       설정                          채널·임베드 설정                              → SCR-C07




                   4↑↓ 이동 · Enter 열기 · Tab 유형 전환   | 권한 있는 항목만, 유형별 최대 5건


                   5

                                                            결과가 없습니다 — 마켓플레이스에서 검색 ›




관련 요구사항(PRD): D10-01


AgentPlaza 화면설계서 · v1.0 · B. 메인·대시보드                                                                                                                                             29
시스템              AgentPlaza                                 화면 ID                 SCR-C01                                                                화면 유형                  페이지
화면명              채팅(AI 어시스턴트)                               화면 경로                 /chat                                                                  접근 권한                  로그인
우선순위             P0                                         PRD 추적                D3-01 D3-03 D2-06                                                      작성일 / 버전               2026-09-19 / v1.0

스트리밍 대화, 도구 호출 진행·결과, 승인 카드를 제공하는 기본 작업 화면이다. POST /api/chat/stream 의 AG-UI SSE(RUN_STARTED → TEXT_MESSAGE_* / TOOL_CALL_* / CUSTOM(approval·review·registry_miss) / SUBAGENT_* →
RUN_FINISHED)를 전량 카드로 렌더한다. 이탈 내성 스트림 store 로 세션을 옮겨도 진행 중 응답이 유지된다.


                                                                                                                                                    No   구성요소          유형             기능 설명 / 동작                        연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                           dev                                       🔔3     ko ▾        ☾               JD

                                                                                                                                                                                      새 대화·검색·오늘/어제 그룹. hover 시 이름변경
    ▫ 대시보드                AI 어시스턴트                                                                                                                  1    세션 패널         list + input                                     SCR-C02
                                                                                                                                                                                      ·고정·삭제

    ▪ AI 어시스턴트
                          AI 어시스턴트                                                                                                                                                    게이트웨이 별칭(GET /api/llm/aliases).

                         1
                                                                                                                                                    2    모델 선택         select
                                                                                                                                                                                           🏠
                                                                                                                                                                                      로컬은 , 등급상 불가 별칭 disabled
                                                                                                                                                                                                                        SCR-J01

    ▫ 마켓플레이스                                                                           2                          3

                                     + 새 대화
                                                                                           모델 plaza/chat    ▾         지식 사내문서       ▾           ⋯   3    지식 선택
                                                                                                                                                                       multi-
                                                                                                                                                                                      컬렉션 선택 시 RAG 도구 자동 활성             SCR-C06
                                                                                                                                                                       select
    ▫ 에이전트 관리
                                                 무엇을 도와드릴까요? — 역할·설치 Addon 기반 추천 프롬프트

    ▫ 워크플로
                               🔍 세션 검색                                                                                                              4    추천 프롬프트
                                                                                                                                                                       chips          빈 상태에서 역할·설치 Addon 기반 제안. 클릭
                                                                                                                                                                                                                        D3-01
                                                4                                                                                                                      ×3~5           시 입력창 채움
                                                           게시판 글 요약해줘                             이번 주 승인 대기                   RAG 로 규정 찾기

                              오늘
    ▫ 지식(RAG)                                                                                                                                                                         TOOL_CALL_*. 시작·진행·성공·실패·차단. 인자
                                                                                               게시판 최근 공지 요약하고 담당자에게 메일 보내줘                          5    도구 호출 카드      CMP-16                                           D3-03
                               재고 조회 문의                                                                                                                                               원문은 admin+ 만 펼침
    ▫ 플레이그라운드
                                                                                                                                                                                      hitl_pending. 대기 중 입력 비활성, 승인자
                               생산 계획 초안                                                                                                             6    승인 카드(HITL)   CMP-15                                           D2-06
    ▫ 거버넌스                                          최근 공지 3건을 요약했습니다 [1][2]. 메일 발송은 승인이 필요합니다.                                                                                        아니면 읽기 전용 + 승인함 링크

                                                5                                                                                                        리뷰 게이트·       badge +        review_gate 통과/수정/차단 사유,
                                                                                                                                                    7                                                                   D2-06
    ▫ LLM·모델                  어제
                                                    🔧 도구 호출 board.manage(list)                                     성공                                    서브에이전트        collapsible    SUBAGENT_* 위임 대상·진행

    ▫ 관측·운영
                               주문 현황 요약             인자 원문은 admin+ 만 펼침 · 결과 게시글 12건 · 0.4s
                                                                                                                                                    8
                                                                                                                                                         품질 지표·피드백·
                                                                                                                                                                       meta +
                                                                                                                                                                       버튼 +
                                                                                                                                                                                      소요·토큰·별칭→실제 모델.      👎😐👍 낙관 갱신.   D3-01
                                                    ⏸ 승인 필요 mail.send(to=hr@acme.com)
                                                6                                                                                                        저하                           폴백·캐시는 저하 배지
                               규정 검색
                                                                                                                                                                       badge
    ▫ 사용자·조직
                                                    정책 humanApproval · 영향 외부 발송 · 만료 09:41                                                               입력·전송·스코프     textarea + ≤8,000자, IME 조합 중 전송 차단, 스트리밍 중
                                                                                                           승인             거부                        9                                                             D3-01
    ▫ 설정                                                                                                                                                 바             button     '중지'. 스코프·등급·마스킹 표시
                              (더보기 · 커서 페이징)
                                                7
                                                    🧭 리뷰 게이트 통과 0.92                                       🤖 서브에이전트 rag ▸
    설치된 Addon
                                                    차단 시 사유 표시                                             위임 대상·진행(접힘)
                                               8 ⏱ 2.4s · 812 토큰 · plaza/chat → qwen3:8b(로컬)    👎😐👍
    ▸ 게시판


    ▸ HR 채용                                                        ⚠ 로컬 모델 응답(퍼블릭 폴백) — MSG-011


                                                9

                                                    📎🎤            메시지 입력… (Enter 전송 / Shift+Enter 줄바꿈)                                  전송 ▶



                                                 스코프: 전체 ▾ · 데이터 등급 L1 ·    🔒 개인정보 마스킹 on
    [‹ 접기]




관련 요구사항(PRD): D3-01 D3-03 D2-06


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                             30
시스템             AgentPlaza                                    화면 ID                     SCR-C02                                                                           화면 유형                탭·패널
화면명             세션 목록·히스토리                                    화면 경로                     /chat (좌측 패널)                                                                     접근 권한                로그인
우선순위            P0                                            PRD 추적                    D3-02                                                                             작성일 / 버전             2026-09-19 / v1.0

대화를 저장·검색·이름변경·삭제·내보내기 한다. 세션은 서버(/api/chat/sessions)에 저장하고 제목+본문 전문검색을 지원하며, 스코프·기간·고정 칩으로 걸러 본다. 보존 기간이 임박한 세션은 사전 안내한다.



                                                                                                                                                                     No   구성요소         유형          기능 설명 / 동작                      연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                dev                                          🔔3           ko ▾          ☾                 JD

                                                                                                                                                                                                   제목·시각·스코프 배지. 최근순 그룹(오늘·어제·N
   ▫ 대시보드                AI 어시스턴트 › 세션                                                                                                                               1    세션 항목        list item                                   D3-02
                                                                                                                                                                                                   일 전)

   ▪ AI 어시스턴트
                         세션 목록·히스토리
                                                                                                                                                                     2    검색           input       제목 + 본문 서버 전문검색                 D3-02

   ▫ 마켓플레이스
                             2
                                 🔍 제목 + 본문 전문검색                                                                                                                      3    필터           chips       스코프·기간·고정. 기본 전체                -
   ▫ 에이전트 관리

                             3                                                                                                                                            hover 컨텍스트               이름 변경(인라인)·고정·삭제(확인 MSG-002).
   ▫ 워크플로                          전체          스코프          기간                     고정                                                                                4                 menu                                        MSG-002
                                                                                                                                                                          메뉴                       진행 중 세션 삭제 불가
                                                                                                hover 컨텍스트 메뉴

   ▫ 지식(RAG)                 1                                                              4
                                 재고 조회 문의                                                                                                                            5    내보내기         menu        md|json. 개인정보 마스킹 옵션 포함         D3-02
                                                                            전체                    이름 변경(인라인)
   ▫ 플레이그라운드                     오늘 14:02

                                                                                                  고정
                                                                                                                                                                     6    보존 안내        text        보존 기간 만료 예정 표시(NFR-C3)          -
   ▫ 거버넌스
                                 생산 계획 초안
                                                                            board                 삭제(확인 MSG-002)
   ▫ LLM·모델                      오늘 11:20


   ▫ 관측·운영
                                 주문 현황 요약
                                                                            전체
                                                                                            5
   ▫ 사용자·조직                      어제
                                                                                                  내보내기 메뉴


   ▫ 설정                                                                                                     Markdown(.md)                         JSON(.json)
                                 규정 검색
                                                                             rag
                                                                                                  ✓     개인정보 마스킹 적용
   설치된 Addon                     09-17



   ▸ 게시판
                             6보존 기간 만료 예정 3건 — 정책에 따라 자동 삭제(NFR-C3)
   ▸ HR 채용
                                                                                                  세션 저장소는 서버(/api/chat/sessions).
                                                                                                  진행 중인 세션은 삭제 불가.
                                                                                                  PATCH /api/sessions/{id} {title} 로 이름 변경.


                                            첫 대화를 시작하세요 / 검색 결과 없음




   [‹ 접기]




관련 요구사항(PRD): D3-02


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                                        31
시스템              AgentPlaza                                      화면 ID                SCR-C03                                                        화면 유형                 모달(인라인 첨부 패널)
화면명              파일·멀티모달 입력                                      화면 경로                /chat (첨부)                                                     접근 권한                 로그인
우선순위             P1                                              PRD 추적               D3-04                                                          작성일 / 버전              2026-09-19 / v1.0

문서·이미지 업로드와 음성 입력을 대화에 첨부한다. 입력창 전체가 드롭존이며 업로드 후 파싱 잡 진행을 칩으로 보여 주고, 메시지 전송 시 attachment id 를 함께 보낸다. 데이터 등급과 별칭의 비전 지원 여부를 검사해 위반을 인라인으로 알린다.



                                                                                                                                                No   구성요소        유형             기능 설명 / 동작                              연계
    첨부 패널 — 채팅 입력창 위 인라인 (SCR-C01 ⑱ 확대)
                                                                                                                                                                                입력창 전체가 드롭 영역.
                                                                                                                                                1    드래그 & 드롭    dropzone                                               D3-04
                                                                                                                                                                                pdf·docx·xlsx·txt·md·png·jpg ≤20MB ×5
                                                   6                                                      3
       📄 규정.pdf 1.2MB                       ✕          🖼 사진.png 340KB                              ✕          🎤 음성 00:12                    ✕
                                                                                                                                                2    파일 선택       file input     형식·크기 검증 후 POST /api/files → 파싱 잡       D3-04


                                                       업로드됨 · ⚠ 비전 모델 필요
                                                                                                                                                                 chip +         파일명·크기·진행·상태. 개별 제거(✕), 썸네일
       업로드됨 · 파싱 중(문서 이해 준비)                                                                                  전사: "재고 현황 알려줘" [재생]              3    첨부 칩                                                               -
                                                                                                                                                                 progress       표시

                                                                                                                                                                 paste
                                                                                                                                                4    클립보드 붙여넣기                  이미지 붙여넣기 → 미리보기 후 첨부                    D3-04
                                                                                                                                                                 handler
   1
                                                                                                                                                                                L2+ 첨부는 로컬 모델 강제. 위반은
                                                                                                                                                5    등급·형식 검증    inline alert                                           SCR-J04
                                                                                                                                                                                MSG-004 / MSG-010
                                                              ① 드래그 & 드롭 영역 — 입력창 전체
                                                 pdf · docx · xlsx · txt · md · png · jpg | ≤20MB × 최대 5개                                                        record         ≤2분 녹음 후 전사. STT Addon(X03) 미설치
                                                                                                                                                6    음성 입력                                                              X03
                                                                                                                                                                 button         시 비표시



                                        2                                      4
                                                   ② 파일 선택                             ④ 클립보드 이미지 붙여넣기




       📎🎤               메시지 입력… (첨부 3개)                                                                                              전송 ▶




   5
       ⚠ 현재 별칭이 vision 미지원 — 비전 가능한 별칭을 제안한다.                                      업로드: POST /api/files (multipart) → 파싱 잡
       데이터 등급 L2+ 첨부는 로컬 모델을 강제한다.                                                 썸네일·진행 표시, 메시지 전송 시 attachment id 동봉.
       형식·크기·등급 위반은 인라인 오류(MSG-004 / MSG-010).                                     음성은 STT Addon(X03) 설치 시에만 노출(≤2분).




관련 요구사항(PRD): D3-04


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                             32
시스템             AgentPlaza                                          화면 ID          SCR-C04                                                                   화면 유형               페이지
화면명             메모리·맞춤지침                                            화면 경로          /profile/memory                                                           접근 권한               본인
우선순위            P1                                                  PRD 추적         D3-05                                                                     작성일 / 버전            2026-09-19 / v1.0

장기 메모리(사실·선호)와 사용자 맞춤지침을 확인·수정·삭제한다. 맞춤지침은 저장 즉시 다음 대화부터 적용되고, 기억된 사실은 출처·시각과 함께 나열해 개별/일괄 삭제할 수 있다. 메모리 사용을 끄면 추출과 주입이 모두 멈춘다.



                                                                                                                                                        No   구성요소       유형            기능 설명 / 동작                               연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                    dev                             🔔3        ko ▾           ☾               JD


   ▫ 대시보드                내 프로필 › 메모리·맞춤지침                                                                                                               1    맞춤지침       textarea      ≤2,000자. 어시스턴트가 항상 따를 지시                 D3-05


   ▫ AI 어시스턴트
                         메모리·맞춤지침                                                                                                                                                     PUT /api/me/instructions → MSG-001. 다음
                                                                                                                                                        2    저장         button                                                 -
                                                                                                                                                                                      대화부터 적용
   ▫ 마켓플레이스
                             맞춤지침 — 어시스턴트가 항상 따를 지시
                                                                                                                                                                                      내용·출처·시각. DELETE
                                                                                                                                                        3    기억된 사실     list                                                   D3-05
                             1                                                                                                                                                        /api/me/memories/{id}
   ▫ 에이전트 관리
                                 답변은 한국어로, 표를 선호합니다. 코드는 예시와 함께 설명해 주세요. (≤2,000자)
                                                                                                                                                                                      개별 삭제는 확인 없이 실행 + 5초 실행취소
   ▫ 워크플로                                                                                                                                               4    삭제·모두 삭제   button                                                 -
                                                                                                                                                                                      토스트

   ▫ 지식(RAG)
                                                                                                                                                        5    메모리 사용     toggle        기본 on. 끄면 추출·주입 중지                       D3-05
                                                                                                                                       2
                             저장 시 다음 대화부터 적용(PUT /api/me/instructions → MSG-001)
   ▫ 플레이그라운드                                                                                                                                 저장
                                                                                                                                                                                      auto|confirm(기본). confirm 이면 대화
                                                                                                                                                        6    추출 방식      select                                                 SCR-C01
   ▫ 거버넌스
                                                                                                                                                                                      중 '기억할까요?' 카드
                                                                                                                                   4
                             기억된 사실 (장기 메모리)
                                                                                                                                           모두 삭제
   ▫ LLM·모델
                             3
   ▫ 관측·운영
                                 사용자는 인사팀 소속                                                             2026-09-10 · 대화에서 추출                      삭제


   ▫ 사용자·조직

                                 선호 형식: 표                                                                2026-09-12 · 대화에서 추출                      삭제
   ▪ 설정



   설치된 Addon                     담당 조직: ACME 서울                                                          2026-09-15 · 프로필 연동                       삭제


   ▸ 게시판                     개별 삭제는 확인 없이 즉시 실행 + 5초 실행취소 토스트


   ▸ HR 채용

                                                                                             메모리 추출 방식
                             5
                                         메모리 사용 (끄면 추출·주입 중지)                              6
                                                                                               confirm (확인 후)                  ▾
                             기본 on
                                                                                             confirm 이면 대화 중 '기억할까요?' 카드 표시
   [‹ 접기]




관련 요구사항(PRD): D3-05


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                                    33
시스템             AgentPlaza                                            화면 ID                SCR-C05                                                           화면 유형               페이지
화면명             에이전트 스코프 채팅(폴백)                                       화면 경로                /a/{agent}/chat                                                   접근 권한               로그인+권한
우선순위            P0                                                    PRD 추적               D3-03                                                             작성일 / 버전            2026-09-19 / v1.0

전용 화면이 없는 에이전트를 대화로 사용한다. SCR-C01 의 대화 영역을 스코프 고정(scope=agent) 상태로 재사용하고, 위에 안내 배너와 agent.yaml capabilities 로 만든 도구 목록·예시 프롬프트를 얹는다. 진입 시 권한을 확인해 없으면 403
안내를 보여 준다.


                                                                                                                                                        No   구성요소       유형          기능 설명 / 동작                               연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                       dev                             🔔3          ko ▾   ☾                  JD

                                                                                                                                                                        info        '전용 화면이 없어 대화로 사용합니다'. 닫기
   ▫ 대시보드                에이전트 › 게시판                                                                                                                     1    안내 배너                                                           D3-03
                                                                                                                                                                        banner      가능(세션 기억)

   ▫ AI 어시스턴트
                         게시판 (board)                                                                                                                                                agent.yaml capabilities 에서 생성. 노출된
                                                                                                                                                        2    도구 목록      chips                                                SCR-D02
                                                                                                                                                                                    도구만 호출 가능
                        1
   ▫ 마켓플레이스
                                                                                                                                                                        SCR-C01     scope=agent 고정(변경 불가). 도구·승인 카드
                             ℹ 이 에이전트는 전용 화면이 없어 대화로 사용합니다. (닫기 가능 · 세션 기억)                                                                      ✕      3    대화 영역                                                           SCR-C01
                                                                                                                                                                        재사용         동일 렌더
   ▫ 에이전트 관리

                                               2
   ▫ 워크플로                사용 가능 도구                    manage.app.board (목록)              board.write (작성)     board.edit (수정)        board.delete (삭제)   4    예시 프롬프트    chips       agent.yaml examplePrompts 값              -


   ▫ 지식(RAG)            3                                                                                                                                               textarea + GET /api/agents/{key} 로 권한·capabilities
                             대화 영역 — SCR-C01 재사용 (scope = board 고정, 변경 불가)                                                                              5    입력·전송                                                           D3-03
                                                                                                                                                                        button     확인 후 활성
   ▫ 플레이그라운드
                                                                                   최근 공지 5개 보여줘
   ▫ 거버넌스


   ▫ LLM·모델                     공지 5건입니다. (표) — 도구 board.manage(list) 사용


   ▫ 관측·운영
                                🔧 도구 호출 manage.app.board(list)                                     성공
   ▫ 사용자·조직
                                capabilities 로 노출된 도구만 호출


   ▫ 설정



   설치된 Addon


   ▸ 게시판


   ▸ HR 채용

                                               4
                                                            최근 글 5개                        공지 작성              댓글 많은 글
                         예시 프롬프트

                        5
                             메시지 입력… (스코프 board 고정)                                                                                       전송 ▶

   [‹ 접기]




관련 요구사항(PRD): D3-03


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                                  34
시스템             AgentPlaza                                   화면 ID                   SCR-C06                                                         화면 유형                 탭·패널(드롭다운 + 드로어)
화면명             지식(RAG) 연결 패널                                화면 경로                   /chat (지식 선택)                                                   접근 권한                 로그인
우선순위            P1                                           PRD 추적                  D3-06                                                           작성일 / 버전              2026-09-19 / v1.0

대화에 사용할 지식 컬렉션을 고르고 인용을 확인한다. 헤더 '지식' 드롭다운에서 권한 있는 컬렉션만 체크할 수 있고, 선택하면 RAG 도구가 자동 활성화된다. 응답의 인용 번호를 누르면 우측 드로어에서 원문 청크와 점수를 확인한다.



                                                                                                                                                No   구성요소         유형          기능 설명 / 동작                         연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                               dev                                🔔3            ko ▾             ☾   JD

                                                                                                                                                                  checkbox    권한 있는 컬렉션만. 청크 수·최신 인덱싱 시각
   ▫ 대시보드                AI 어시스턴트                                                                                                               1    컬렉션 선택                                                      D3-06
                                                                                                                                                                  list        표시

   ▪ AI 어시스턴트
                         지식(RAG) 연결
                                                                                                                                                2    인용 표시        toggle      기본 on. 끄면 인용 번호·드로어 비활성            -

   ▫ 마켓플레이스
                                                                                              지식 사내문서       ▾          헤더 '지식' 드롭다운                               select +    하이브리드(BM25+dense RRF) 기본, k 1~20
                                                                                                                                                3    검색 방식·상위 k                                                  D3-06
                                                                                                                                                                  number      기본 5
   ▫ 에이전트 관리
                                                                                                        5
                                                                                 4        지식 관리 →
                                 지식 컬렉션 선택 (권한 있는 컬렉션만)                                                     응답 인용 드로어
   ▫ 워크플로                                                                                                                                       4    지식 관리 링크     link        컬렉션 생성·인덱싱 화면으로 이동                 SCR-G01
                                1
                                    ✓    사내 규정             1,204 청크 · 2026-09-10                                [1]       score 0.83
   ▫ 지식(RAG)
                                                                                                                                                5    인용 드로어       drawer      번호 클릭 → 원문 청크·score·문서 링크          D3-06
                                                                                                                규정 §3.2 — 연차 산정 기준…
   ▫ 플레이그라운드
                                         제품 매뉴얼            3,880 청크 · 2026-09-08
                                                                                                                원문 보기 ›

   ▫ 거버넌스

                                         회의록               620 청크 · 2026-09-01                                  [2]       score 0.74
   ▫ LLM·모델
                                2                                                                               규정 §5.1 — 승인 절차…
   ▫ 관측·운영                                 인용 표시 (기본 on)
                                                                                                                원문 보기 ›
                                 검색 방식                              상위 k
   ▫ 사용자·조직
                                3
                                    하이브리드(RRF)        ▾              5               (1~20)
                                                                                                            인용 번호 클릭 → 원문 청크·문서 링크.
   ▫ 설정                                                                                                     인용 표시를 끄면 드로어가 열리지 않는다.

                                 선택 변경 → 세션 설정 PATCH, 다음 메시지부터 적용

   설치된 Addon


   ▸ 게시판
                                 컬렉션 선택 시 RAG 도구가 자동 활성화되고, 대화 입력 시 선택한 컬렉션만 검색한다.
   ▸ HR 채용




   [‹ 접기]




관련 요구사항(PRD): D3-06


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                      35
시스템             AgentPlaza                                           화면 ID                SCR-C07                                                                              화면 유형                   페이지
화면명             채널·임베드 설정                                            화면 경로                /settings/channels                                                                   접근 권한                   admin
우선순위            P2                                                   PRD 추적               D3-07                                                                                작성일 / 버전                2026-09-19 / v1.0

웹 위젯·메신저 채널을 발급·연결한다. 웹 위젯은 origin allowlist 를 필수로 요구하고 iframe+postMessage 스니펫을 제공하며, 메신저 채널은 해당 Addon 설치 후 토큰을 시크릿 저장소에 넣어 연결한다. 채널마다 기본 스코프·데이터 등급·허용
그룹을 지정한다.


                                                                                                                                                                          No   구성요소           유형          기능 설명 / 동작                                     연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                     dev                                            🔔3          ko ▾            ☾              JD


   ▫ 대시보드                설정 › 채널·임베드                                                                                                                                      1    웹 위젯 활성        toggle      허용 도메인 미설정 시 활성 불가                             D3-07


   ▫ AI 어시스턴트
                         채널·임베드 설정                                                                                                                                                            input(목
                                                                                                                                                                          2    허용 도메인                     origin allowlist. 미등록 origin 의 요청은 거부          D3-07
                                                                                                                                                                                              록)
   ▫ 마켓플레이스                                                      1
                               웹 위젯                                    활성                                                                                                                     code +
                               허용 도메인 (origin allowlist · 필수)                                                                                                             3    임베드 스니펫                    iframe + postMessage 방식 스니펫 생성·복사              -
                                                                                              3                                                                                               복사
   ▫ 에이전트 관리
                             2                                                                    <script src="https://plaza/embed.js"
                                                                                                    data-channel="web" data-scope="board"></script>
                                    app.acme.com, portal.acme.com                                                                                                                             connect     POST /api/channels/slack {secret_ref, scope,
   ▫ 워크플로
                                                                                                  <!-- iframe + postMessage -->                                           4    Slack 연결                                                                  D3-07
                                                                                                                                                                                              card        classification}

   ▫ 지식(RAG)                   origin allowlist 미설정 시 활성 불가.                                                                                                                                  connect
                                                                                                                                                                          5    Telegram·카카오               채널 Addon 설치 시 활성. 미설치면 마켓 링크                   SCR-E01
                               스니펫은 iframe + postMessage 방식.                                                                                                                                  card
   ▫ 플레이그라운드                                                                                                                                               스니펫 복사
                                                                                                                                                                                                          채널별 기본 스코프·데이터 등급·허용 사용자
                                                                                                                                                                          6    채널 공통 설정       표                                                          SCR-J04
   ▫ 거버넌스
                                                                                                                                                                                                          그룹


   ▫ LLM·모델             4                                              5
                               Slack                           연결됨           Telegram                       미연결                   카카오                        설치 필요

   ▫ 관측·운영
                               워크스페이스 acme · 봇 토큰 ••••                       봇 토큰 미등록                                             채널 Addon 설치 필요

   ▫ 사용자·조직


   ▪ 설정
                                        해제            토큰=시크릿                        연결                토큰=시크릿                             마켓 →             토큰=시크릿


   설치된 Addon


   ▸ 게시판                 채널 공통 설정

   ▸ HR 채용              6
                            채널                           기본 스코프                          데이터 등급                           허용 사용자 그룹


                            웹 위젯                         board                           L1                               익명(도메인 제한)


                            Slack                        전체                              L1                               직원 그룹


   [‹ 접기]                   Telegram                     -                               L0                               미설정




관련 요구사항(PRD): D3-07


AgentPlaza 화면설계서 · v1.0 · C. AI 어시스턴트                                                                                                                                                                                                                              36
시스템             AgentPlaza                                                          화면 ID                               SCR-D01                                                                              화면 유형                    페이지
화면명             에이전트 목록                                                             화면 경로                               /agents                                                                              접근 권한                    로그인(관리 기능은 admin+)
우선순위            P0                                                                  PRD 추적                              D5-06 D10-01                                                                         작성일 / 버전                 2026-09-19 / v1.0

내장·설치됨·원격 에이전트를 한 목록에서 상태와 함께 관리한다. 참조 구현의 카드덱에 검색·필터·표 보기·헬스·버전·신뢰 등급·업데이트 배지와 원격 탭을 더했다. 카드 클릭으로 상세(SCR-D02)로 이동한다.



                                                                                                                                                                                                        No   구성요소            유형          기능 설명 / 동작                       연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                                     dev                                                      🔔3       ko ▾               ☾                  JD

                                                                                                                                                                                                                             split       만들기 ▾: 스캐폴드·ZIP 업로드·마켓에서.
   ▫ 대시보드                에이전트 관리                                                                                                                                                                        1    새 Agent·원격 등록                                                SCR-D03 D04 E01
                                                                                                                                                                                                                             button      admin+ 만 노출
                                                                                                                                      1
   ▫ AI 어시스턴트
                         에이전트 관리                                                                                                            ✦ 새 Agent 만들기 ▾                                원격 등록
                                                                                                                                                                                                        2    탭               탭+건수        내장|설치됨|원격. URL ?tab= 반영          -

   ▫ 마켓플레이스             2
                                    내장 3                     설치됨 12                        원격 2                                                                                                                              입력·선택·      도메인·상태(활성/비활성/unhealthy)·신뢰등급.
                                                                                                                                                                                                        3    검색·필터·보기                                                     -
                                                                                                                                                                                                                             토글          카드/표 전환 기억
   ▪ 에이전트 관리
                        3

   ▫ 워크플로
                             🔍 에이전트 검색                                             도메인 ▾                        상태 ▾                        신뢰 등급 ▾                                        카드      표
                                                                                                                                                                                                        4    내장 카드           카드
                                                                                                                                                                                                                                         REQUIRED 배지(토글 불가). MCP·Worker
                                                                                                                                                                                                                                                                          D5-06
                                                                                                                                                                                                                                         아이콘
                        4                                                                  5                                                             6
   ▫ 지식(RAG)                                    Orchestrator            REQUIRED                                   게시판                    활성 ◯━                           송장 대조                                                          활성 토글 PATCH(실패 롤백 토스트)·MCP       SCR-D06 D08
                                                                                                                                                                                                        5    설치됨 카드          카드
                                    ◈                                                                ◈                                                       ◈                                                                           팝오버·추출·더보기                       D10
                                                v1.0.0 · orchestrator                                              v1.2.0 · common                                        원격 A2A · acme.com
   ▫ 플레이그라운드
                                                                                                                                                                                                                             카드(점
                                의도 분류·라우팅 담당                                                     게시글·댓글 CRUD                                                                                            6    원격 카드                       연결·계약 시험 시각. 더보기: 재시험·해제         SCR-D11
   ▫ 거버넌스                       ⚠ 퍼블릭 키 미설정                                                      🔔1.3.0 업데이트 가능                                                                                                              선)
                                    healthy                                                          healthy · G1                         🌐📦↗⋯               계약 OK · 시험 2h 전
                                                                                                                                                                                                                             데이터         키·이름·유형·버전·등급·헬스·MCP·동작. 정렬·
   ▫ LLM·모델                                                                                                                                                                                             7    표 보기                                                         D10-01
                                                                                                                                                                                                                             그리드         페이징

   ▫ 관측·운영                                official                         ↓ 내장                              official                      ↓ 1.2k                    external                       ⋯


   ▫ 사용자·조직
                         카드 본문 클릭 → SCR-D02 상세 · 50건 초과 시 표 보기 기본

   ▫ 설정
                        7
                            키                        이름                            유형                버전                    등급                헬스                  MCP                동작

   설치된 Addon
                            board                    게시판                           설치됨               1.2.0                 official          ● healthy           켬                  설정 ⋯
   ▸ 게시판

                            ragagent                 지식 검색                         내장                1.0.0                 official          ● healthy           켬                  설정 ⋯
   ▸ HR 채용

                            invoice-x                송장 대조                         원격                1.2.0                 external          ● 계약 OK             -                  재시험 ⋯


                         … 외 9건 · 정렬·페이징(50/쪽)




   [‹ 접기]




관련 요구사항(PRD): D5-06 D10-01


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                                                                    37
시스템              AgentPlaza                                               화면 ID                 SCR-D02                                                                 화면 유형                페이지
화면명              에이전트 상세·설정                                               화면 경로                 /agents/{key}                                                           접근 권한                admin+
우선순위             P0                                                       PRD 추적                D5-06 D1-06 D9-02                                                       작성일 / 버전             2026-09-19 / v1.0

모델 별칭·프롬프트·설명(다국어)·권한·카테고리를 설정한다. 탭 7개(개요·설정·프로토콜·정책·버전·로그·가이드)로 나누고, 개요는 매니페스트·capabilities·거버넌스·런타임·출처를 읽기 전용으로 보여 준다.



                                                                                                                                                                   No   구성요소           유형         기능 설명 / 동작                          연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                                         dev                                     🔔3      ko ▾            ☾             JD

                                                                                                                                                                                                                                      SCR-D07 D12
    ▫ 대시보드                에이전트 관리 › 게시판                                                                                                                            1    탭              탭          7개. URL 반영. user 권한은 개요만 조회
                                                                                                                                                                                                                                      D09

    ▫ AI 어시스턴트
                          게시판 (board)                                                                        official          G1 MIT
                                                                                                                                                                                                  유형·도메인·업무·업종·토폴로지. agent.yaml
                                                                        v1.2.0 ● healthy                                                활성               ⋯         2    매니페스트 요약       KV                                             D5-06
                                                                                                                                                                                                  원문 코드 블록
    ▫ 마켓플레이스             1
                                    개요                     설정                 프로토콜                정책               버전·업데이트        로그·트레이스               가이드                            목록+        verb.domain 목록, 입력/출력 JSON Schema
                                                                                                                                                                   3    capabilities                                                  D2-02
                                                                                                                                                                                       스키마        트리
    ▪ 에이전트 관리

                               개요                                                                      설정                                                                              서비스        서비스별 헬스·재시작(admin+)·로그. 서명
    ▫ 워크플로                                                                                                                                                         4    런타임·출처                                                        SCR-M02
                                                                                                                                                                                       목록         ·SBOM·라이선스·설치자
                              2매니페스트 요약                                                                표시명 ko (≤100)                   en

    ▫ 지식(RAG)                  유형 app · 도메인 common · 업무 W19 · 업종 전업종                                 5                                                                                 입력         ko 필수, en 선택. ≤100 / ≤500. 언어 탭
                               토폴로지 T1~T5     [agent.yaml 원문 보기]                                                                                                   5    표시명·설명                                                        D1-06
                                                                                                         게시판                            Board                                          (다국어)      추가 가능
    ▫ 플레이그라운드
                              3                                                                        설명 ko / en (다국어 탭, ≤500)
                                                                                                                                                                                                  게이트웨이 별칭. 데이터 등급상 불가 별칭은
                                  capabilities manage (app.board)                                                                                                  6    모델 별칭          선택                                             D1-06
    ▫ 거버넌스                        입력/출력 JSON Schema 트리 보기                                                                                                                                         disabled
                                                                                                         게시글·댓글 CRUD 에이전트
                                                                                                                                                                                                  매니페스트 프롬프트 뒤 append. 원문 수정 불가
    ▫ LLM·모델                                                                                           모델 별칭                           네비 그룹                       7    프롬프트 추가        textarea                                 D9-02
                               거버넌스                                                                                                                                                               ≤4,000
                                                                                                     6
    ▫ 관측·운영                           등급 internal              승인 불필요             감사 standard                                                                                                     required/optional. 시크릿은 참조만. 변경 시
                                                                                                         plaza/chat      ▾              경영지원             ▾         8    환경 변수·시크릿      폼                                              D5-06
                                                                                                                                                                                                  재시작 필요
                              4런타임 컨테이너 3 (be ● fe ● db ●) · 0.5CPU/512MB
    ▫ 사용자·조직                                                                                           시스템 프롬프트 추가(append · ≤4,000 · 원문 수정 불가)
                                    마지막 재시작 2일 전 [재시작][로그]
                               출처    퍼블리셔 Wise ✓ · 서명 ✓ · SBOM 142 · MIT                                                                                                                          변경 없으면 disabled. PATCH 후 MSG-001,
                                                                                                     7                                                             9    저장             버튼                                             D5-06
    ▫ 설정                            설치 2026-09-10 admin                                                  게시판 운영 규칙을 지켜 답하세요…                                                                      재시작 항목은 확인


    설치된 Addon
                         8
                               환경 변수(required_env) BOARD_PAGE_SIZE [20] BOARD_ATTACH_MAX [10MB]
    ▸ 게시판
                               시크릿 참조 (없음) — 값은 비노출, 참조만 표시
                               카테고리 slug [common-utility ×] [collab-board ×] · 변경 시 재시작 필요 안내
    ▸ HR 채용




                                                                                                                                                    9
                                                                                                                               취소                       저장
    [‹ 접기]




관련 요구사항(PRD): D5-06 D1-06 D9-02


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                                38
시스템                   AgentPlaza                                                    화면 ID                    SCR-D03                                                                           화면 유형                위저드(모달 5단계)
화면명                   새 Agent 만들기 — 스캐폴드                                            화면 경로                    /agents (모달 탭1)                                                                   접근 권한                admin+
우선순위                  P0                                                            PRD 추적                   D4-01 D4-02                                                                       작성일 / 버전             2026-09-19 / v1.0

9유형 템플릿에서 이름·도메인·LLM 요구를 받아 agent.zip 을 생성한다. 참조 구현 Builder 의 build 모드 4단계를 5단계(유형·기본·기능/LLM·화면/DB·확인)로 확장하고 다국어·토폴로지·카테고리·미리보기를 추가했다.



                                                                                                                                                                                          No   구성요소           유형        기능 설명 / 동작                                    연계

      ✦ 새 Agent 만들기                                                                                                                                                                  ✕
                                                                                                                                                                                          1    모드 탭           탭         scaffold|upload|market. 참조 구현 3모드 승계          SCR-D04
      1
               스캐폴드                       ZIP 업로드                      마켓에서                                                                                                                                             5단계. 이전·다음, 완료 단계 클릭 이동, 오류
                                                                                                                                                                                          2    단계             stepper                                                 -
                                                                                                                                                                                                                        단계 경고점
      2
                                                                                                                                                                                                              라디오       app·service·rag·tool-
          1      유형                          2       기본 정보                          3       기능·LLM                         4         화면·DB                     5        확인                3    유형                                                                       D4-01
                                                                                                                                                                                                              카드 ×9     proxy·reviewer·execution·hitl·memory·federation

                                3                                                                                                                                                                             입력        키 정규식 검증. 중복 409 → 인라인 오류 +
      1 유형                                                                                                                                                                                4    키·표시명·설명                                                               D4-02
                                    app               service            rag            tool-proxy           reviewer          execution          hitl         memory        federation                       (다국어)     '-2' 제안 키

      2 기본 정보                                                                                                                                                                                                           도메인·업무·업종 → 카테고리 slug 자동 생성
                                                                                                                                                                                          5    3축 분류          선택 ×3                                                   D2-02
                                                                                                                                                                                                                        (수정 가능)
      키 ^[a-z][a-z0-9-]{1,40}$            표시명 ko                               en                              도메인                         업무                  업종

      4                                                                                                      5                                                                                                          verb·domain·설명·스키마. 1개 이상 필수, 형식
                                                                                                                                                                                          6    capabilities   반복 폼                                                    D2-02
          inventory                        재고 관리                                Inventory                        manufact…▾                  W14 ▾             C        ▾                                               검증

      3 기능·LLM·거버넌스
                                                                                                                                                                                          7    LLM·거버넌스       체크·선택     별칭·로컬 허용·최소 컨텍스트 / 등급·승인·감사                   D1-06 D9-02
      6                                                                                              7
          capabilities [+ 추가]                                                                            ✓     LLM 필요 · 별칭 [plaza/chat]
          verb [manage] domain [app.inventory] 설명 …                                                                                                                                       8    미리보기           코드+트리     agent.yaml·compose.yaml·디렉터리 구조               D4-01
                                                                                                         로컬 허용 [x] · 최소 컨텍스트 [8000]
          verb.domain 형식 검증 · 1개 이상 필수 · 유형별 프리셋
                                                                                                         등급 [internal ▾] 승인 [ ] 감사 [standard ▾]
                                                                                                                                                                                                                        ZIP 다운로드(로컬 개발) / 바로 배포 → 설치
                                                                                                                                                                                          9    다운로드·배포        버튼                                                      SCR-D05
                                                                                                                                                                                                                        진행
      4 화면·DB·권한                          프런트 [x] 마운트 [iframe ▾] · DB [own ▾] 엔진 [sqlite,postgres] · 토폴로지 [T1][T3][T5] · egress [] · fs writable [/data]



      5 확인

      8
          agent: {key: inventory, type: app, domain: manufacturing}                                                      생성될 파일
          capabilities: [{verb: manage, domain: app.inventory}]                                                           agent.yaml · compose.yaml
          llm: {alias: plaza/chat, minContext: 8000}                                                                      be/ · fe/ · db/ · tests/
          governance: {grade: internal, audit: standard}                                                                  README.md




                                                                                                                                                           9
                                                                                                                                  ZIP 다운로드                          바로 배포 →




관련 요구사항(PRD): D4-01 D4-02


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                                                                39
시스템              AgentPlaza                                                 화면 ID                   SCR-D04                                                               화면 유형              모달
화면명              새 Agent 만들기 — ZIP 업로드                                      화면 경로                   /agents (모달 탭2)                                                       접근 권한              admin+
우선순위             P0                                                         PRD 추적                  D5-01 D5-02                                                           작성일 / 버전           2026-09-19 / v1.0

단일·다중 ZIP 을 업로드해 등록 파이프라인을 시작한다. 드래그&드롭 드롭존과 클라이언트 사전 검증(크기·확장자·agent.yaml 존재·v1 flat zip 감지)을 거쳐 파일별 직렬 업로드하고, 부분 성공을 한 화면에서 보여 준다.



                                                                                                                                                                     No   구성요소       유형           기능 설명 / 동작                             연계

                                                                                                                                                                                     dropzone(
                                                                                                                                                                                                  .zip ≤100MB ×10. 참조 구현 div onClick →
            ZIP 업로드 등록                                                                                                                                        ✕
                                                                                                                                                                     1    드롭존        button
                                                                                                                                                                                                  button·aria 보강
                                                                                                                                                                                                                                         D5-01
                                                                                                                                                                                     역할)

           1                                                                                                                                                         2    다른 소스      링크           Git URL · OCI ref · https zip 등록 모달    SCR-E05

                                                                ⬆ ZIP 을 끌어다 놓거나 클릭해 선택 (여러 개 가능)
                                                                                                                                                                                     목록+사전        크기·확장자·agent.yaml·flat zip 감지. 서버
                                                                                                                                                                     3    선택 파일 목록                                                       D5-02
                                                                                                                                                                                     검증           검증은 SCR-D05
                                                           agent.zip 규격 또는 v1 flat zip({Name}-app.py …) · .zip ≤100MB × 10

                                                                                                                                                                                                  force 덮어쓰기 / 런타임 container|
                                                                                                                                                                     4    옵션         체크·선택                                               D5-01
           2                                                                                                                                                                                      inprocess(서명 시만)
                다른 소스:                      Git URL                         OCI ref                       https zip              → SCR-E05

                                                                                                                                                                                     진행률
                                                                                                                                                                     5    진행                      직렬 업로드 · 개별 취소 가능(완료분 유지)              D5-02
            선택 파일 (3)                                                                                                                                                                (i/n)

           3                                                                                                                                                                         성공+경고        부분 성공 MSG-018. 성공 항목은 설치 진행
                                                                                                                                                                     6    결과 배너                                                          SCR-D05
               파일                                     크기                사전 검증(클라이언트)                                                                                                 동시           링크

                                                                                                                                                                                                  9유형 템플릿 zip 다운로드, 개발 가이드
               Board-1.2.0.zip                        2.1MB             ✓ agent.yaml v1 · 서명 ✓ · common                                                   ×          7    템플릿·가이드    접기                                                  D4-01
                                                                                                                                                                                                  마크다운

               Inventory.zip                          1.4MB             ⚠ v1 flat zip → 자동 변환 예정                                                          ×


               Legacy.zip                             9.8MB             ✗ agent.yaml 없음 · zip-slip 의심                                                     ×

           4                                                                                                                          inprocess 는 서명 시만
                     기존 동일 키 덮어쓰기(force)                                                     런타임: 컨테이너                       ▾


            ◌ 업로드 중 (2/3) Inventory.zip · 71%                                                                                                                 [취소]

           5

           6
                  ✓ 'Board' 등록 완료                                                               ⚠ 'Legacy.zip' 검증 실패
                  → 설치 진행(SCR-D05)                                                              사유 표시 · 부분 성공 MSG-018




           7
            ▸ 개발 템플릿 다운로드(9유형 zip)                                                             ▸ 개발 가이드(마크다운)                                       닫기




관련 요구사항(PRD): D5-01 D5-02


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                               40
시스템              AgentPlaza                                     화면 ID                  SCR-D05                                                                화면 유형              페이지
화면명              설치·등록 진행(8단계)                                  화면 경로                  /agents/{key}/install                                                  접근 권한              admin+
우선순위             P0                                             PRD 추적                 D5-02 D5-03 D5-04 D5-05 D5-06 D5-07                                    작성일 / 버전           2026-09-19 / v1.0

업로드→검증→서명→정책→빌드→등록→기동→노출 8단계 게이트의 진행과 실패 사유를 실시간(SSE)으로 보여 준다. 세 경로(스캐폴드·ZIP·원격 등록)가 모두 이 화면으로 수렴하며 백그라운드 전환이 가능하다.



                                                                                                                                                         No   구성요소         유형       기능 설명 / 동작                        연계
   ▣   AgentPlaza             🔍 검색 (⌘K)                              dev                                             🔔3    ko ▾       ☾             JD


    ▫ 대시보드                에이전트 관리 › board › 설치                                                                                                           1    백그라운드        버튼       이탈해도 잡 진행. 대시보드·알림 센터에서 복귀        SCR-B01
                                                                                                                                           1
    ▫ AI 어시스턴트
                          설치 진행 · board 1.2.0                                                      경과 01:42 · 잡 #a1f3                          백그라운드                       상태 목록    완료✓·진행◌·대기○·실패✗. 단계별 요약 + 상세
                                                                                                                                                         2    단계 목록                                                   D5-02
                                                                                                                                                                           (8)      펼치기(로그 스트림)
    ▫ 마켓플레이스             2
                                                                                                                                                              보안 게이트(3단             cosign 서명·SBOM·취약점. High 있으면 경고
                                  1 업로드·수집                   2.1MB · sha256 63873c…                                                                 ✓    3                 상태 행                                       D5-03
                                                                                                                                                              계)                    배지(설치는 진행)
    ▪ 에이전트 관리

                                  2 구조 검증                    agent.yaml OK · 경로 안전 · ruff 0 · SQL DDL 만                                             ✓
    ▫ 워크플로                                                                                                                                               4    빌드 진행(5단계)   진행률      이미지 빌드 진행률 + 로그 펼치기               D5-04
                                                            3
    ▫ 지식(RAG)                     3 서명·SBOM·취약점              cosign ✓ Wise · SBOM 142 · Critical 0 / High 2 ⚠ [보기]                                  ✓                               1~4 실패=거부(재업로드), 5~8 실패=롤백 후
                                                                                                                                                         5    실패 처리        경고+버튼                                      D5-05
                                                                                                                                                                                    재시도 가능
    ▫ 플레이그라운드
                                  4 라이선스·정책                  G1 MIT · egress[] fs[/data] · 정책 통과                                                    ✓
                                                                                                                                                                                    MSG-014. 에이전트 열기 / 대화로 사용 / MCP
                                                                                                                                                         6    완료 동작        버튼                                       SCR-D02 D06
    ▫ 거버넌스                                                                                                                        4                                                 설정
                                  5 빌드                       board-be 이미지 빌드 중… [로그 ▾]                                                             ◌

    ▫ LLM·모델                                                                                                                                             7    승인 대기        상태       supervisor 승인 필요 시 7단계 앞에서 대기 표시 D5-07
                                  6 등록                       레지스트리 반영 대기                                                                            ○
    ▫ 관측·운영

                                  7 기동·헬스                    컨테이너 기동 · /healthz 확인 대기                                                               ○
    ▫ 사용자·조직


    ▫ 설정                          8 노출                       라우트·네비·MCP·A2A 노출 대기                                                                   ○



    설치된 Addon
                         5
                              ✗ 실패 시 — 단계 · 사유 표시(MSG-007/008/009)
                              1~4 실패 = 거부(재업로드 필요) · 5~8 실패 = 롤백 후 재시도
    ▸ 게시판
                                                                                                                          재시도             로그       롤백

    ▸ HR 채용
                         6
                              ✓ 설치 완료 (MSG-014)
                              8단계 통과 · 노출 반영됨
                                                                                                        에이전트 열기           대화로 사용               MCP 설정



                         7대기 상태: admin 업로드 → supervisor 승인 필요 시 7단계 앞에서 '승인 대기' 표시 · 이탈해도 진행(대시보드·알림에서 복귀)
    [‹ 접기]




관련 요구사항(PRD): D5-02 D5-03 D5-04 D5-05 D5-06 D5-07


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                              41
시스템             AgentPlaza                                                   화면 ID             SCR-D06                                                      화면 유형            모달
화면명             MCP 노출 설정·가이드                                                화면 경로             /agents/{key}/mcp (모달)                                       접근 권한            admin+
우선순위            P0                                                           PRD 추적            D7-01 D7-02                                                  작성일 / 버전         2026-09-19 / v1.0

에이전트를 MCP 서버로 열고 클라이언트 접속 스니펫을 제공한다. 참조 구현의 포트 기반 설정을 경로 기반 기본값으로 바꾸고, 사양 버전 동시 광고·도구 목록 해시 핀닝·API 키 발급 연결을 추가했다.



                                                                                                                                                       No   구성요소        유형        기능 설명 / 동작                               연계


                                                                                                                                                                                  PUT /mcp {enabled}. 게이트웨이 라우트 갱신.
                                                                                                                                                       1    노출 토글·상태    토글+배지                                              D7-01
             MCP 노출 설정 · 게시판                                                                                                                    ✕
                                                                                                                                                                                  사양 2버전 동시 광고

                                                                                                                                                            엔드포인트·호환    읽기전용      경로 기반 기본. 포트 모드는 설정에서 켠 경우만
            1                                                                                                                                          2                                                      D7-01
                    MCP 서버 노출                                                                                                                               포트          +선택       (20000~59999)
                                                              켬                    ● 응답 OK       사양 2026-07-28 / 2025-11-25 동시 광고

             엔드포인트(경로 기반 기본값)                                                                                                                                                     API 키 발급(범위=이 에이전트) / OAuth CIMD
                                                                                                                                                       3    인증          링크                                                 SCR-K04
                                                                                                                                                                                  클라이언트 등록
            2
                https://plaza.local/mcp/board                                                                                             복사
                                                                                                                                                       4    노출 도구       체크 목록     capabilities 단위 허용. 정책 탭과 양방향 동기         SCR-D12
             (호환 모드) 전용 포트 [자동 ▾] 20000~59999 — 구클라이언트용, 기본 꺼짐
                                                                                                                                                                        코드 탭      Claude Desktop·Cursor·VS Code·curl. 키는
                                                                                                                                                       5    클라이언트 스니펫                                                      D7-02
            3                                                                                                                                                           +복사       자리표시자
                    인증                           API 키 발급 → SCR-K04                               OAuth(CIMD) 설정

                                                                                                                                                                        읽기전용      tools/list 결과 비교로 rug-pull 방어. 시험 결과
                                                                                                                                                       6    도구 해시·시험                                                       D7-02
                                                                                                                                                                        +버튼       표시
             노출 도구

            4                                                                                    허용목록 동기 → 정책 SCR-D12
                ✓     manage (app.board)                              (전체 선택)


             클라이언트 스니펫                                      Claude Desktop            Cursor        VS Code              curl


            5                                                                                                                                   [복사]
                    { "mcpServers": { "board": {
                        "url": "https://plaza.local/mcp/board",
                        "headers": { "Authorization": "Bearer <API_KEY>" } } } }




            6       도구 목록 해시 sha256:9c1f…7d20 (핀닝됨 2026-09-19)
                                                                                                                                tools/list 시험

             키는 자리표시자로만 삽입(실제 키 미노출) · 필수 내장 에이전트도 노출 가능



                                                                                                                   닫기                  저장




관련 요구사항(PRD): D7-01 D7-02


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                 42
시스템              AgentPlaza                                          화면 ID                        SCR-D07                                                               화면 유형               탭(에이전트 상세)
화면명              A2A 카드·프로토콜 표면                                      화면 경로                        /agents/{key}/protocols                                               접근 권한               admin+
우선순위             P1                                                  PRD 추적                       D7-03 D7-05 D7-06                                                     작성일 / 버전            2026-09-19 / v1.0

Agent Card·OpenAPI·AG-UI 노출 상태와 서명을 확인한다. v1 의 자체 A2A 라우터를 SDK 로 교체한 결과가 표면별 상태 행으로 표시되며, 모든 경로는 매니페스트에서 생성되어 손편집할 수 없다.



                                                                                                                                                                   No   구성요소           유형      기능 설명 / 동작                                    연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                                      dev                                        🔔3        ko ▾      ☾              JD


    ▫ 대시보드                에이전트 관리 › board                                                                                                                          1    탭              탭       에이전트 상세 7탭 중 프로토콜. URL 반영                     SCR-D02


    ▫ AI 어시스턴트
                          프로토콜 · board
                                                                                                                                                                   2    REST 표면        상태 행    /a/{key}/api · OpenAPI 문서 열기 · 상태 점           D7-05

    ▫ 마켓플레이스             1
                                  개요               설정                     프로토콜                         정책        버전·업데이트             로그·트레이스         가이드           3    MCP 표면         상태 행    /mcp/{key} · 사양 버전 · 설정 모달로 이동                SCR-D06
    ▪ 에이전트 관리
                         2
                                                                                                                                                                                       상태 행    agent-card.json · 버전 · JWS 서명 · skills · 카드
    ▫ 워크플로
                                     REST         /a/board/api                                                    OpenAPI [열기]                              ● OK   4    A2A 카드                                                               D7-03
                                                                                                                                                                                       +동작     보기 · 재서명

    ▫ 지식(RAG)            3
                                                                                                                                                                        AG-UI·OpenAI   상태 행    /api/agui spec 1.0 · /v1
                                     MCP          /mcp/board                                                      사양 2026-07-28                       ● OK → D06   5                                                                         D7-06
                                                                                                                                                                        호환             +토글     model=plaza/agent/{key} 토글
    ▫ 플레이그라운드
                         4                                                                                                                                                                     생성물 ↔ 런타임 일치 검사(NFR-P3). 마지막
                                                  /a/board/.well-known/agent-card.json                                           v1.0.1                서명 JWS ✓    6    일치 검사          버튼+결과                                                 D7-05
    ▫ 거버넌스
                                     A2A                                                                                                                                                       검사 시각 표시

                                                  skills: manage · streaming ✓ · push ✗ · protocolVersion 1.0                             카드 보기       재서명
    ▫ LLM·모델


    ▫ 관측·운영
                         5
                                     AG-UI        /a/board/api/agui                                               spec 1.0                                  ● OK
    ▫ 사용자·조직


    ▫ 설정                           OpenAI 호환
                                                  /v1   model=plaza/agent/board                                                             켬


    설치된 Addon
                         6
                              생성물 ↔ 런타임 일치 검사 (NFR-P3)
    ▸ 게시판
                              마지막 검사 2026-09-19 ✓ — 매니페스트 protocols.* 와 게이트웨이 라우트 일치
                                                                                                                                                  지금 검사
    ▸ HR 채용




                          모든 표면은 agent.yaml protocols.* 에서 생성된다 — 손편집 불가(DP4)




    [‹ 접기]




관련 요구사항(PRD): D7-03 D7-05 D7-06


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                                   43
시스템          AgentPlaza                                                     화면 ID     SCR-D08                                 화면 유형                 모달
화면명          추출(파생·Standalone 번들)                                           화면 경로     /agents/{key}/export (모달)               접근 권한                 admin+
우선순위         P0                                                             PRD 추적    D4-07                                   작성일 / 버전              2026-09-19 / v1.0

새 이름으로 파생 ZIP 을 만들거나, compose·Dockerfile 을 포함한 독립 구동(Standalone) 번들을 내보낸다. 참조 구현 ExportAgentModal 의 두 모드를 승계하고 포함 내용 미리보기를 추가했다.



                                                                                                                         No   구성요소            유형         기능 설명 / 동작                           연계


                                                                                                                                                         기본 선택. 출처(provenance.baseAgent) 자동
                      추출 · 게시판                                                                                       ✕
                                                                                                                         1    파생 ZIP          라디오
                                                                                                                                                         기록
                                                                                                                                                                                              D4-07


                   1                                                                                                     2    새 키·표시명         입력         키 규칙 검증. 중복 키 409 → 인라인 오류           D4-02
                               파생 ZIP — 새 이름으로 복제

                       새키                                          표시명 ko                     en
                                                                                                                                                         독립 구동(M1) agent.zip. 플랫폼 없이 실행
                                                                                                                         3    Standalone 번들   라디오                                             D4-07
                                                                                                                                                         가능
                       2
                           board-hr                                  게시판(인사)                   Board HR                       포트·이미지·포함                  포트 1024~65535, 이미지명, compose
                                                                                                                         4                    입력·체크                                           D4-07
                                                                                                                              옵션                         포함 / 이미지 tar(대용량 경고)
                       provenance.baseAgent 자동 기록 · 중복 키 409 인라인 오류

                                                                                                                         5    포함 내용 미리보기 트리              생성될 파일 트리와 PROVENANCE.json 표시        D4-07
                   3

                               Standalone 번들 — 독립 구동(M1) agent.zip                                                                                       POST /export {mode,…} → zip(또는 잡).
                                                                                                                         6    추출              버튼                                              D4-07
                                                                                                                                                         대용량은 알림 후 링크
                       포트 1024~65535                           이미지명

                       4
                           8001                                   plaza/agent-board


                           ✓   compose·Dockerfile·.env 포함                             이미지 tar(대용량 경고)




                       포함 내용 미리보기

                   5
                       agent.zip
                        ├ agent.yaml · compose.yaml · .env.example · Dockerfile
                        ├ be/ · fe/ · db/
                        └ PROVENANCE.json (baseAgent: board@1.2.0)




                                                                                                          6
                                                                                              취소              추출 ▾




관련 요구사항(PRD): D4-07


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                  44
시스템          AgentPlaza                                              화면 ID                SCR-D09                                      화면 유형           모달
화면명          Worker·설치 가이드                                           화면 경로                /agents/{key}/guide (모달)                     접근 권한           로그인
우선순위         P1                                                      PRD 추적               D4-05 D8-01                                  작성일 / 버전        2026-09-19 / v1.0

에이전트별 설치·워커 실행 가이드를 마크다운으로 렌더한다. 워커 유형(bundled/external/none)에 따라 패키지 다운로드와 명령 스니펫을 제공하고, 해시로 무결성을 확인하게 한다.



                                                                                                                                  No   구성요소       유형        기능 설명 / 동작                               연계


                                                                                                                                                            bundled | external | none. none 이면 가이드
                                                                                                                                  1    워커 유형      배지                                                 D8-01
                                                                                                                                                            본문만 표시
                  설치 가이드 · vasca-cve                                                                                          ✕
                                                                                                                                  2    언어         토글        ko | en. 기본값은 UI 언어                      D1-06
                                         1                                                              2
                  워커 유형                                     external — 별도 호스트 설치                         언어 ko | en

                                                                                                                                  3    패키지 다운로드   버튼+해시     워커 .tar.gz 다운로드, sha256·용량 병기            D8-01
                  3
                                                                             sha256 7f3a…c19 · 12.4MB
                              워커 패키지 다운로드 .tar.gz
                                                                                                                                                            README/guide.md 렌더. 사전 요구·설치·등록·
                                                                                                                                  4    가이드 본문     마크다운                                               D4-05
                                                                                                                                                            확인 4단계
                  4
                      vasca-cve 워커 설치                                                                                             5    코드 블록      코드+복사     설치·등록 명령. 복사 버튼 제공                       D4-05

                      1. 사전 요구 Docker 24+ · 2 vCPU / 4GB · outbound 443 허용
                      2. 설치   패키지 해제 후 ./install.sh 실행
                      3. 등록   발급된 워커 토큰으로 POST /api/workers/enroll
                      4. 확인   에이전트 상세 › 런타임에서 워커 ● healthy




                                                                                                                           [복사]

                      5
                          $ tar xzf vasca-cve-worker.tar.gz
                          $ ./install.sh --plaza-url https://plaza.local \
                                --token wk_01J8…K2Q9
                          $ systemctl status vasca-worker




                  bundled 워커는 이 모달 대신 런타임 탭에서 관리 · none 이면 가이드 본문만 노출




                                                                                                                      닫기




관련 요구사항(PRD): D4-05 D8-01


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                         45
시스템          AgentPlaza                                              화면 ID           SCR-D10                         화면 유형           모달(확인 다이얼로그)
화면명          삭제·해제 확인                                                화면 경로           (확인 다이얼로그)                      접근 권한           admin+
우선순위         P0                                                      PRD 추적          D5-05 D5-06                     작성일 / 버전        2026-09-19 / v1.0

설치 흔적(테이블·화면·MCP·라우트) 제거 범위를 고지하고 키 재입력으로 확인받는다. 참조 구현의 '해제 즉시 실행(확인 없음)' 을 교정해 파괴적 작업 앞에 확인 단계를 둔다.



                                                                                                                No   구성요소       유형      기능 설명 / 동작                                연계


                                                                                                                                        컨테이너·라우트·MCP·메뉴·도구·A2A 카드·
                                                                                                                1    제거 범위 고지   경고 목록                                             D5-05
                                                                                                                                        테이블·배포 산출물


                          ⚠ 게시판(board) 해제                                                                   ✕
                                                                                                                2    데이터 삭제     체크박스    기본 off. 체크 시 '되돌릴 수 없음' 경고 강조             D5-05


                                                                                                                3    백업         체크박스    기본 on. 백업 잡을 선행 실행한 뒤 해제                  D5-05
                          다음이 제거됩니다


                          1                                                                                                             에이전트 키 정확 일치. 불일치 시 해제 버튼
                                                                                                                4    키 재입력      입력                                                D5-06
                                  · 컨테이너 3 · 라우트 /a/board · MCP /mcp/board                                                              disabled
                                  · 좌측 메뉴 항목 · 어시스턴트 도구 · A2A 카드
                                  · 설치 테이블 DROP · 배포 tsx 삭제 · web 재빌드
                                                                                                                                버튼(위    DELETE /api/agents/{key}?purge=&backup=
                                                                                                                5    해제                                                           D5-06
                                                                                                                                험)      → 진행 토스트 → MSG-015




                          2
                                   데이터 볼륨·DB 스키마도 삭제
                                   되돌릴 수 없습니다


                          3
                              ✓    백업 후 진행 (백업 잡 선행)


                          확인하려면 키를 정확히 입력

                          4
                                                                              불일치 시 [해제] 비활성
                              board


                          60초 내 완료 목표(NFR-I6) · 완료 시 MSG-015

                                                                                                   5
                                                                                       취소              해제




관련 요구사항(PRD): D5-05 D5-06


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                      46
시스템                   AgentPlaza                                                      화면 ID                     SCR-D11                                                              화면 유형             위저드(5단계)
화면명                   원격 에이전트 등록(연동·연계)                                               화면 경로                     /agents/link                                                         접근 권한             admin+
우선순위                  P0                                                              PRD 추적                    D6-04 D7-02 D7-04                                                    작성일 / 버전          2026-09-19 / v1.0

A2A Agent Card URL 또는 MCP 서버 URL 을 등록해 코드 설치 없이 편입한다(경로 C). 카드 미리보기·인증·계약 시험·분류/정책 4단계를 통과하면 설치 6~8단계(등록·기동·노출)만 수행한다.



                                                                                                                                                                                No   구성요소       유형        기능 설명 / 동작                                    연계

      원격 에이전트 등록(연동·연계)                                                                                                                                                     ✕                             5단계. 실패 단계에 사유 표시, 이전 단계 복귀
                                                                                                                                                                                1    단계         stepper                                                 -
                                                                                                                                                                                                          가능

      1                                                                                                                                                                                         라디오       A2A 카드 URL / MCP 서버 URL(전송 방식
          1         유형·주소                         2       인증                            3       계약 시험                     4      분류·정책                  5        확인             2    유형·주소                                                              D7-04
                                                                                                                                                                                                +URL      선택). https 필수

                                  2                                                                                                                                                                       name·version·skills·protocolVersion·서명·발급자.
      1 유형·주소                             A2A Agent Card URL                            https://invoice.acme.com/.well-known/agent-card.json                      불러오기          3    카드 미리보기    KV                                                      D7-03
                                                                                                                                                                                                          1.0 아니면 경고

                                                                                                                                                                                                선택+       API Key / OAuth(CIMD). 키는 시크릿 저장소
                                          MCP 서버 URL                                    https://mcp.acme.com/http                              streamable-http          ▾       4    인증                                                                 D7-02
                                                                                                                                                                                                시크릿       참조로 보관

      3
              카드 미리보기 name: Invoice Matcher · version 1.2.0 · skills 2 · protocol Version 1.0 · 서명 ✓ 발급자 acme                                                                                   체크리스      스키마·JWS 서명·agent-scan·tools/list 해시
                                                                                                                                                                                5    계약 시험                                                              D6-04
              protocolVersion 이 1.0 이 아니면 경고(v0.3 비호환) · https 필수, http 는 허용 시 경고                                                                                                               트         핀닝

                                                                                                                                                                                                          카테고리·업무·egress allowlist·데이터 등급 상한·
                                                                                                                                                                                6    분류·정책      선택 ×N                                                   D9-02
                                                                                                                                                                                                          승인 필요
                              4
      2 인증                                                                                                             또는 OAuth 클라이언트 등록(CIMD)
                                  API Key                  ▾               •••••••• 시크릿 저장
                                                                                                                                                                                7    등록         버튼        POST /api/agents/link → 설치 6~8단계 진행           SCR-D05

                                      5   스키마 검증                                JWS 서명                              agent-scan 위험 0              tools/list 3개(해시 핀닝)
      3 계약 시험


      실패 항목은 사유와 함께 적색 표시 · [재시험] 으로 해당 항목만 다시 실행



      4 분류·정책

      6
              카테고리 [logistics-customs ▾] 업무 [W16 ▾] 신뢰 등급 external(고정) egress allowlist [acme.com ×] [+]
              데이터 등급 상한 [internal ▾] 승인 필요 [x] (외부 전송)




      5 확인                      요약 확인 후 등록 → 설치 6~8단계(등록·기동·노출) 진행

                                                                                                                                                  7
                                                                                                                                      이전                         등록




관련 요구사항(PRD): D6-04 D7-02 D7-04


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                                              47
시스템             AgentPlaza                                   화면 ID                    SCR-D12                                                                        화면 유형            탭(에이전트 상세)
화면명             도구 정책·권한                                     화면 경로                    /agents/{key}/policy                                                           접근 권한            admin+
우선순위            P1                                           PRD 추적                   D9-02 D9-05                                                                    작성일 / 버전         2026-09-19 / v1.0

허용·거부 도구와 데이터 등급·승인 필요 여부를 지정한다. deny 가 allow 보다 우선하는 매트릭스로 도구 단위 정책을 잡고, 역할·그룹·egress allowlist 까지 한 화면에서 관리한다.



                                                                                                                                                                No   구성요소        유형      기능 설명 / 동작                             연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                            dev                                         🔔3          ko ▾        ☾                    JD


   ▫ 대시보드                에이전트 관리 › board                                                                                                                        1    탭           탭       에이전트 상세 7탭 중 정책                        SCR-D02


   ▫ AI 어시스턴트
                         정책 · board                                                                                                                                              매트릭스    capabilities × (허용·거부·승인 필요). 승인 필요
                                                                                                                                                                2    도구 정책 표                                                    D9-02
                                                                                                                                                                                 체크      = HITL 리뷰
   ▫ 마켓플레이스             1
                                    개요           설정            프로토콜                       정책            버전·업데이트             로그·트레이스               가이드                                    매니페스트 governance 보다 낮출 수 없음. 초과
                                                                                                                                                                3    상향만 허용 안내   안내                                      D9-05
                                                                                                                                                                                         시 MSG-009
   ▪ 에이전트 관리

                         도구 정책                                                                                                                                                           거부 > 허용. 변경 즉시 게이트웨이 반영 + 감사
   ▫ 워크플로                                                                                                                                                       4    우선순위 규칙     규칙                                             D9-02
                                                                                                                                                                                         기록
                        2                                                                                                        3
                            도구(capability)               허용             거부            승인 필요             비고                           상향만 허용
   ▫ 지식(RAG)                                                                                                                         매니페스트 governance 보다                                 internal/confidential 등 등급, 감사 수준
                                                                                                                                                                5    데이터 등급·감사   선택                                             D9-05
                                                                                                                                     낮은 값으로 내릴 수 없다.                                     standard/verbose
   ▫ 플레이그라운드                manage (list)                ✓                                              조회

                                                                                                                                                                6    허용 역할·그룹    다중 선택   역할 + 조직 그룹. 설치 시 배치값이 기본               SCR-K02
                                                                                                                                     정책 상한 초과 시
   ▫ 거버넌스                                                                                                                            MSG-009 오류
                            manage (create)              ✓                                              -


   ▫ LLM·모델                                                                                                                                                     7    egress      태그 입력   host:port allowlist. 정책 상한 초과 시 오류     D9-05
                            manage (delete)              ✓                            ✓                 HITL 리뷰

   ▫ 관측·운영                                                                                                                                                                               PUT /api/agents/{key}/policy → 게이트웨이
                                                                                                                                                                8    저장          버튼                                             D9-02
                            export (csv)                                ✓                               데이터 반출                                                                           반영 + 감사
   ▫ 사용자·조직
                        4
                                  거부가 허용보다 우선 · 변경은 즉시 게이트웨이에 반영되고 감사 로그에 기록

   ▫ 설정
                         데이터 등급                               감사 수준

                        5
   설치된 Addon
                             internal              ▾           standard                        ▾

   ▸ 게시판
                        6
                                  사용 허용 역할·그룹                                user ▾             인사팀 ×             영업팀 ×                   +
   ▸ HR 채용


                        7
                                  네트워크 egress                                   api.acme.com:443 ×                 +




                                                                                                                                              8
                                                                                                                           초기화                    저장
   [‹ 접기]




관련 요구사항(PRD): D9-02 D9-05


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                      48
시스템             AgentPlaza                                              화면 ID                  SCR-D13                                                                         화면 유형             페이지
화면명             capability·라우팅 인덱스                                      화면 경로                  /agents/capabilities                                                            접근 권한             admin+
우선순위            P1                                                      PRD 추적                 D2-02 D5-06                                                                     작성일 / 버전          2026-09-19 / v1.0

verb·domain 인덱스와 오케스트레이터 라우팅 대상을 점검한다. 중복 verb.domain 을 경고로 드러내고, 문장을 넣어 의도 분류·대상 선택 결과를 dry-run 으로 확인할 수 있다.



                                                                                                                                                                          No   구성요소        유형       기능 설명 / 동작                              연계
  ▣   AgentPlaza              🔍 검색 (⌘K)                                      dev                                         🔔3        ko ▾        ☾                     JD


   ▫ 대시보드                에이전트 관리 › capability 인덱스                                                                                                                         1    검색          입력       verb.domain 부분 일치 검색. 정렬 가능             D2-02
                                                                                                         1
   ▫ AI 어시스턴트
                         capability·라우팅 인덱스                                                                  🔍 verb.domain 검색                             라우팅 시험                           데이터      verb·domain·에이전트·우선순위 P·상태·마지막
                                                                                                                                                                          2    인덱스 표                                                        D2-02
                                                                                                                                                                                           그리드      호출
   ▫ 마켓플레이스
                                                                                                                                                                                                    동일 verb.domain 중복 시 경고 행. P 값으로
                                                                                                                                                                          3    우선순위·중복 경고 상태 열                                              D2-02
                                                                                                                                                                                                    선택 결정
   ▪ 에이전트 관리
                        2                                                                            3
                            verb                   domain                          에이전트                      P         상태                          마지막 호출                 4    페이징         목록       … 외 N건. 50건/쪽                           D5-06
   ▫ 워크플로

                            manage                 app.board                       board                     1         ● 활성                        2분 전
   ▫ 지식(RAG)                                                                                                                                                                                        문장 입력 → POST /api/orchestrator/route-
                                                                                                                                                                          5    라우팅 시험 입력   입력+버튼                                            D2-02
                                                                                                                                                                                                    test {text}
                            retrieve               rag.docs                        ragagent                  1         ● 활성                        -
   ▫ 플레이그라운드
                                                                                                                                                                                                    의도·대상·점수·우선순위·폴백 사유
                                                                                                                                                                          6    시험 결과·근거    결과 패널                                            SCR-C01
   ▫ 거버넌스
                            query                  security.cve                    vasca-cve                 2         ○ 비활성                       -                                                (registry_miss 등)

                            manage                 app.board                       board-hr                  2         ⚠ 중복 verb.domain            -
   ▫ LLM·모델
                        4… 외 38건 · 정렬·검색 · 중복 verb.domain 은 경고 행으로 강조(우선순위 P 로 결정)
   ▫ 관측·운영


   ▫ 사용자·조직
                                라우팅 시험

   ▫ 설정                       5
                                                                                                                                                           dry-run
                                    이번 달 CVE 알려줘                                                                                          시험
   설치된 Addon
                              6
                                       의도 query.security.cve → 대상 vasca-cve (비활성 → registry_miss)
   ▸ 게시판                               근거: verb 매칭 0.91 · domain 매칭 0.88 · 우선순위 P2 · 폴백 = 어시스턴트 일반 응답


   ▸ HR 채용




                         출처: tbl_addon_agent_capabilities + registry_dynamic_routing · 오케스트레이터가 이 인덱스로 대상을 선택한다




   [‹ 접기]




관련 요구사항(PRD): D2-02 D5-06


AgentPlaza 화면설계서 · v1.0 · D. 에이전트 관리                                                                                                                                                                                                                  49
시스템             AgentPlaza                                                   화면 ID                      SCR-E01                                                                              화면 유형             페이지
화면명             마켓 홈(카탈로그)                                                   화면 경로                      /market                                                                              접근 권한             로그인
우선순위            P0                                                           PRD 추적                     D6-01                                                                                작성일 / 버전          2026-09-19 / v1.0

검색·3축 파셋 필터·정렬·서버 페이징으로 에이전트 자산을 탐색한다. 4층 카드(아이콘·이름·버전 / 게시자·평점 / 3축·태그 / 통계·신뢰 배지)를 그리드로 보이고, 비교 트레이와 원격 레지스트리 편입 섹션을 함께 제공한다.



                                                                                                                                                                                        No   구성요소       유형        기능 설명 / 동작                                   연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                            dev                                               🔔3       ko ▾           ☾                     JD

                                                                                                                                                                                                                  자산 등록(E06)·직접 설치(E05)·설치됨(E11).
   ▫ 대시보드                마켓플레이스                                                                                                                                                         1    헤더 동작      버튼                                                     SCR-E05 SCR-E06
                                                                                                                                                                                                                  admin+ 만 렌더
                                                                                                                    1
   ▫ AI 어시스턴트
                         마켓플레이스                                                                                               자산 등록              직접 설치 ▾                     설치됨                                  q≤100, 300ms 디바운스(IME 무시).
                                                                                                                                                                                        2    검색·정렬·보기   입력·선택                                                  D6-01
                                                                                                                                                                                                                  sort=installs|rating|updated…
   ▪ 마켓플레이스             2
                             🔍 이름·키·설명·태그 (⌘K)                                                정렬: 설치수 ↓            ▾            보기: 카드   ▾
                                                                                                                                                                                        3    파셋 필터      선택·칩
                                                                                                                                                                                                                  업무·업종·도메인·유형·게시자·토폴로지 다중
                                                                                                                                                                                                                                                               SCR-E02
                                                                                                                                                                                                                  선택. URL ?q=&sort= 동기화
   ▫ 에이전트 관리
                        3
                         업무 W ▾ · 업종 ▾ · 도메인 ▾ · 유형(app/service) ▾ · 게시자 ▾ · 토폴로지 ▾
                                                                                                                                                                                                                  featured 최대 6건. supervisor 가 지정(E07),
   ▫ 워크플로                                                                                                                                                                               4    추천 밴드      캐러셀                                                    SCR-E07
                                 Featured                        Validated                서명됨             무료                 도입됨만                                                                                 없으면 섹션 숨김

   ▫ 지식(RAG)             적용 필터: common × T3 × [초기화]                                                                                                                                                               신뢰 배지 official/partner/community/external·
                                                                                                                                                                                        5    자산 카드      카드(4층)                                                 SCR-E03
                        4                                                                                                                                                                                         등급·서명·설치수. 클릭→E03
   ▫ 플레이그라운드                 ★ 추천(Featured) 밴드 — 카드 3개 가로 스크롤 ‹ › (supervisor 지정, 없으면 숨김)
                                                                                                                                                                                                        텍스트·
                                                                                                                                                                                        6    결과 수·페이징             서버 페이징. page_size 20|50|100, total 표기        D6-01
   ▫ 거버넌스
                                                                                                                                                                                                        페이저
                        5
                                           게시판                                                      송장 대조                                               채용 스크리닝
   ▫ LLM·모델                     ◈                                                         ◈                                                  ◈                                          7    비교 트레이     트레이       2~4개 담으면 하단 고정 노출 → 비교(E09)                  SCR-E09
                                           v1.2.0 · common·W19                                      v2.0.0 · logistics·W16                              v1.0.0 · hr·W11

   ▫ 관측·운영                   게시글·댓글 관리 담당                                               전표-거래 대조 ⚠High                                   이력서 1차 선별                                                      섹션(점      연결 시만. 체크섬 검증 후 편입, 409 는
                                                                                                                                                                                        8    원격 레지스트리                                                          SCR-E13
                                                                                                                                                                                                        선)        덮어쓰기 확인
                                     official            ↓ 1.2k · 도입됨                         partner                   ↓ 88 · 무료                   community              ↓ 340 · 구독
   ▫ 사용자·조직


   ▫ 설정                                    지식 검색                                                    보안 점검                                               재고 관리
                                ◈                                                         ◈                                                  ◈
                                           v3.1.0 · common·W04                                      v1.4.0 · security·W07                               v1.0.0 · mfg·W16
   설치된 Addon
                             사내 RAG 질의응답                                                취약점·공급망 점검                                       자재 소요 산출
   ▸ 게시판
                                     official          ↓ 2.4k · 업데이트                           external                 ↓ 52 · 무료                   community               ↓ 17 · 무료

   ▸ HR 채용
                        6
                         Showing 1-20 of 143      ‹ 1 2 3 … 8 ›              페이지당 [20 ▾] (서버 페이징)

                        7
                             비교 트레이 [게시판 ×] [송장 대조 ×] (2/4)                                                                                             [비교하기] [비우기]


                        8
                             원격 레지스트리 acme-registry 3건 — 체크섬 검증 후 로컬 카탈로그 편입 [다운로드·편입]
   [‹ 접기]




관련 요구사항(PRD): D6-01


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                                        50
시스템             AgentPlaza                               화면 ID    SCR-E02                                                               화면 유형            페이지
화면명             카테고리 브라우즈(3축)                            화면 경로    /market/categories                                                    접근 권한            로그인
우선순위            P0                                       PRD 추적   D6-01                                                                 작성일 / 버전         2026-09-19 / v1.0

업무(W01~W19)·업종(KSIC)·도메인(10) 3축과 계층 트리로 카탈로그를 좁힌다. 노드를 고르면 우측에 E01 카드 그리드를 재사용해 결과를 보여 주고, 하위 포함·미분류·비어있는 카테고리 표시를 제어한다.



                                                                                                                                   No   구성요소        유형       기능 설명 / 동작                           연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                      dev                              🔔3          ko ▾   ☾             JD

                                                                                                                                                             include_empty 로 빈 카테고리 표시. 관리는
   ▫ 대시보드                마켓플레이스 › 카테고리                                                                                             1    전체 보기·관리    선택·버튼                                         D6-01
                                                                                                                                                             supervisor(CRUD·정렬)
                                                                                                  1
   ▫ AI 어시스턴트
                         카테고리 브라우즈(3축)                                                                    전체 보기 ▾         관리                                 업종 트리 / 업무 W01~W19 / 도메인 10.
                                                                                                                                   2    축 전환        탭                                             SCR-E01
                                                                                                                                                             URL ?axis= 동기화
   ▪ 마켓플레이스
                        2
                                  업종 트리            업무 W01~W19     도메인 10                                                                                     루트=업종, 2단=업무. 접기·자산 수 표시,
                                                                                                                                   3    계층 트리       트리                                            D6-01
                                                                                                                                                             루트는 하위 합산(중복 1회)
   ▫ 에이전트 관리
                        3
                                                                   선택: 공통 유틸(common-utility) · 11건                                                  카드(E01   선택 노드 필터로 조회. [목록에서 보기] →
   ▫ 워크플로                     ▾ 전업종 (41)                                                                                           4    결과 그리드                                                    SCR-E01
                                                                                                                                                    재사용)     필터가 걸린 E01
                                                                   4
   ▫ 지식(RAG)                      · 대화·어시스턴트 (4)
                                                                                 ◈                       ◈            ◈                             체크박스·    include_descendants 기본 on. 미분류 자산은
                                                                                                                                   5    하위 포함·미분류                                                 SCR-E06
                                                                                                                                                    링크       별도 링크로 진입
                                  · 지식·RAG (6)
   ▫ 플레이그라운드                                                                   게시판                    사용자             셸

                                                                                app                      app        service
                                  · 공통 유틸 (11) ◀
   ▫ 거버넌스

                              ▾ 정보통신 J (52)
   ▫ LLM·모델                                                                      ◈                       ◈            ◈

                                  · 보안운영 (18)
   ▫ 관측·운영                                                                    지식 검색                    알림           스케줄

                                                                                app                   service       service
                                  · 취약점·공급망 (9)
   ▫ 사용자·조직

                              ▸ 제조 C (70)                          … 외 5건        [E01 목록에서 이 필터로 보기 ›]
   ▫ 설정
                                                                   5
                              ▸ 운수·창고 H (24)                           ✓     하위 카테고리 포함(include_descendants)
   설치된 Addon
                              ▸ 전문·과학 M (31)                       미분류 (4) [보기] — 카테고리 미지정 자산
   ▸ 게시판
                              ▸ 공공행정 O (18)
                                                                           slug 체계(17.4)를 시드로 전량 등록.
   ▸ HR 채용                                                                 업로드 시 미존재 slug 는 자동 생성(경고).
                              … 외 6개 업종                                    루트 카운트는 하위 합산(중복 1회).




   [‹ 접기]




관련 요구사항(PRD): D6-01


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                         51
시스템              AgentPlaza                                               화면 ID                 SCR-E03                                                                                   화면 유형                페이지
화면명              자산 상세                                                    화면 경로                 /market/{key}                                                                             접근 권한                로그인
우선순위             P0                                                       PRD 추적                D6-01 D5-03 D5-04                                                                         작성일 / 버전             2026-09-19 / v1.0

매니페스트·capabilities·버전 이력·README·스크린샷·스캔 결과·리뷰를 한 페이지 7개 탭에서 본다. 신뢰 배지(official/partner/community/external)와 등급·서명 상태를 상단에 고정하고, 설치 경로 3가지(도입 위저드·직접 설치·CLI)를 제시한다.



                                                                                                                                                                                     No   구성요소          유형        기능 설명 / 동작                                연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                                            dev                                        🔔3           ko ▾           ☾                 JD

                                                                                                                                                                                                                  official/partner/community/external +
    ▫ 대시보드                마켓플레이스 › 게시판                                                                                                                                               1    신뢰·운영 배지      배지                                                  D5-04
                                                                                                                                                                                                                  Featured·Validated·서명·등급 G1~G5
                                                                                                                            2
    ▫ AI 어시스턴트
                          게시판 (board) v1.2.0                                                                                           설치                      비교 +              ⋯                                설치(admin+, 도입됨이면 열기·업데이트)·비교
                                                                                                                                                                                     2    헤더 동작         버튼·메뉴                                               SCR-E04
                                                                                                                                                                                                                  담기·⋯(신고·공유·매니페스트 원문)
                         1
    ▪ 마켓플레이스                       official                   Featured                    Validated                  서명 ✓ Wise                    G1               ★ 4.6 (12)
                                                                                                                                                                                     3    역할 한 줄        텍스트       manifest role. 유형·3축 분류 병기                D5-03
                         3
    ▫ 에이전트 관리             역할: 게시글·댓글 관리 담당 · app · common · W19 · 전업종

                         4
    ▫ 워크플로                                                                                                                                                                           4    스크린샷          갤러리       최대 5장. 없으면 아이콘 크게 표시                      D6-01
                              ◀               스크린샷 1                          스크린샷 2                          스크린샷 3                                                             ▶
    ▫ 지식(RAG)                                                                                                                                                                                                     개요·기능·버전·변경·권한·보안·호환성·리뷰
                                                                                                                                                                                     5    탭7            탭                                                   SCR-E08
                                                                                                                                                                                                                  (E08)·의존성. URL ?tab=
    ▫ 플레이그라운드
                         5
                                  개요                     기능                       버전·변경               권한·보안              호환성                       리뷰                 의존성
                                                                                                                                                                                                                  요구 권한·스캔(Critical/High)·토폴로지·RAM·
                                                                                                                                                                                     6    요약 패널         패널 3                                                D5-04
    ▫ 거버넌스
                                                                                                                                                                                                                  코어·의존 에이전트
                                                                                                                 6
                              개요 — README 렌더(markdown)                                                                 권한·보안
    ▫ LLM·모델                                                                                                                                                                         7    설치 명령         코드·복사     plaza install oci://… CLI 경로 복사           D6-01
                                                                                                                       요구 권한 db.read · db.write · network egress
                              게시판 에이전트는 조직 내 공지·게시글·댓글을                                                                스캔 Critical 0 · High 2 ⚠ · SBOM 첨부
                              관리합니다. 목록·작성·검색·첨부를 지원하며
    ▫ 관측·운영                   권한은 조직 역할을 따릅니다. …                                                                                                                                                        텍스트·      free|subscription|per_seat|per_call. 결제
                                                                                                                                                                                     8    가격                                                                SCR-E12
                                                                                                                       호환성
                                                                                                                                                                                                        버튼        정산은 범위 밖, 라이선스까지
    ▫ 사용자·조직
                                                                                                                       토폴로지 T1 T3 T5 · GPU none                                                                   A 마켓 도입(E04) · B 직접 설치(E05) · C CLI.
                                                                                                                       최소 RAM 2GB · 코어 ≥ 2.0.0                                       9    설치 경로 A/B/C   버튼                                                  SCR-E05
    ▫ 설정                          board                cms               collab                                                                                                                                   함께 설치는 의존성 사전 포함

                              게시자 Wise ✓ (인증) · 다른 자산 12개                                                              의존성
    설치된 Addon                 예시 프롬프트 3 · 데이터 소스 2 · capabilities 1
                                                                                                                       requires.agents → hrcore(승인·미도입)
                                                                                                                       [함께 설치] → E04 에 사전 포함
    ▸ 게시판


    ▸ HR 채용              7                                                                                                               8
                              $ plaza install oci://reg.plaza.local/agents/board:1.2.0           [복사]                                        가격 무료
                                                                                                                                             (유료면 [구매] → E12)



                                                9
                          설치 경로
                                                         A 도입 위저드                           B 직접 설치                             C CLI 설치

    [‹ 접기]




관련 요구사항(PRD): D6-01 D5-03 D5-04


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                                   52
시스템                      AgentPlaza                                              화면 ID                 SCR-E04                                                                         화면 유형             위저드
화면명                      설치(도입=배치) 위저드                                           화면 경로                 /market/{key}/adopt                                                             접근 권한             admin+
우선순위                     P0                                                      PRD 추적                D6-02 D6-05 D9-02                                                               작성일 / 버전          2026-09-19 / v1.0

권한 동의 → 배치 대상(조직/그룹/개인) → 도구 정책 → 버전 고정·호환성 확인 → 라이선스 → 확인의 6단계로 자산을 도입(=배치)한다. 권한을 전부 동의해야 진행되고, 호환성 경고는 차단하지 않으며 중복 설치는 교체 확인을 받는다.



                                                                                                                                                                                  No   구성요소       유형        기능 설명 / 동작                               연계

          게시판 도입(설치 = 배치)                                                                                                                                                     ✕   1    단계 표시      스텝퍼       6단계. 서버 422/409 는 해당 단계로 복귀              D6-02


      1                                                                                                                                                                                                     permissions[] 전부 체크 필수. 하나라도
                                                                                                                                                                                  2    권한 동의      체크박스                                               D9-02
                                                                                                                                                                                                            미체크면 다음 비활성
          1           권한 동의               2       배치 대상                 3       도구 정책                  4        버전·호환             5    라이선스                    6         확인

                                                                                                                                                                                                            데이터 등급·감사 수준 고지. 미서명이면 격리
                                                                                                                                                                                  3    거버넌스·서명    배지                                                 D9-02
                                                                                                                                                                                                            고지 + 확인 체크(MSG-008)
              1 권한 동의 — 전부 체크해야 다음 단계 활성(422 방지)

              2                                                                                                                       3                                                           라디오·      org|group|user. user 역할은 개인만. 네비
                  ✓                           ✓                                                                                                  등급 internal           서명 ✓       4    배치 범위·네비                                                      SCR-D02
                        db.read                    db.write                           network egress api.acme.com                                                                                 선택        그룹은 매니페스트 기본값

                                                                                                                                                                                                            허용/거부/승인 필요. 거부 우선, 승인 필요는
                                                                                                                                                                                  5    도구 정책      매트릭스                                               SCR-I04
              2 배치 대상 — deploy_scope                                                                                                                                                                        HITL 승인함으로

              4
                        조직 전체                             그룹            ▾                 개인(user 역할은 개인만)                                                         ▾
                                                                                                                                                                                                            승인된 버전만. 기본 최신, pinned_version 으로
                                                                       인사팀                                                                 네비 그룹: 경영지원                            6    버전 고정      선택                                                 D6-02
                                                                                                                                                                                                            저장

              3 도구 정책 — 거부 우선, '승인 필요' 는 HITL(I04)로                                                                                                                                               체크리스      토폴로지·GPU·RAM·코어 검사. 불일치는 경고
                                                                                                                                                                                  7    호환성                                                           D6-02
              5                                                                                                                                                                                   트         (차단 아님) 확인 후 진행
                  도구(capability)                                   허용                    거부                 승인 필요
                                                                                                                                 기본값 전부 허용.
                  manage(list)                                     ●                     ○                  ○                    변경은 감사 대상.
                  manage(delete)                                   ●                     ○                  ●                                                                     8    라이선스       입력·검증     유료만 노출. 오프라인 검증 실패 시 진행 불가               SCR-E12

              4 버전 고정 · 호환성 확인                                                                                                                                                                              POST /api/market/adoptions → 설치 잡(SCR-
                                                                                                                 7
                                                                                                                                                                                  9    요약·설치      요약·버튼                                              SCR-D05
              6                                                                                                                                                                                             D05). 409 는 교체 확인
                                                    T1 ✓ T3 ✓ · GPU none ✓ · RAM 2GB ✓ · 코어 2.0.0 ✓                  ⚠ 토폴로지 T2 미지원 — 경고(차단 아님), 확인 후 진행
                   1.2.0 (승인됨) 고정     ▾




              5 라이선스 — 유료 자산만(무료는 자동 통과)
              8
                                                                                                  좌석 5 · 만료 2027-09 · 검증 실패 시 진행 불가 (E12 와 동일)
                   AP-7F3A-9C21-…                                                검증


              6 확인
                                                                                                                                                   9
              게시판 1.2.0 · 조직 전체 · 경영지원 · 권한 2 · 정책 1건 변경
                                                                                                                                      이전                       설치
              409 중복 → '1.1.0 이 설치되어 있습니다 [1.2.0 으로 교체] [취소]'




관련 요구사항(PRD): D6-02 D6-05 D9-02


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                            53
시스템          AgentPlaza                                             화면 ID                 SCR-E05                                          화면 유형            모달
화면명          직접 설치(Zip·Git·OCI·URL)                                 화면 경로                 /market/install-direct                           접근 권한            admin+
우선순위         P0                                                     PRD 추적                D6-03                                            작성일 / 버전         2026-09-19 / v1.0

마켓 카탈로그를 거치지 않고 로컬 ZIP·Git 저장소·OCI 아티팩트·https ZIP 에서 자산을 가져온다. 매니페스트를 먼저 파싱해 키·버전·서명 여부를 미리 보이고, 이후 설치 진행은 SCR-D05 1단계로 이어진다.



                                                                                                                                      No   구성요소       유형         기능 설명 / 동작                                   연계


                                                                                                                                                                 ZIP / Git / OCI / https ZIP 4종. 선택에 따라
                                                                                                                                      1    소스 유형      라디오                                                     D6-03
                                                                                                                                                                 입력 필드 전환
                  직접 설치 (마켓 경유 없음)                                                                                                ✕
                                                                                                                                                                 agent.yaml 포함 ZIP ≤100MB. SCR-D04
                                                                                                                                      2    ZIP 드롭존    드롭존                                                     SCR-D04
                                                                                                                                                                 드롭존 재사용
                  소스 유형
                                                                                                                                                                 URL·서브경로·ref(태그/커밋). ref 없으면 기본
               1
                                                                                                                                      3    Git 입력     입력                                                      D6-03
                                                                                                                                                                 브랜치 HEAD
                       ZIP 파일                        Git 저장소                        OCI 아티팩트                  https ZIP

               2                                                                                                                                                 레지스트리 ref + digest. digest 없으면 태그
                                                                                                                                      4    OCI 입력     입력                                                      SCR-E13
                                                                                                                                                                 이동 경고
                                                          agent.yaml 을 포함한 ZIP 을 끌어다 놓기 (≤100MB)
                                                                                                                                                                 https 만 허용 + sha256 체크섬(권장, 없으면
                                                                                                                                      5    URL 입력     입력                                                      D6-03
                                                                            파일 선택                                                                                경고)

                                                                                                                                                                 매니페스트 파싱 결과. 미서명은 community
                                                                                                                                      6    미리보기       요약(KV)                                                  D5-03
                  Git URL                                                         경로                          ref(태그·커밋)                                         등급·격리 고지

               3
                                                                                                                                                                 POST /api/agents/install-direct {source} →
                   https://github.com/acme/agents.git                               invoice                     v1.2.0                7    가져오기       버튼                                                      SCR-D05
                                                                                                                                                                 설치 잡 D05 1단계


                  OCI ref                                                                                     digest

               4
                   reg.plaza.local/agents/invoice:1.2.0                                                         sha256:9f3c…



                  https ZIP URL                                                                               sha256

               5
                   https://cdn.acme.com/invoice-1.2.0.zip                                                       1d4b…


               6
                    미리보기 agent.yaml 감지 ✓ · key invoice · v1.2.0 · 서명 ✗ → community 등급으로 격리 설치




                                                                                                                       7
                                                                                                       취소                  가져오기




관련 요구사항(PRD): D6-03


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                     54
시스템                 AgentPlaza                                                      화면 ID               SCR-E06                                                                    화면 유형               위저드
화면명                 자산 등록(게시)                                                       화면 경로               /market/publish                                                            접근 권한               admin+·퍼블리셔
우선순위                P1                                                              PRD 추적              D6-06 D4-06                                                                작성일 / 버전            2026-09-19 / v1.0

ZIP 패키지(다중)·카탈로그 메타·3축 카테고리·서명을 붙여 카탈로그에 게시한다. 각 ZIP 의 agent.yaml 을 읽어 키·버전을 자동 채우고, 자동 검사(스키마·정적검사·취약점·라이선스)를 통과해야 게시된다.



                                                                                                                                                                              No   구성요소         유형        기능 설명 / 동작                          연계


        자산 등록(게시)                                                                                                                                                         ✕   1    패키지 첨부
                                                                                                                                                                                                드롭존       .zip ≤100MB. agent.yaml 파싱 실패 시 항목별
                                                                                                                                                                                                                                              D4-06
                                                                                                                                                                                                (다중)      오류 표시


                                                                                                                                                                              2    파싱 결과        목록        키·버전 자동 채움. v1 flat 구조는 변환 경고       D5-03
              1        패키지                                    2        카탈로그 정보                            3      심사·서명                                      4    확인
                                                                                                                                                                                                폼(다국      표시명 ko/en·역할 한 줄·태그 ≤10(^[a-z0-
                                                                                                                                                                              3    카탈로그 정보                                                    D6-06
                                                                                                                                                                                                어)        9-]{1,30}$)
          1 패키지 — ZIP 다중 첨부, 각 파일의 agent.yaml 로 키·버전·이름 자동 채움

          1                                                                                    2                                                                                                          3축 slug 다중, 미존재 slug 자동 생성(경고).
                                                                                                                                                                              4    분류·가격·라이선스   선택                                            SCR-E02
                                                                                                   Board-1.2.0.zip → board 1.2.0 ✓                                                                        SPDX 라이선스
                                   ZIP 을 끌어다 놓기 (다중, ≤100MB)
                                                                                                   Inventory.zip → inventory 1.0.0 ⚠ v1 flat 구조                                                 라디오·      keyless(OIDC) 또는 키 파일. 공개 마켓은 서명
                                                                                                                                                                              5    서명                                                         D6-06
                                               파일 선택                                                                                                                                            파일        필수

                                                                                                                                                                                                체크리스      스키마·정적검사·취약점·라이선스 등급. Critical
          2 카탈로그 정보 — 여러 ZIP 이면 항목별 아코디언 폼                                                                                                                                    6    자동 검사·심사                                                   SCR-E07
                                                                                                                                                                                                트         있으면 게시 불가
           표시명 ko / en                                                 역할 한 줄                                           태그 ≤10 (a-z0-9-)
                                                                                                                                                                                                          supervisor 즉시 승인 / admin 대기. 409 중복은
          3                                                                                                                                                                   7    확인·게시        요약·버튼                                          SCR-E11
                                                                                                                                                                                                          덮어쓰기 확인
                  게시판 / Board                                           게시글·댓글 관리 담당                                      board, cms, collab


          4
                  분류: common-utility 외 2        ▾                 가격: free      ▾           라이선스: MIT     ▾               게시자 Wise(자동) · 스크린샷 3




          3 심사 · 서명

          5                                                                                             심사: supervisor → 즉시 승인 / admin → 대기
                     keyless 서명(OIDC)                              키 파일 업로드
          6                                                                                                                                    Critical 1건 → 게시 불가
                   스키마 ✓               정적검사 ✓                      취약점 High 1 ⚠                    라이선스 G1 ✓



          4 확인
                                                                                                                                                        7
          board 1.2.0 · common-utility 외 2 · free · MIT · 서명 keyless
                                                                                                                                         이전                          게시
          중복 키@버전 → '이미 등록된 자산입니다' 확인(덮어쓰기 / 취소, 파랑 톤)




관련 요구사항(PRD): D6-06 D4-06


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                      55
시스템             AgentPlaza                                             화면 ID                    SCR-E07                                                              화면 유형            페이지
화면명             퍼블리셔 관리                                                화면 경로                    /market/publishers                                                   접근 권한            supervisor
우선순위            P1                                                     PRD 추적                   D6-06                                                                작성일 / 버전         2026-09-19 / v1.0

게시자 프로필·인증 배지·설치 통계·서명키를 관리하고, 자산의 운영 배지(Featured·Validated)와 심사 대기 자산의 승인·거부를 처리한다. 서명키는 공개키만 등록하며 철회하면 해당 자산이 미검증으로 강등된다.



                                                                                                                                                                No   구성요소       유형        기능 설명 / 동작                            연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                        dev                                       🔔3      ko ▾         ☾             JD

                                                                                                                                                                                          이름·slug 검색. 게시자는 게시 시 자동 생성될 수
   ▫ 대시보드                마켓플레이스 › 퍼블리셔                                                                                                                          1    검색         입력                                       SCR-E06
                                                                                                                                                                                          있음

   ▫ AI 어시스턴트
                         퍼블리셔 관리                                                                                                                  + 퍼블리셔                                  인증 여부·자산 수·설치·다운로드·서명키 상태.
                                                                                                                                                                2    게시자 목록     그리드                                             D6-06
                                                                                                                                                                                          정렬 지원
   ▪ 마켓플레이스             1
                             🔍 이름·slug 검색                                                                                                                       3    상세 드로어     드로어
                                                                                                                                                                                          프로필·URL·통계·자산 목록. can_edit 인 계정만
                                                                                                                                                                                                                                D6-06
                                                                                                                                                                                          편집
   ▫ 에이전트 관리
                        2                                                                                     3
                            이름                   slug          인증      자산           설치           서명키              Wise · 상세 드로어                                                           공개키 등록·회전·철회. 철회 시 자산 '미검증'
   ▫ 워크플로                                                                                                                                                       4    서명키        버튼                                              D5-04
                                                                                                                                                                                          강등
                                                                                                                  프로필 https://wise.example.com
                            Wise                 wise          ✓       12           3,204        cosign 활성        연락 market@wise.example.com
   ▫ 지식(RAG)                                                                                                      자산 12 · 설치 3,204 · 다운로드 8,910                                           Featured(기간)·Validated(근거 ref) 지정 →
                                                                                                                                                                5    운영 배지      폼                                               SCR-E01
                                                                                                                  평균 평점 ★4.5 · 신고 0건                                                      E01 카드·E03 상단 반영
                            ACME                 acme          -       3            88           (없음)
   ▫ 플레이그라운드
                                                                                                                                                                                          admin 이 올린 자산 승인·거부(사유 필수).
                            Hanul                hanul         ✓       5            412          cosign 활성                                                      6    심사 대기      목록                                              SCR-E06
   ▫ 거버넌스
                                                                                                                                                                                          게시자에게 알림

                         … 외 5개 게시자          정렬 [자산 수 ▾]   supervisor 만 편집
                                                                                                                  4
   ▫ LLM·모델                                                                                                       서명키

                        5                                                                                         cosign:3f1c…9a2b (활성, 2027-03 만료)
   ▫ 관측·운영                    운영 배지 지정                                                                            공개키만 등록 — 개인키는 서버에 저장하지 않음


   ▫ 사용자·조직
                                                           ▾
                                   Featured: 게시판 ~2026-12-31            Validated: 근거 test/impl/3rd   ▾

                                                                                                                         등록             회전            철회
   ▫ 설정                       지정 이력은 감사 로그에 남고 카드 배지로 즉시 반영



   설치된 Addon            6                                                                                             ⚠ 키 철회 시 해당 게시자의 자산은 '미검증' 으로 강등되고 카드
                              심사 대기 자산 2건 (supervisor)                                                                배지가 사라진다.

   ▸ 게시판
                              inventory 1.0.0 · ACME
                                                                                    승인                거부
   ▸ HR 채용                                                                                                        자산 목록 12건 [보기 ›]
                                                                                                                  인증(verify) 처리 → 카드에 ✓ 배지
                              screening 1.1.0 · Hanul
                                                                                    승인                거부




   [‹ 접기]




관련 요구사항(PRD): D6-06


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                       56
시스템             AgentPlaza                                        화면 ID              SCR-E08                                                                    화면 유형            탭
화면명             리뷰·평점                                             화면 경로              /market/{key} (탭)                                                          접근 권한            도입자
우선순위            P1                                                PRD 추적             D6-01                                                                      작성일 / 버전         2026-09-19 / v1.0

자산 상세(E03)의 리뷰 탭. 평점 분포와 리뷰 목록을 보이고 활성 도입자만 작성할 수 있다. 업보트·게시자 답글·supervisor 숨김을 지원하며 평점 변경은 카탈로그 카드에 즉시 반영된다.



                                                                                                                                                           No   구성요소       유형        기능 설명 / 동작                               연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                dev                                     🔔3     ko ▾        ☾                  JD


   ▫ 대시보드                마켓플레이스 › 게시판 › 리뷰                                                                                                                 1    탭 위치       탭         E03 의 6번째 탭. URL ?tab=reviews            SCR-E03


   ▫ AI 어시스턴트
                         리뷰·평점
                                                                                                                                                           2    평점 분포      막대        ★5~★1 분포와 건수. 평균·리뷰 수·도입 조직 수 D6-01

   ▪ 마켓플레이스
                        1
                                   개요              기능               버전·변경              권한·보안               호환성              리뷰                의존성
                                                                                                                                                                           평점·
                                                                                                                                                           3    작성 폼                 1~5점, 코멘트 ≤1,000자, 버전 자동 기록              D6-01
                                                                                                                                                                           텍스트
   ▫ 에이전트 관리
                        2                                                               3
                                                                                            리뷰 쓰기 (활성 도입자만)                                                                          활성 도입자만. 조직 도입=조직당 1건, 개인=
   ▫ 워크플로                     ★ 4.6            12개 리뷰 · 도입 조직 9
                                                                                                                                                           4    등록         버튼
                                                                                                                                                                                     사용자당 1건
                                                                                                                                                                                                                              SCR-E04
                                                                                            평점 ★★★★☆
   ▫ 지식(RAG)
                              5★                                            8                                                                              5    리뷰 카드      카드        업보트 토글·게시자 답글·본인 수정/삭제·신고                D6-01
                              4★                                            3                 코멘트 (≤1,000자) — 응답 정확도 양호
   ▫ 플레이그라운드
                              3★                                            1                                                                                                        supervisor 가 사유와 함께 숨김. include_hidden
                                                                                                                                                           6    숨김         버튼                                                 SCR-E07
   ▫ 거버넌스
                                                                                                                                                                                     으로 조회 가능
                              2★                                            0                                                         4
                                                                                            버전 v1.2.0 자동 기록
                                                                                                                                             등록
                              1★                                            0
   ▫ LLM·모델


   ▫ 관측·운영              5
                             ★★★★☆ 홍길동 (인사팀) · v1.2.0 · 2주 사용                                                                               👍2
   ▫ 사용자·조직                  "응답 정확도 양호. 첨부 처리도 안정적입니다."
                             ↳ 게시자 답글(Wise): 1.3.0 에서 검색 정확도를 개선했습니다.

   ▫ 설정
                                                                                                                                     [답글] [수정] [삭제] [신고]


   설치된 Addon
                        6
                             ★★★☆☆ 김철수 (총무팀) · v1.1.0 · 1개월 사용                                                                              숨김
   ▸ 게시판
                             "첨부 용량 제한이 아쉽습니다." (숨김 처리됨 — 사유: 중복 게시)
   ▸ HR 채용




                         조직 도입 = 조직당 1건 · 개인 도입 = 사용자당 1건 · supervisor 는 [숨김] + 사유(include_hidden 으로 조회)


                         평점 변경 시 rating_avg·분포 즉시 재계산 → E01 카드·E03 상단 배지에 반영
   [‹ 접기]




관련 요구사항(PRD): D6-01


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                     57
시스템              AgentPlaza                              화면 ID                SCR-E09                                               화면 유형             모달
화면명              비교(Compare)                             화면 경로                /market/compare                                       접근 권한             로그인
우선순위             P2                                      PRD 추적               D6-01                                                 작성일 / 버전          2026-09-19 / v1.0

E01 비교 트레이에 담은 자산 2~4개를 항목별로 나란히 비교한다. 유형·도메인·평점·설치·토폴로지·권한·등급·서명·가격·capabilities 를 행으로 두고 값이 다른 행을 강조해 선택을 돕는다.



                                                                                                                               No   구성요소       유형          기능 설명 / 동작                     연계


                                                                                                                                                           2~4개. 트레이(E01)에서 담거나 상세(E03)
                                                                                                                               1    비교 대상      안내                                         SCR-E01
                                                                                                                                                           에서 [비교 +]
           자산 비교 (3)                                                                                                       ✕
                                                                                                                                               표(열=        유형·도메인/평점·설치/토폴로지/권한/등급·
                                                                                                                               2    비교 표                                                  D6-01
                                                                                                                                               자산)         서명/가격·capabilities
           1
           최대 4개까지 나란히 비교 · 값이 다른 행은 '(차이)' 로 강조
                                                                                                                                                           값이 다른 행에 '(차이)' 표기 — 색만으로
                                                                                                                               3    차이 강조      표시                                         D6-01
           2                                                                                                                                               구분하지 않음
               항목                   게시판 1.2.0                    게시판Pro 2.0                     송장 대조 2.0
                                                                                                                                                           각 열에서 바로 도입 위저드(E04) 진입. 유료면
                                                                                                                               4    열별 설치      버튼                                         SCR-E04
                                                                                        3                                                                  E12 선행
               유형 · 도메인             app · common                 app · common                   service · logistics (차이)
                                                                                                                                                           카탈로그에서 추가, 열 × 로 제거. 2개 미만이면
                                                                                                                               5    추가·제거      링크                                       SCR-E03
                                                                                                                                                           모달 닫힘
               평점 · 설치              ★4.6 · 1.2k                  ★4.2 · 340                     ★4.1 · 88



               토폴로지                 T1 T3 T5                     T1 T2 T5 (차이)                  T2 T5 (차이)



               권한                   db.r/w                       db.r/w · egress (차이)           egress (차이)



               등급 · 서명              G1 ✓                         G1 ✓                           G1 ✗ (차이)



               가격 · capabilities    무료 · 1                       구독 · 3 (차이)                    무료 · 2



                                     4
                                                   설치                              설치                                설치


           5
           자산 추가 [+ 카탈로그에서 선택]     각 열 × 로 제거 · 2개 미만이면 비교 닫힘




                                                                                   닫기               선택 자산 모두 설치




관련 요구사항(PRD): D6-01


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                 58
시스템             AgentPlaza                                                     화면 ID                SCR-E10                                                                      화면 유형            페이지
화면명             컬렉션(업종 스타터 팩)                                                  화면 경로                /market/collections                                                          접근 권한            로그인
우선순위            P1                                                             PRD 추적               D6-02 D6-01                                                                  작성일 / 버전         2026-09-19 / v1.0

업종별 스타터 팩(자산 묶음)을 정의된 설치 순서대로 일괄 도입한다. 팩마다 대상 업종·항목 수·토폴로지·도입 현황을 보이고, 일괄 도입은 E04 를 축약한 3단계 위저드로 처리하며 이미 도입된 항목은 건너뛴다.



                                                                                                                                                                            No   구성요소       유형       기능 설명 / 동작                              연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                                  dev                               🔔3            ko ▾       ☾                   JD

                                                                                                                                                                                                     이름·대상 업종·항목 수·토폴로지 배지.
   ▫ 대시보드                마켓플레이스 › 컬렉션                                                                                                                                       1    팩 카드       카드                                               D6-01
                                                                                                                                                                                                     supervisor 가 컬렉션 생성

   ▫ AI 어시스턴트
                         컬렉션(업종 스타터 팩)                                                                                                                        + 컬렉션                                  의존 관계를 반영한 고정 순서. 도입된 항목은
                                                                                                                                                                            2    설치 순서      순서 칩                                             D6-02
                                                                                                                                                                                                     강조 표시
   ▪ 마켓플레이스             1
                              pack-hr HR 팩                                                업종 M 인사                 5개 자산              T1 T3 T5
                                                                                                                                                                            3    도입 현황      진행 막대    도입됨 n/m. 부분 도입 상태에서 재실행 가능              D6-02
   ▫ 에이전트 관리                 2
                                        1 hrcore            ›            2 jobposting         ›     3 screening      ›    4 interview          ›       5 onboarding
                                                                                                                                                                                                     위저드 진입. 유료 항목이 있으면 해당 항목만
   ▫ 워크플로                                                                                                                                                                   4    일괄 도입      버튼                                               SCR-E12
                                                                                                                                                                                                     라이선스 단계
                             3                                                                                            4
                              도입됨 2/5
   ▫ 지식(RAG)                                                                                                                         일괄 도입 →                      상세                                 배치 범위 → 항목별 권한 동의(묶음) →
                                                                                                                                                                            5    위저드 3단계    스텝퍼                                              SCR-E04
                                                                                                                                                                                                     순서대로 설치
   ▫ 플레이그라운드
                                                                                                                                                                                                     adopted/already_adopted/failed 집계. 부분
                                                                                                                                                                            6    결과 요약      요약                                               SCR-D05
   ▫ 거버넌스                     pack-haccp 식품 HACCP 팩                                                                                                                                                  실패는 MSG-018

                              1 haccp-core › 2 ccp-monitor › 3 audit-report · 도입됨 0/3
   ▫ LLM·모델
                                                                                                                                     일괄 도입 →                      상세


   ▫ 관측·운영
                         … 외 6개 팩 (v2 17.7 스타터 팩 8종)

   ▫ 사용자·조직

                              일괄 도입 위저드 (E04 축약)
   ▫ 설정
                                  5
                                       1        배치 범위                                         2   권한 동의(묶음)                      3       순서대로 설치
   설치된 Addon


   ▸ 게시판                      권한 동의는 항목별로 묶어 한 번에 표시 · 이미 도입된 항목은 건너뜀(already_adopted)

                              설치는 팩에 정의된 순서대로 순차 실행 — 각 항목의 진행은 SCR-D05 잡으로 연결
   ▸ HR 채용

                        6
                              결과 요약

                              3 adopted · 2 already_adopted · 0 failed   부분 실패 시 MSG-018 + 실패 항목만 재시도



   [‹ 접기]




관련 요구사항(PRD): D6-02 D6-01


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                    59
시스템             AgentPlaza                                                   화면 ID                   SCR-E11                                                                          화면 유형            페이지
화면명             설치됨·업데이트 관리                                                  화면 경로                   /market/installed                                                                접근 권한            admin+
우선순위            P0                                                           PRD 추적                  D6-07 D8-06                                                                      작성일 / 버전         2026-09-19 / v1.0

설치된 자산의 버전·배치 범위·상태를 한 표에서 관리한다. 업데이트는 변경 로그와 권한 변화를 보이고 권한이 늘면 재동의를 강제하며, 롤백은 백업이 있는 버전으로만 되돌린다. 해제는 확인 절차(D10)를 거친다.



                                                                                                                                                                                 No   구성요소       유형       기능 설명 / 동작                        연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                                dev                                    🔔3            ko ▾        ☾                    JD

                                                                                                                                                                                                          상태 필터 + '업데이트 있음만'. 모두 업데이트
   ▫ 대시보드                마켓플레이스 › 설치됨                                                                                                                                            1    검색·필터      입력·선택                                      D6-07
                                                                                                                                                                                                          확인은 일괄 점검

   ▫ AI 어시스턴트
                         설치됨 · 업데이트 관리 (12)                                                                                                            모두 업데이트 확인                                         설치/최신 버전·배치 범위·활성 여부·설치자·일
                                                                                                                                                                                 2    설치 목록      그리드                                        D6-07
                                                                                                                                                                                                          시. 업데이트 배지
   ▪ 마켓플레이스             1
                             🔍 자산 검색                                                  상태: 전체          ▾               ✓   업데이트 있음만
                                                                                                                                                                                 3    업데이트
                                                                                                                                                                                                 다이얼로     변경 로그·권한 변화 재동의·백업 선행 → 설치
                                                                                                                                                                                                                                            D8-06
                                                                                                                                                                                                 그        잡(D05)
   ▫ 에이전트 관리
                        2
                            자산                         설치                 최신                   배치              상태            설치자·일시                        동작                                    다이얼로     이전 버전 목록(백업 유무). 이미지 다이제스트
   ▫ 워크플로                                                                                                                                                                        4    롤백                                                    D8-06
                                                                                                                                                                                                 그        좌표로 복원

   ▫ 지식(RAG)
                            게시판                        1.2.0              1.3.0   🔔            조직              ● 활성          admin 09-10                   업데이트 · 해제

                                                                                                                                                                                 5    심사 대기      목록       supervisor 가 admin 게시 자산을 승인·거부   SCR-E07
                            송장 대조                      2.0.0              2.0.0                인사팀             ○ 비활성         admin 09-12                   활성 · 해제
   ▫ 플레이그라운드
                                                                                                                                                                                                          즉시 실행 금지 — SCR-D10 확인(MSG-015,
                            지식 검색                      3.1.0              3.1.0                조직              ● 활성          sysop 08-30                   롤백 · 해제               6    해제         버튼                                         SCR-D10
   ▫ 거버넌스
                                                                                                                                                                                                          데이터 보존 선택)

                         … 외 9건      정렬 [설치일 ▾]        pinned_version 고정 자산은      🔒 표시
   ▫ LLM·모델
                        3                                                                                  4
   ▫ 관측·운영                    업데이트 다이얼로그                                                                        롤백

                              변경 로그 1.3.0 — 검색 정확도 개선, 첨부 50MB                                                  1.2.0              현재 · 09-10
   ▫ 사용자·조직                   권한 변화 + network egress (신규)
                              백업 설치 전 자동 스냅샷 생성
                                                                                                                1.1.0              백업 있음 · 08-22                       롤백
   ▫ 설정

                                                                                                                1.0.0              백업 없음 · 07-15
                                 ⚠ 권한이 늘면 재동의 필수 — 미동의 시 업데이트 불가
   설치된 Addon

                                                                                                                이미지 다이제스트 좌표로 되돌림 → 진행은 SCR-D05
   ▸ 게시판                                                                              업데이트

   ▸ HR 채용
                        5
                              심사 대기 (supervisor) 2건 — admin 이 게시한 자산

                              inventory 1.0.0 · ACME   screening 1.1.0 · Hanul
                                                                                                                            승인                    거부

                             6해제(uninstall)는 즉시 실행하지 않고 SCR-D10 확인 절차를 거친다(MSG-015, 데이터 보존 선택)

   [‹ 접기]




관련 요구사항(PRD): D6-07 D8-06


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                   60
시스템          AgentPlaza                                   화면 ID       SCR-E12                                    화면 유형            위저드(모달)
화면명          구매·라이선스                                      화면 경로       /market/{key}/purchase                     접근 권한            admin+
우선순위         P1                                           PRD 추적      D6-05                                      작성일 / 버전         2026-09-19 / v1.0

유료 자산의 라이선스 키를 발급·검증하고 좌석·만료를 확인한다. 키는 Ed25519 서명 토큰으로 네트워크 없이 오프라인 검증하며, 적용하면 도입 위저드(E04)의 라이선스 단계로 되돌아가 설치를 이어간다.



                                                                                                            No   구성요소       유형       기능 설명 / 동작                                 연계


                                                                                                                                     free|subscription|per_seat|per_call 표시만.
                                                                                                            1    가격         텍스트                                                 SCR-E03
                                                                                                                                     결제 정산은 범위 밖
                  라이선스 · 게시판Pro                                                                         ✕                            키 직접 입력 / 결제로 발급(결제 어댑터 미연결
                                                                                                            2    발급 방식      라디오                                                 D6-05
                                                                                                                                     시 비활성)
                  1
                      가격 구독 ₩50,000 / 월 · 좌석 기반 (표시만 — 결제 정산은 범위 밖)                                                                  base64url 본문 + 서명. 형식 오류는 인라인
                                                                                                            3    키 입력·검증    입력·버튼                                               D6-05
                                                                                                                                     표시

                                                                                                                            체크리스     대상·버전 범위·좌석·만료·호스트 바인딩.
                                                                                                            4    검증 결과                                                          D6-05
                                                                                                                            트        오프라인 공개키 검증
                  발급 방식

                  2                                                                                         5    증적         다운로드     영수증·라이선스 증적 파일. 감사 보관                      SCR-M04
                        라이선스 키 직접 입력

                        결제로 발급 (연결된 결제 어댑터가 있을 때만 활성)                                                                                POST /api/licenses {key, listing} → E04
                                                                                                            6    적용         버튼                                                  SCR-E04
                                                                                                                                     라이선스 단계 통과
                  3
                      AP-7F3A-9C21-8D55-…                                            검증


                  4
                      검증 결과 (Ed25519 오프라인 공개키 검증)

                           대상 자산 board-pro 일치

                           버전 범위 >= 2.0.0, < 3.0.0

                           좌석 5 (현재 배정 3)

                           만료 2027-09-01

                           호스트 바인딩 *.acme.local

                      네트워크 없이 검증 · 실패 항목은 적색 + 사유(만료·좌석 초과·대상 불일치)



                  5
                  영수증 · 라이선스 증적 [다운로드] (감사 증적으로 보관)
                                                                                               6
                                                                                취소                 적용




관련 요구사항(PRD): D6-05


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                       61
시스템             AgentPlaza                                                         화면 ID               SCR-E13                                                                             화면 유형            페이지
화면명             원격 레지스트리 연결                                                        화면 경로               /settings/registries                                                                접근 권한            supervisor
우선순위            P1                                                                 PRD 추적              D6-07                                                                               작성일 / 버전         2026-09-19 / v1.0

사설·공개 마켓 서버(plaza-host·OCI·MCP·git-json)를 등록해 카탈로그를 동기화하고, 이 서버를 호스트로 공개하거나 폐쇄망용 오프라인 번들을 주고받는다. 편입은 체크섬 검증을 통과한 항목만 허용한다.



                                                                                                                                                                                      No   구성요소       유형        기능 설명 / 동작                         연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                                      dev                                     🔔3             ko ▾         ☾                JD


   ▫ 대시보드                설정 › 레지스트리                                                                                                                                                   1    레지스트리 추가   버튼        supervisor 만. 추가 후 연결 시험 자동 수행     D6-07
                                                                                                                                                              1
   ▫ AI 어시스턴트
                         원격 레지스트리 연결                                                                                                                                  + 레지스트리                                   유형·상태·마지막 동기화. 인증 실패는 ◐ +
                                                                                                                                                                                      2    레지스트리 목록   그리드                                          SCR-E01
                                                                                                                                                                                                                재인증 동작
   ▫ 마켓플레이스             2
                            이름                             URL                                        유형                  상태                   마지막 동기화                동작                                        이름·유형·URL(https)·인증 토큰 시크릿·자동
                                                                                                                                                                                      3    추가 폼       폼                                            D6-07
                                                                                                                                                                                                                동기화 주기
   ▫ 에이전트 관리
                            공개 AgentPlaza                  reg.agentplaza.io                          plaza-host          ● OK                 1시간 전                  동기화 · 편집
                                                                                                                                                                                                                공개 카탈로그 API 활성화 → 외부 인스턴스가
   ▫ 워크플로                                                                                                                                                                             4    호스트 공개     토글·URL                                       D6-07
                                                                                                                                                                                                                편입 가능
                            사내 미러                          zot.internal                               oci                 ● OK                 -                      편집

   ▫ 지식(RAG)                                                                                                                                                                                                    폐쇄망용 .tar 번들 가져오기·내보내기. 체크섬
                            MCP 공식                         registry.modelcontextprotocol.io           mcp                 ● OK                 어제                     동기화             5    오프라인 번들    버튼                                           D6-03
                                                                                                                                                                                                                검증 필수
   ▫ 플레이그라운드
                            ACME                           reg.acme.com                               git-json            ◐ 인증 실패              3일 전                   재인증
                                                                                                                                                                                                                증분(updated_since)·체크섬 불일치 거부·409
                                                                                                                                                                                      6    동기화 규칙     규칙                                           SCR-E01
   ▫ 거버넌스
                                                                                                                                                                                                                덮어쓰기 확인

                        3                                                                                          4
   ▫ LLM·모델                   레지스트리 추가 폼                                                                               이 서버를 호스트로 공개
                              이름                                          유형


   ▫ 관측·운영                                                                                                                         공개 카탈로그 API 사용
                                 사내 미러                                         plaza-host         ▾
                                                                                                                       https://plaza.acme.local/market/catalog [복사]
   ▫ 사용자·조직                   URL (https 만 허용)



   ▪ 설정                          https://zot.internal/v2                                                           5
                                                                                                                       오프라인 번들(폐쇄망)
                              인증(토큰 시크릿)                                  자동 동기화
   설치된 Addon                                                                                                           번들 파일(.tar) 가져오기 → 체크섬 검증 후
                                                                                                                       로컬 카탈로그 편입. 내보내기도 동일 형식.
                                 vault:reg-token           ▾                   6시간마다              ▾
   ▸ 게시판
                                                                                                                               번들 가져오기
   ▸ HR 채용

                        6
                              동기화 규칙

                              증분 동기화(updated_since) · 체크섬 불일치 항목은 편입 거부 · 409 중복 키는 덮어쓰기 확인(파랑 톤)
                              연결 시험 실패는 MSG-016/017, 인증 실패 레지스트리는 카탈로그 섹션에서 숨김 + 조용한 경고



   [‹ 접기]




관련 요구사항(PRD): D6-07


AgentPlaza 화면설계서 · v1.0 · E. 마켓플레이스                                                                                                                                                                                                                          62
시스템             AgentPlaza                                            화면 ID                  SCR-F01                                                                           화면 유형                  페이지
화면명             워크플로 목록                                               화면 경로                  /workflow                                                                         접근 권한                  admin+·빌더
우선순위            P1                                                    PRD 추적                 D2-03 X01                                                                         작성일 / 버전               2026-09-19 / v1.0

워크플로를 생성·복제·활성화하고 최근 실행 상태를 본다. 이름 검색과 상태·트리거 필터로 걸러 보며 기본 정렬은 updated desc 이다. 활성 토글은 즉시 PATCH 하고 실패 시 이전 값으로 롤백한다.



                                                                                                                                                                          No   구성요소         유형           기능 설명 / 동작                               연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                      dev                                       🔔3         ko ▾        ☾                  JD

                                                                                                                                                                                            input +      이름 검색, 상태·트리거 유형 필터. 정렬·페이징
   ▫ 대시보드                워크플로                                                                                                                                             1    검색·필터                                                              D2-03
                                                                                                                                                                                            select       지원
                                                                                                                     2
   ▫ AI 어시스턴트
                         워크플로                                                                                                 + 새 워크플로                  DSL 반입                 새 워크플로·DSL
                                                                                                                                                                          2                 button       빈 워크플로 생성 → 빌더 / 외부 DSL 반입 모달            SCR-F02 SCR-F05
                                                                                                                                                                               반입
                        1
   ▫ 마켓플레이스
                             🔍 이름 검색                                              상태 전체       ▾                트리거 전체     ▾                             정렬 updated desc
                                                                                                                                                                                                         이름·트리거·노드 수·활성·최근 실행·성공률·동작
                                                                                                                                                                          3    목록 그리드       grid                                                  X01
                                                                                                                                                                                                         열
   ▫ 에이전트 관리
                        3
                                                                                                                                                                                                         PATCH /api/workflows/{id} {enabled} 즉시
   ▪ 워크플로                   이름                             트리거               노드        활성         최근 실행                   성공률           동작                                4    활성 토글        toggle                                                D2-03
                                                                                                                                                                                                         반영, 실패 시 롤백
                                                                                      4           5                                     6
   ▫ 지식(RAG)                신규 입사 온보딩                      webhook           6         ON         09-19 14:02 ✓           98%           열기·실행·복제·⋯                                          상태 +         성공/실패 아이콘과 시각. 성공률 낮으면 적색
                                                                                                                                                                          5    최근 실행·성공률                                                          SCR-F03
                                                                                                                                                                                            수치           강조
   ▫ 플레이그라운드
                            일일 CVE 리포트                     schedule          4         ON         09-19 06:00 ✓           100%          열기·실행·복제·⋯                                          buttons +    열기→빌더 / 실행→즉시 run / 복제 / ⋯(트리거
                                                                                                                                                                          6    행 동작                                                     SCR-F04
   ▫ 거버넌스
                                                                                                                                                                                            menu         ·삭제 확인·YAML 내보내기)
                            견적 승인                          manual            8         OFF        09-12 ✗ 실패              75%           열기·실행·복제·⋯
                                                                                                                                                                                                         '워크플로가 없습니다' + 새 워크플로·DSL 반입
   ▫ LLM·모델                                                                                                                                                               7    빈 상태         empty                                                 -
                                                                                                                                                                                                         유도
                            채용 공고 배포                       webhook           5         ON         09-18 09:10 ✓           92%           열기·실행·복제·⋯
   ▫ 관측·운영


   ▫ 사용자·조직


   ▫ 설정                  … 외 7건 (커서 페이징)



   설치된 Addon                 활성 토글 = PATCH /api/workflows/{id} {enabled} 즉시 반영, 실패 시 롤백.                동작: 열기→SCR-F02 / 실행→POST run 후 SCR-F03 / 복제 /
                             성공률 80% 미만은 적색 강조.                                                         ⋯ = 트리거(SCR-F04)·삭제(확인)·YAML 내보내기
   ▸ 게시판


   ▸ HR 채용



                        7

                                                                         워크플로가 없습니다 — [새 워크플로] 또는 [DSL 반입]


   [‹ 접기]




관련 요구사항(PRD): D2-03 X01


AgentPlaza 화면설계서 · v1.0 · F. 워크플로                                                                                                                                                                                                                             63
시스템                       AgentPlaza                                             화면 ID                       SCR-F02                                                                          화면 유형                페이지(전체화면 3분할)
화면명                       워크플로 빌더                                                화면 경로                       /workflow/builder/{id}                                                           접근 권한                admin+·빌더
우선순위                      P1                                                     PRD 추적                      D2-03 X01                                                                        작성일 / 버전             2026-09-19 / v1.0

팔레트·캔버스·인스펙터 3분할로 DAG 를 구성한다. 셸 없이 전체화면으로 열리며 노드 편집은 부분 PATCH 로 자동 저장되고, 실행은 저장 후 SSE 로 노드 상태를 캔버스에 하이라이트한다. 캔버스는 마우스 중심이므로 키보드 사용자를 위한 '목록
편집 모드'를 함께 제공한다.


                                                                   1                                                                                                                     No   구성요소        유형             기능 설명 / 동작                                           연계
  ← 워크플로 신규 입사 온보딩                                                         저장됨 14:05                         실행 ▶            트리거          v3        ▾                설정             ✕
                                                                                                                                                                                                                         저장 상태(자동 저장·디바운스)·실행·트리거·버전
                                                                                                                                                                                         1    헤더          buttons                                    SCR-F04
  ① 팔레트 (240px)                             ② 캔버스 (React Flow · drag & drop)                                                          ③ 인스펙터 (320px)
                                                                                                                                                                                                                         ·설정. 실행은 저장 후

  노드 유형 8종 (드래그 / Enter 추가)                                                                                                           노드: agent                                                                          trigger·agent·llm·condition·http·hitl·notify·code.
                                                                                                                                                                                         2    팔레트 노드 8종   list(drag)                                                          D2-03
                                           4                                                                                                                                                                             Enter 로 캔버스 추가
 2                                                                                     agent: hrcore
                                                                                                                                      에이전트
                                                     trigger
         ▫ trigger             ▫ agent              webhook                             지원자 등록                                                                                                                           설치 에이전트의 capability 목록(D13 인덱스)
                                                                                                                                      7                                                  3    컴포넌트 검색     input + list                                                        SCR-D02
                                                                                                                                                                                                                         에서 검색
                                                                                                                                          hrcore                                ▾
           ▫ llm             ▫ condition                                                                                              capability                                                          graph          드래그·연결·삭제·다중 선택. 좌표는
                                                                                                                                                                                         4    캔버스                                                                             X01
                                                                                                                                                                                                          editor         definition_json.nodes[].position
          ▫ http                 ▫ hitl                                                                                                   manage                                ▾
                                                                                                                                                                                                          상태 +           SSE 노드 상태 하이라이트. POST validate 로
                                                                                         condition                                                                                       5    실행·검증 상태                                                                        SCR-F03
                                                                                                                                                                                                          배지             미연결·순환·필수 누락을 노드 배지로
                                                                                          승인?
         ▫ notify                ▫ code                                                                                               입력 매핑

                                                                                                                                                                                         6    캔버스 컨트롤     buttons        미니맵·줌·자동 배치·실행 경로 표시                                 -
                                                                                                                                              applicant ← trigger.body
                                                                                                                                              email ← trigger.body.mail
 3
     🔍 컴포넌트 검색                                                                                                                                                                           7    인스펙터
                                                                                                                                                                                                          form(노드        agent: 에이전트·capability·입력 매핑·재시도·
                                                                                                                                                                                                                                                                              D2-03
                                                                                                                                                                                                          별)             타임아웃·승인 필요. 유형별 폼 전환
                                                        notify                                        hitl
     ▸ hrcore · manage                                                                                                                재시도                           타임아웃
                                                        (yes)                                        (no)                                                                                                                캔버스 대체 표 편집. KWCAG·키보드 사용자
                                                                                                                                                                                         8    목록 편집 모드    toggle                                                              -
                                                                                                                                                                                                                         지원
     ▸ board · list                                                                                                                       3                           60s

     ▸ rag · search
                                           5실행 중: 노드 3/6 ✓ ✓ ◌ (SSE 경로 하이라이트)
                                                                                                                                          ✓      승인 필요(hitl)
     … 외 12건                                                   ⚠ 검증: 미연결 1 · 필수 누락 1 → 노드 배지
                                                                                                                                      유형별 폼: llm 별칭·프롬프트 / condition 식 / http URL·메서드·
                                                                                                                                      시크릿 / hitl 승인자·만료 / notify 채널 / code 언어·샌드박스

  컴포넌트 = 설치 에이전트의 capability (D13
  인덱스)
                                                                                                                       미니맵



                                                                                                                                      부분 PATCH · 자동 저장(디바운스)


 8
                      목록 편집 모드             6                                                                                                                   노드 삭제
                                                  줌±                   자동 배치           실행 경로 표시

  캔버스 대체 표 편집(KWCAG·키보드)




관련 요구사항(PRD): D2-03 X01


AgentPlaza 화면설계서 · v1.0 · F. 워크플로                                                                                                                                                                                                                                                       64
시스템             AgentPlaza                                            화면 ID                 SCR-F03                                                                            화면 유형                페이지
화면명             실행 이력·노드 런                                            화면 경로                 /workflow/{id}/runs                                                                접근 권한                admin+·빌더
우선순위            P1                                                    PRD 추적                D2-07                                                                              작성일 / 버전             2026-09-19 / v1.0

실행별 노드 상태·입출력·재시도·오류를 추적한다. 실행 헤더(번호·시각·상태·소요·트리거·실행자) 아래에 노드 런 표를 중첩해 보여 주고, 실패 실행은 실패 노드부터 재실행할 수 있다. 입·출력 요약에는 PII 마스킹 규칙을 적용한다.



                                                                                                                                                                          No   구성요소        유형          기능 설명 / 동작                           연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                      dev                                          🔔3            ko ▾       ☾                  JD


   ▫ 대시보드                워크플로 › 신규 입사 온보딩 › 실행 이력                                                                                                                         1    상태·기간 필터    select      성공/실패/진행 중, 기간 선택. 커서 페이징            D2-07
                                                                                                             1
   ▫ AI 어시스턴트
                         실행 이력 · 노드 런                                                                            상태 전체   ▾              기간 7일 ▾                 재실행
                                                                                                                                                                          2    실행 목록 행     grid        실행 번호·일시·상태·소요·트리거 유형·실행자            D2-07
                        2
   ▫ 마켓플레이스
                              실행 #128 09-19 14:02 12.4s 트리거 webhook 실행자 시스템                                                                                 ✓ 성공
                                                                                                                                                                                           nested
                                                                                                                                                                          3    노드 런 표                  노드·상태·시작·소요·입력/출력 요약·재시도 횟수          D2-07
                                                                                                                                                                                           grid
   ▫ 에이전트 관리
                             3
                                 노드                  상태         시작                소요           입력(요약)                    출력(요약)                       재시도       로그
   ▪ 워크플로                                                                                                                                                                 4    로그 보기       button      노드별 실행 로그·트레이스 링크                    SCR-M02
                                                                                                                                                            4
                                 trigger             ✓          14:02:01          0.1s         {applicant…}              {id:1024}                    0         보기
   ▫ 지식(RAG)                                                                                                                                                                               카드 +        실패 노드·사유 표시. POST runs/{id}/retry?
                                                                                                                                                                          5    실패 실행·재실행                                                    SCR-F01
                                                                                                                                                                                           button      from=node → 새 실행
   ▫ 플레이그라운드                     agent hrcore        ✓          14:02:01          3.2s         {id:1024}                 {status:ok}                  1⚠        보기

                                                                                                                                                                                                       입·출력은 PII 마스킹 적용, 원문 열람은 admin+
                                                                                                                                                                          6    마스킹 규칙      안내                                               SCR-I02
   ▫ 거버넌스
                                                                                                                                                                                                       만
                                 condition           ✓          14:02:04          0.1s         {status:ok}               yes                          0         보기


   ▫ LLM·모델
                                 hitl                ✓          14:02:05          8.9s         승인자 홍길동                   approved                     0         보기


   ▫ 관측·운영
                             6입·출력은 마스킹 규칙(PII) 적용 — 원문 열람은 admin+ 만 가능

   ▫ 사용자·조직

                        5
   ▫ 설정
                              실행 #127 09-12 09:31 4.1s 트리거 manual 실행자 hong                                                                                  ✗ 실패


   설치된 Addon                  실패 노드: http — 502 Bad Gateway (재시도 3회 소진)
                                                                                                                                     재실행 (실패 노드부터)
   ▸ 게시판


   ▸ HR 채용


                         … 외 126건 (상태·기간 필터 + 커서 페이징)




                              POST /api/workflows/runs/{id}/retry?from=node → 새 실행 생성. 원본 실행은 보존한다.

   [‹ 접기]




관련 요구사항(PRD): D2-07


AgentPlaza 화면설계서 · v1.0 · F. 워크플로                                                                                                                                                                                                                     65
시스템          AgentPlaza                                          화면 ID     SCR-F04                                      화면 유형                   모달
화면명          트리거 설정                                              화면 경로     /workflow/{id}/triggers                      접근 권한                   admin+
우선순위         P1                                                  PRD 추적    D2-03                                        작성일 / 버전                2026-09-19 / v1.0

수동·webhook·스케줄 트리거와 시크릿 회전을 설정한다. webhook 은 URL·시크릿·HMAC 서명 헤더·속도 제한을 함께 관리하며 시크릿은 재발급 시 1회만 노출한다. 스케줄은 cron 5필드를 받고 다음 실행 5회를 미리 보여 준다.



                                                                                                                   No   구성요소          유형             기능 설명 / 동작                               연계


                                                                                                                                      radio +        manual|webhook|schedule. cron 5필드 + 다음
                                                                                                                   1    트리거 유형                                                                D2-03
                                                                                                                                      cron           5회 미리보기
                  트리거 설정 · 신규 입사 온보딩                                                                           ✕
                                                                                                                                      read-only
                                                                                                                   2    webhook URL                  POST 대상 엔드포인트. 복사 버튼 제공                  D2-03
                                                                                                                                      + 복사
                  1
                           수동(manual)                         webhook              스케줄(cron)                                          password       POST …/trigger/webhook/rotate. 재발급 시 1
                                                                                                                   3    시크릿·재발급                                                               MSG-020
                                                                                                                                      + button       회만 표시, 구 시크릿 즉시 무효

                  다음 실행 미리보기 5회: 09-20 06:00, 09-21 06:00 …
                                                                                0 6 * * * (5필드)                                       text +         X-Webhook-Signature sha256=. 필수 체크 시
                                                                                                                   4    서명 헤더                                                                 D2-03
                                                                                                                                      checkbox       미서명 요청 거부
                  webhook URL (읽기 전용)

                  2                                                                                                5    속도 제한         number         1~600 회/분, 기본 60. 초과는 429                -
                      https://plaza/api/workflows/12/trigger/webhook                                      복사

                                                                                                                                                     실행 권한 = 생성자 역할(스코프 토큰)으로
                  시크릿                                                                                              6    실행 권한 안내      text                                                    SCR-K03
                                                                                                                                                     고정
                  3
                      ••••••••••••                                                       재발급          1회만 표시



                  서명 헤더

                  4
                      X-Webhook-Signature: sha256=…                                          ✓   필수


                  속도 제한 (회/분)

                  5
                      60                         1~600. 초과 요청은 429




                  6

                      실행 권한 = 생성자 역할(스코프 토큰)으로 고정. 재발급 시 구 시크릿은 즉시 무효화된다(MSG-020 규칙).


                                                                                        취소              저장




관련 요구사항(PRD): D2-03


AgentPlaza 화면설계서 · v1.0 · F. 워크플로                                                                                                                                                                       66
시스템          AgentPlaza                                                   화면 ID                  SCR-F05                                           화면 유형               모달
화면명          DSL 반입                                                       화면 경로                  /workflow/import                                  접근 권한               admin+
우선순위         P2                                                           PRD 추적                 X01                                               작성일 / 버전            2026-09-19 / v1.0

외부 DSL(YAML)을 매핑표에 따라 반입한다. 파일 선택 또는 붙여넣기로 받은 정의를 PRD 7.2.2 매핑표로 변환해 미리 보여 주고, 매핑되지 않는 노드는 건너뛰거나 자리표시자 노드로 만든다. 반입 결과는 초안 상태로 빌더에서 열린다.



                                                                                                                                              No   구성요소       유형            기능 설명 / 동작                                  연계


                                                                                                                                              1    형식 선택      select        Dify DSL(YAML) | AgentPlaza YAML            X01
                  DSL 반입                                                                                                                  ✕
                                                                                                                                                              file +
                                                                                                                                              2    파일·붙여넣기                  YAML ≤2MB. 파일 선택 또는 본문 붙여넣기                 X01
                  형식                                                                                                                                          textarea

                  1                                                                                             2                                                           start→trigger·llm→llm·if-
                        Dify DSL (YAML)                       ▾            | AgentPlaza YAML                               파일 선택 (≤2MB)                                     else→condition·knowledge-
                                                                                                                                              3    매핑 미리보기    표                                                         X01
                                                                                                                                                                            retrieval→agent(rag)·http-
                                                                                                                                                                            request→http·tool→agent·answer/end→notify
                         app:
                           nodes: [start, llm, if-else, tool, answer]                                                                         4    미매핑 처리     radio         건너뛰기 | 자리표시자 노드 생성(기본)                      -
                           ← 파일 대신 본문 붙여넣기도 가능


                                                                                                                                                                            POST /api/workflows/import {format, content,
                                                                                                                                              5    반입         button                                                     SCR-F02
                                                                                                                                                                            unmapped} → 빌더(초안)

                  매핑 미리보기 (PRD 7.2.2 매핑표)

                  3
                      Dify 노드                                           AgentPlaza 노드                               결과



                      start / answer·end                                trigger / notify                            ✓ 매핑



                      llm / if-else / http-request                      llm / condition / http                      ✓ 매핑



                      knowledge-retrieval / tool(x)                     agent(rag) / agent                          ⚠ 미매핑 1건




                  미매핑 노드 처리

                  4
                             건너뛰기(노드 제거)                                                   자리표시자 노드 생성(기본)


                                                                                                            5
                                                                                                       취소                      반입 → 빌더




관련 요구사항(PRD): X01


AgentPlaza 화면설계서 · v1.0 · F. 워크플로                                                                                                                                                                                                  67
시스템              AgentPlaza                                        화면 ID                   SCR-G01                                                                  화면 유형            페이지
화면명              지식 컬렉션 목록                                         화면 경로                   /rag                                                                     접근 권한            로그인
우선순위             P1                                                PRD 추적                  D3-06 X07                                                                작성일 / 버전         2026-09-19 / v1.0

컬렉션을 만들고 임베딩 모델·권한을 지정한다. 문서·청크 수와 벡터 백엔드(pgvector/Qdrant/local 폴백) 상태를 함께 보여 주며, 데이터 등급에 따라 선택 가능한 임베딩 모델이 제한된다.



                                                                                                                                                               No   구성요소       유형       기능 설명 / 동작                              연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                                    dev                                      🔔3        ko ▾         ☾              JD

                                                                                                                                                                                        생성 폼 모달 → POST /api/rag/collections →
    ▫ 대시보드                지식(RAG)                                                                                                                              1    + 컬렉션      버튼                                               SCR-G02
                                                                                                                                                                                        문서 화면으로 이동
                                                                                                                                               1
    ▫ AI 어시스턴트
                          지식 컬렉션                                                                         🔍 컬렉션 검색                                  + 컬렉션                       데이터
                                                                                                                                                               2    컬렉션 표               컬렉션·문서·청크·임베딩 모델·백엔드·권한·동작              D3-06
                                                                                                                                                                               그리드
    ▫ 마켓플레이스
                                                                                                                                                                                        confidential 등급은 로컬 임베딩만 선택 가능
                         2                                                             3                                                                       3    임베딩 모델 열   표시                                               D1-07 X07
                                                                                                                                                                                        (퍼블릭 disabled)
    ▫ 에이전트 관리
                             컬렉션                   문서        청크             임베딩 모델                             백엔드                   권한

                                                                                                                                                                                        이름 ≤100 필수·설명·임베딩 별칭·데이터 등급·
    ▫ 워크플로                                                                                                                                                     4    생성 폼       모달 폼                                             D3-06
                             사내 규정                 24        1,204          nomic-embed (로컬)                   pgvector              전체            열기 ⋯
                                                                                                                                                                                        허용 역할/그룹

    ▪ 지식(RAG)                                                                                                                                                                           크기 100~4000 / 겹침 0~50% / 전략. 모델
                             제품 매뉴얼                8         512            text-embedding-3 (퍼블릭)             pgvector              영업팀           열기 ⋯        5    청킹 설정      폼                                                D3-06
                                                                                                                                                                                        변경 시 재인덱싱 경고
    ▫ 플레이그라운드
                             보안 표준                 12        788            nomic-embed (로컬)                   pgvector              보안팀           열기 ⋯                                 pgvector ● / Qdrant ○ 미구성 → local 폴백
                                                                                                                                                               6    백엔드 상태     배지                                               X07
    ▫ 거버넌스                … 외 6건 · 데이터 등급 confidential 컬렉션은 로컬 임베딩 모델만 선택 가능                                                                                                            경고 + 설정 링크


    ▫ LLM·모델             4                                                                                       6
                              컬렉션 생성 폼(모달)                                                                            벡터 백엔드 상태

    ▫ 관측·운영                   이름 (≤100)                               설명

                                                                                                                          pgvector 구성됨
    ▫ 사용자·조직                      사내 규정                                취업규칙·복무·보안

                              임베딩 별칭                                  데이터 등급                                               Qdrant 미구성
    ▫ 설정

                                  nomic-embed           ▾              internal                      ▾
    설치된 Addon                                                                                                             ⚠ 벡터 백엔드 미구성 시
                                                                                                                          local 폴백으로 동작
                                                                                                                          → 설정에서 구성
    ▸ 게시판                     허용 역할·그룹 [전체 ▾] [인사팀 ×]

                              5
    ▸ HR 채용                       청킹 설정 크기 [800] 겹침 [120] 전략 [문단 ▾]
                                  임베딩 모델 변경 시 전체 재인덱싱 경고




    [‹ 접기]




관련 요구사항(PRD): D3-06 X07


AgentPlaza 화면설계서 · v1.0 · G. 지식(RAG)                                                                                                                                                                                                        68
시스템              AgentPlaza                                      화면 ID              SCR-G02                                                                         화면 유형            페이지
화면명              문서 업로드·인덱싱                                      화면 경로              /rag/{id}/documents                                                             접근 권한            지식 담당
우선순위             P1                                              PRD 추적             D3-06 D1-07                                                                     작성일 / 버전         2026-09-19 / v1.0

문서를 올리고 파싱·청킹·임베딩 진행을 확인한다. 파일별 상태(인덱싱됨·처리 중·실패)를 SSE 로 갱신하고, 실패 문서만 골라 재시도할 수 있게 부분 실패를 명시한다.



                                                                                                                                                               No   구성요소       유형          기능 설명 / 동작                             연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                              dev                                        🔔3            ko ▾        ☾               JD

                                                                                                                                                                               dropzone(   pdf·docx·xlsx·md·txt·html ≤50MB ×20.
    ▫ 대시보드                지식(RAG) › 사내 규정                                                                                                                      1    업로드 드롭존                                                       D3-06
                                                                                                                                                                               다중)         데이터 등급 확인

    ▫ AI 어시스턴트
                          사내 규정 · 문서 (24)                                                          업로드                     URL 추가                  재인덱싱                        데이터
                                                                                                                                                               2    문서 표                   문서·크기·상태·청크·갱신·동작. 상태별 필터              D3-06
                                                                                                                                                                               그리드
    ▫ 마켓플레이스             1
                                                                                                                                                                                           docling 파싱 → 청킹 → 임베딩 잡 SSE 로 %
                                                                                                                                                               3    진행 표시      진행률                                                D1-07
                                                                                                                                                                                           갱신
    ▫ 에이전트 관리                                                      ⬆ pdf · docx · xlsx · md · txt · html ≤50MB × 20

                                                                   끌어다 놓거나 클릭해 선택 · 업로드 시 컬렉션 데이터 등급 확인
    ▫ 워크플로                                                                                                                                                     4    미리보기       드로어         문서의 청크 목록·본문 조각 확인. 삭제 가능              D3-06


    ▪ 지식(RAG)            2                                                                                                                                                                 크기 100~4000 / 겹침 0~50% / 전략. 변경
                                                                                                                                                               5    청킹 설정      폼                                                  D3-06
                             문서                           크기               상태                          청크             갱신                                                                   시 재인덱싱 경고
    ▫ 플레이그라운드                                                                                                                        4
                                                                                                                                                                                           실패 문서 배지 + 해당 문서만 재시도
                             취업규칙.pdf                     1.2MB            ✓ 인덱싱됨                      84             09-10              미리보기 삭제               6    부분 실패 배너   경고                                                 D3-06
    ▫ 거버넌스                                                                                3                                                                                                (MSG-018)

                             보안정책.docx                    340KB            ◌ 파싱 중 · 60%                -              -                  취소
    ▫ LLM·모델

                             회의록.md                       12KB             ✗ 실패: 인코딩                   -              09-19              재시도
    ▫ 관측·운영

                             복무규정.pdf                     780KB            ✓ 인덱싱됨                      51             09-12              미리보기 삭제
    ▫ 사용자·조직
                          … 외 20건 · 상태별 필터(전체/인덱싱됨/처리 중/실패) · 미리보기 = 청크 목록 드로어

    ▫ 설정
                         5
                              청킹 설정                                                                              ⚠ 청킹 설정 변경 시
                              크기 100~4000        겹침 0~50%              전략                                        컬렉션 전체 재인덱싱이 필요합니다.
    설치된 Addon                                                                                                    [재인덱싱] 잡으로 실행


    ▸ 게시판                         800              120                     문단                 ▾

    ▸ HR 채용

                         6
                              ⚠ 부분 실패 (1/4) — '회의록.md' 인코딩 오류. 실패 문서만 [재시도] 가능 (MSG-018)




    [‹ 접기]




관련 요구사항(PRD): D3-06 D1-07


AgentPlaza 화면설계서 · v1.0 · G. 지식(RAG)                                                                                                                                                                                                      69
시스템              AgentPlaza                                          화면 ID                 SCR-G03                                                                         화면 유형            탭(컬렉션 상세)
화면명              검색 시험·인용 확인                                         화면 경로                 /rag/{id}/search                                                                접근 권한            로그인
우선순위             P1                                                  PRD 추적                D3-06                                                                           작성일 / 버전         2026-09-19 / v1.0

질의로 하이브리드 검색(BM25 + dense, RRF 병합) 결과와 인용 근거를 점검한다. 점수·출처 문서·청크 미리보기를 표로 보이고, 원문 드로어로 인용의 실제 위치를 확인한다.



                                                                                                                                                                      No   구성요소       유형       기능 설명 / 동작                                연계
  ▣    AgentPlaza                🔍 검색 (⌘K)                                 dev                                          🔔3        ko ▾         ☾                 JD


    ▫ 대시보드                지식(RAG) › 사내 규정                                                                                                                             1    탭          탭        컬렉션 상세 탭 중 검색 시험                          SCR-G02


    ▫ AI 어시스턴트
                          검색 시험 · 사내 규정                                                                                                                                               입력·선택·   방식 hybrid|bm25|dense · k(기본 5) · 리랭크
                                                                                                                                                                      2    질의·옵션                                                         D3-06
                                                                                                                                                                                      체크       on
    ▫ 마켓플레이스             1
                                       문서                 검색 시험                      설정                권한                                                                                      POST /api/rag/collections/{id}/search → 결과·
                                                                                                                                                                      3    검색 실행      버튼                                                   D3-06
                                                                                                                                                                                               진단 갱신
    ▫ 에이전트 관리             질의                                                         방식                     k

                         2                                                                                                                         3
    ▫ 워크플로                                                                                                                                                            4    결과 표       표        순위·점수·문서·청크 미리보기. 점수 내림차순                 D3-06
                                 연차 이월 규정                                             hybrid       ▾            5                 ✓      리랭크                검색
    ▪ 지식(RAG)                                                                                                                                                                                  선택 청크의 원문·페이지·청크 번호. 문서 열기
                                                                                                                                                                      5    원문 드로어     드로어                                                D3-06
                                                                                                                                                                                               연결
                         4
    ▫ 플레이그라운드
                             #        점수           문서                            청크 미리보기                                                                                                       지연·BM25/dense 건수·RRF 병합·리랭크 적용
                                                                                                                                                                      6    진단         텍스트                                                D3-06
    ▫ 거버넌스
                                                                                                                                                                                               여부(튜닝 근거)
                             1        0.83         취업규칙.pdf                      "연차휴가는 발생 연도 종료 후 1년간 …"                                              보기
    ▫ LLM·모델
                             2        0.71         복무규정.pdf                      "미사용 연차의 이월은 노사 합의에 따라 …"                                             보기
    ▫ 관측·운영
                             3        0.64         취업규칙.pdf                      "이월 연차는 다음 회계연도 말까지 …"                                                보기
    ▫ 사용자·조직
                         6                                                                                          5
                                 진단 지연 42ms · BM25 5건 · dense 5건 · RRF 병합 · 리랭크 적용                                      원문 드로어
                                 튜닝 근거로 사용(방식·k·리랭크 조합 비교)
    ▫ 설정
                                                                                                                        취업규칙.pdf · p.12 · 청크 #84

    설치된 Addon

                                                                                                                        제31조(연차휴가) 연차휴가는 발생
    ▸ 게시판                 confidential 등급 컬렉션은 로컬 임베딩·로컬 리랭커만 사용
                                                                                                                        연도 종료 후 1년간 행사하지 아니
                                                                                                                        하면 소멸한다. 다만 …
    ▸ HR 채용
                          결과 0건이면 질의 변형 제안(동의어·철자) 표시

                                                                                                                        [문서 열기] [청크 목록]




    [‹ 접기]




관련 요구사항(PRD): D3-06


AgentPlaza 화면설계서 · v1.0 · G. 지식(RAG)                                                                                                                                                                                                               70
시스템             AgentPlaza                                      화면 ID             SCR-H01                                                                      화면 유형            페이지
화면명             플레이그라운드                                         화면 경로             /playground                                                                  접근 권한            개발자·admin
우선순위            P1                                              PRD 추적            D10-05                                                                       작성일 / 버전         2026-09-19 / v1.0

프롬프트·모델·지식 조합을 즉시 실험한다. 좌측 설정 폼과 우측 스트리밍 출력이 나란히 놓이고, 출력 아래에 지연·토큰·비용·실제 모델이 항상 표시된다. 실험은 저장해 A/B·평가로 이어 쓴다.



                                                                                                                                                          No   구성요소       유형         기능 설명 / 동작                            연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                             dev                                         🔔3         ko ▾         ☾             JD

                                                                                                                                                                                     게이트웨이 별칭. 데이터 등급 위반 별칭은
   ▫ 대시보드                플레이그라운드                                                                                                                          1    모델 별칭      선택                                               D1-06
                                                                                                                                                                                     disabled

   ▫ AI 어시스턴트
                         플레이그라운드                                                           저장된 실험 ▾                        저장              A/B 로 →
                                                                                                                                                          2    시스템 프롬프트   textarea   실험용 프롬프트. 저장 시 실험 레코드에 포함             D10-05

   ▫ 마켓플레이스
                             설정                                          출력                                                                     ● 스트리밍
                                                                                                                                                          3    지식(RAG)    선택         컬렉션 선택 시 rag.retrieve 도구가 자동 연결       SCR-G01
   ▫ 에이전트 관리                 모델 별칭

                             1
   ▫ 워크플로                        plaza/chat                 ▾                연차 이월은 취업규칙 제31조에 따라                                                         4    파라미터       입력         온도 0~2 · 최대 토큰 1~32k                  D10-05
                                                                             발생 연도 종료 후 1년간 행사하지 않으면
                                                                             소멸합니다. 다만 노사 합의가 있으면
   ▫ 지식(RAG)                                                                 다음 회계연도 말까지 이월할 수 있습니다.
                             시스템 프롬프트                                                                                                                                                POST /api/playground/run → SSE 스트리밍
                                                                                                                                                          5    입력·실행      입력+버튼                                            D10-05
                                                                                                                                                                                     출력
                             2
   ▪ 플레이그라운드                     사내 규정에 근거해 간결히 답하고
                                 근거 문서를 인용하세요.                               근거: 취업규칙.pdf p.12 · 복무규정.pdf p.4                                                                        지연·토큰(in/out)·비용·실제 모델. 로컬은 비용
                                                                                                                                                          6    출력 메타      메타 라인                                            D10-04
   ▫ 거버넌스
                                                                                                                                                                                     0


   ▫ LLM·모델                                                                                                                                               7    동작         버튼         평가 시나리오에 추가 / 트레이스 보기                 SCR-H03 M02
                             지식(RAG)
   ▫ 관측·운영
                             3
                                                                             ⏱ 1.9s · 640 토큰(in 210 / out 430) · ₩1.2 · qwen3:8b(로컬)
                                                                         6
                                 사내 규정                      ▾
   ▫ 사용자·조직
                             온도 0~2                 최대 토큰

   ▫ 설정                      4
                                 0.3                 1024
                                                                             도구 호출 · rag.retrieve                                          성공
   설치된 Addon
                             도구                                              query="연차 이월" · k=5 · 42ms
                                                                             결과 3건 인용 → 출력에 근거 표시
   ▸ 게시판
                                 ✓   board.manage
   ▸ HR 채용
                                     rag.retrieve
                                                                         7
                             5                                                    평가 시나리오에 추가                                     트레이스 보기
                                 메시지…
                                                            실행
                                                                         비용 = 카탈로그 단가 × 토큰 (로컬 모델 0)

   [‹ 접기]




관련 요구사항(PRD): D10-05


AgentPlaza 화면설계서 · v1.0 · H. 플레이그라운드·평가                                                                                                                                                                                                  71
시스템             AgentPlaza                                              화면 ID                      SCR-H02                                                                           화면 유형           탭(플레이그라운드)
화면명             A/B 비교·비용                                               화면 경로                      /playground/compare                                                               접근 권한           개발자·admin
우선순위            P1                                                      PRD 추적                     D10-04 D10-05                                                                     작성일 / 버전        2026-09-19 / v1.0

같은 입력을 두 설정(A/B)에 동시에 보내 출력·지연·토큰·비용을 나란히 비교한다. 판정과 메모는 평가 데이터로 저장되고, 누적 비용 그래프는 LLM 비용 화면과 같은 소스를 쓴다.



                                                                                                                                                                                No   구성요소       유형      기능 설명 / 동작                       연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                          dev                                               🔔3         ko ▾           ☾            JD


   ▫ 대시보드                플레이그라운드 › A/B                                                                                                                                          1    탭          탭       플레이그라운드 내 A/B 비교 탭               SCR-H01


   ▫ AI 어시스턴트
                         A/B 비교 · 비용
                                                                                                                                                                                2    공통 입력      입력+버튼   같은 입력을 A·B 에 동시 전송(둘 다 실행)       D10-05

   ▫ 마켓플레이스             1
                                     실행                         A/B 비교                         저장된 실험                                                                                                   SCR-H01 설정 폼 복제. 출력 + 지연·토큰·비용
                                                                                                                                                                                3    A 설정·출력    패널                                       D10-05
                                                                                                                                                                                                        메타
   ▫ 에이전트 관리
                                                   2
                         공통 입력
   ▫ 워크플로                                              연차 이월 규정을 알려줘                                                                                            둘 다 실행          4    B 설정·출력    패널      설정 복제 버튼으로 A 에서 복사 후 일부만 변경      D10-05


   ▫ 지식(RAG)                                                                                                                                                                                            A 우수 / B 우수 / 동등 + 메모. 평가 데이터로
                        3                                                                                 4                                                                     5    판정·메모      버튼+메모                                    SCR-H03
                                 A         plaza/chat · qwen3:8b(로컬) · 온도 0.3
                                                                                                                   B        plaza/fast · 퍼블릭 API · 온도 0.3                                               저장
   ▪ 플레이그라운드
                                                                                                                                                                                                        기간별 A/B 비용 누적. LLM 비용(SCR-J05) 과
                               연차 이월은 취업규칙 제31조에 따라                                                            연차는 원칙적으로 1년 내 사용해야                                              6    누적 비용      차트                                       D10-04
   ▫ 거버넌스                      발생 연도 종료 후 1년간 행사하지                                                             하며, 합의가 있으면 이월이
                                                                                                                                                                                                        동일 소스
                               않으면 소멸합니다. 노사 합의 시                                                              가능합니다. (근거 인용 없음)
                               다음 회계연도 말까지 이월…
   ▫ LLM·모델


   ▫ 관측·운영


   ▫ 사용자·조직
                               2.1s · 640tk · ₩0                                                               0.9s · 610tk · ₩4.8

   ▫ 설정

                                                   5
                         판정                               A 우수                        B 우수                    동등
                                                                                                                                  메모: A 가 근거 인용 우수
   설치된 Addon


   ▸ 게시판                6
                             누적 비용 (최근 7일)                                                   ■ A(로컬) ₩0   ■ B(퍼블릭) ₩4.8/회                                           기간 [7일 ▾]
   ▸ HR 채용




                                      09-13                09-14                09-15                 09-16               09-17                  09-18          09-19



   [‹ 접기]




관련 요구사항(PRD): D10-04 D10-05


AgentPlaza 화면설계서 · v1.0 · H. 플레이그라운드·평가                                                                                                                                                                                                            72
시스템             AgentPlaza                                          화면 ID                    SCR-H03                                                                    화면 유형              페이지
화면명             평가 시나리오·회귀                                          화면 경로                    /eval                                                                      접근 권한              QA·admin
우선순위            P1                                                  PRD 추적                   D10-05                                                                     작성일 / 버전           2026-09-19 / v1.0

시나리오 세트를 돌려 품질 점수와 회귀를 판정한다. 세트 목록에서 기준선 대비 하락을 강조하고, 세트 상세에서 케이스별 입력·기대·판정 기준과 실행 이력을 확인한다.



                                                                                                                                                                   No   구성요소         유형       기능 설명 / 동작                               연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                      dev                                          🔔3          ko ▾       ☾             JD

                                                                                                                                                                        + 시나리오 세트·            세트 생성 / POST /api/eval/sets/{id}/run →
   ▫ 대시보드                플레이그라운드 › 평가                                                                                                                              1                 버튼                                                D10-05
                                                                                                                                                                        실행                    잡 진행 → 결과
                                                                                                                         1
   ▫ AI 어시스턴트
                         평가 시나리오·회귀                                                                                             + 시나리오 세트                실행                          데이터      세트·케이스 수·대상 에이전트·마지막 실행·점수·
                                                                                                                                                                   2    세트 목록                                                          D10-05
                                                                                                                                                                                     그리드      회귀
   ▫ 마켓플레이스
                        2                                                                                                        3                                 3    회귀 열         상태       기준선 대비 증감. 하락은 적색 강조                     D10-05
   ▫ 에이전트 관리
                            세트                            케이스         대상 에이전트                        마지막 실행              점수           회귀

                                                                                                                                                                                              케이스 표(입력·기대·판정 기준·마지막 결과).
   ▫ 워크플로                                                                                                                                                          4    세트 상세        패널                                                D10-05
                            게시판 기본                        24          board                          09-19               0.91         ✓ 유지          열기
                                                                                                                                                                                              케이스 편집

   ▫ 지식(RAG)                                                                                                                                                                                  promptfoo·deepeval 형식으로 내보내 CI 에서
                            채용 스크리닝                       40          hr-screening                   09-18               0.78         ✗ -0.06       열기             5    YAML 내보내기    동작                                                D10-05
                                                                                                                                                                                              재실행
   ▪ 플레이그라운드
                            지식 검색 정확도                     18          ragagent                       09-19               0.86         ✓ +0.02       열기
                                                                                                                                                                   6    기준선 비교       차트       기준선·최근·목표 점수 비교와 실행 이력                   D10-05
   ▫ 거버넌스                … 외 4건 · 회귀는 기준선(baseline) 대비 하락을 적색으로 강조


                        4                                                                                            6                                                                        게시 전 필수 세트 표시, CI
   ▫ LLM·모델                                                                                                                                                        7    마켓 게시 연동     배지+링크                                             SCR-E06
                             세트 상세 · 채용 스크리닝 (40)                                                                            기준선 비교                                                           결과(test/impl/<N>/result.md) 링크

   ▫ 관측·운영
                             5
                                 #   입력                 기대                 판정 기준                결과                           기준선 09-12 0.84
   ▫ 사용자·조직
                                 1   이력서 A 요약           핵심 3항목             포함 여부                ✓
   ▫ 설정
                                                                                                                             최근 09-18 0.78
                                 2   결격 사유 탐지           탐지됨                LLM judge            ✗

   설치된 Addon
                                 3   점수 산출              0~100              범위·근거                ✓

   ▸ 게시판                                                                                                                     목표 0.85
                                                                                                                              ✗ 회귀 -0.06
                             케이스 편집 · YAML 내보내기(promptfoo/deepeval 형식)                                                        케이스 #2 판정 실패
   ▸ HR 채용
                             실행 이력: 09-18 0.78 / 09-12 0.84 / 09-05 0.81



                        7                                                      CI 결과 링크 test/impl/<N>/result.md · 심사(SCR-E06)에서 참조
                                          마켓 게시 전 필수 세트




   [‹ 접기]




관련 요구사항(PRD): D10-05


AgentPlaza 화면설계서 · v1.0 · H. 플레이그라운드·평가                                                                                                                                                                                                          73
시스템             AgentPlaza                                        화면 ID             SCR-I01                                                                     화면 유형               페이지
화면명             가드레일 도메인 카탈로그                                     화면 경로             /guardrails                                                                 접근 권한               컴플라이언스·admin
우선순위            P1                                                PRD 추적            D9-06                                                                       작성일 / 버전            2026-09-19 / v1.0

업종·도메인 규칙셋 24종을 켜고 적용 범위(에이전트·카테고리)를 지정한다. global 규칙셋은 해제할 수 없고, 판정 방식(regex 결정적 / LLM classifier 옵션)과 적용 지점(입력·출력·도구 인자), 차단 시 동작을 함께 정한다.



                                                                                                                                                           No   구성요소         유형        기능 설명 / 동작                           연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                   dev                                  🔔3            ko ▾        ☾             JD

                                                                                                                                                                                       판정 시험(I02) 이동 · 규칙 데이터 재빌드
   ▫ 대시보드                거버넌스 › 가드레일                                                                                                                       1    헤더 동작        버튼                                             SCR-I02
                                                                                                                                                                                       (백그라운드 잡)
                                                                                                              1
   ▫ AI 어시스턴트
                         가드레일 도메인 카탈로그                                                                                 판정 시험                    규칙 재빌드
                                                                                                                                                           2    global 규칙셋   고정 행      PII·신용정보·비밀키. 항상 적용, 해제 불가           D9-06

   ▫ 마켓플레이스             2
                              global (필수)                                                                                                   적용 ● 고정                          그리드·      24종. 규칙 수를 실판정/휴리스틱으로 분리
                                                                                                                                                           3    도메인 목록                                                      D9-06
                                                                                                                                                                             토글        표기
   ▫ 에이전트 관리                  PII · 신용정보 · 비밀키 — 규칙 256 (실판정 180 · 휴리스틱 76)                                                              해제 불가(정책)

                                                                                                                                                                                       전체 또는 에이전트·카테고리 패턴(dopq-* 등)
   ▫ 워크플로                                                                                                                                                  4    적용 범위        선택                                             SCR-D02
                                                                                                                                                                                       으로 한정
                         업종 · 도메인 카탈로그 (24)                                                              적용             에이전트 범위
   ▫ 지식(RAG)                                                                                                                                                                 체크박스·     regex 기본 on. LLM classifier 는 옵션이며
                                                                                                                                                           5    판정 방식                                                       SCR-J02
                        3                                                                                                                                                    선택        비결정적 경고 병기
                              금융 (K)                        규칙 231 · 실 140 · 휴 91                 4                     전체 ▾
   ▫ 플레이그라운드
                                                                                                                                                                             체크박스·
                                                                                                                                                           6    적용 지점·동작               입력·출력·도구 인자 / 차단·마스킹·경고 중 선택         SCR-I02
   ▪ 거버넌스 ●2
                                                                                                                                                                             선택
                              의료 (Q)                        규칙 210 · 실 128 · 휴 82                                       -

   ▫ LLM·모델

                              제조 (C)                        규칙 204 · 실 121 · 휴 83                                       dopq-* ▾
   ▫ 관측·운영


   ▫ 사용자·조직                   공공행정 (O)                      규칙 198 · 실 119 · 휴 79                                       -


   ▫ 설정
                         … 외 20개 도메인 (총 24) — 업종 KSIC 대분류 + 공통 도메인


   설치된 Addon            5                                                                 6
                             판정 방식                                                            적용 지점 · 차단 시 동작
   ▸ 게시판
                              ✓   regex (결정적 · 실판정)                                           ✓       입력           ✓    출력               ✓    도구 인자
   ▸ HR 채용
                                  LLM classifier (옵션)            plaza/guard    ▾                 차단 ▾             ▾
                                                                                                                                   마스킹 · 경고 선택 가능

                             classifier 는 비결정적 — 경고 배지 병기                                     Orchestrator 게이트에서 동일 규칙 적용



                         저하: classifier 미구성이면 'regex 만' 배지 · 토글 변경은 즉시 반영되고 감사 로그에 남는다



   [‹ 접기]




관련 요구사항(PRD): D9-06


AgentPlaza 화면설계서 · v1.0 · I. 가드레일·거버넌스                                                                                                                                                                                                74
시스템             AgentPlaza                                           화면 ID             SCR-I02                                                                           화면 유형            탭
화면명             판정 로그·시험                                             화면 경로             /guardrails/decisions                                                             접근 권한            컴플라이언스·admin
우선순위            P1                                                   PRD 추적            D9-06 D9-07                                                                       작성일 / 버전         2026-09-19 / v1.0

입력·출력·도구 인자에 대한 가드레일 판정 결과와 차단 사유를 조회하고, 임의 입력을 넣어 dry-run 으로 재현한다. 매칭 규칙을 실판정/휴리스틱으로 구분해 보이고 마스킹 결과를 미리 보여 준다.



                                                                                                                                                                    No   구성요소       유형        기능 설명 / 동작                              연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                      dev                                        🔔3         ko ▾           ☾             JD


   ▫ 대시보드                거버넌스 › 가드레일 › 판정 로그                                                                                                                        1    탭 전환       탭         도메인 카탈로그(I01) ↔ 판정 로그·시험                SCR-I01


   ▫ AI 어시스턴트
                         판정 로그 · 시험                                                                                                                                                 텍스트영      임의 문자열 입력. 실제 대화·감사에 영향 없는
                                                                                                                                                                    2    시험 입력                                                        D9-06
                                                                                                                                                                                    역         dry-run
   ▫ 마켓플레이스
                        1
                                        도메인 카탈로그                           판정 로그·시험                                                                                                           적용할 도메인(다중)과 판정 지점(입력·출력·
                                                                                                                                                                    3    대상 선택      선택                                                SCR-I01
                                                                                                                                                                                              도구 인자)
   ▫ 에이전트 관리

                              시험(dry-run) — 실제 대화에 영향 없음                                                                                                                                      POST /api/guardrails/evaluate → 결과 카드
   ▫ 워크플로                                                                                                                                                           4    판정         버튼                                                D9-06
                                                                                                                                                                                              갱신
                             2                                                                                   3                                   4
                                 주민번호 900101-1234567 로 조회하고                                                           도메인: global, 금융     ▾              판정
   ▫ 지식(RAG)                     카드 4111-1111-1111-1111 결제 내역을 알려줘                                                                                                                            차단·마스킹·통과 + 매칭 규칙(실판정/휴리스
                                                                                                                                                                    5    판정 결과      카드                                                D9-06
                                                                                                                                                                                              틱)·마스킹 미리보기
                                                                                                                      지점: 입력              ▾              초기화
   ▫ 플레이그라운드
                                                                                                                                                                                              기간·판정·규칙 필터. [재현] 은 시험 폼을
                                                                                                                                                                    6    판정 로그      그리드                                               D9-07
   ▪ 거버넌스 ●2
                              로그의 [재현] 을 누르면 이 폼이 자동으로 채워진다                                                                                                                                   자동으로 채움


   ▫ LLM·모델
                        5
                                       차단                판정 결과 — 매칭 규칙 2건
   ▫ 관측·운영
                              global.pii.rrn                      실판정                       마스킹 미리보기
                                                                                            주민번호 ●●●●●●-●●●●●●● · 카드 ●●●●-●●●●-●●●●-1111
   ▫ 사용자·조직                                                                                 차단 대신 마스킹으로 전환 시의 결과
                              finance.card.pan                    휴리스틱

   ▫ 설정



   설치된 Addon            6
                            시각                 에이전트                   지점              판정             규칙                                  사용자             동작
   ▸ 게시판
                            14:02              board                  입력              차단             global.pii.rrn                      홍길동             재현
   ▸ HR 채용
                            13:47              hr-onboarding          출력              마스킹            finance.card                        김철수             재현


                            13:20              invoice                도구 인자           통과             -                                   admin           재현


                         원문은 마스킹 저장 — 평문 열람은 admin+ 만, 열람 자체가 감사 이벤트로 기록된다

   [‹ 접기]




관련 요구사항(PRD): D9-06 D9-07


AgentPlaza 화면설계서 · v1.0 · I. 가드레일·거버넌스                                                                                                                                                                                                          75
시스템             AgentPlaza                                           화면 ID    SCR-I03                                                                          화면 유형            페이지
화면명             정책·데이터 등급                                            화면 경로    /governance/policy                                                               접근 권한            supervisor
우선순위            P1                                                   PRD 추적   D9-05 D1-06                                                                      작성일 / 버전         2026-09-19 / v1.0

데이터 등급 L0~L3 을 정의하고 등급별 허용 모델·도구·내보내기 정책을 정한다. 조직 정책은 OPA Rego 로 편집·검증하며, 조직 유형별 카탈로그 노출과 dry-run 정책 시험을 함께 제공한다.



                                                                                                                                                          No   구성요소        유형       기능 설명 / 동작                                       연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                  dev                                 🔔3          ko ▾        ☾                JD

                                                                                                                                                                                    L0 public / L1 internal / L2 confidential / L3
   ▫ 대시보드                거버넌스 › 정책                                                                                                                        1    등급 정의       편집 표                                                      D1-06
                                                                                                                                                                                    regulated. 이름 변경 불가

   ▫ AI 어시스턴트
                         정책 · 데이터 등급                                                                             정책 시험                        내보내기                                  L2 로컬 전용·L3 로컬+격리망. LLM 라우팅
                                                                                                                                                          2    등급별 허용 모델   매트릭스                                                      SCR-J04
                                                                                                                                                                                    (J04)과 동기
   ▫ 마켓플레이스              ① 등급 정의 (이름 변경 불가 · 설명만 편집)                                    ④ 조직 정책 (OPA Rego)
                                                                                                                                                                                    L2+ 외부 egress 금지 · 파일 내보내기 승인
                        1                                                               4                                                                 3    도구·내보내기     규칙                                                        SCR-I04
                                                                                                                                                                                    필요 · L3 복사 금지
   ▫ 에이전트 관리                등급         이름               설명 · 예시                                package plaza.authz



   ▫ 워크플로                   L0         public           공개 자료 · 제품 소개                                                                                     4    Rego 편집기    코드·검증    supervisor 만. 검증 실패 시 저장 불가                      D9-05
                                                                                               default allow = false
                            L1         internal         사내 일반 · 공지
   ▫ 지식(RAG)                                                                                                                                                                        org_type × 카테고리. 에이전트 단위에 더해
                                                                                                                                                          5    노출 정책       매트릭스                                                      SCR-E01
                                                                                                                                                                                    카테고리 단위 추가
                            L2         confidential     인사·계약 · 고객 식별정보                        allow {
   ▫ 플레이그라운드                                                                                     input.grade <= data.model[input.model].max
                                                                                                 not input.tool in data.denied_tools                                                요청 예시로 dry-run. 판정 결과와 근거 규칙
                            L3         regulated        개인정보·의료·금융 규제                          }                                                          6    정책 시험       폼                                                         D9-05
   ▪ 거버넌스 ●2
                                                                                                                                                                                    표시

                         ② 등급별 허용 모델
   ▫ LLM·모델
                        2                                                                                              검증 실패 시 저장 불가
                            등급           허용 모델                                                         검증
   ▫ 관측·운영
                            L0           전체(1차 퍼블릭 포함)                                  ⑤ 조직 유형별 카탈로그 노출
   ▫ 사용자·조직
                                                                                        5
                            L1           1차 퍼블릭 + 로컬
                                                                                            org_type             허용 카테고리
   ▫ 설정
                            L2           로컬 전용
                                                                                            government           공공 전용 팩 + 공통

   설치된 Addon                L3           로컬 + 격리망
                                                                                            finance              금융 + 공통(외부 egress 제외)

   ▸ 게시판                 ③ 등급별 도구 · 내보내기                                                    general              전체

                        3
   ▸ HR 채용                       L2 이상 외부 egress 금지 · MCP 외부 서버 차단                      ⑥ 정책 시험(dry-run)
                                 L2 이상 파일 내보내기 승인 필요(I04)
                                 L3 대화 내보내기·복사 금지 + 워터마크                                6
                                                                                               요청 예시: L2 문서 + 외부 모델 → 거부
                                                                                               근거 규칙: plaza.authz.model_grade




   [‹ 접기]




관련 요구사항(PRD): D9-05 D1-06


AgentPlaza 화면설계서 · v1.0 · I. 가드레일·거버넌스                                                                                                                                                                                                         76
시스템             AgentPlaza                                            화면 ID            SCR-I04                                                                 화면 유형            페이지
화면명             승인 대기함(HITL)                                          화면 경로            /approvals                                                              접근 권한            승인자
우선순위            P0                                                    PRD 추적           D2-06                                                                   작성일 / 버전         2026-09-19 / v1.0

에이전트가 요청한 도구 실행 승인을 카드 목록으로 검토하고 승인·거부한다. 각 카드는 요청자·대화·인자·영향·정책 근거와 만료 타이머를 보이며, 만료되면 서버가 취소 처리하고 요청자에게 알린다.



                                                                                                                                                          No   구성요소       유형       기능 설명 / 동작                                 연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                      dev                             🔔3       ko ▾       ☾                    JD

                                                                                                                                                                                   대기(건수 배지)·처리됨·만료. 좌측 네비
   ▫ 대시보드                거버넌스 › 승인함                                                                                                                       1    탭          탭                                                   SCR-B01
                                                                                                                                                                                   거버넌스에도 배지 표시

   ▫ AI 어시스턴트
                         승인 대기함 (HITL)                                                                                                                                             에이전트·요청자 기준 필터. 그룹 승인자는 자기
                                                                                                                                                          2    필터         선택                                                  SCR-K03
                                                                                                                                                                                   그룹만 조회
                        1                                                                    2
   ▫ 마켓플레이스
                                    대기 2                처리됨                 만료                   에이전트: 전체        ▾          요청자: 전체              ▾
                                                                                                                                                                                   도구·요청자·대화·인자(마스킹)·영향·정책 근거.
                                                                                                                                                          3    승인 카드      카드                                                  SCR-C01
                                                                                                                                                                                   원문 보기는 권한 필요
   ▫ 에이전트 관리

                              ⏸ mail.send — hr-onboarding
                        3
                                                                                                                                      만료 29:10
   ▫ 워크플로                                                                                                                                                 4    사유         입력       ≤500자. 거부 시 필수, 승인 시 선택                    D2-06
                              요청자 홍길동 / 대화 #a1f3 · 요청 14:02
                              인자 to=new@acme.com · subject="입사 안내" · 첨부 1 [원문 보기]
   ▫ 지식(RAG)                  영향 외부 발송 · 데이터 등급 internal · 정책 근거 tool_policy.approve
                                                                                                                                                                                   POST /approvals/{id}/approve|reject → 대화
                                                                                                                                                          5    승인 / 거부    버튼                                                  SCR-C01
                                                                                                                                                                                   재개 또는 종료
   ▫ 플레이그라운드

                             4                                                                        5                                                   6    처리됨 목록     그리드      처리자·시각·사유. 감사 이벤트 링크                       SCR-M04
   ▪ 거버넌스 ●2                                                                                                                                     ⋯
                                 사유 (거부 시 필수, ≤500자)                                                        승인                  거부
                                                                                                                                                                                   만료 시 서버가 취소(MSG-013). 승인자
   ▫ LLM·모델                                                                                                                                               7    만료·권한      규칙                                                  D2-06
                                                                                                                                                                                   역할만, 본인 요청 승인 불가

   ▫ 관측·운영                    ⏸ db.write(orders) — invoice                                                                            만료 25:40

                              요청자 김철수 / 대화 #77c2 · 요청 13:58 · 인자 3건
   ▫ 사용자·조직                   영향 쓰기 작업 · 등급 confidential(L2)


   ▫ 설정

                        6
   설치된 Addon                처리 시각              도구                        요청자            처리           처리자             사유


   ▸ 게시판                    13:41              mail.send                 홍길동            승인           박부장             고객 안내 승인


   ▸ HR 채용                  13:12              file.export               이영희            거부           박부장             L2 반출 불가


                            12:55              db.delete                 admin          만료           -               30분 무응답 → 취소

                        7
                              만료: 서버가 만료시키고 대화는 취소로 종료(MSG-013) · 승인자 역할·그룹만 처리 가능하며 본인 요청은 승인 불가
                              빈 상태: '대기 중인 승인이 없습니다' · 처리 결과는 요청자에게 알림 + 감사 기록


   [‹ 접기]




관련 요구사항(PRD): D2-06


AgentPlaza 화면설계서 · v1.0 · I. 가드레일·거버넌스                                                                                                                                                                                                  77
시스템             AgentPlaza                                   화면 ID                   SCR-I05                                                                화면 유형           탭
화면명             리뷰어 게이트 설정                                   화면 경로                   /governance/reviewer                                                   접근 권한           admin+
우선순위            P1                                           PRD 추적                  D2-05                                                                  작성일 / 버전        2026-09-19 / v1.0

응답을 사용자에게 전달하기 전에 검토하는 리뷰어 에이전트를 지정하고, 점수 임계값에 따라 차단·수정 요청·통과를 나눈다. 적용 범위와 로그 보존 기간을 정하고 최근 판정 분포를 확인한다.



                                                                                                                                                       No   구성요소       유형       기능 설명 / 동작                            연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                               dev                                          🔔3     ko ▾      ☾              JD

                                                                                                                                                                                끄면 모든 응답이 검토 없이 전달. 변경은 감사
   ▫ 대시보드                거버넌스 › 리뷰어 게이트                                                                                                                1    사용 여부      토글                                             D2-05
                                                                                                                                                                                대상

   ▫ AI 어시스턴트
                         리뷰어 게이트 설정                                                                                                                                             reviewer 역할 에이전트 중 선택(D01 목록).
                                                                                                                                                       2    리뷰어 에이전트   선택                                             SCR-D01
                                                                                                                                                                                미지정 시 게이트 비활성
   ▫ 마켓플레이스
                                        정책·데이터 등급                리뷰어 게이트                                                                                                        외부 도구 결과 포함 응답(기본) / 모든 응답
                                                                                                                                                       3    적용 범위      체크박스                                           D2-05
                                                                                                                                                                                (지연·비용 증가)
   ▫ 에이전트 관리

                             1                                                             2
   ▫ 워크플로                                                                                                                          에이전트 목록(D01)        4    차단 기준      구간       < 0.5 차단 · 0.5~0.8 수정 요청 · ≥ 0.8 통과   D2-05
                                          리뷰어 게이트 사용                                           리뷰어: reviewer-default     ▾


   ▫ 지식(RAG)                  끄면 모든 응답이 검토 없이 사용자에게 전달된다(변경은 감사 대상)
                                                                                                                                                       5    임계값·보존     입력·선택    0~1 수치 입력, 로그 보존 기간(기본 90일)           SCR-M04

   ▫ 플레이그라운드
                                                                                                                                                                                최근 7일 통과·수정 요청·차단 건수. 임계값 조정
                              적용 범위                                                                                                                    6    판정 분포      막대                                             SCR-H03
   ▪ 거버넌스 ●2
                                                                                                                                                                                근거
                             3
                                 ✓   외부 도구 결과가 포함된 응답                                             모든 응답 (지연·비용 증가)
   ▫ LLM·모델


   ▫ 관측·운영

                              차단 기준 (리뷰어 점수 0~1)
   ▫ 사용자·조직

                             4
   ▫ 설정
                              < 0.5 차단               0.5~0.8 수정 요청                 ≥ 0.8 통과

   설치된 Addon
                                                                           5
                                                                                                                임계값 변경은 즉시 적용 · 감사 기록
                                 0.50               0.80                       로그 보존 90일          ▾

   ▸ 게시판
                        6
   ▸ HR 채용                    최근 7일 판정 분포 (1,284건)

                              통과                                                                                                1,104건


                              수정 요청                                                                                             141건


                              차단                                                                                                39건


   [‹ 접기]




관련 요구사항(PRD): D2-05


AgentPlaza 화면설계서 · v1.0 · I. 가드레일·거버넌스                                                                                                                                                                                          78
시스템              AgentPlaza                                             화면 ID                 SCR-J01                                                                            화면 유형            페이지
화면명              모델 카탈로그                                                화면 경로                 /llm/models                                                                        접근 권한            admin+
우선순위             P0                                                     PRD 추적                D1-06                                                                              작성일 / 버전         2026-09-19 / v1.0

별칭·공급자·컨텍스트·도구호출·라이선스·상용가능 여부를 한 표에서 관리한다. 행을 열면 단가·verified_at·라이선스 의무·프라이버시 허용 등급(L0~L3)을 보여 주고, 별칭→모델 매핑은 별도 모달에서 다룬다. 참조 구현의 /api/llm/models 동적
목록을 카탈로그 스키마로 확장한 화면이다.


                                                                                                                                                                            No   구성요소       유형       기능 설명 / 동작                                연계
   ▣   AgentPlaza             🔍 검색 (⌘K)                                        dev                                        🔔3         ko ▾           ☾                  JD

                                                                                                                                                                                                     별칭·모델 ID 검색, 공급자·로컬만·상용가능 조합
    ▫ 대시보드                LLM·모델 › 모델 카탈로그                                                                                                                                  1    검색·필터 바    필터                                                 D1-06
                                                                                                                                                                                                     필터

    ▫ AI 어시스턴트
                          모델 카탈로그                                                                                                                                                                    별칭·모델ID·공급자·컨텍스트·도구/비전·허용등급
                                                                                                                                                                            2    모델 표       그리드                                  D1-06
                                                                                                                                                                                                     ·라이선스·상태. 열 정렬
                         1                                                                                                                  3
    ▫ 마켓플레이스                  🔍 별칭·모델 ID 검색                                   공급자 전체▾                   로컬만       상용가능 ▾                        + 모델                별칭 관리
                                                                                                                                                                                                     POST /api/llm/models — 공급자별 입력 필드가
                                                                                                                                                                            3    + 모델       버튼                                          SCR-J02
                         2                                                                                                                                                                           달라짐
    ▫ 에이전트 관리
                             별칭                모델 ID                      공급자           컨텍스트        도구/비전          허용등급          라이선스·상용                    상태
                                                                                                                                                                4                                    PATCH /api/llm/models/{id}. conditional
    ▫ 워크플로                                                                                                                                                                  4    활성 토글      상태 배지                                              D1-06
                             plaza/chat        qwen3:8b                   ollama ●      32k         ✓/✗            L0~L3         Apache-2.0 · allowed       ● 활성
                                                                                                                                                                                                     라이선스는 기본 비활성 + 승인 필요

    ▫ 지식(RAG)                                                                                                                                                                                        행 클릭 → 단가·컨텍스트·라이선스 의무·허용
                             plaza/fast        claude-haiku-4-5           anthropic     200k        ✓/✓            L0~L1         상용 API · allowed           ● 활성            5    상세 드로어     드로어                                                D1-06
                                                                                                                                                                                                     등급 표시
    ▫ 플레이그라운드                (없음)              llama4-scout               vllm ●        128k        ✓/✓            L0~L2         Llama 4 CL · conditional   ○ 비활성
                                                                                                                                                                                                     verified_at 180일 경과 시 주의 배지. 재검증
                                                                                                                                                                            6    재검증 경고     배지                                                 D1-06
    ▫ 거버넌스
                                                                                                                                                                                                     전까지 신규 배치 제한
                             …                 외 12건                      -             -           -              -             -                          -

                                                                                                                                                                                                     별칭 → 모델 매핑. 삭제 시 사용 중 에이전트 수
    ▪ LLM·모델                                                                                                                                                                7    별칭 관리      모달                                                 SCR-J04
                         5                                                                                    7                                                                                      경고
                                 상세 드로어 — plaza/chat (qwen3:8b)                                                   별칭 관리 (모달)
    ▫ 관측·운영

                                 단가 입력 ₩0 / 출력 ₩0 (로컬 실행)
    ▫ 사용자·조직                     컨텍스트 32k · 도구호출 ✓ · 비전 ✗                                                         별칭                 모델                         사용
                                 라이선스 Apache-2.0 · 상용 allowed
                                 의무(obligations) 고지문 포함 · 재배포 표기
                                                                                                                  plaza/chat         qwen3:8b                   7
    ▫ 설정                         프라이버시 허용 등급 L0 · L1 · L2 · L3

                                                                                                                  plaza/fast         claude-haiku-4-5           3
    설치된 Addon
                                                                                                                  plaza/embed        nomic-embed                2
    ▸ 게시판

                                                                                                                  별칭 삭제 시 사용 에이전트 수 경고.
    ▸ HR 채용                                                                                                       등급별 primary/fallback 지정은 SCR-J04.



                              6
                                                  ⚠ verified_at 2025-02-10 · 180 일 경과
                                                                                                                                                                저장




    [‹ 접기]




관련 요구사항(PRD): D1-06


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                                                      79
시스템              AgentPlaza                                         화면 ID                SCR-J02                                                                      화면 유형              페이지
화면명              공급자 연결·키                                           화면 경로                /llm/providers                                                               접근 권한              admin+
우선순위             P0                                                 PRD 추적               D1-03 D9-04                                                                  작성일 / 버전           2026-09-19 / v1.0

퍼블릭 LLM 공급자의 API 키를 등록·검증하고 마스킹 상태로 보관한다. 키 값은 등록 시 1회만 노출되며 실제 값은 시크릿 저장소와 게이트웨이만 보유한다. 재판매 경유 공급자(OpenRouter 등)는 L1 이상 등급 차단 배지를 붙인다.



                                                                                                                                                                 No   구성요소         유형       기능 설명 / 동작                         연계
   ▣   AgentPlaza             🔍 검색 (⌘K)                                    dev                                     🔔3         ko ▾        ☾                 JD

                                                                                                                                                                                            공급자·유형(public/local/재판매)·키 상태·모델
    ▫ 대시보드                LLM·모델 › 공급자 연결·키                                                                                                                      1    공급자 표        그리드                                         D1-03
                                                                                                                                                                                            수·월 사용액

    ▫ AI 어시스턴트
                          공급자 연결·키                                                                                                                                                          마스킹 표시(•••• 7f)·검증 여부·미설정.
                                                                                                                                                                 2    키 상태 배지      상태                                          D1-03
                                                                                                                                                                                            재판매는 L1 이상 금지 경고
    ▫ 마켓플레이스                                                                                                                                        + 공급자
                                                                                                                                                                                   입력(모
                                                                                                                                                                 3    API 키 입력              ≤256자. 저장 후 즉시 마스킹, 재조회 불가         D9-04
                         1                                                                                                                                                         달)
    ▫ 에이전트 관리
                             공급자                  유형                 키 상태                               모델 수          월 사용           동작

    ▫ 워크플로
                                                                         2                                                                                       4    학습 미사용 확인    체크박스     no-training 계약 확인 필수. 미체크 시 저장 불가 D1-03
                             Anthropic            public             •••• 7f 검증 ✓                       3             ₩120k          검증 · 회전 · 해제

    ▫ 지식(RAG)                OpenAI               public             미설정                                -             -              설정
                                                                                                                                                                 5    기본 등급 상한     선택       이 공급자로 보낼 수 있는 최대 프라이버시 등급         SCR-J04

    ▫ 플레이그라운드                OpenRouter           public(재판매)        설정됨 ⚠ L1 이상 금지                     12            ₩8k            검증 · 회전 · 해제
                                                                                                                                                                                            POST providers/{id}/verify → 성공
                                                                                                                                                                 6    검증           버튼                                          SCR-J01
    ▫ 거버넌스                   Ollama               local              http://…:11434 ●                   4             0              SCR-J03                                                MSG-016 / 실패 MSG-017, 모델 목록 갱신

                             vLLM                 local              미구성                                -             -              SCR-J03                                                값은 시크릿 저장소·게이트웨이만 보유(NFR-
    ▪ LLM·모델                                                                                                                                                     7    키 1회 노출 안내   안내                                          SCR-K06
                                                                                                                                                                                            S3). 화면·로그 비노출

    ▫ 관측·운영                     공급자 설정 폼 (모달)                                                        검증 결과 · 키 취급                                                                           새 키 검증 성공 후 교체, 구 키 즉시 폐기.
                                                                                                                                                                 8    회전·해제        버튼                                          D9-04
                                                                                                                                                                                            해제는 확인 다이얼로그
    ▫ 사용자·조직                    API 키 (≤256자 · 저장 후 마스킹)                                                      연결 성공 · 모델 3건 동기화 (MSG-016)

                              3
    ▫ 설정                                                                                                      실패 시 MSG-017 + 원인(401·네트워크)
                                  sk-ant-••••••••••••7f

                                                                                                    7
    설치된 Addon                   베이스 URL                                     조직 ID                           키 값은 등록 직후 1회만 노출되고, 이후 화면·API·로그 어디에도
                                                                                                            표시되지 않는다. 실제 값은 시크릿 저장소(SCR-K06)와
                                                                                                            게이트웨이만 보유(NFR-S3).
    ▸ 게시판
                                  https://api.anthropic.com                  acme

    ▸ HR 채용
                              4
                                  ✓      학습 미사용(no-training) 계약 확인

                                                                                                    8회전: 새 키 입력 → 검증 성공 → 교체 → 구 키 즉시 폐기
                              5                                          6
                                  기본 등급 상한 L1                   ▾                   검증


    [‹ 접기]




관련 요구사항(PRD): D1-03 D9-04


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                                      80
시스템              AgentPlaza                                                     화면 ID                SCR-J03                                                             화면 유형                    페이지
화면명              로컬 런타임·모델 준비                                                   화면 경로                /llm/local                                                          접근 권한                    admin+
우선순위             P0                                                             PRD 추적               D1-01 D1-02 D8-05                                                   작성일 / 버전                 2026-09-19 / v1.0

Ollama·vLLM 런타임의 감지 상태(버전·URL·런타임 종류)와 GPU 배정을 보여 주고, 모델 pull 진행을 실시간으로 표시한다. 오프라인 환경에서는 파일로 모델을 반입한다. 런타임 미감지 시 퍼블릭 전용 저하 모드로 안내한다.



                                                                                                                                                                    No   구성요소               유형       기능 설명 / 동작                               연계
   ▣   AgentPlaza             🔍 검색 (⌘K)                                              dev                                          🔔3      ko ▾   ☾             JD

                                                                                                                                                                                                     감지
    ▫ 대시보드                LLM·모델 › 로컬 런타임                                                                                                                           1    Ollama 상태 카드       상태 카드    결과·버전·엔드포인트·런타임(mlx/cpu/gpu)             D1-01
                                                                                                                                                                                                     표시
    ▫ AI 어시스턴트
                          로컬 런타임·모델 준비                                                                                                                                                               미구성 시 [구성] 안내. GPU 는 llm-provider
                                                                                                                                                                    2    vLLM·GPU           상태 카드                                             D1-02 D8-05
                         1                                                                                 2
                                                                                                                                                                                                     프로필에만 예약
    ▫ 마켓플레이스
                                      Ollama 실행 중                                                                    vLLM 미구성                             구성                                         크기·준비 상태·사용 별칭·삭제. 별칭 사용 중이면
                                                                                                                                                                    3    모델 표               그리드                                   D1-01
    ▫ 에이전트 관리
                                                                                                                                                                                                     삭제 경고
                                  v0.34.2 · http://host.docker.internal:11434                                     GPU NVIDIA A10 24GB ● 사용 가능
                                  런타임 mlx (호스트 네이티브 브리지)                                                          llm-provider 프로필에만 예약 배정
                                                                                                                                                                                                     POST /api/llm/local/pull → SSE 진행률·속도.
    ▫ 워크플로                                                                                                                                                          4    pull 진행            진행 바                                              D1-01
                                                                                                                                                                                                     [취소] 가능

    ▫ 지식(RAG)            3                                                                                                                                                                           모델 이름 입력 후 pull. 오프라인은 파일에서
                             모델                                                 크기              상태                         사용 별칭                     동작             5    모델 추가              입력+버튼                                             D8-05
                                                                                                                                                                                                     가져오기
    ▫ 플레이그라운드
                             qwen3:8b                                           5.2 GB          ✓ 준비                       plaza/chat                삭제
                                                                                                                                                                    6    예열·keep_alive      체크·입력    예열 기본 on, keep_alive 기본 -1(상주)           D1-02
    ▫ 거버넌스
                             nomic-embed-text                                   274 MB          ✓ 준비                       plaza/embed               삭제

                                                                                4                                                                                                                    Docker Metal 불가 → 호스트 네이티브 브리지.
    ▪ LLM·모델                                                                                     41 % · 12 MB/s                                                     7    Apple Silicon 안내   안내                                                D1-01
                                  qwen3:32b 20 GB                               ◌ pull 중                                                                  취소
                                                                                                                                                                                                     미감지 시 저하 모드

    ▫ 관측·운영

                          모델 추가
    ▫ 사용자·조직
                         5
    ▫ 설정                      qwen3:14b                                                           pull                파일에서 가져오기(오프라인)




    설치된 Addon
                         6
                              ✓     모델 예열(preload)                                         keep_alive -1
    ▸ 게시판


    ▸ HR 채용              7
                                  ⚠ Apple Silicon: 컨테이너에서 Metal/GPU 를 쓸 수 없다. Ollama 는 호스트 네이티브로 실행하고 브리지 URL(host.docker.internal)로 연결한다.
                                  런타임이 감지되지 않으면 화면은 저하 모드로 전환되어 '퍼블릭 전용' 배지와 구성 안내를 표시한다.




    [‹ 접기]




관련 요구사항(PRD): D1-01 D1-02 D8-05


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                                                         81
시스템              AgentPlaza                                              화면 ID                 SCR-J04                                                                               화면 유형           페이지
화면명              라우팅·폴백 정책                                               화면 경로                 /llm/routing                                                                          접근 권한           supervisor
우선순위             P0                                                      PRD 추적                D1-05 D1-06                                                                           작성일 / 버전        2026-09-19 / v1.0

프라이버시 등급(L0~L3)별 기본 모델·폴백 체인·차단 목록·이그레스 허용 여부를 한 매트릭스에서 정의한다. 전환 트리거(로컬 장애·429·예산)를 숫자로 지정하고, 저장 전에 dry-run 시험으로 정책이 의도대로 동작하는지 확인한다.



                                                                                                                                                                                No   구성요소       유형       기능 설명 / 동작                                       연계
   ▣   AgentPlaza              🔍 검색 (⌘K)                                    dev                                             🔔3           ko ▾        ☾                     JD

                                                                                                                                                                                                         등급 × primary/fallback/deny/egress. 별칭
    ▫ 대시보드                LLM·모델 › 라우팅·폴백                                                                                                                                       1    정책 매트릭스    편집 표                                                      D1-05
                                                                                                                                                                                                         목록에서 선택

    ▫ AI 어시스턴트
                          라우팅·폴백 정책                                                                                                                                                                      L0 public · L1 internal · L2 confidential · L3
                                                                                                                                                                                2    등급 행       행                                                         D1-05
                                                                                                                                                                                                         regulated 고정 4행
                                                                                                                                                              7
    ▫ 마켓플레이스                                                                                                                                        시험                    저장
                                                                                                                                                                                                         위→아래 순서로 시도. L2 이상에 퍼블릭 지정
                                                                                                                                                                                3    폴백 체인      정렬 목록                                                     D1-06
                         1                                                                                                                                                                               시 저장 차단(MSG-010)
    ▫ 에이전트 관리
                             등급                   primary                         fallback (순서)                                      deny                    egress
                                                                                                                                                                                                         로컬 5xx 연속 3회 → 폴백, 퍼블릭 429 →
    ▫ 워크플로               2                                                              3                                                                                       4    전환 트리거     숫자 입력                                                     D1-05
                                                                                                                                                                                                         다른 키 → 로컬
                             L0 public            local/qwen3-8b                  public/claude-haiku → openrouter/auto              -                       허용

    ▫ 지식(RAG)                                                                                                                                                                                            월 예산 80% 도달 시 로컬 강제. 사용량은
                                                                                                                                                                                5    예산 강제      숫자 입력                                                     SCR-J05
                             L1 internal          public/claude-sonnet            public/gpt-5 → local/qwen3-8b                      openrouter/*            허용                                          SCR-J05
    ▫ 플레이그라운드
                             L2 confidential      local/qwen3-8b                  local/qwen3-32b                                    public/*                차단                                          등급·별칭·상황을 골라 dry-run. 실제 호출 없이
                                                                                                                                                                                6    정책 시험      폼                                                         D1-05
    ▫ 거버넌스
                                                                                                                                                                                                         경로만 판정
                             L3 regulated         local/qwen3-8b                  (없음)                                               *                       차단
                                                                                                                                                                                                         PUT /api/llm/routing → 게이트웨이 즉시 반영
    ▪ LLM·모델                                                                                                                                                                    7    저장         버튼                                                        SCR-M03
                         4                                                                               6
                                                                                                                                                                                                         + 감사 기록
                                전환 트리거                                                                        정책 시험 (dry-run)
    ▫ 관측·운영


    ▫ 사용자·조직                    로컬 5xx 연속 실패
                                                                            3회
                                                                                                                  등급 L2          ▾              plaza/chat            ▾
    ▫ 설정
                                퍼블릭 429 → 다른 키 → 로컬

    설치된 Addon                                                                                                     상황: 로컬 런타임 장애                                       ▾

    ▸ 게시판                       월 예산 도달 시 로컬 강제
                                                                            80 %
    ▸ HR 채용                                                                                                           결과: 요청 실패 (폴백 금지)
                                                                                                                      정책대로 동작 — L2 는 퍼블릭 폴백 없음
                              5
                                   L2 이상 등급에 퍼블릭 모델을 넣으면 저장 차단(MSG-010)




    [‹ 접기]




관련 요구사항(PRD): D1-05 D1-06


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                                                                 82
시스템              AgentPlaza                          화면 ID               SCR-J05                                                                               화면 유형            페이지
화면명              사용량·비용                              화면 경로               /llm/usage                                                                            접근 권한            admin+
우선순위             P1                                  PRD 추적              D10-04                                                                                작성일 / 버전         2026-09-19 / v1.0

토큰·비용·폴백 발생·로컬 비율을 기간과 그룹(에이전트·사용자·별칭) 기준으로 본다. 일별 추이와 상세 표를 함께 제공하고 월 예산 소진율을 표시한다. 예산 80% 도달 시 라우팅 정책이 로컬 강제로 전환된다.



                                                                                                                                                          No   구성요소       유형       기능 설명 / 동작                             연계
   ▣   AgentPlaza             🔍 검색 (⌘K)                 dev                                                🔔3          ko ▾       ☾                  JD

                                                                                                                                                                                   기간(7/30/90일)과 그룹 기준(에이전트·
    ▫ 대시보드                LLM·모델 › 사용량·비용                                                                                                                 1    기간·그룹 필터   선택                                              D10-04
                                                                                                                                                                                   사용자·별칭) 전환

    ▫ AI 어시스턴트
                          사용량·비용
                                                                                                                                                          2    핵심 지표      스탯 타일    토큰·비용·폴백 발생 수·로컬 처리 비율 4종              D10-04
                                                                                   1                                                    6
    ▫ 마켓플레이스                                                                           기간 30일          ▾             그룹 에이전트 ▾                     CSV
                                                                                                                                                                          막대       일별 토큰·비용. 막대 클릭 → 해당 일자
                                                                                                                                                          3    일별 추이                                                      SCR-M02
                         2                                                                                                                                                그래프      트레이스 목록
    ▫ 에이전트 관리
                              토큰                비용                                     폴백 발생                                   로컬 비율

    ▫ 워크플로                                                                                                                                                4    상세 표       그리드      에이전트·별칭별 토큰·비용. 열 정렬·페이징               D10-04
                              12.4 M            ₩184k                                  23 회                                    71 %
    ▫ 지식(RAG)                                                                                                                                                             진행 바     소진율 표시. 80% 도달 시 로컬 강제.
                                                                                                                                                          5    월 예산                                                       SCR-J04
                                                                                                                                                                          +입력      supervisor 만 편집
    ▫ 플레이그라운드            3                                                     4
                              일별 토큰·비용 추이                                              에이전트·별칭별 사용(정렬)                                                                             GET /api/llm/usage/export — 현재 필터 범위
                                                                                                                                                          6    CSV 내보내기   버튼                                              D10-04
    ▫ 거버넌스
                                                                                                                                                                                   그대로 출력
                              09-14                             270k
                                                                                       에이전트                     별칭               토큰         비용
    ▪ LLM·모델
                              09-15                             369k
                                                                                       hr-onboarding            plaza/chat       4.1M       ₩62k
    ▫ 관측·운영
                              09-16                             228k
                                                                                       board                    plaza/fast       3.3M       ₩51k
    ▫ 사용자·조직
                              09-17                             447k
                                                                                       rag-agent                plaza/embed      2.8M       ₩0

    ▫ 설정                                                        327k
                              09-18
                                                                                       …                        외 9건             2.2M       ₩71k


                              09-19                             405k
    설치된 Addon


    ▸ 게시판


    ▸ HR 채용              5
                              월 예산


                              ₩300,000 중 61 %                                                                                 예산 ₩300,000
                                                80 % 도달 시 로컬 강제(SCR-J04) · supervisor 만 편집



    [‹ 접기]




관련 요구사항(PRD): D10-04


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                                 83
시스템              AgentPlaza                                      화면 ID               SCR-J06                                                                화면 유형           탭
화면명              임베딩·리랭크 설정                                      화면 경로               /llm/embeddings                                                        접근 권한           admin+
우선순위             P1                                              PRD 추적              D1-07                                                                  작성일 / 버전        2026-09-19 / v1.0

RAG 파이프라인이 쓰는 임베딩 모델·차원·백엔드와 리랭크 백엔드를 지정한다. 차원이 바뀌면 기존 벡터와 호환되지 않으므로 저장 전에 재인덱싱 대상 컬렉션을 확인 다이얼로그로 알린다.



                                                                                                                                                       No   구성요소       유형       기능 설명 / 동작                               연계
   ▣   AgentPlaza             🔍 검색 (⌘K)                               dev                                     🔔3          ko ▾     ☾              JD


    ▫ 대시보드                LLM·모델 › 임베딩·리랭크                                                                                                             1    탭          탭        LLM·모델 그룹 내 탭. URL 에 반영                  D1-07


    ▫ AI 어시스턴트
                          임베딩·리랭크 설정                                                                                                                                            plaza/embed — 지식(RAG) 컬렉션이 참조하는
                                                                                                                                                       2    임베딩 별칭     입력                                                D1-07
                                                                                                                                                                                논리 이름
                         1
    ▫ 마켓플레이스                      모델 카탈로그                공급자                로컬 런타임                  라우팅                    사용량         임베딩·리랭크
                                                                                                                                                       3    모델·차원      선택·입력    모델 선택 시 차원 자동 채움. 수동 변경은 경고              D1-07
    ▫ 에이전트 관리
                                                                                          4
                              임베딩                                                             선택 가능한 백엔드                                                                        Ollama nomic-embed 768 / TEI bge-m3
    ▫ 워크플로                                                                                                                                             4    백엔드 후보     표                                                 D1-07
                                                                                                                                                                                1024 / 퍼블릭 1536
                              별칭
    ▫ 지식(RAG)                                                                                                                                                                   사용 on/off, 백엔드(TEI /rerank | llama.cpp
                                                                                              백엔드             모델                       차원              5    리랭크        토글·선택                                             D1-07
                              2                                                                                                                                                 /reranking)·모델 지정
    ▫ 플레이그라운드                     plaza/embed
                                                                                              Ollama          nomic-embed-text         768
                                                                                                                                                                                차원 변경 시 대상 컬렉션 목록·예상 소요 표시
                              모델                                 차원                                                                                    6    재인덱싱 경고    안내                                                D1-07
    ▫ 거버넌스
                                                                                                                                                                                후 확인
                                                                                              TEI             bge-m3                   1024
                              3
    ▪ LLM·모델                      nomic-embed-text       ▾        768                         퍼블릭             text-embedding-3         1536


                                                                                              퍼블릭 임베딩은 등급 상한(SCR-J04)을 넘는 컬렉션에 쓸 수 없다.
    ▫ 관측·운영                   백엔드 Ollama (로컬) · 배치 32 · 정규화 on



    ▫ 사용자·조직


    ▫ 설정                      리랭크


                              5
    설치된 Addon                             리랭크 사용                      TEI /rerank                      ▾         모델 bge-reranker              ▾

    ▸ 게시판
                                                                   대체 백엔드: llama.cpp /reranking · top-k 재정렬 후 상위 N 만 컨텍스트에 투입

    ▸ HR 채용



                         6
                              ⚠ 임베딩 모델·차원을 바꾸면 기존 벡터와 호환되지 않는다. 저장 시 재인덱싱이 필요한 컬렉션 목록과 예상 소요를 확인 다이얼로그로 보여 준다.




    [‹ 접기]




관련 요구사항(PRD): D1-07


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                              84
시스템              AgentPlaza                                         화면 ID                     SCR-J07                                                                              화면 유형            페이지
화면명              CLI 에이전트 백엔드                                       화면 경로                     /llm/cli-agents                                                                      접근 권한            supervisor
우선순위             P1                                                 PRD 추적                    D1-04                                                                                작성일 / 버전         2026-09-19 / v1.0

Claude Code·Codex·Gemini CLI 같은 CLI 코딩 에이전트를 플랫폼 백엔드로 등록하고 권한을 제한한다. 어댑터(NDJSON / ACP)·작업 디렉터리·허용 도구·타임아웃을 지정하고, 시험 실행으로 이벤트 스트림이 정상인지 확인한 뒤 사용한다.



                                                                                                                                                                              No   구성요소       유형        기능 설명 / 동작                              연계
   ▣   AgentPlaza              🔍 검색 (⌘K)                                 dev                                            🔔3          ko ▾          ☾                      JD

                                                                                                                                                                                                        이름·종류·어댑터·작업 디렉터리·승인 정책·헬스
    ▫ 대시보드                LLM·모델 › CLI 에이전트 백엔드                                                                                                                               1    백엔드 표      그리드                                               D1-04
                                                                                                                                                                                                        상태

    ▫ AI 어시스턴트
                          CLI 에이전트 백엔드                                                                                                                                                                  NDJSON(-p 스트림) 또는 ACP(--acp). 종류에
                                                                                                                                                                              2    어댑터        선택                                                D1-04
                                                                                                                                                                                                        따라 기본값 제시
                                                                                                                                                       7
    ▫ 마켓플레이스                                                                                                                                                      + 등록
                                                                                                                                                                                                        종류·바이너리 경로/컨테이너 이미지·허용 도구
                                                                                                                                                                              3    등록 폼       모달                                                D1-04
                         1                                                                                                                                                                              ·MCP 주입 설정
    ▫ 에이전트 관리
                             이름                     종류                      어댑터                      작업 디렉터리                           승인                  상태
                                                                    2                                                              5                                                                    샌드박스 볼륨 하위 경로만 허용. 그 외 경로는
    ▫ 워크플로                                                                                                                                                                    4    작업 디렉터리    입력                                                D1-04
                             claude-code            Claude Code             NDJSON (-p)              /work/sandbox/*                   항상                  ● OK
                                                                                                                                                                                                        저장 차단

    ▫ 지식(RAG)                                                                                                                                                                                           항상 승인 / 허용목록 도구는 자동. 승인은
                             gemini-cli             Gemini CLI              ACP (--acp)              /work/sandbox/*                   허용목록                ● OK               5    승인 정책      선택                                                SCR-I04
                                                                                                                                                                                                        승인함으로 전달
    ▫ 플레이그라운드                codex-cli              Codex CLI               NDJSON (-p)              /work/sandbox/*                   항상                  ○ 미시험
                                                                                                                                                                                                        프롬프트 실행 후 이벤트 스트림
                                                                                                                                                                              6    시험 실행      폼+스트림                                             D1-04
    ▫ 거버넌스
                                                                                                                                                                                                        (session·tool·message) 확인

                         3                                                                            6                                                                                                 POST /api/llm/cli-agents → 헬스 확인 후 목록
    ▪ LLM·모델                                                                                                                                                                  7    등록         버튼                                                D1-04
                                등록 폼 (모달)                                                                  시험 실행                                                                                        반영. supervisor 전용

    ▫ 관측·운영                     종류                                어댑터

    ▫ 사용자·조직                                                                                                 프롬프트: 저장소 구조를 요약해줘
                                  Claude Code       ▾              NDJSON                 ▾

    ▫ 설정
                                바이너리 경로 / 컨테이너 이미지                                                                                                              실행


    설치된 Addon                                                                                                {"type":"session.start","id":"s_01"}
                                  docker://plaza/claude-code:1.0                                             {"type":"tool.call","name":"read_file"}
                                                                                                             {"type":"tool.result","bytes":812}
    ▸ 게시판                                                                                                    {"type":"message","role":"assistant"}
                                                                                                             {"type":"session.end","usage":{...}}
                                작업 디렉터리                                 타임아웃
    ▸ HR 채용
                              4
                                  /work/sandbox/*                       600 s


                                  ✓       허용 도구 목록만 노출 · MCP 서버 주입


    [‹ 접기]




관련 요구사항(PRD): D1-04


AgentPlaza 화면설계서 · v1.0 · J. LLM·모델                                                                                                                                                                                                                       85
시스템             AgentPlaza                                      화면 ID                SCR-K01                                                              화면 유형            페이지
화면명             사용자 관리                                          화면 경로                /users                                                               접근 권한            admin+
우선순위            P0                                              PRD 추적               D9-02                                                                작성일 / 버전         2026-09-19 / v1.0

계정 생성·역할 변경·상태 토글·임시 비밀번호 발급·세션 강제 종료를 한 화면에서 처리한다. 검색·필터·페이징과 선택 일괄 동작을 제공하고, 본인·동급 이상 역할은 제어할 수 없도록 버튼을 비활성화한다.



                                                                                                                                                     No   구성요소       유형       기능 설명 / 동작                             연계
  ▣   AgentPlaza                🔍 검색 (⌘K)                           dev                                       🔔3       ko ▾       ☾             JD

                                                                                                                                                                              아이디·이름 검색, 역할·상태·조직 필터. 서버
   ▫ 대시보드                사용자·조직 › 사용자                                                                                                                1    검색·필터      필터                                              D9-02
                                                                                                                                                                              페이징

   ▫ AI 어시스턴트
                         사용자 관리                                                                                                                                               체크박스·아이디·이름·역할·조직/그룹·상태·
                                                                                                                                                     2    사용자 표      그리드                                             D9-02
                                                                                                                                                                              마지막 로그인
                        1
   ▫ 마켓플레이스                     🔍 아이디·이름 검색                 역할      ▾            상태     ▾        조직       ▾               + 사용자           초대 링크
                                                                                                                                                                              클릭 → 확인 후 PATCH /api/users/{id}/status.
                                                                                                                                                     3    상태 토글      상태 배지                                            D9-02
                        2                                                                                                                                                     비활성은 로그인 차단
   ▫ 에이전트 관리


   ▫ 워크플로
                            ☐       아이디       이름
                                                       3
                                                            역할               조직/그룹                   상태            마지막 로그인
                                                                                                                              4
                                                                                                                                      동작

                                                                                                                                                     4    행 동작       메뉴
                                                                                                                                                                              편집 ·  🔑
                                                                                                                                                                                   임시 비밀번호(1회 노출) · ⋯
                                                                                                                                                                                                                     SCR-A04
                            ☑       hong      홍길동           admin            ACME/인사팀                ● 활성          09-19 09:12        편집   🔑⋯                                 역할/그룹/세션/삭제

   ▫ 지식(RAG)
                            ☐       kim       김철수           user             ACME/영업팀                ○ 비활성         08-30              편집   🔑⋯        5    일괄 동작      툴바       선택 사용자 비활성·그룹 이동·세션 강제 종료              D9-02

   ▫ 플레이그라운드                ☐       lee       이영희           감사자              ACME/감사                 ● 활성          09-18 17:40        편집   🔑⋯
                                                                                                                                                                              아이디·이름·비밀번호·역할·조직/그룹. 비밀번호
                                                                                                                                                     6    생성 폼       모달                                              D9-02
   ▫ 거버넌스
                                                                                                                                                                              정책 검증
                                    …         외 128명        -                -                       -             -                  -
                        5
                                                                                                                                                                              본인·동급 이상 제어 불가, admin 은 자기 조직
   ▫ LLM·모델                                                                                                                                          7    제어 규칙      규칙                                              D9-02
                                1명 선택됨                              일괄 비활성                     그룹 이동                     세션 강제 종료                                             만. 삭제는 재입력 확인

   ▫ 관측·운영
                        6
   ▪ 사용자·조직                     사용자 생성 (모달)                                                     제어 규칙 · 부가 동작


   ▫ 설정                         아이디                        이름                                  7· 본인 계정과 동급 이상 역할은 제어 불가
                                                                                                  (버튼 비활성 + 사유 툴팁)
                                                                                                · admin 은 자기 조직 사용자만
   설치된 Addon
                                  park                     박민수                                  ·🔑  임시 비밀번호 발급 → 1회 노출(MSG-020)
                                                                                                · ⋯ 역할 변경 · 그룹 이동 · 세션 종료 · 삭제
                                                                                                · 삭제는 아이디 재입력 확인
   ▸ 게시판                        비밀번호                       역할

   ▸ HR 채용
                                  ••••••••                 user                  ▾




                                  조직/그룹 ACME / 영업팀                               ▾

   [‹ 접기]




관련 요구사항(PRD): D9-02


AgentPlaza 화면설계서 · v1.0 · K. 조직·사용자·권한                                                                                                                                                                                         86
시스템             AgentPlaza                       화면 ID                   SCR-K02                                                                   화면 유형            페이지
화면명             조직·그룹·구성원                        화면 경로                   /orgs                                                                     접근 권한            supervisor·조직 admin
우선순위            P1                               PRD 추적                  X09 D6-05                                                                 작성일 / 버전         2026-09-19 / v1.0

조직(테넌트)과 부서 그룹, 구성원을 관리해 에이전트 배치 대상을 만든다. 조직 유형(company/government/personal)에 따라 노출 정책과 기본 등급이 달라지고, 그룹은 배치·권한 부여의 최소 단위다.



                                                                                                                                              No   구성요소       유형        기능 설명 / 동작                            연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                    dev                                   🔔3         ko ▾       ☾                  JD

                                                                                                                                                                        supervisor 는 전체, 조직 admin 은 자기 조직만.
   ▫ 대시보드                사용자·조직 › 조직                                                                                                          1    조직 목록      목록                                              X09
                                                                                                                                                                        선택 시 우측 상세

   ▫ AI 어시스턴트
                         조직·그룹·구성원                                                                                                                                      이름·코드(^[a-z0-9-]{2,40}$)·유형·설정.
                                                                                                                                              2    조직 상세      폼                                               X09
                                                                                                                                                                        유형 변경은 노출 정책 재평가 경고
                                                                                                                  6
   ▫ 마켓플레이스                                                                                                               + 조직 (supervisor)
                                                                                                                                                                        이름 ≤50자. 에이전트 배치·권한 부여의 대상
                                                                                                                                              3    그룹(부서)     목록+모달                                           D6-05
                        1                                                                                                                                               단위
   ▫ 에이전트 관리
                             조직 목록                 ACME 식품 — 상세

   ▫ 워크플로                                                                                                                                     4    구성원        그리드       사용자·소속 그룹·역할. 추가·이동·제거                D9-02
                                                   조직 이름                                    코드                    유형
                                ACME 식품
   ▫ 지식(RAG)                                      2                                                                                                                     이 조직에 배치된 에이전트 수·적용 팩. 클릭 →
                                                                                                                                              5    도입 현황      요약                                              D6-05
                                company                ACME 식품                                 acme               company            ▾                                  배치 화면
   ▫ 플레이그라운드

                                서울시                설정 노출 정책 internal · 기본 등급 L1 · SSO 그룹 매핑 acme-*                                            6    + 조직       버튼        POST /api/orgs. supervisor 만 생성 가능    X09
   ▫ 거버넌스
                                government
                                                  3
                                                   그룹(부서)                                                                       + 그룹
   ▫ LLM·모델

                                (개인)
   ▫ 관측·운영                                                      인사팀 12                  영업팀 8                     IT 5
                                personal

   ▪ 사용자·조직                                       4
                                                   구성원                                                추가          이동                제거

   ▫ 설정                      supervisor 는 전체,
                             admin 은 자기 조직만 조회        사용자                              그룹                         역할


   설치된 Addon                                          홍길동 (hong)                       인사팀                        admin


   ▸ 게시판                                              김철수 (kim)                        영업팀                        user


   ▸ HR 채용                                            …                                외 23명                      -


                                                  5
                                                          도입 현황 배치된 에이전트 7 · 적용 팩 pack-hr → 상세 보기




   [‹ 접기]




관련 요구사항(PRD): X09 D6-05


AgentPlaza 화면설계서 · v1.0 · K. 조직·사용자·권한                                                                                                                                                                                87
시스템             AgentPlaza                                               화면 ID                 SCR-K03                                                                화면 유형                페이지
화면명             역할·권한 매트릭스                                               화면 경로                 /settings/roles                                                        접근 권한                supervisor
우선순위            P1                                                       PRD 추적                D9-02                                                                  작성일 / 버전             2026-09-19 / v1.0

역할 × 기능 권한을 한 표에서 지정하고, 아래쪽에서 에이전트 × capability 로 확장한다. supervisor 행은 잠겨 있고, 저장 전에 영향 받는 사용자·조직 수를 미리보기로 보여 준 뒤 감사 기록과 함께 반영한다.



                                                                                                                                                                 No   구성요소           유형        기능 설명 / 동작                               연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                       dev                                           🔔3        ko ▾     ☾             JD

                                                                                                                                                                                     체크
   ▫ 대시보드                설정 › 역할·권한                                                                                                                              1    권한 매트릭스                  권한 행 × 역할 열. 기본값은 PRD 역할 정의              D9-02
                                                                                                                                                                                     그리드

   ▫ AI 어시스턴트
                         역할·권한 매트릭스
                                                                                                                                                                 2    supervisor 열   잠금        해제 불가. 잠금 아이콘 + 사유 툴팁                    D9-02

   ▫ 마켓플레이스                                                                                                   역할 admin      ▾                 + 사용자 정의 역할
                                                                                                                                                                                               새 역할 추가 후 열 생성. 이름·설명·기반 역할
                                                                                                                                                                 3    사용자 정의 역할      버튼                                                 D9-02
                        1                                                                                                                                                                      지정
   ▫ 에이전트 관리
                            권한                              supervisor             admin               user          승인자             감사자          사용자 정의
                        2                            3                                                                                                                에이전트 ×         체크
   ▫ 워크플로                                                                                                                                                        4                             에이전트별 read·write·tool.call·admin 세분 권한   D9-02
                            에이전트 설치·배치                      ✓ (잠금)                 ☑                   ☐             ☐               ☐            ☐
                                                                                                                                                                      capability     그리드

   ▫ 지식(RAG)
                            승인 처리(HITL)                     ✓ (잠금)                 ☑                   ☐             ☑               ☐            ☐              5    기본값 안내         안내        기본 권한은 PRD 정의를 따르며 초기화 가능                D9-02

   ▫ 플레이그라운드                감사 원장 조회                        ✓ (잠금)                 조회만                 ☐             ☐               ☑            ☐
                                                                                                                                                                                     다이얼로
                                                                                                                                                                 6    변경 미리보기                  추가·제거 항목과 영향 받는 사용자·조직 수 표시              D9-02
   ▫ 거버넌스                   LLM·라우팅 변경                      ✓ (잠금)                 ☐                   ☐             ☐               ☐            ☐
                                                                                                                                                                                     그

                                                            (아래 매트릭스에서
   ▫ LLM·모델                 에이전트별 capability                에이전트 × capability                                                                                    7    저장             버튼        PUT /api/roles → 즉시 반영 + 감사 원장 기록        SCR-M03
                                                            로 확장)

   ▫ 관측·운영
                        4                                                                                           6
                              에이전트 × capability 확장                                                                       변경 미리보기 (다이얼로그)
   ▫ 사용자·조직


   ▪ 설정                       에이전트                   read            write         tool.call       admin                 admin 역할 변경 요약
                                                                                                                         · 추가: 감사 원장 조회(읽기)
                                                                                                                         · 제거: LLM·라우팅 변경
                              board                  ☑               ☑             ☑               ☐
   설치된 Addon

                              hr-onboarding          ☑               ☐             ☑               ☐
   ▸ 게시판                                                                                                                 영향 받는 사용자 12명
                                                                                                                         영향 받는 조직 2개
                              rag-agent              ☑               ☐             ☐               ☐
   ▸ HR 채용


                             5supervisor 행은 잠금(해제 불가). 기본값은 PRD 역할 정의를 따른다.
                                                                                                                                              7
                                                                                                                                취소                    저장



   [‹ 접기]




관련 요구사항(PRD): D9-02


AgentPlaza 화면설계서 · v1.0 · K. 조직·사용자·권한                                                                                                                                                                                                            88
시스템             AgentPlaza                                             화면 ID                   SCR-K04                                                                          화면 유형            페이지
화면명             서비스 계정·API 키                                           화면 경로                   /settings/api-keys                                                               접근 권한            admin+
우선순위            P0                                                     PRD 추적                  D9-03                                                                            작성일 / 버전         2026-09-19 / v1.0

외부 MCP·A2A·REST 클라이언트가 쓰는 서비스 키를 발급하고 범위·만료·허용 IP 를 지정한다. 발급된 키 값은 1회만 노출되며 Claude Desktop·Cursor 설정 스니펫을 함께 제공한다. 회전·철회는 즉시 반영되고 감사에 남는다.



                                                                                                                                                                           No   구성요소       유형       기능 설명 / 동작                              연계
  ▣   AgentPlaza              🔍 검색 (⌘K)                                       dev                                            🔔3          ko ▾       ☾                 JD


   ▫ 대시보드                설정 › 서비스 계정·API 키                                                                                                                                 1    키 목록       그리드      이름·용도·범위·만료·마지막 사용. 만료 임박 배지 D9-03


   ▫ AI 어시스턴트
                         서비스 계정·API 키
                                                                                                                                                                           2    만료 임박      배지       30일 이내 만료 시 주의 배지 + 회전 유도               D9-03

   ▫ 마켓플레이스                                                                                                                                                  + 키 발급
                                                                                                                                                                                                    이름·범위·용도(MCP|A2A|REST)·만료·허용 IP.
                                                                                                                                                                           3    발급 폼       모달                                               D9-03
                        1                                                                                                                                                                           범위 필수
   ▫ 에이전트 관리
                            이름                  용도            범위(에이전트·capability)                            만료                        마지막 사용           동작
                                                                                                                  2                                                                                 에이전트 다중 + capability 조합. 최소 권한 안내
   ▫ 워크플로                                                                                                                                                                  4    범위 선택      다중 선택                                            SCR-K03
                            cursor-dev          MCP           board:*, ragagent:retrieve                     2027-03 ⚠ 임박              1시간 전            회전 · 철회
                                                                                                                                                                                                    문구 고정

   ▫ 지식(RAG)
                            ci-runner           REST          *:read                                         -                         3일 전             회전 · 철회            5    만료·허용 IP   선택·입력    기본 90일. CIDR 로 호출 출발지 제한                D9-03

   ▫ 플레이그라운드                partner-a2a         A2A           hr-onboarding:tool.call                        2026-12                   미사용              회전 · 철회
                                                                                                                                                                                                    키 1회 노출 + 복사 버튼. 재조회 불가
                                                                                                                                                                           6    발급 결과      모달                                               D9-03
   ▫ 거버넌스
                                                                                                                                                                                                    (MSG-020)

                        3                                                                            6                                                                                              Claude Desktop·Cursor 용 mcpServers 설정
   ▫ LLM·모델                                                                                                                                                                7    연결 스니펫     코드                                               D9-03
                               키 발급 폼 (모달)                                                               발급 결과 (1회 노출)                                                                              조각 복사

   ▫ 관측·운영                     이름

   ▫ 사용자·조직                                                                                                  ap_sk_01J8…K2Q9                                   복사
                                 cursor-dev

   ▪ 설정                        범위 (에이전트 다중 선택)                            용도                             7
                                                                                                             {
                             4                                                                                   "mcpServers": {
                                                                                                                   "agentplaza": {
   설치된 Addon                     board × , rag-agent ×    ▾                 MCP            ▾                         "url": "https://plaza/mcp",
                                                                                                                     "headers": {"Authorization":
                                                                                                                       "Bearer ap_sk_…"}}}}
   ▸ 게시판
                               만료                          허용 IP(CIDR)

   ▸ HR 채용                   5
                                 90일             ▾            10.0.0.0/8


                               최소 권한 안내: 필요한 에이전트·capability 만 고른다.                                      MSG-020 — 이 값은 다시 볼 수 없다. 철회 시 즉시 무효 + 감사.




   [‹ 접기]




관련 요구사항(PRD): D9-03


AgentPlaza 화면설계서 · v1.0 · K. 조직·사용자·권한                                                                                                                                                                                                                89
시스템             AgentPlaza                                             화면 ID            SCR-K05                                                         화면 유형             페이지
화면명             SSO·IdP 설정                                             화면 경로            /settings/sso                                                   접근 권한             supervisor
우선순위            P1                                                     PRD 추적           D9-01                                                           작성일 / 버전          2026-09-19 / v1.0

OIDC 발급자·클라이언트·역할 매핑을 설정하고 연결을 시험한다. 디스커버리로 엔드포인트를 자동으로 채우며, IdP 그룹을 플랫폼 역할·조직·그룹으로 매핑한다. 로컬 로그인은 비상 경로로 유지하는 것을 기본값으로 둔다.



                                                                                                                                                   No   구성요소        유형        기능 설명 / 동작                             연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                    dev                                   🔔3        ko ▾       ☾        JD


   ▫ 대시보드                설정 › SSO·IdP                                                                                                              1    SSO 사용 토글   토글        off 면 아래 설정 비활성. 연결 상태 배지 병기           D9-01


   ▫ AI 어시스턴트
                         SSO·IdP 설정                                                                                                                                           Issuer URL(https)·클라이언트 ID·시크릿(시크릿
                                                                                                                                                   2    발급자·클라이언트   입력                                               D9-01
                                                                                                                                                                              저장소 참조)
                        1
   ▫ 마켓플레이스
                                                                                          연결 상태: 미검증                                                                          .well-known 조회로 엔드포인트 자동 채움.
                                                  SSO(OIDC) 사용                                                                                     3    디스커버리       버튼                                               D9-01
                                                                                                                                                                              리다이렉트 URI 는 읽기
   ▫ 에이전트 관리

                                                                                                                                                                              IdP 그룹 → 역할 / 조직 / 그룹. 미매핑 그룹은
   ▫ 워크플로                                                                                                                                          4    역할 매핑       편집 표                                             SCR-K03
                                                                                                                                                                              기본 역할

   ▫ 지식(RAG)                 발급자(Issuer) URL                                                                                                                                  자동 생성 또는 대기(관리자 승인 후 활성). 기본
                                                                                                                                                   5    신규 사용자      라디오                                    D9-01
                             2                                                                          3                                                                     대기
   ▫ 플레이그라운드                       https://sso.acme.com/realms/plaza                                                 디스커버리

                                                                                                                                                   6    로컬 로그인 유지   체크박스      비상 경로. 해제 시 경고 + 연결 시험 성공 필수           D9-01
   ▫ 거버넌스
                                                                                                        리다이렉트 URI (읽기 전용)
                                   클라이언트 ID plaza                        시크릿 •••• (시크릿 저장소)             https://console/…/callback                                            POST /api/sso/test → 성공 MSG-016 / 실패
   ▫ LLM·모델                                                                                                                                        7    연결 시험·저장    버튼                                               D9-01
                                                                                                                                                                              MSG-017
                        4
   ▫ 관측·운영
                             역할 매핑 (편집 표)                                                                   신규 사용자 처리

   ▫ 사용자·조직
                                                                                                            5
                                 IdP 그룹                     역할            조직 / 그룹                                    자동 생성(매핑 역할 부여)
   ▪ 설정
                                 plaza-admins               admin         ACME / IT
                                                                                                                     대기(관리자 승인 후 활성)
   설치된 Addon
                                 plaza-auditors             감사자           ACME / 감사

   ▸ 게시판                                                                                                    6
                                 plaza-users                user          ACME / (없음)
                                                                                                                ✓    로컬 로그인 유지(비상 경로)

   ▸ HR 채용




                             ⚠ 로컬 로그인을 해제하면 IdP 장애 시 접속 경로가 사라진다. 해제 전 연결 시험 성공 필수.                                   7
                                                                                                                             연결 시험       저장


   [‹ 접기]




관련 요구사항(PRD): D9-01


AgentPlaza 화면설계서 · v1.0 · K. 조직·사용자·권한                                                                                                                                                                                         90
시스템             AgentPlaza                                                화면 ID              SCR-K06                                                                        화면 유형            페이지
화면명             시크릿 관리                                                    화면 경로              /settings/secrets                                                              접근 권한            supervisor
우선순위            P1                                                        PRD 추적             D9-04                                                                          작성일 / 버전         2026-09-19 / v1.0

시크릿을 참조 단위로 등록·회전하고 사용처를 추적한다. 값은 어떤 화면·API·로그에도 표시되지 않으며, 회전은 검증 → 교체 → 재시작 대상 확인 순으로 진행한다. 90일 이상 회전하지 않으면 경고를 띄운다.



                                                                                                                                                                       No   구성요소       유형        기능 설명 / 동작                             연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                       dev                                         🔔3          ko ▾        ☾                JD

                                                                                                                                                                                                 compose secrets(sops) 또는 OpenBao. 전환
   ▫ 대시보드                설정 › 시크릿                                                                                                                                      1    저장소 선택     선택                                               D9-04
                                                                                                                                                                                                 시 마이그레이션 안내

   ▫ AI 어시스턴트
                         시크릿 관리                                                                                                                                                                  이름·유형·사용처·마지막 회전. 값 열은 존재하지
                                                                                                                                                                       2    시크릿 목록     그리드                                              D9-04
                                                                                                                                                                                                 않음
                                                                                                         1
   ▫ 마켓플레이스                                                                                                  저장소 compose secrets(sops) ▾                    + 시크릿
                                                                                                                                                                       3    회전 필요 표시   배지        미회전 또는 90일 경과 시 주의 배지                  D9-04
   ▫ 에이전트 관리            2
                            이름                                     유형              사용처(에이전트·공급자)                                 마지막 회전                동작

   ▫ 워크플로                                                                                         3                                                                    4    회전 모달      모달        새 값 입력 → 검증 → 교체. 구 값 즉시 폐기            D9-04
                            ANTHROPIC_API_KEY                      공급자 키           llm-gateway                                   30일 전                 회전 · 사용처

   ▫ 지식(RAG)                                                                                                                                                                                     참조 중인 서비스 목록 표시 후 확인. 재시작 중
                            TOOL_PROXY_API_KEY                     내부 토큰           toolproxy, board-be                           미회전 ⚠                 회전 · 사용처        5    재시작 대상     목록                                               SCR-M04
                                                                                                                                                                                                 503 안내
   ▫ 플레이그라운드                SSO_CLIENT_SECRET                      OIDC            gateway                                       12일 전                 회전 · 사용처
                                                                                                                                                                       6    값 비노출 원칙   규칙        목록·상세·API·로그 모두 마스킹. 참조만 관리            D9-04
   ▫ 거버넌스                   …                                      -               외 8건                                          -                     -


   ▫ LLM·모델                                                                                                                                                            7    사용처 추적     버튼        해당 시크릿을 참조하는 에이전트·공급자 역추적 SCR-J02
                        4                                                                                6
                                회전 (모달)                                                                      값 비노출 원칙
   ▫ 관측·운영
                                새값
   ▫ 사용자·조직                                                                                                  · 시크릿 값은 목록·상세·API·로그 어디에도
                                                                                                               표시되지 않는다(참조만 관리)
                                 ••••••••••••••••                                                            · 저장소: compose secrets(sops) 또는 OpenBao
                                                                                                             · 90일 미회전이면 주의 배지
   ▪ 설정
                                                                                                             · [사용처] 는 참조 중인 서비스·공급자 역추적
                                                                                                             · 모든 회전은 감사 원장에 기록
                                1) 검증 → 2) 교체 → 3) 재시작 대상 확인
   설치된 Addon


   ▸ 게시판                     5
                                    재시작 필요 서비스


   ▸ HR 채용                      llm-gateway · board-be (2건)
                                재시작 중 해당 에이전트 요청은 503


                                                                                                             7
                                                                                                                           90일 미회전 경고
                                                              취소                   회전


   [‹ 접기]




관련 요구사항(PRD): D9-04


AgentPlaza 화면설계서 · v1.0 · K. 조직·사용자·권한                                                                                                                                                                                                            91
시스템             AgentPlaza                                       화면 ID         SCR-L01                                                              화면 유형           페이지
화면명             시스템 설정                                           화면 경로         /settings                                                            접근 권한           admin+
우선순위            P0                                               PRD 추적        D10-01 D10-06                                                        작성일 / 버전        2026-09-19 / v1.0

플랫폼 전역 설정을 6개 섹션 탭으로 나눠 관리한다. 브랜딩·기능 토글·보존 정책·알림 채널·고급 한도를 한 곳에서 다루고, 환경변수로 고정된 값은 읽기 전용으로 표시한다. 저장 실패 시 반드시 오류를 통지한다.



                                                                                                                                               No   구성요소       유형      기능 설명 / 동작                            연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                              dev                                  🔔3        ko ▾      ☾            JD

                                                                                                                                                                       일반·브랜딩·기능·보존/개인정보·알림·고급 6종.
   ▫ 대시보드                설정 › 시스템 설정                                                                                                           1    섹션 탭       탭                                             D10-01
                                                                                                                                                                       URL 에 반영

   ▫ AI 어시스턴트
                         시스템 설정
                                                                                                                                               2    일반         폼       시스템 이름·기본 언어·시간대·환경 배지 표시             D10-01
                        1
   ▫ 마켓플레이스                        일반                      브랜딩            기능               보존·개인정보                  알림               고급
                                                                                                                                                                       제품명·로고 업로드·강조색(대비 검사)·로그인
                                                                                                                                               3    브랜딩        폼                                             D10-01
                                                                                                                                                                       문구
   ▫ 에이전트 관리
                        2                                                            3
                             일반                                                            브랜딩                                                                         마켓·워크플로·플레이그라운드·리뷰어 게이트
   ▫ 워크플로                                                                                                                                      4    기능 토글      체크박스                                          D10-01
                                                                                                                                                                       ·MCP 호환모드
                             시스템 이름 AgentPlaza                                             제품명 · 로고 업로드(SVG/PNG)
   ▫ 지식(RAG)                 기본 언어 [ko ▾] · 시간대 [Asia/Seoul ▾]                             강조색 #3F51E5 — 대비 검사 통과 ✓                                                    대화 365일·파일 90일·감사 불변. 고지문·
                             환경 배지 표시 [x] (dev/stg/prod)                                   로그인 화면 문구                                           5    보존·개인정보    폼                                             D10-06
                                                                                                                                                                       삭제권 절차
   ▫ 플레이그라운드

                                                                                                                                               6    알림         폼       메일·Slack 채널과 이벤트별 수신 대상               D10-01
   ▫ 거버넌스

                        4                                                            5                                                                                 도구 호출 최대 라운드·동시 스트림·업로드 상한·
   ▫ LLM·모델                                                                                                                                    7    고급         숫자 입력                                         D10-01
                             기능 토글                                                         보존·개인정보                                                                     로그 레벨

   ▫ 관측·운영                   마켓 [x] 워크플로 [x] 플레이그라운드 [x]                                   대화 [365일] · 파일 [90일] · 감사 [불변]                                              변경 없으면 비활성. PUT /api/settings, 실패 시
                             리뷰어 게이트 [x]                                                   개인정보 고지문 편집                                         8    저장         버튼                                            D10-01
                                                                                                                                                                       오류 메시지 필수
                             MCP 포트 호환모드 [ ] (v1 클라이언트용)                                   삭제권(파기 요청) 처리 절차
   ▫ 사용자·조직


   ▪ 설정



   설치된 Addon            6                                                            7
                             알림                                                            고급
   ▸ 게시판
                             채널 메일 · Slack                                                 도구 호출 최대 라운드 [6] · 스트림 동시 [1]
                             이벤트별 수신 대상(승인·장애·예산)                                          업로드 상한 [100MB] · 로그 레벨 [info ▾]
   ▸ HR 채용




                                                                                                                                 8
                         설정 우선순위: 환경변수(env) > 설정 UI > 기본값 · 재시작 필요 항목은 저장 후 안내
                                                                                                                      초기화            저장

   [‹ 접기]




관련 요구사항(PRD): D10-01 D10-06


AgentPlaza 화면설계서 · v1.0 · L. 설정·프로필                                                                                                                                                                                   92
시스템             AgentPlaza                                       화면 ID          SCR-L02                                                                    화면 유형            페이지
화면명             내 프로필                                            화면 경로          /profile                                                                   접근 권한            본인
우선순위            P0                                               PRD 추적         D3-05 D9-01                                                                작성일 / 버전         2026-09-19 / v1.0

개인 정보·선호 언어·테마·2단계 인증·맞춤지침과 메모리·로그인 세션·개인정보 내보내기를 본인이 관리한다. 선호 언어 변경은 저장 즉시 화면에 반영되고, 세션은 개별 강제 종료할 수 있다.



                                                                                                                                                      No   구성요소       유형         기능 설명 / 동작                           연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                dev                                 🔔3        ko ▾        ☾                JD


   ▫ 대시보드                내 프로필                                                                                                                        1    탭          탭          기본·보안·맞춤지침/메모리·세션·개인정보 5종            D3-05


   ▫ AI 어시스턴트
                         내 프로필
                                                                                                                                                      2    기본 정보      폼          이름·이메일. 조직/그룹은 읽기 전용                 D9-01
                        1
   ▫ 마켓플레이스                                     기본          보안                  맞춤지침·메모리                       세션                       개인정보
                                                                                                                                                                                 ko/en, system/light/dark. 저장 즉시 반영
                                                                                                                                                      3    선호 언어·테마   선택                                              D3-05
                                                                                                                                                                                 (localeChanged)
   ▫ 에이전트 관리

                             기본                                                            보안
   ▫ 워크플로                                                                                                                                             4    비밀번호 변경    버튼         현재 비밀번호 확인 후 변경. 정책 검증               SCR-A04

                             이름                            이메일                             4
   ▫ 지식(RAG)
                             2                                                                    비밀번호 변경                                             5    2단계 인증     QR·버튼      TOTP 등록 QR 표시, 설정·해제. 해제는 재인증        D9-01

   ▫ 플레이그라운드                       홍길동                     hong@acme.com
                                                                                           5
                                                                                           2단계 인증(TOTP)
                             선호 언어                         테마                                                                                         6    내 API 키    링크         개인 범위 서비스 키 목록으로 이동                  SCR-K04
   ▫ 거버넌스                                                                                                                                QR
                             3
                                                                                                  설정                   해제
                                   ko                 ▾    system           ▾                                                                                                    기기·IP·마지막 활동. 현재 세션 표시, 나머지
   ▫ LLM·모델                                                                                                                                           7    세션 목록      그리드                                             D9-01
                                                                                                                                                                                 강제 종료
                                                                                           6    내 API 키(개인 범위) — SCR-K04 로 이동
                             조직/그룹 ACME 식품 / 인사팀 (읽기 전용)
   ▫ 관측·운영                                                                                                                                                                       내 데이터 내보내기(대화·메모리) · 계정 삭제
                                                                                                                                                      8    개인정보       버튼                                              D10-06
                                                                                                                                                                                 요청
   ▫ 사용자·조직             7
                             세션

   ▫ 설정
                                 기기 / 브라우저                       IP              마지막 활동                상태                       동작

   설치된 Addon
                                 macOS · Chrome 131              10.1.2.7        방금                    현재 세션                    -

   ▸ 게시판
                                 Windows · Edge                  10.1.9.3        2시간 전                 활성                       강제 종료

   ▸ HR 채용
                                 iOS · Safari                    203.0.x         3일 전                  활성                       강제 종료

                        8
                             개인정보

                             내 데이터 내보내기(대화·메모리·첨부 목록) · 계정 삭제 요청(정책 절차)                                              내보내기                삭제 요청

   [‹ 접기]




관련 요구사항(PRD): D3-05 D9-01


AgentPlaza 화면설계서 · v1.0 · L. 설정·프로필                                                                                                                                                                                             93
시스템             AgentPlaza                                   화면 ID                    SCR-M01                                                                                      화면 유형             페이지
화면명             관측 대시보드                                      화면 경로                    /observability                                                                               접근 권한             운영자·admin
우선순위            P0                                           PRD 추적                   D10-03                                                                                       작성일 / 버전          2026-09-19 / v1.0

서비스 헬스·지연·오류율·자원·LLM 지표와 큐 상태를 한 화면에 모은다. 상세 분석은 SigNoz·Opik 딥링크로 넘기고 콘솔은 요약·진입·상관관계에 집중한다. 이상 항목은 목록으로 모아 런타임 화면과 연결한다.



                                                                                                                                                                              No   구성요소        유형       기능 설명 / 동작                        연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                          dev                                                  🔔3          ko ▾              ☾                    JD

                                                                                                                                                                                                        인프라·게이트웨이·에이전트 상태 점. 클릭 →
   ▫ 대시보드                관측·운영 › 대시보드                                                                                                                                         1    서비스 헬스 격자   상태 격자                                      SCR-M04
                                                                                                                                                                                                        런타임 서비스

   ▫ AI 어시스턴트
                         관측 대시보드                                                                                                                                                               막대       게이트웨이·에이전트 p50/p95, 5xx 비율. 기간
                                                                                                                                                                              2    지연·오류율                                                 D10-03
                                                                                                                                                                                               그래프      필터 적용
                                                                             7                                                          8
   ▫ 마켓플레이스                                                                      1h        ▾               자동 갱신 30s▾                          SigNoz ↗              Opik ↗
                                                                                                                                                                                               막대
                                                                                                                                                                              3    자원                   CPU·메모리·GPU 사용률. OTel 메트릭 기반      D10-03
                        1                                                                                                                                                                      그래프
   ▫ 에이전트 관리
                             서비스 헬스                                                                                                         에이전트 12 · unhealthy 1

   ▫ 워크플로                                                                                                                                                                     4    LLM 지표      스탯       요청 수·토큰·폴백 비율·첫 토큰 지연             SCR-J05
                                 traefik           gateway        postgres                     valkey                   otel                        llm-provider

   ▫ 지식(RAG)                                                                                                                                                                                            설치·인덱싱·워크플로·내보내기 잡의 대기/진행
                                                                                                                                                                              5    큐·잡         목록                                         D10-03
                        2                                                                      3                                                                                                        수
   ▫ 플레이그라운드                 지연 · 오류율                                                               자원 · LLM
                                                                                                                                                                                                        unhealthy·429·디스크 임계 등. 항목 클릭 →
                                                                                                                                                                              6    이상 목록       목록                                         SCR-M04
   ▫ 거버넌스                    gateway p50                                 0.42s                      CPU                                                        47%
                                                                                                                                                                                                        해당 화면

                                                                                                                                                                                                        기간(15m/1h/24h)과 자동 갱신
   ▫ LLM·모델                  gateway p95                                 1.9s                       메모리                                                        62%            7    기간·자동 갱신    선택                                         D10-03
                                                                                                                                                                                                        주기(off/30s/5m)
                             agent p95                                   3.4s                       GPU                                                        35%
   ▪ 관측·운영
                                                                                                                                                                              8    외부 딥링크      버튼       SigNoz·Opik 새 탭 열기(SSO 세션 전달)     D10-03
                             5xx 비율                                      0.8%                      4LLM 요청 1,842 · 토큰 412k · 폴백 3.1% · 첫 토큰 0.9s
   ▫ 사용자·조직


   ▫ 설정
                        5                                                                      6
                             큐·잡                                                                    이상 목록

   설치된 Addon

                             설치 잡 대기 1 · 진행 1                                                             rag-be unhealthy — 12분 경과
   ▸ 게시판                     인덱싱 잡 대기 4 · 진행 2 (평균 42s)
                             워크플로 실행 대기 0 · 진행 3
                             내보내기 대기 0
                                                                                                          퍼블릭 공급자 429 — 6회/1h
   ▸ HR 채용


                                                                                                          데이터 디스크 사용률 82%




                                                                                                             런타임 보기                                 알림 규칙 편집


   [‹ 접기]




관련 요구사항(PRD): D10-03


AgentPlaza 화면설계서 · v1.0 · M. 관측·감사·운영                                                                                                                                                                                                               94
시스템             AgentPlaza                                                       화면 ID            SCR-M02                                                                                    화면 유형            페이지
화면명             LLM 트레이스·세션                                                      화면 경로            /observability/traces                                                                      접근 권한            운영자·개발자
우선순위            P1                                                               PRD 추적           D10-04                                                                                     작성일 / 버전         2026-09-19 / v1.0

요청 단위 트레이스를 검색하고, 상세 드로어에서 span 트리(에이전트 호출 → 계획 → 도구 호출 → 모델 호출)를 따라간다. 각 span 의 gen_ai.* 속성과 입출력을 마스킹 상태로 보여 주고, 외부 관측 도구와 평가 화면으로 넘긴다.



                                                                                                                                                                                        No   구성요소       유형       기능 설명 / 동작                                  연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                              dev                                       🔔3               ko ▾          ☾                     JD

                                                                                                                                                                                                                 trace id·세션·사용자·에이전트 검색, 기간·상태
   ▫ 대시보드                관측·운영 › 트레이스                                                                                                                                                   1    검색·필터      필터                                                   D10-04
                                                                                                                                                                                                                 필터

   ▫ AI 어시스턴트
                         LLM 트레이스·세션                                                                                                                                                                             시각·세션·에이전트·별칭→모델·지연·토큰·비용·
                                                                                                                                                                                        2    트레이스 목록    그리드                                                  D10-04
                                                                                                                                                                                                                 상태. 페이징
                        1
   ▫ 마켓플레이스                  🔍 trace id · 세션 · 사용자 · 에이전트                                      기간 1h           ▾   상태           ▾
                                                                                                                                                                                                                 invoke_agent > plan > execute_tool > chat
                                                                                                                                                                                        3    span 트리    트리                                                   D10-04
                        2                                                                                                                                                                                        계층과 소요 시간 막대
   ▫ 에이전트 관리
                            시각                  세션               에이전트                     별칭 → 모델                        지연                    토큰                비용         상태
                                                                                                                                                                                                                 _meta traceparent 전파로 하위 서비스 span
   ▫ 워크플로                                                                                                                                                                               4    MCP 홉      트리 노드                                                D10-04
                            14:02:01            #a1f3            orchestrator             plaza/orch → qwen3             2.4s                  812               ₩0         ✓
                                                                                                                                                                                                                 연결

   ▫ 지식(RAG)                                                                                                                                                                                                     gen_ai.system·request.model·usage.tokens·tool
                            14:01:44            #a1f3            hr-onboarding            plaza/fast → haiku             1.1s                  402               ₩12        ✓           5    span 속성    키·값 표                                                  D10-04
                                                                                                                                                                                                                 .name 등
   ▫ 플레이그라운드                13:58:12            #9c02            rag-agent                plaza/chat → qwen3             6.8s                  1,940             ₩0         ✗ 오류
                                                                                                                                                                                                                 기본 마스킹. admin+ 만 원문 열람하며 열람도
                                                                                                                                                                                        6    입출력 마스킹    규칙                                                   SCR-M03
   ▫ 거버넌스
                                                                                                                                                                                                                 감사 기록

                        3                                                                                          5
   ▫ LLM·모델                   span 트리 — trace 4f1c… (드로어)                                                               span 상세                                                         7    외부 연결      버튼       Opik 에서 열기 ↗ · 평가 데이터셋에 추가                  SCR-H03

   ▪ 관측·운영
                              invoke_agent orchestrator                                                   2.40s         속성                             값

   ▫ 사용자·조직
                                                                                                                        gen_ai.system                  ollama
                                 4└ plan                                                                  0.41s

   ▫ 설정                                                                                                                 gen_ai.request.model           qwen3:8b

                                         └ chat qwen3:8b                                                  0.33s
                                                                                                                        gen_ai.usage.tokens            812
   설치된 Addon

                                   └ execute_tool board.manage                                            1.12s         tool.name                      board.manage
   ▸ 게시판


   ▸ HR 채용                                                                                                             6입력/출력 마스킹 표시 (admin+ 만 원문 열람, 열람 자체가 감사 기록)
                                         └ mcp hop → board-be                                             0.91s




                                   └ chat qwen3:8b (최종 응답)                                                0.84s                                            7
                                                                                                                                 Opik 열기 ↗                             평가에 추가

                              하위 MCP 홉은 _meta traceparent 로 이어 붙인다.

   [‹ 접기]




관련 요구사항(PRD): D10-04


AgentPlaza 화면설계서 · v1.0 · M. 관측·감사·운영                                                                                                                                                                                                                                   95
시스템             AgentPlaza                                              화면 ID                         SCR-M03                                                                            화면 유형            페이지
화면명             감사 원장                                                   화면 경로                         /audit                                                                             접근 권한            감사자·supervisor
우선순위            P0                                                      PRD 추적                        D9-07                                                                              작성일 / 버전         2026-09-19 / v1.0

누가 어느 에이전트로 어떤 도구를 호출했는지 불변 기록으로 조회한다. 행위자·에이전트·동작·기간 필터와 CSV 내보내기를 제공하고, 해시 체인 재계산으로 위변조 여부를 검증한다. 편집·삭제 기능은 존재하지 않는다.



                                                                                                                                                                                    No   구성요소       유형       기능 설명 / 동작                            연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                          dev                                               🔔3       ko ▾       ☾                        JD

                                                                                                                                                                                                             행위자·에이전트·동작·기간 조합 + 대상/해시
   ▫ 대시보드                관측·운영 › 감사 원장                                                                                                                                              1    필터 바       필터                                             D9-07
                                                                                                                                                                                                             검색

   ▫ AI 어시스턴트
                         감사 원장                                                                                                                                                                      그리드
                                                                                                                                                                                                             시각·행위자·에이전트·동작·대상·결과·해시.
                                                                                                                                                                                    2    원장 목록      (읽기 전                                          D9-07
                                                                                                                                                                                                             페이징
                        1                                                                                                                                   7                                       용)
   ▫ 마켓플레이스                  🔍 대상·해시 검색                            행위자      ▾                 에이전트 ▾                   동작     ▾            기간     ▾             CSV            검증
                                                                                                                                                                                                             인자/결과 해시·정책 근거·이전 해시(체인)·
                                                                                                                                                                                    3    상세 보기      드로어                                            SCR-M02
   ▫ 에이전트 관리            2                                                                                                                                                                                    트레이스 링크
                            시각              행위자                에이전트                   동작                       대상                      결과             해시              상세
                                                                                                                                                                           3                                 편집·삭제 없음. 원문은 auditLevel=full 일 때만
   ▫ 워크플로                                                                                                                                                                           4    불변 규칙      규칙                                             D9-07
                            14:02:05        홍길동                hr-onb                 tool.call                mail.send               승인됨            3f…             보기                                     참조

   ▫ 지식(RAG)                                                                                                                                                                                                 POST /api/audit/verify — 해시 체인 재계산,
                            14:01:50        admin              board                  agent.install            1.2.0                   성공             9a…             보기            5    무결성 검증     버튼+결과                                          D9-07
                                                                                                                                                                                                             끊김 위치 표시
   ▫ 플레이그라운드                13:58:12        시스템                gateway                llm.fallback             L1 → local              -              c1…             보기
                                                                                                                                                                                                             감사자·supervisor 전체, admin 은 자기 조직
                                                                                                                                                                                    6    권한 범위      규칙                                             D9-02
   ▫ 거버넌스                                                                                                                                                                                                    범위만
                            13:40:02        supervisor         -                      roles.update             admin 역할                성공             7b…             보기


                        4                                                                                      6                                                                                             현재 필터 범위 그대로 출력. 내보내기 행위
   ▫ LLM·모델                                                                                                                                                                         7    CSV 내보내기   다운로드                                           D9-07
                              상세 (드로어) — 읽기 전용                                                                     무결성 검증 결과                                                                                 자체도 감사 기록

   ▪ 관측·운영
                              행위자 홍길동 (hong) · ACME/인사팀                                                                    해시 체인 재계산 완료 — 위변조 없음
                              에이전트 hr-onboarding v1.4.0
   ▫ 사용자·조직                   동작 tool.call mail.send
                              인자 해시 sha256:8c1e… (원문 비저장)
                              결과 해시 sha256:20af…
   ▫ 설정                                                                                                            검사 구간 2026-09-01 ~ 09-19
                              정책 근거 승인 규칙 R-07 (승인자 이영희)
                                                                                                                   레코드 48,210건 · 소요 3.2s
                              이전 해시 sha256:c1b3… → 체인 연결


   설치된 Addon


   ▸ 게시판
                                                                                                                       불일치 시 첫 끊김 위치(시퀀스·시각)를 표시하고 이후 구간을 경고
                                                                                                                       표시한다.
   ▸ HR 채용



                                                                                                                   CSV 는 현재 필터 범위 그대로 출력.
                             5원문 열람은 auditLevel=full 인 경우만 · 편집·삭제 없음(불변)                                          감사자·supervisor 는 전체, admin 은 자기 조직만.




   [‹ 접기]




관련 요구사항(PRD): D9-07


AgentPlaza 화면설계서 · v1.0 · M. 관측·감사·운영                                                                                                                                                                                                                        96
시스템              AgentPlaza                                                       화면 ID                           SCR-M04                                                                              화면 유형              페이지
화면명              런타임·컨테이너 상태                                                      화면 경로                           /runtime                                                                             접근 권한              운영자
우선순위             P1                                                               PRD 추적                          D8-01 D8-02 D8-06                                                                    작성일 / 버전           2026-09-19 / v1.0

에이전트별 compose 서비스와 인프라 서비스를 그룹 트리로 보고, 상태·이미지 다이제스트·자원·재시작 횟수를 확인한다. 실시간 로그 tail 과 재시작·중지·시작 제어를 제공하며 compose 정의는 읽기 전용으로 노출한다.



                                                                                                                                                                                                  No   구성요소         유형       기능 설명 / 동작                           연계
  ▣    AgentPlaza              🔍 검색 (⌘K)                                                   dev                                                    🔔3          ko ▾              ☾            JD

                                                                                                                                                                                                                    그룹       에이전트·인프라 그룹별 서비스. unhealthy 는
    ▫ 대시보드                관측·운영 › 런타임                                                                                                                                                             1    서비스 트리                                                     D8-01
                                                                                                                                                                                                                    그리드      강조 표시

    ▫ AI 어시스턴트
                          런타임·컨테이너 상태                                                                                                                                                                                        up/unhealthy/exited, 이미지@sha256 고정
                                                                                                                                                                                                  2    상태·다이제스트     상태                                            D8-02
                                                                                                                                                                                                                             좌표 표시
    ▫ 마켓플레이스                                                                                                          프로젝트 plaza ▾                      🔍 서비스                       루트 compose
                                                                                                                                                                                                  3    로그 드로어       스트림      실시간 tail. level·텍스트·시간 필터, 다운로드      D8-01
    ▫ 에이전트 관리            1
                             그룹 / 서비스                                  상태                                이미지@digest                                 CPU / 메모리               재시작      동작
                                                                                                                                                                                                                             PII·시크릿 값 마스킹 후 표시. 다운로드는 운영자
    ▫ 워크플로                                                                                                                                                                                        4    로그 마스킹       규칙                                     D9-04
                             ▾ board / board-be                        ● up 2d                           agent-board-be:1.2.0@sha256…               3% / 210MB              0        로그 · 재시작
                                                                                                                                                                                                                             이상

    ▫ 지식(RAG)
                               board / board-fe                        ● up 2d                           agent-board-fe:1.2.0@…                     1% / 64MB               0        로그 · 재시작     5    서비스 제어       버튼       재시작·중지·시작. 필수 인프라 중지는 2중 확인          D8-02
                                                                 2
    ▫ 플레이그라운드                ▾ rag / rag-be                            ✗ unhealthy                       agent-rag-be:0.9.1@…                       12% / 1.1GB             6        로그 · 재시작
                                                                                                                                                                                                                             조회는 운영자, 제어는 운영자·supervisor. 모든
                                                                                                                                                                                                  6    권한           규칙                                            SCR-M03
    ▫ 거버넌스
                                                                                                                                                                                                                             제어는 감사
                                                                       ● traefik · postgres · valkey
                             ▾ infra
                                                                       · otel · gateway

    ▫ LLM·모델             3                                                                                                      5                                                                 7    compose 보기   코드       읽기 전용. 시크릿 값은 참조 이름만 표시              D8-06
                                로그 (드로어 · 실시간 tail)                                              level        ▾                     제어 · compose 보기

    ▪ 관측·운영
                              4                                                                                                     6
                                       2026-09-19T14:02:01Z INFO boot ok
                                                                                                                                           재시작                       중지               시작
    ▫ 사용자·조직                           2026-09-19T14:02:44Z WARN retry pg (1/5)
                                       2026-09-19T14:03:02Z ERROR healthcheck failed
                                         probe=/healthz status=503
                                       2026-09-19T14:03:12Z INFO restarting…
    ▫ 설정                                                                                                                            필수 인프라 서비스 중지는 2중 확인. supervisor·운영자만 실행 가능.




    설치된 Addon
                                                                                                                                    7
                                                                                                                                        services:
                                                                                                                                          board-be:
    ▸ 게시판
                                                                                                                                            image: agent-board-be:1.2.0
                                                                                                                                            secrets: [TOOL_PROXY_API_KEY]
                                                                                                                                            healthcheck: {test: …}
    ▸ HR 채용




                                PII 마스킹 적용 · [다운로드] 는 운영자 이상
                                필터: level · 텍스트 · 시간 범위




    [‹ 접기]




관련 요구사항(PRD): D8-01 D8-02 D8-06


AgentPlaza 화면설계서 · v1.0 · M. 관측·감사·운영                                                                                                                                                                                                                                       97
시스템             AgentPlaza                                         화면 ID           SCR-M05                                                                       화면 유형              페이지
화면명             백업·업그레이드·롤백                                        화면 경로           /runtime/maintenance                                                          접근 권한              supervisor
우선순위            P1                                                 PRD 추적          D8-06                                                                         작성일 / 버전           2026-09-19 / v1.0

백업 실행·스케줄·보존과 복원 시험, 플랫폼 이미지 업그레이드, 그리고 이미지 다이제스트 + 백업 ID 한 쌍으로 정의된 롤백 좌표를 관리한다. 최근 백업이 없으면 업그레이드를 시작할 수 없다.



                                                                                                                                                            No   구성요소         유형        기능 설명 / 동작                        연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                      dev                               🔔3       ko ▾          ☾                 JD


   ▫ 대시보드                관측·운영 › 유지보수                                                                                                                       1    백업 상태        상태        마지막 백업 시각·크기·검증 결과 표시             D8-06


   ▫ AI 어시스턴트
                         백업·업그레이드·롤백
                                                                                                                                                            2    스케줄·대상·보존    폼         cron 스케줄, 백업 대상 범위, 보존 기간 설정      D8-06

   ▫ 마켓플레이스                         백업                    업그레이드                   롤백
                                                                                                                                                                 지금 백업 · 복원             즉시 백업 잡 생성. 복원 시험은 별도 환경에서
                                                                                                                                                            3                 버튼                                          D8-06
                                                                                                                                                                 시험                     수행
   ▫ 에이전트 관리
                        1
                             백업                                                                                                                                               간이        현재/가용 버전과 변경 로그. 진행 화면으로
   ▫ 워크플로                                                                                                                                                   4    업그레이드                                                    D8-06
                                                                                                                                                                              위저드       전환
                                  마지막 백업 2026-09-19 03:00 · 4.2 GB · 검증 ✓
   ▫ 지식(RAG)                                                                                                                                                                            최근 백업·여유 디스크 확인. 미충족 시 시작
                                                                                                                                                            5    사전 조건        체크 목록                                       D8-06
                             스케줄(cron)                             대상                       보존                                                                                          불가
   ▫ 플레이그라운드
                             2                                                                                         3
                                 매일 03:00                           전체             ▾            30일                           지금 백업                 복원 시험   6    롤백 좌표        목록        시각·버전·이미지 digest·백업 ID 한 쌍으로 기록   D8-02
   ▫ 거버넌스

                                                                                                                                                                              버튼(위
   ▫ LLM·모델                  복원 시험 이력 분기 1회 강제 · 마지막 2026-07-01 ✓ (별도 환경에서 수행)                                                                              7    롤백 실행                  확인 키 재입력 후 실행. 진행·결과는 감사 기록       SCR-M03
                                                                                                                                                                              험)

   ▪ 관측·운영
                        4                                                               6
   ▫ 사용자·조직                  업그레이드                                                          롤백 좌표


   ▫ 설정                      현재 2.0.0 → 사용 가능 2.1.0
                             변경 로그 보기 ↗                                                         시각             버전          이미지 digest / 백업


   설치된 Addon                                                                                    09-19 03:00    2.0.0       sha256:4c1a… / bk-0919
                             5
                                  사전 조건
   ▸ 게시판
                                                                                                09-05 03:00    1.9.2       sha256:9f77… / bk-0905


   ▸ HR 채용                        최근 백업 존재 ✓
                                                                                            각 좌표 = 이미지 다이제스트 + 백업 ID 한 쌍

                                  여유 디스크 ✓ (18 GB)

                                                                                            7
                                                                    업그레이드 시작                             2.0.0 으로 롤백            확인 키 재입력



   [‹ 접기]




관련 요구사항(PRD): D8-06


AgentPlaza 화면설계서 · v1.0 · M. 관측·감사·운영                                                                                                                                                                                               98
시스템             AgentPlaza                                                   화면 ID         SCR-M06                                                                  화면 유형           페이지
화면명             오프라인·에어갭 번들                                                  화면 경로         /runtime/airgap                                                          접근 권한           supervisor
우선순위            P2                                                           PRD 추적        D8-07                                                                    작성일 / 버전        2026-09-19 / v1.0

폐쇄망 반입용 번들(플랫폼·에이전트 이미지 tar, 모델 파일, 카탈로그·자산 zip, 선택적 백업)을 생성해 내려받고, 다른 인스턴스에서 만든 번들을 체크섬·서명 검증 후 반입한다.



                                                                                                                                                               No   구성요소       유형       기능 설명 / 동작                              연계
  ▣   AgentPlaza             🔍 검색 (⌘K)                                               dev                         🔔3         ko ▾        ☾                 JD

                                                                                                                                                                                        이미지 tar·모델 파일·카탈로그 zip·백업 포함
   ▫ 대시보드                관측·운영 › 에어갭 번들                                                                                                                        1    내보내기 옵션    체크박스                                             D8-07
                                                                                                                                                                                        여부 선택

   ▫ AI 어시스턴트
                         오프라인·에어갭 번들
                                                                                                                                                               2    선택 에이전트    다중 선택    번들에 포함할 에이전트를 칩으로 추가·삭제                 D8-07

   ▫ 마켓플레이스                  내보내기
                                                                                                                                                                                        선택에 따라 실시간 재계산. 디스크 여유 부족 시
                                                                                                                                                               3    예상 크기      요약                                   D8-07
                                                                                                                                                                                        경고
   ▫ 에이전트 관리
                             1
                                 ✓     이미지 tar (플랫폼 + 선택 에이전트)                                       ✓    모델 파일 (로컬 런타임용)
                                                                                                                                                                                        POST /api/airgap/export → 잡 진행률, 완료 시
   ▫ 워크플로                                                                                                                                                      4    번들 생성      버튼+잡                                             D8-07
                                                                                                                                                                                        다운로드 알림
                                 ✓     카탈로그·자산 zip                                                        최근 백업 포함
   ▫ 지식(RAG)
                                                                                                                                                               5    번들 파일 선택   파일 입력    다른 인스턴스에서 만든 번들 업로드                     D8-07
                             2
   ▫ 플레이그라운드                          선택 에이전트                              board ×          rag-agent ×              + 추가

                                                                                                                                                               6    검증 단계      체크 목록    체크섬·서명·버전 호환성·반입 대상 요약                  D8-07
   ▫ 거버넌스                                                                                                                                   4
                             3
                                      예상 크기 18.4 GB
                                                                                                                                                  번들 생성
                                                                                                                                                                                        POST /api/airgap/import → 검증 통과 항목만
   ▫ LLM·모델                                                                                                          34 % 생성 중                                 7    반입 적용      버튼                                               SCR-M03
                                                                                                                                                                                        적용, 감사 기록

   ▪ 관측·운영


   ▫ 사용자·조직
                             가져오기

   ▫ 설정
                             5                                                                                                      7
                                     plaza-airgap-2026-09-19.tar (파일 선택)                                              검증                        반입 적용
   설치된 Addon


   ▸ 게시판
                                 6      체크섬(sha256) 일치
   ▸ HR 채용                                                                                                                       지식(RAG) 오프라인 가져오기와 동일한 검증
                                                                                                                                 절차를 쓴다.
                                        서명 검증 — 발급 인스턴스 확인


                                        버전 호환성 2.1.0 ≥ 현재 2.0.0


                                        반입 대상: 이미지 12 · 모델 3 · 카탈로그 1

   [‹ 접기]




관련 요구사항(PRD): D8-07


AgentPlaza 화면설계서 · v1.0 · M. 관측·감사·운영                                                                                                                                                                                                     99
시스템              AgentPlaza                                                       화면 ID                               SCR-N01                                                                                      화면 유형                     공통 규약
화면명              Addon 화면 마운트 규약                                                  화면 경로                               /a/{agent}/ui                                                                                접근 권한                     권한 상속
우선순위             P0                                                               PRD 추적                              D5-07 D3-03                                                                                  작성일 / 버전                  2026-09-19 / v1.0

Addon 에이전트 화면은 코어가 만들지 않고 콘솔 셸 안의 iframe 으로 마운트한다(별 오리진 + sandbox). 콘솔은 헤더·토스트·모달·URL 을 소유하고, Addon 은 postMessage 규약 v1 로 요청만 한다. Module Federation 은 1st-party 한정 선택
사항이다.


                                                                                                                                                                                                              No   구성요소             유형          기능 설명 / 동작                                         연계
  ▣    AgentPlaza             🔍 검색 (⌘K)                                                    dev                                                    🔔3            ko ▾            ☾                        JD

                                                                                                                                                                                                                                                에이전트 이름·버전·헬스. 새로고침은 iframe
    ▫ 대시보드                Addon › 게시판                                                                                                                                                                         1    페이지 헤더           헤더                                                             D3-03
                                                                                                                                                                                                                                                재로드
                                                                     1
    ▫ AI 어시스턴트
                          게시판                                               v1.2.0 · healthy
                                                                                                                                                       새로고침                    전체화면                  ⋯                                          에이전트별 서브도메인. 높이는 resize 메시지로
                                                                                                                                                                                                              2    iframe 마운트       iframe                                                         D5-07
                                                                                                                                                                                                                                                조정
    ▫ 마켓플레이스             2
                               iframe — 별 오리진 https://board.addons.plaza.local
                                                                                                                                                                                                                                                allow-scripts/forms/downloads, frame-
                                                                                                                                                                                                              3    sandbox·CSP      속성                                                             D5-07
                              3sandbox="allow-scripts allow-forms allow-downloads"                                                                                                                                                              ancestors 로 상호 제한
    ▫ 에이전트 관리                                                                                      ·   title="게시판 화면"       ·   loading=lazy

                                                                                                                                                                                                                                                {v:1, type, id?, payload}. origin 화이트리스트
    ▫ 워크플로                                                                                                                                                                                                    4    postMessage 규약   규약                                                             D5-07
                                                                                                                                                                                                                                                대조, targetOrigin 명시

    ▫ 지식(RAG)                                                                                     [ Addon 이 그리는 화면 — SCR-N02 골격 ]                                                                                                               ready·auth·context·resize·navigate·notify·modal·
                                                                                                                                                                                                              5    메시지 표            표                                                              D5-07
                                                                                                     높이는 Addon 이 resize 메시지로 통보                                                                                                                 error 등
    ▫ 플레이그라운드
                                                                                                                                                                                                                                                토스트·모달·네비·URL(?path=)·오류 배너는
                                                                                                                                                                                                              6    콘솔 소유 UI         규칙                                                             D3-03
    ▫ 거버넌스
                                                                                                                                                                                                                                                콘솔이 렌더링

                               ready 미수신·load 실패 시 iframe 대신 안내 화면 + 재시도 + 런타임 링크
                                                                                                                                                                                                                                                단명 JWT 재푸시, ready 3초 초과 시 재시도,
    ▫ LLM·모델                                                                                                                                                                                                  7    토큰·상태 전이         규칙                                                             SCR-M04
                                                                                                                                                                                                                                                unhealthy 시 안내 화면
                         4                                                                                                               6
    ▫ 관측·운영
                               postMessage 규약 v1                                                                                               콘솔 소유 · 보안 하드닝

    ▫ 사용자·조직                   { v:1, type:"agentplaza.<name>", id?, payload }                                                                 콘솔이 소유: 토스트 · 모달 · 네비게이션 · URL(?path=) · 오류 배너


    ▫ 설정                      5
                                  방향        type                          payload · 설명                                                       7· CSP(콘솔) frame-src 'self' https://*.addons.{domain}
                                                                                                                                               · CSP(Addon) frame-ancestors https://console.{domain}
                                  A→C       ready                         {protocolVersion} 초기화 완료                                             · 에이전트마다 별 서브도메인(스토리지 분리)
    설치된 Addon
                                                                                                                                               · allow-same-origin 은 꼭 필요할 때만
                                                                                                                                               · Addon 백엔드가 aud 를 반드시 검증
                                                                                                                                               · iframe title 필수(접근성)
    ▸ 게시판                         C→A       auth                          단명 JWT · aud=agent:{id}



    ▸ HR 채용                       C→A       context                       {locale, theme, timezone, classification}


                                  A→C       resize · navigate             {height} · {path,title} → URL ?path=


                                  A→C       notify · modal · error        토스트·모달·오류 배너는 콘솔이 띄움


                               telemetry · chat.open · approval.request 도 동일 형식

    [‹ 접기]




관련 요구사항(PRD): D5-07 D3-03


AgentPlaza 화면설계서 · v1.0 · N. Addon 화면 규약                                                                                                                                                                                                                                                                     100
시스템                   AgentPlaza                                            화면 ID                 SCR-N02                                                    화면 유형             공통 규약
화면명                   Addon 화면 템플릿(목록·폼·상세)                                 화면 경로                 (Addon 내부)                                                 접근 권한             Addon 정의
우선순위                  P0                                                    PRD 추적                D4-01 D4-03                                                작성일 / 버전          2026-09-19 / v1.0

Addon 개발자가 따르는 화면 골격이다. 툴바·목록·상세/폼·차트·상태 표현 5개 영역과 SDK(@agentplaza/ui) 컴포넌트, API 경로·i18n·테마·접근성 규약을 정하고, plaza validate 가 위반을 검사한다.



                                                                                                                                                        No   구성요소         유형      기능 설명 / 동작                               연계
    Addon 화면 골격 — 템플릿이 생성하고 개발자가 채운다

    헤더 없음: 콘솔 헤더가 이름·버전을 표시한다. Addon 은 에이전트명 <h1> 금지, 섹션 h2 부터.                                                                                                                   검색·필터·정렬 + 주요 동작 버튼(새 항목·
                                                                                                                                                        1    툴바           영역                                               D4-01
                                                                                                                                                                                  내보내기)

        1                                                                                                                                               2    목록           표/카드    컬럼 정의·정렬·서버 페이징. 행 클릭 → 상세               D4-01
            🔍 검색                               필터         ▾            정렬         ▾                                             + 새 항목           내보내기

                                                                                                                                                                          드로      필드·검증·저장·삭제. 확인 다이얼로그는 콘솔
        2
                                                                                                                                                        3    상세·폼                                                          SCR-N01
                                                                                                                                                                          어/모달    modal 브리지
            선택          제목                                                                작성자                            상태              수정일

                                                                                                                                                        4    차트 영역        선택 영역   도메인 KPI. dataviz 규약(색·범례·축) 준수           D4-01
            ☐           9월 공지사항                                                           홍길동                            게시              09-19


            ☐           사내 규정 개정                                                          김철수                            임시저장            09-18                                    EmptyState·Skeleton·오류 컴포넌트 필수 사용
                                                                                                                                                        5    빈·로딩·오류      상태                                               D4-03
                                                                                                                                                                                  (ST-01~08)
            ☐           … 서버 페이징 · 행 클릭 → 상세                                              -                              -               -
                                                                                                                                                                                  /a/{agent}/api/{prefix}/… 만 호출. 코어 API
                                                                                                                                                        6    SDK·API 경로   규약                                               D4-03
                                                                                                                                                                                  직접 import 금지
        3                                                                                 4
                상세 / 폼 (드로어 — 콘솔 모달 브리지 권장)                                                   차트 영역(선택) — 도메인 KPI                                                                 h1 금지·하드코딩 문자열·외부 CDN·접근성
                                                                                                                                                        7    검증 규칙        검사                                               D4-03
                                                                                                                                                                                  (axe)·IME Enter 차단
                제목


                 9월 공지사항

                                                                                          5
                분류

                                                                                                      빈 · 로딩 · 오류 상태 — 코어와 같은 문구 규약(ST-01~08)
                 공지                                                  저장


       7        필드 하단 오류 + 제출 실패 요약(SDK 표준 메시지 키)                                                                            첫 항목 만들기




   6
       SDK @agentplaza/ui — client(axios, 토큰 자동) · useLocale(t) · useTheme · useContext(classification)
         Table · Form · Drawer · EmptyState · Skeleton · Badge · Toast(→ 콘솔 notify) · Modal(→콘솔 modal) · PageContainer
       API 경로 /a/{agent}/api/{prefix}/…     (v1 /api/addon/{key}/{prefix} 호환 별칭) · 코어 API 직접 호출 금지




관련 요구사항(PRD): D4-01 D4-03


AgentPlaza 화면설계서 · v1.0 · N. Addon 화면 규약                                                                                                                                                                                             101
       PART 3


       부록
       모달·위저드 카탈로그 · 메시지 정의·오류 처리 · 요구사항 추적표(RTM) · 비화면 요구 표출 위치 · 참조 구현 변경 총람 · 참고 자료




AgentPlaza 화면설계서 · v1.0 · 부록                                                             102
A. 모달·위저드 카탈로그 (1~14 / 18)
화면 ID · 이름 · 트리거(경로) · 주요 버튼 · 파괴적 여부(danger 확인 필수)


화면 ID          이름                         유형              트리거(경로)                     주요 버튼      파괴적


SCR-A02        최초 설치 위저드                  위저드(5단계·전체화면)   /setup                      -          -


SCR-A04        비밀번호 변경·임시 비밀번호            모달(2종)          /profile/password · 모달      -          -


SCR-B04        전역 검색                      모달(커맨드 팔레트)     (상단바 팔레트)                   -          -


SCR-C03        파일·멀티모달 입력                 모달(인라인 첨부 패널)   /chat (첨부)                  -          -


SCR-D03        새 Agent 만들기 — 스캐폴드         위저드(모달 5단계)     /agents (모달 탭1)             다운로드·배포    -


SCR-D04        새 Agent 만들기 — ZIP 업로드      모달              /agents (모달 탭2)             -          -


SCR-D06        MCP 노출 설정·가이드              모달              /agents/{key}/mcp (모달)      도구 해시·시험   -


SCR-D08        추출(파생·Standalone 번들)       모달              /agents/{key}/export (모달)   추출         -


SCR-D09        Worker·설치 가이드              모달              /agents/{key}/guide (모달)    패키지 다운로드   -


SCR-D10        삭제·해제 확인                   모달(확인 다이얼로그)    (확인 다이얼로그)                  해제         ●


SCR-D11        원격 에이전트 등록(연동·연계)          위저드(5단계)        /agents/link                등록         -


SCR-E04        설치(도입=배치) 위저드              위저드             /market/{key}/adopt         요약·설치      -


SCR-E05        직접 설치(Zip·Git·OCI·URL)     모달              /market/install-direct      가져오기       -


SCR-E06        자산 등록(게시)                  위저드             /market/publish             확인·게시      -




AgentPlaza 화면설계서 · v1.0 · 부록 A                                                                       103
A. 모달·위저드 카탈로그 (15~18 / 18)
화면 ID · 이름 · 트리거(경로) · 주요 버튼 · 파괴적 여부(danger 확인 필수)


화면 ID          이름                         유형          트리거(경로)                   주요 버튼          파괴적


SCR-E09        비교(Compare)                모달          /market/compare           열별 설치          -


SCR-E12        구매·라이선스                    위저드(모달)     /market/{key}/purchase    키 입력·검증 / 적용   -


SCR-F04        트리거 설정                     모달          /workflow/{id}/triggers   -              -


SCR-F05        DSL 반입                     모달          /workflow/import          -              -




AgentPlaza 화면설계서 · v1.0 · 부록 A                                                                     104
B. 메시지 정의 — 상황 · 문구(ko/en) · 처리 시나리오
i18n 키로 관리(ko 기본·en 폴백). 화면에 키 이름 노출 금지(참조 구현 settings.llmUsage* 키 누락 결함)

ID           상황                  종류        문구(ko)                                        문구(en)                                                           처리 시나리오

MSG-001      저장 성공               success   저장했습니다.                                       Saved.                                                           토스트 3초·폼 편집 유지

MSG-002      삭제 확인               confirm   {대상}을(를) 삭제합니다. 관련 데이터가 함께 제거되며 되돌릴 수 없습니다.   Delete {target}? Related data is removed and cannot be undone.   danger 확인 → 실행/취소

MSG-003      필수 입력               error     필수 항목입니다.                                     This field is required.                                          인라인 + 상단 요약·첫 오류 포커스

MSG-004      형식 오류               error     형식이 올바르지 않습니다. ({규칙})                         Invalid format. ({rule})                                         인라인, {규칙} 에 허용 형식 예시

MSG-005      중복                  error     이미 존재하는 {대상}입니다. 다른 이름을 사용하세요.                {target} already exists.                                         인라인 + '-2' 대체 이름 제안

MSG-006      권한 없음               error     이 작업을 수행할 권한이 없습니다.                           You do not have permission for this action.                      버튼 비활성 + 툴팁 / 403 화면

MSG-007      검증 실패(등록)           error     패키지 검증에 실패했습니다: {사유}                          Package validation failed: {reason}                              D05 해당 단계 사유 목록·재업로드

MSG-008      서명 미검증              warning   서명이 확인되지 않은 자산입니다. 설치 시 강한 격리가 적용됩니다.         Unsigned asset. Strong isolation will be applied.                E04 1단계 경고 배너 + 동의 필수

MSG-009      정책 차단               error     조직 정책에 의해 차단되었습니다: {정책}                       Blocked by organization policy: {policy}                         차단 사유 + 정책 화면 링크

MSG-010      데이터 등급 위반           error     이 등급의 데이터는 외부 모델로 전송할 수 없습니다.                 This data classification cannot be sent to external models.      전송 전 차단 배너 + 로컬 별칭 제안

MSG-011      로컬 폴백               info      외부 모델을 사용할 수 없어 로컬 모델로 응답했습니다.                Responded with a local model (external unavailable).             응답 버블 하단 저하 배지·감사

MSG-012      승인 대기               info      승인 요청을 보냈습니다. 승인 후 계속 진행됩니다.                  Approval requested. Execution resumes after approval.            승인 카드 인라인·입력 비활성·배지+1

MSG-013      승인 만료               warning   승인 요청이 만료되어 작업이 취소되었습니다.                      Approval expired; the task was cancelled.                        카드 만료 + 재요청·알림

MSG-014      설치 완료               success   설치했습니다. 좌측 메뉴와 어시스턴트 도구에서 사용할 수 있습니다.         Installed. Available in the navigation and assistant tools.      토스트 + 열기 링크·네비 갱신

MSG-015      해제 완료               success   해제했습니다. 관련 라우트·화면·MCP 노출이 제거되었습니다.            Uninstalled. Routes, screens and MCP exposure were removed.      토스트·네비·도구 목록 즉시 갱신

MSG-016      연결 성공               success   연결을 확인했습니다.                                   Connection verified.                                             배지 ✓ + 다음 단계 활성

MSG-017      연결 실패               error     연결에 실패했습니다: {사유}                              Connection failed: {reason}                                      배지 ✗ + 사유 + 재시도·진행 차단

MSG-018      부분 성공               warning   {성공}건 성공, {실패}건 실패했습니다.                       {ok} succeeded, {fail} failed.                                   요약 배너 + 실패 목록 + 실패만 재시도

MSG-019      세션 만료               warning   세션이 만료되어 다시 로그인해야 합니다.                        Session expired. Please sign in again.                           로그인 배너·원래 경로 복귀

MSG-020      임시 비밀번호             info      임시 비밀번호는 이 화면에서만 확인할 수 있습니다.                  The temporary password is shown only once.                       1회 노출 모달·닫기 전 확인·복사




AgentPlaza 화면설계서 · v1.0 · 부록 B                                                                                                                                                      105
C. 요구사항 추적표(RTM) PRD ↔ 화면 (1~48 / 94)
PRD v2 FR-D 70 · FR-X 12 · FR-P 12 전부가 최소 1개 화면에 매핑됨(빌드 시 assert). 미커버 0 · 유령 ID 0

PRD       항목                     화면 ID(SCR-)                         수      PRD      항목                       화면 ID(SCR-)               수

D1-01     Ollama 로컬 런타임 어댑터      A02 J03                             2      D4-04    agent.yaml 스키마·검증기       D04 D05                   2

D1-02     고성능 로컬 서빙 엔진           J03                                 1      D4-05    로컬 개발·계약 시험              D09 H03                   2

D1-03     퍼블릭 LLM API 어댑터        A02 J02                             2      D4-06    패키징·서명                   E06                       1

D1-04     CLI 에이전트 백엔드 브리지       J07                                 1      D4-07    파생·독립 실행 내보내기            D08                       1

D1-05     통합 게이트웨이·라우터           A02 J04                             2      D5-01    Zip 업로드                  D04                       1

D1-06     모델 카탈로그·데이터 등급 정책      A02 D02 I03 J01 J04                 5      D5-02    구조 검증 게이트                D04 D05                   2

D1-07     임베딩·리랭크 서빙             G02 J06                             2      D5-03    서명·SBOM·취약점 게이트          D05 E03                   2

D2-01     의도 분류·계획               C01 D13                             2      D5-04    라이선스·정책 게이트              D05 E03                   2

D2-02     레지스트리 라우팅              D13                                 1      D5-05    디플로이 모드                  D05 D10 D04               3

D2-03     실행 패턴 엔진               F01 F02 F04                         3      D5-06    카탈로그 DB·capability 인덱스   D01 D02 D05 D10 D13       5

D2-04     도구 호출 실행기              C01                                 1      D5-07    프론트 통합 파이프라인             D05 N01                   2

D2-05     리뷰어 게이트                I05                                 1      D6-01    스토어 UI                   E01 E02 E03 E08 E09 E10   6

D2-06     휴먼 승인 게이트              C01 I04                             2      D6-02    설치 경로 A                  E04 E10                   2

D2-07     상태·내구성·합성              F03                                 1      D6-03    설치 경로 B                  E05                       1

D3-01     채팅 UI·스트리밍             C01                                 1      D6-04    설치 경로 C                  D11                       1

D3-02     세션·히스토리                C02                                 1      D6-05    구매·라이선스·엔타이틀먼트           E04 E12 K02               3

D3-03     도구 호출 UX·스코프 채팅        C01 C05 N01                         3      D6-06    퍼블리셔 계정·릴리스              E06 E07                   2

D3-04     파일·멀티모달 입력             C03                                 1      D6-07    업데이트·마켓 서버               E11 E13                   2

D3-05     메모리·개인화                C04 L02                             2      D7-01    에이전트별 MCP 서버             D06                       1

D3-06     지식(RAG) 연결             C06 G01 G02 G03                     4      D7-02    MCP 클라이언트·서버 등록          D06 D11                   2

D3-07     채널·임베드                 C07                                 1      D7-03    A2A 서버                   D07                       1

D4-01     에이전트 템플릿 9유형           D03 N02                             2      D7-04    A2A 클라이언트                D11                       1

D4-02     스캐폴드 위저드·CLI           D03                                 1      D7-05    OpenAI 호환·OpenAPI 변환     D07                       1

D4-03     에이전트 SDK               N02                                 1      D7-06    AG-UI·ACP 브리지            D07 C01                   2




AgentPlaza 화면설계서 · v1.0 · 부록 C                                                                                                              106
C. 요구사항 추적표(RTM) PRD ↔ 화면 (49~94 / 94)
PRD v2 FR-D 70 · FR-X 12 · FR-P 12 전부가 최소 1개 화면에 매핑됨(빌드 시 assert). 미커버 0 · 유령 ID 0

PRD       항목                     화면 ID(SCR-)                         수      PRD      항목            화면 ID(SCR-)   수

D7-07     게이트웨이 정책               D06 D12 K04                         3      X03      음성            C03           1

D8-01     에이전트 compose 골격        D09 M04 D08                         3      X04      자동화 연계        D11           1

D8-02     플랫폼 루트 compose         M04                                 1      X05      코드 실행 샌드박스    F02           1

D8-03     라우팅·TLS                M04 D06                             2      X06      브라우저 에이전트     N01           1

D8-04     격리·샌드박스                D04 D12                             2      X07      RAG 엔진 연계     G01           1

D8-05     GPU·모델 자원              J03                                 1      X08      파인튠·로컬 학습     J03           1

D8-06     헬스·업그레이드·롤백·백업         B02 E11 M04 M05                     4      X09      멀티테넌시         K02           1

D8-07     오프라인·설치자               M06 E13                             2      X10      쿠버네티스         M04           1

D9-01     계정·SSO                 A01 A03 K05 L02                     4      X11      데스크톱·모바일 셸    B01           1

D9-02     역할 기반 권한               A04 D02 D12 E04 K01 K03             6      X12      상거래 정산        E12           1

D9-03     서비스 계정·API 키           K04                                 1      P01      리버스 프록시       M04 D06       2

D9-04     시크릿                    J02 K06                             2      P02      에이전트 레지스트리    D13 D01       2

D9-05     거버넌스 정책 엔진             D12 I03                             2      P03      이벤트 버스        B03           1

D9-06     가드레일                   I01 I02                             2      P04      공유 Postgres   M04           1

D9-07     감사 원장                  I02 M03 I04                         3      P05      공유 Valkey     M04           1

D10-01    플랫폼 콘솔                 B01 B02 B04 D01 L01                 5      P06      OTel 컬렉터      M01           1

D10-02    셋업 위저드·온보딩             A02                                 1      P07      신원 제공자        K05           1

D10-03    OTel 트레이스·메트릭·로그       M01                                 1      P08      시크릿 저장소       K06           1

D10-04    LLM 관측 UI              H02 J05 M02                         3      P09      마켓 서버         E13 E07       2

D10-05    평가·시험 표준               H01 H02 H03                         3      P10      빌드 서비스        D05           1

D10-06    데이터 모델·마이그레이션          L01                                 1      P11      작업 실행기        D05 F03       2

D10-07    알림·상태                  B02 B03                             2      P12      plaza CLI     D03 E03       2

X01       비주얼 플로우 빌더             F01 F02 F05                         3

X02       이미지·비디오 생성             N01                                 1




AgentPlaza 화면설계서 · v1.0 · 부록 C                                                                                       107
D. 비화면(백엔드·프로토콜·인프라) 요구의 표출 위치
직접 화면이 없는 PRD 항목은 '설정·상태를 보여주는 화면' 을 커버 화면으로 본다(누락 방지)


PRD                        요구                                                   표출 위치(화면)                                                               표출 방식



D1-05 / D1-07              통합 게이트웨이·라우터 · 임베딩·리랭크 서빙                            J04 라우팅 정책 · J06 임베딩 · M04 런타임                                          규칙 목록·폴백 순서·헬스



D2-01~D2-07                의도 분류·라우팅·실행 패턴·도구 실행·리뷰·승인·내구성                      C01 대화 카드 · D13 capability 인덱스 · F02/F03 워크플로 · I04/I05                 AG-UI 이벤트 카드·실행 이력·게이트 설정



D4-03 / D4-06              에이전트 SDK · 패키징·서명                                    N02 템플릿 규약 · E06 게시(서명·SBOM)                                            SDK 브리지 어휘·서명 상태 배지



D5-06 / D5-07              카탈로그 DB·capability 인덱스 · 프런트 통합 파이프라인                D13 · N01 iframe 마운트 · D05 7단계                                          인덱스 표·마운트 상태·단계 로그


                           에이전트별 MCP 서버·클라이언트·A2A·OpenAI 호환·AG-UI·게이트웨이
D7-01~D7-07                                                                     D06 MCP 탭 · D07 프로토콜 탭 · D11 원격 등록 · D12 정책 · K04 API 키                 server.json·Agent Card·엔드포인트·토큰 범위
                           정책

                                                                                M04 런타임 · D08 Standalone 내보내기 · D10 디플로이 모드 · J03 GPU · M05 백업 · M06
D8-01~D8-07                compose 골격·루트 compose·라우팅/TLS·격리·GPU·헬스/백업·오프라인                                                                              컨테이너 상태·compose 미리보기·자원 게이지·번들 생성
                                                                                에어갭


D9-04 / D9-05 / D9-07      시크릿 · 정책 엔진 · 감사 원장                                  K06 시크릿 · I03 정책·등급 · D12 · M03 감사                                      마스킹·1회 노출·정책 규칙·원장 CSV(OUT-01)



D10-03 / D10-06 / D10-07   OTel 트레이스 · 데이터 모델·마이그레이션 · 알림·상태                    M01/M02 관측 · L01 설정(스키마 버전) · B03 알림 센터                                 트레이스 트리·버전 표시·알림 목록



X02 / X03 / X05 / X06      이미지·비디오 · 음성 · 코드 샌드박스 · 브라우저 에이전트                   N01(Addon 화면) · C03 파일·멀티모달 · F02 노드                                    Addon 으로 제공, 코어는 마운트·입력만



X09 / X10 / X11 / X12      멀티테넌시 · 쿠버네티스 · 데스크톱/모바일 · 상거래 정산                    K02 조직 · M04 런타임 · B01 셸(반응형) · E12                                     확장 지점만 표기(범위 밖, PRD 8장)


                           리버스 프록시·레지스트리·이벤트 버스·Postgres·Valkey·OTel·IdP·시크릿·
P01~P12                                                                         M04 · D13/D01 · B03 · M01 · K05 · K06 · E13/E07 · D05 · F03 · D03/E03   플랫폼 서비스 상태·설정. CLI 는 화면 동등 명령 코드 블록
                           마켓 서버·빌드·실행기·CLI




AgentPlaza 화면설계서 · v1.0 · 부록 D                                                                                                                                                                108
E. 참조 구현 결함 → 설계 변경 총람
SeCuardian-Marketplace · MAS-Marketplace · MultiAIAgent-Template(addon-agents) · DOPQ/HR Addon 소스 역문서화에서 확인. 각 화면 노트의 '참조 구현 대비 변경' 과 대응


#     참조 구현 상태                                                                                      본 설계 결정                                            화면


      도구 호출 UI 없음 — 백엔드 intent/agent_start/hitl_pending/review_gate 이벤트를 프론트가 버림(delta/done/error
B1                                                                                                  AG-UI 이벤트 전부 렌더(도구·승인·리뷰·서브에이전트 카드)                C01
      만)


B2    SetupWizard: i18n·다크모드·뒤로가기 없음, API 키 .env 수동                                                 5단계 위저드, 뒤로·언어·테마, 키 입력·검증                         A02



B3    ProtectedRoute 토큰 유무만 검사 → URL 직접 입력으로 관리 화면 열림                                               라우트 역할 가드 + 서버 403 2중화                             6·B01



B4    토스트 없음(alert/console) · 해제(uninstall) 확인·catch 없음                                             코어 토스트 스택 · danger 확인 + 영향 범위                      E11·D02



B5    목록 상태 URL 미반영 · 서버 페이징은 MAS 마켓만                                                               쿼리 파라미터 동기화 · 전 목록 서버 페이징(100건)                    E01·D01



B6    Addon 프런트 = import.meta.glob 빌드타임 통합(재빌드 30초, 격리 없음) · `.page` 규약 실재하지 않음                     iframe + postMessage 런타임 마운트 · SDK PageContainer   N01·N02



B7    DOPQ/HR Addon: i18n 미적용·h1 중복·코어 API 직접 import · `suggest.*` 키는 건의 기능                         규약 검증기(plaza validate) 차단 · 추천 프롬프트 별도 키           N02·C01



B8    MAS 카테고리 seed 4개, slug 28종 미연결 · AdoptWizard 단일 스크롤 폼(호환 경고 무시 가능)                            3축 분류 전부 seed · 단계형 도입 위저드(경고 확인 필수)               E02·E04



B9    모달 a11y 는 ConfirmDialog 만 · MCP 포트 정책 코드/문서 불일치 · 가드레일 도메인 23 vs 24                           전 모달 포커스 트랩·Esc · 런타임 화면 단일 정본 · 서버 카탈로그 정본        8·D06·I01



B10   Playground 비용·토큰 없음 · AssetRegisterModal 진행 표시 없음 · 409 처리 3패턴 · i18n 키 누락 노출                 응답별 토큰·비용 · 8단계 진행 · 409 통일(9장) · 키 누락 빌드 검사       H01·D04·9




AgentPlaza 화면설계서 · v1.0 · 부록 E                                                                                                                                     109
F. 참고 자료 · 템플릿 출처 · 한계
표준·관행은 research/ui_doc_standard.md, 참조 구현은 research/ui_secmp.md·ui_mas.md·ui_core_addon.md 에 원문. [미확인] 은 인용하지 않음



구분             출처                                                                                                                     준용한 요소



               CBD SW개발 표준 산출물 관리 가이드(2011.12) D2 사용자 인터페이스 설계서 —                                                                     구조도 → 화면 목록·출력물 → 화면 상세(화면 ID·유형·경로·개요 + 입출력 항목·처리·기술 고려) · R3 요구사항 추적표
공공 표준
               cisp.or.kr/wp-content/uploads/2012/01/20160909_074634.pdf (전문 확보)                                                      (부록 C)



공공 가이드         디지털 정부서비스 UI/UX 가이드라인(KRDS) v04.krds.go.kr                                                                             접근성(WCAG 2.1 AA)·상태 패턴·레이아웃 항목 범위



               brunch @mojuns 기획 산출물 #2 화면 설계서 · john33fiao.dev 화면정의서 · velog @corone_hi 화면 설계서 작성 · planez 웹기획                       슬라이드 상단 메타(화면ID·이름·경로·버전) + 좌 와이어프레임 번호주석 + 우 Description 표 · 화면 ID 계층·팝업 접미사 ·
국내 관행
               화면설계서 · brunch @junovoir                                                                                               [상황/문구/처리 시나리오] 메시지 표 · 개정 이력·메뉴구조


               이랜서 스토리보드 작성법(blog/detail/66) · 기능 정의서(blog/detail/299) · yamestyle 화면설계서 v1.0 양식 · UIpac 모바일
국내 관행                                                                                                                                 화면 ID 목록 절 · SCR_ 접두 체계 · '선·면·텍스트만' 와이어프레임 · 번호 표기 후 우측 Description
               화면설계서 템플릿 · 프리모아 스토리보드 양식


               NN/g Creating Design Specs for Development · Balsamiq wireframe annotations/annotation guidelines · DECODE Wireframe
국제                                                                                                                                    스펙 = 개발 계약 · 번호 콜아웃 + 별도 설명 영역 · 주석 4분류(Functional/Content/Design/Interaction)
               annotations guide · Helio/ZURB Annotated Wireframes



국제             Material Design 3 · M2 States · Trendyol Tech States · AU Agriculture DS · ServiceNow Horizon Empty state              상태 정의 원칙 · 로딩/빈/오류/콘텐츠 4상태 · 빈 상태 구성요소



               AgentPlaza_PRD.docx v2 (2026-09-18) · 참조 구현 소스(wise-SeCuardian/* · eden-MultiAIAgent/* ·                               FR-D/X/P 94항 · 8단계 등록 · 3경로 · 3축 분류 · AG-UI/MCP 2026-07-28/A2A v1.0.1 · 화면 구조·동작(코드 복제
기준
               eden-project/DOPQ·HRAgent·SmartHaccp·MAA)                                                                              없음)



[미확인]          전자정부사업 품질관리 매뉴얼 · KOSA SW사업 가이드북 · TTA 산출물 검토 가이드 · 민간 PPTX 원본 파일(K9·K11·K12)                                          본문 미열람 — 인용하지 않음. 표준 근거는 CBD 가이드 1건만 전문 확보




한계: ① 참조 화면은 실행 캡처가 아니라 소스(React 컴포넌트·라우트·i18n 키) 역문서화 ② 화면 수는 설계 기준이며 구현 시 -Mnn/-Tnn 파생으로 늘어난다 ③ X09 멀티테넌시 전면·X11 모바일 앱·X12 정산은 확장 지점만 표기 ④ 색·아이콘·
타이포 실제 값은 디자인 시스템 문서에서 확정 ⑤ 시험 ID(TC-UI-…) 열은 구현 착수 시 test/impl 규칙으로 채운다.




AgentPlaza 화면설계서 · v1.0 · 부록 F                                                                                                                                                                                            110
