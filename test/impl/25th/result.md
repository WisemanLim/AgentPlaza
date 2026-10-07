# 시험 결과 / Test Result — impl 25th (Epic 25 채널·임베드, P2 D3-07)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · 마이그레이션 0015 · local 스택(Traefik /widget) · 가짜 Slack·Telegram·카카오 콜백 서버 · 콘솔·브라우저 위젯
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 10, 통과 Pass: 9, 실패 Fail: 0, MANUAL 1, 최종 Verdict: **PASS** (E25-10 실 메신저 연결은 사용자 수행)
- pytest 284 passed (E25 7 + 회귀 277) · 실 스택 5단계 · 콘솔·위젯 E2E 2건 · 접근성 C07·위젯 화면 라이트·다크 위반 0

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E25-01 | PASS | telegram 생성 → WEBHOOK_SECRET 1회 · BOT_TOKEN 저장 후 목록에 원문 없음 · 생성 비밀값 덮어쓰기 422 · web 오리진 없음/javascript: 422 · 재발급 값 변경 · 사용자 403 |
| E25-02 | PASS | challenge 응답 · 서명 틀림·1시간 전 401 · "<@U0BOT> 안녕 슬랙" → thread_ts 111.1 에 "echo: 안녕 슬랙"(Bearer 봇 토큰) · 후속 답 같은 세션(메시지 4) · 재전송·봇 메시지 무시 · 원장 channel.rejected |
| E25-03 | PASS | 비밀 틀림 401 · sendMessage {chat_id 42, reply_parameters 7} · 채널 끔 401 |
| E25-04 | PASS | 토큰 틀림 401 · 즉시 simpleText · 콜백 블록 useCallback → bot-api.kakao.com 콜백에 template · evil.example 콜백은 호출하지 않고 즉시 답 |
| E25-05 | PASS | 로더 JS 문자열 이스케이프 · 인사말 HTML 이스케이프 · CSP frame-ancestors https://shop.example(없으면 'none') · SSE "echo: 위젯 질문" · 같은 방문자 재사용 · 위젯 토큰으로 /api/sessions 401 · 다른 위젯 토큰 401 · 끔 404 |
| E25-06 | PASS | ops.execute_action → 답에 승인 안내, 승인함 요청자 channel:kk2:kakao:u |
| E25-07 | PASS (round 2) | 브라우저 위젯 E2E 에서 발견 — 방문자마다 좌석을 씀 → 채널 단위 좌석 하나로 |
| E25-08 | PASS (round 2) | 채널 4종 · 카카오(전체 에이전트) 오케스트레이션 4.5초 초과 → 안내 문구(콜백 블록 권장) · round 2 LLM 단독 채널 0.39·0.29초 답·기록 회상 · Slack challenge·서명 틀림 401 · Telegram 401 · /widget 로더 200·CSP·SSE 실 답 · 위젯 토큰 플랫폼 401 |
| E25-09 | PASS (round 3) | make test 284 · C07 화면 · 고객 사이트(허용 오리진 127.0.0.1:8099)에 삽입 → 버튼 → iframe 대화 "안녕하세요" · axe 위반 0 |
| E25-10 | MANUAL | 실 Slack·Telegram·카카오 계정·공개 HTTPS 필요 — scenario.md 절차 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | Slack 답장이 가짜 서버로 가지 않음(ConnectError) | 시험 전송 키를 API 기준 URL 전체로 찾음 | 기준 URL 의 오리진으로 찾음 | E25-02 |
| 1 | (보안) 위젯 토큰이 플랫폼 API 에서 500 가능 | current_principal 이 typ 을 user 로 가정하고 사용자 id 로 변환 | user·service 외 토큰 유형은 401 | E25-05 |
| 2 | 공개 위젯이 유료 에이전트 좌석을 방문자마다 소진 | 채널 주체가 방문자별 | 좌석 보유자를 채널 단위(channel:<id>)로 | E25-07 |
| 2 | (시험 환경) 브라우저가 위젯 스크립트를 막음 | Chromium Local Network Access: 가짜 고객 사이트(공개 취급) → 루프백 | 위젯 E2E 만 LNA 검사 끔(실제 배포는 공개 주소라 해당 없음) | E2E PASS |
| 2 | (운영 메모) 카카오 동기 블록 5초 제한 | 오케스트레이션(계획 LLM)은 수 초 | 4.5초에 안내 문구, 긴 답은 콜백 블록 또는 LLM 단독 채널 | E25-08 |

## 첨부 / Logs

- `logs/make-test.txt`(284) · `logs/e25-live.txt` · `logs/e2e.txt` · `logs/e2e/screens/p1-25-channels.png` · `logs/e2e2/screens/p1-25-widget.png` · `logs/a11y/a11y.jsonl`
