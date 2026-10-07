# 시험 결과 / Test Result — impl 13th (Epic 13 거버넌스·보안)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · AES-GCM(cryptography) · Valkey 8 · 실 qwen3:8b(리뷰어)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 20, 통과 Pass: 20, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 197 passed (E13 28 + 회귀 169) · 실 스택 시나리오 2묶음 · 콘솔 E2E 1건(스크린샷 3)

## 청크별 결과 / Chunk Results

| 청크 | 영역 | 총 | PASS | FAIL | 판정 |
|---|---|---|---|---|---|
| chunk-1 | 시크릿·정책 엔진 (D9-04·D9-05) | 11 | 11 | 0 | PASS |
| chunk-2 | 가드레일·리뷰어·게이트웨이 (D9-06·D2-05·D7-07) | 9 | 9 | 0 | PASS |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | compose 시크릿 주입 불가 | Compose 5.5 는 read_only 서비스에 `file` 시크릿만 허용, runtime(docker-in-docker)은 호스트 경로가 없어 file 시크릿 불가 | 설계 변경: 에이전트가 자기 키로 플랫폼에서 pull(SDK `ctx.secret`, 30초 캐시) — 원문이 디스크·컨테이너 설정에 없음 | PASS |
| 1 | 기본 정책이 원격(link) 에이전트를 막아 P0 경로 C 회귀(e8_07) | external_tool_max_level 기본 L1 < 기본 요청 등급 L2 | 기본 L2(L3 만 차단, 조직이 L1 로 강화 가능) | 169→197 passed |
| 1 | 계좌번호 패턴이 카드형 숫자 일부를 잡음 | 경계에 `-` 미포함 | `(?<![\d-])…(?![\d-])` | PASS |
| 1 | 레이트리밋 시험의 익명 호출이 사용자로 집계 | TestClient 가 세션 쿠키를 유지(쿠키도 신원) | 시험에서 쿠키 제거. 다른 시험은 RATE_LIMIT_ENABLED=false | PASS |
| 1 | 실 스택: 에이전트가 시크릿을 못 받음(빈 값) | 생성 compose 의 environment 매핑에 PLAZA_API_URL 누락 | generator be_env 에 추가 | round 2 PASS |
| 2 | 실 스택: board 호출 DNS 실패 | 로컬 스택의 board·ops-approval 컨테이너가 사라져 있었음(같은 Docker 호스트에 다른 프로젝트 세션 다수, 원인 시점 이벤트 기록 없음). `make test` 는 실 runtime 의 build/up/down 을 호출하지 않음을 계수로 확인 | 마켓에서 재설치. 방어: conftest `RUNTIME_DRIVER=none` 으로 시험이 실 runtime 에 닿지 않게 | round 2 PASS |

## 첨부 / Logs

- `chunk-1/logs/make-test.txt`(197 passed), `chunk-1/logs/e13-live.txt`, `chunk-2/logs/e13-live.txt`, `chunk-2/logs/e2e/screens/p1-13-*.png`
