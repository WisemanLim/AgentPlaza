# impl 25th — Epic 25 채널·임베드 (P2, D3-07)

FR: D3-07(웹 위젯·메신저 채널) · UI C07 · 결정: 웹 위젯·Slack·Telegram·카카오 모두, 실 서비스 토큰은 사용자 입력·시험은 가짜 서버

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E25-01 | 채널 관리 | 생성(4종)·비밀값·재발급·삭제·권한·검증 | 생성 비밀값 1회 노출, 쓰기 전용, 사용자 403, 잘못된 오리진 422 | P0 |
| E25-02 | Slack Events | url_verification · 서명 틀림/오래됨 · app_mention · 스레드 후속 · 재전송·봇 메시지 | challenge · 401 · 스레드에 답(chat.postMessage) · 같은 스레드 = 같은 세션 · 무시 | P0 |
| E25-03 | Telegram | secret token 틀림 · 정상 · 채널 끔 | 401 · sendMessage(reply_parameters) · 401 | P0 |
| E25-04 | 카카오 i 오픈빌더 | 토큰 틀림 · 콜백 없는 블록 · 콜백 블록 · 외부 도메인 콜백 | 401 · simpleText 즉시 · useCallback → 콜백 POST · 카카오 도메인만(SSRF 차단) | P0 |
| E25-05 | 웹 위젯 | 로더·페이지·app.js · CSP · 세션 토큰 · SSE 대화 · 다른 위젯 토큰 · 플랫폼 API · 꺼짐 | 이스케이프 · frame-ancestors=허용 오리진 · 같은 방문자 연속 · 401 · 404 | P0 |
| E25-06 | 승인 필요 작업 | 채널에서 승인 필요 capability | 콘솔 승인함 안내 + 승인 요청 생성(요청자 = 채널 주체) | P1 |
| E25-07 | 유료 좌석 | 채널 방문자 여럿 | 채널 = 좌석 하나 | P1 |
| E25-08 | 실 스택 | 채널 4종 생성 · 카카오(오케스트레이션·LLM 단독) · Slack challenge · Telegram 거부 · 위젯 Traefik /widget·SSE | 동작 · 401 · 실 LLM 답 | P0 |
| E25-09 | 회귀·콘솔·접근성 | make test · C07 화면 · 고객 사이트에 삽입한 위젯(브라우저) · axe | 전체 통과 · 대화 · 위반 0 | P0 |
| E25-10 | 실 메신저 | 실제 Slack 앱·Telegram 봇·카카오 채널에 연결 | MANUAL(아래 절차) | P2 |

> MANUAL(E25-10): Slack 앱 Event Subscriptions URL = 채널의 웹훅 주소, Signing Secret·Bot Token(chat:write) 입력 · Telegram `setWebhook(url=웹훅 주소, secret_token=생성 비밀값)` + 봇 토큰 입력 · 카카오 i 오픈빌더 스킬 URL = 스킬 주소, 헤더 X-Plaza-Channel-Token = 생성 토큰, 답이 5초를 넘는 블록은 콜백 사용 설정. 모두 공개 HTTPS 주소(PUBLIC_BASE_URL)가 필요하다.
