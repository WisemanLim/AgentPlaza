# 시험 결과 / Test Result — impl 24th (Epic 19 알림·상태, P2 D10-07)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · 마이그레이션 0014 · local 스택 · mailpit v1.31.4(compose-optional) · 콘솔
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 7, 통과 Pass: 7, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 277 passed (E19 5 + 회귀 272) · 실 스택 5단계 · 콘솔 E2E 1건 · 접근성 /status·/notifications 라이트·다크 위반 0

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E19-01 | PASS | 관리자: 전체 공지·관리자 알림 / 사용자: 전체 공지·개인 알림 · 중복 None · 읽음 사람마다 · 사용자 /api/status 403 |
| E19-02 | PASS | 첫 점검 변화 0 → 503 → [agents, svc19, False]·unhealthy·routable 비어 있음 → 복구 [.., True]·healthy · 센터 agents_up/agents_down |
| E19-03 | PASS | Slack 2건(warn·error)·Telegram 1건(error)·메일 2건(STARTTLS·로그인) · 재발송 0 · 비밀값 응답에 없음 · 웹훅 URL 아님·tls 잘못 422 · Telegram 연결 시험 ok |
| E19-04 | PASS | 잘못된 zip 업로드 → install_failed(error) · note_forced → budget_forced(warn) · 5일 남은 라이선스만 알림, 두 번째 점검 0건 |
| E19-05 | PASS | 리포트 마크다운 · Slack(min error)에도 리포트 발송 · 주간 켬 → 방금 보내 due 아님 · admin 발송 403 |
| E19-06 | PASS | 구성요소 db·valkey·bifrost·runtime·gateway 정상, Ollama 정상, 에이전트 4 정상 · mailpit 연결 시험 메일 · calculator 정지 → 장애 알림·메일(email ok)·unhealthy → 재기동 → 복구(info, 메일 없음)·healthy · 리포트 메일(LLM 150 호출·비용 $0.072·로컬 97% 등) · 벨 미읽음 3 |
| E19-07 | PASS (round 2) | make test 277 · E2E round 1: 벨 링크 이름이 "🔔 3"(Link 가 aria-label 을 넘기지 않음) → 화면낭독 텍스트로 "알림 3" · axe 위반 0 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | e18_07 회귀: 'function' object has no attribute 'emit' | updates.notify() 함수가 가져온 notify 모듈 이름을 가림 | `from app.services import notify as alerts` | 277 passed |
| 1 | 벨의 접근 가능한 이름이 이모지 | 공용 Link 가 aria-label 을 넘기지 않음 | 이모지 aria-hidden + sr-only "알림" | E2E PASS |
| 1 | (예방) 알림 목록 순서 흔들림 | 같은 초에 만든 알림의 created_at 동률 | id 내림차순 보조 정렬 | E19-01 |
| 1 | (예방) 시험이 호스트 Ollama 에 의존 | 스냅샷이 Ollama 를 직접 확인 | 시험에서 OLLAMA_BASE_URL 을 가짜로 | E19-02 결정적 |

## 첨부 / Logs

- `logs/make-test.txt`(277) · `logs/e19-live.txt` · `logs/e2e.txt` · `logs/e2e/screens/p1-19-*.png` · `logs/a11y/a11y.jsonl`
