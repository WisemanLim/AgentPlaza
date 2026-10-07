# 시험 결과 / Test Result — impl 20th (Epic 20 LLM 게이트웨이 Bifrost 전환·월 예산 로컬 강제)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · Bifrost `maximhq/bifrost:v2.2.6`(Apache-2.0, compose 서비스) · 호스트 Ollama · 콘솔 LLM 화면
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 8, 통과 Pass: 8, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 259 passed (E20 6 + 회귀 253) · 실 스택 6단계 · 콘솔 E2E 1건 · 접근성 /llm 라이트·다크 위반 0

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E20-01 | PASS | 가짜 Bifrost 가 받은 모델: ollama/granite4.1:3b · anthropic/claude-x · ollama/bge-m3, 퍼블릭 공급자 api_key 빈 값 |
| E20-02 | PASS | 닫힌 포트 → 직접 Ollama 응답, fallbacks 1, openai 는 ProviderError |
| E20-03 | PASS | openai/gpt-x 400 → ollama/granite4.1:3b, fallback_from=openai/gpt-x |
| E20-04 | PASS | 강제 후 mock/echo + x-plaza-budget · 원장 1건 · 퍼블릭 전용 별칭 403 reason=budget · 예산 0 → 퍼블릭 복귀 |
| E20-05 | PASS | admin 조회 200·변경 403, user 403, ratio 0.3·monthly -1 → 422 |
| E20-06 | PASS | find_spec('litellm') None, compose api 키 "", bifrost v-태그·ports 없음·read_only·cap_drop |
| E20-07 | PASS (round 2) | 공급자: bifrost reachable·ollama/퍼블릭 4종 via bifrost · plaza/fast 응답 시 Bifrost 메트릭 12→15 · L3 → 로컬 · Bifrost 정지 → 응답 유지(직접 폴백 1) → 재기동 healthy · 예산 0.05 USD: 1·2번째 호출 mistral(가상 유료, 단가 1.0/1k) → 3·4번째 granite + local-forced, 사용률 1.44, 원장 month:2026-10 1건 · 정리(예산 0·가상 모델 비활성) |
| E20-08 | PASS | make test 259 · /llm: "ollama (15) · via Bifrost"·"bifrost · 직접 호출 폴백"·예산 meter · axe 위반 0 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | (사전 조사) Bifrost 가 호스트 Ollama 에 502 | Bifrost 기본 SSRF 차단: 사설 IP 연결 거부 | Ollama 공급자에만 `network_config.allow_private_network: true` | 실 호출 200 |
| 1 | (예방) Bifrost 장애 = 로컬 대화 중단 | 경유 엔진이 단일 장애점 | 연결 실패(ProviderUnreachable)면 로컬 Ollama 직접 호출 | E20-02·실 스택 정지 시험 |
| 1 | (예방) api 에 퍼블릭 키 잔존 | env_file 이 api 에도 키를 넘김 | compose api environment 에서 키를 빈 값으로 덮고 bifrost 에만 주입 | E20-06·실 스택 env 확인 |
| 1 | 실 스택 예산 시험 별칭 422 | 별칭은 plaza/ 접두어 규칙(시험 스크립트 오류) | plaza/budget-test 로 재실행(round 2) | PASS |

## 첨부 / Logs

- `logs/make-test.txt`(259) · `logs/e20-live.txt` · `logs/e2e/screens/p1-20-llm-budget.png` · `logs/a11y/a11y.jsonl`
