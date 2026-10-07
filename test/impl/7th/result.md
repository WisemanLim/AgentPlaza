# 시험 결과 / Test Result — impl 7th (Epic 7 런타임·compose·라우팅·격리)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` + runtime(docker:cli + stdlib) + traefik v3.7.13 · Docker Engine 29.8 · Compose v5.5.1 · runc(gVisor 미설치)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 15, 통과 Pass: 15, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 119 passed · 실 E2E(설치·라우팅·격리·LLM·삭제) · M1 매트릭스 8/8

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E7-01 | PASS | |
| E7-02 | PASS | 13 변형 |
| E7-03 | PASS | |
| E7-04 | PASS | |
| E7-05 | PASS | |
| E7-06 | PASS | |
| E7-07 | PASS | |
| E7-08 | PASS | |
| E7-09 | PASS | 경로 /a/board/… 키는 Traefik 이 주입, 클라이언트 비노출 |
| E7-10 | PASS | `Network is unreachable` |
| E7-11 | PASS | internal 네트워크 |
| E7-12 | PASS | |
| E7-13 | PASS (round 2) | 계획 정확·실행됨(id 2). 합성 문장 시제 지침 보강 |
| E7-14 | PASS | 403(forwardAuth: 카탈로그에 없음) |
| E7-15 | PASS | 6–9s/유형 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | E7-04 무인증 기대 401 → 200 | (시험) 셋업 응답 쿠키가 TestClient 에 남음 — 쿠키 인증은 정상 | 시험 시작 시 쿠키 제거 | 119 passed |
| 1 | Traefik 첫 요청 404 | 기동 직후 provider 설정 로딩 전 요청 | 재요청 200. 진단용 `--log.level` INFO 기본 추가 | — |
| 1 | 실 LLM 이 빈 계획 → 일반 답변이 "등록해 드리겠습니다"(미실행 환각) | 카탈로그에 에이전트명·enum 없음, 일반 답변 지침 부재 | 계획 프롬프트(표시명·enum·예시), 일반 답변에 "도구 미실행 시 실행 주장 금지" | round 2: 계획·실행 성공, 날씨 요청은 정직 답변 |
| 2 | 합성 답변 미래형("등록하겠습니다") | 지침이 결과 요약만 요구 | "이미 실행됨 — 과거형 보고" 지침 | — |
| 2 | Epic 6 실패 설치가 빈 `installed/live6` 디렉터리 남김 | 실패 시 하위만 삭제 | 실패·롤백 후 빈 상위 디렉터리 정리(_prune), E6-11 단언 강화 | 119 passed |
| — | (하네스) zsh `set -- $spec`·`$DCP` 단어 분리 안 됨 | zsh 동작 | 명령 개별 실행·래퍼 스크립트 | — |

## 첨부 / Logs

- `logs/make-test.r1~r3.txt`, `logs/e7-install-status.txt`, `logs/e7-live-routing-isolation.txt`, `logs/e7-live-isolation-orchestrate.txt`, `logs/e7-live-orchestrate.r2.txt`, `logs/e7-live-delete.txt`, `logs/e7-m1-matrix.txt`
