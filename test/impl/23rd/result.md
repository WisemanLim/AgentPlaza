# 시험 결과 / Test Result — impl 23rd (Epic 23 조직·부서 단위 배치·조직 화면)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · 마이그레이션 0013(orgs·org_members·org_groups·group_members·agent_scopes) · local 스택 · 콘솔
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 7, 통과 Pass: 7, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 272 passed (E23 5 + 회귀 267) · 실 스택 4단계 · 콘솔 E2E 1건 · 접근성 /orgs 라이트·다크 위반 0

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E23-01 | PASS | 기본 조직 구성원 4(supervisor+3) · dev1 조직 생성 403 · acme-kr 비구성원 404 · default 삭제 409 |
| E23-02 | PASS | sales1(플랫폼 user, 조직 admin): 그룹 생성·중복 409·구성원 추가 · 다른 조직 403 · 없는 사용자 404 · 배치 범위 403 |
| E23-03 | PASS (round 2) | 영업팀 배치: sales 목록·실행·MCP 200·forward 200·agent/calc / dev 목록 없음·상세 404·실행 없음·MCP 403·forward 403·모델 없음 · supervisor 보임 · 원장 agent.scope_set |
| E23-04 | PASS | user 범위 → dev1 만 · 조직(lab) 범위 → sales2 만 · 비구성원 지정 422 · 없는 조직 404 · 해제 → 모두 · 구성원 제거 |
| E23-05 | PASS | board 설치 + deploy_scope(그룹) 저장 · 없는 그룹 422 |
| E23-06 | PASS | 기본 조직 이관 구성원 2 · staff 범위 밖: 목록 False·MCP 403·/a/calculator/health 403·/v1 False → 영업팀 가입 후 True·200·200·True · 해제 |
| E23-07 | PASS (round 2) | make test 272 · E2E: 조직 탭·영업팀·구성원, 에이전트 상세 배치 범위(그룹 체크박스), 마켓 도입 배치 대상(사용자) · axe round 1 /orgs color-contrast → round 2 위반 0 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | (시험) 범위 밖 사용자의 계획에 misses 가 없음 | 후보에서 빠지면 계획 단계 자체가 만들어지지 않음(registry_miss 아님) | 시험 기대를 "실행되지 않음"으로 정정 — 노출 차단이 목적 | PASS |
| 1 | /orgs 선택된 조직 탭의 숫자 대비 1.1:1 | 강조(primary) 버튼 안에 회색 보조 글자(.sub) | 탭 안에서는 버튼 글자색 그대로 | 위반 0 |
| 1 | (예방) 시험 정리가 기본 조직을 지움 | 시험은 매번 모든 테이블을 비움 | 기본 조직은 사용할 때 없으면 만든다(default_org) | 시험 통과 |

## 첨부 / Logs

- `logs/make-test.txt`(272) · `logs/e23-live.txt` · `logs/e2e.txt` · `logs/e2e/screens/p1-23-*.png` · `logs/a11y/a11y.jsonl`
