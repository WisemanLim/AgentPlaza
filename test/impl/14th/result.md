# 시험 결과 / Test Result — impl 14th (Epic 14 실행 내구성·운영)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · LangGraph 1.2 + langgraph-checkpoint-sqlite/postgres · runtime(docker:cli) 백업·복원
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 12, 통과 Pass: 12, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 206 passed (E14 9 + 회귀 197) · 실 스택(실 runtime·api 재시작·오프라인 번들) 5건 · 콘솔 E2E 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E14-01 | PASS | s2 도중 예외 → Task running·결과는 체크포인트에만 → recover_stale 가 s2 만 실행(호출 3회 = s1 1 + s2 2), 원장 task.recovered |
| E14-02 | PASS | 실 스택: 20초 단계 실행 중 api 컨테이너 재시작 → 진행 신호 정지 후 복구 루프가 재개, 약 2분 뒤 succeeded(단어 수 2) |
| E14-03 | PASS | 최근 heartbeat 의 running 작업은 잡지 않는다 |
| E14-04 | PASS | 연결 실패 1회 → 2회째 성공·retry 이벤트, 비멱등 503 재시도 안 함, 멱등 503 3회 한도·원장 attempts=3 |
| E14-05 | PASS | 글 생성 후 계산 실패 → compensation(delete id={{result.id}}) 실행, 글 목록 비어 있음, tool.compensated |
| E14-06 | PASS | 선언 안 된 compensation verb → 검증 오류 |
| E14-07 | PASS (round 2) | Fake: build→backup→up, 실패 시 down→restore→up. 실 runtime: 1.0.1(선언 vs 핸들러 불일치로 컨테이너 종료) → 롤백·복원 → 1.0.0 healthy, 글 보존. 실패 버전 이력·산출물 제거 |
| E14-08 | PASS | 사전 백업 실패 → 5단계 중단, 이전 버전 유지 |
| E14-09 | PASS | 실 runtime: 글 → 백업(일시정지 스냅숏 tar.gz + manifest sha256) → 삭제 → 복원 → 글 복구, `../../etc` 422 · 없는 백업 404 |
| E14-10 | PASS | /api/admin/backup·`make backup`: SQLite 온라인 백업(385KB) + board·ops-approval 볼륨, supervisor 전용 |
| E14-11 | PASS (round 2) | `make offline-bundle`(이미지 2 + 카탈로그 + trivy DB 125MB + 모델 목록, 209MB) → 이미지 삭제 → `make offline-load` 로 복원·trivy 볼륨 적재. 변조 번들은 해시 불일치로 거부 |
| E14-12 | PASS | make test 206 passed · 콘솔: 에이전트 백업 섹션(지금 백업·복원)·설정 전체 백업 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 변조 번들이 적재됨 | load.sh 의 `check && echo` — `set -e` 는 `&&` 목록 안 실패로 종료하지 않는다 | `check \|\| { echo FAIL; exit 1; }` | 변조 거부(rc≠0), 정상 번들 OK |
| 1 | 실패한 업그레이드 버전(1.0.1)이 버전 이력에 남아 '롤백' 버튼 노출 | 롤백이 새 버전 AgentVersion·산출물을 지우지 않음(P0부터) | 롤백 시 실패 버전 행·zip·SBOM 삭제 | 시험 단언 추가, PASS |
| 1 | E2E 백업 행 수 단언 실패 | 목록 로드 전에 행 수를 셈 | 첫 행 표시를 기다린 뒤 셈 | PASS |

## 첨부 / Logs

- `logs/make-test.txt`(206 passed), `logs/e14-live.txt`, `logs/e2e/screens/p1-14-*.png`
