# 시험 결과 / Test Result — impl 6th (Epic 6 패키지·레지스트리 8단계)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · 런타임 드라이버 fake(시험) / none(실 스택) — 실 Docker 빌드·기동은 Epic 7
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 17, 통과 Pass: 17, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 100 passed (E6 35 케이스 파라미터 포함 + 회귀) · 실 스택 게이트 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E6-01 | PASS | |
| E6-02 | PASS | |
| E6-03 | PASS | 8 변형 |
| E6-04 | PASS | |
| E6-05 | PASS | |
| E6-06 | PASS | FTS5 는 sqlglot 파싱 불가 → 허용 패턴으로 예외 처리 |
| E6-07 | PASS | |
| E6-08 | PASS | |
| E6-09 | PASS | |
| E6-10 | PASS | |
| E6-11 | PASS | |
| E6-12 | PASS | |
| E6-13 | PASS | 실 컨테이너 제거 시간은 Epic 7 에서 재측정 |
| E6-14 | PASS | |
| E6-15 | PASS | |
| E6-16 | PASS | |
| E6-17 | PASS | |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | E6-03[bomb] 압축 폭탄 미탐지 | (시험 하네스) `ZipInfo` 기본 compress_type=STORED → 비율 1 | 시험 zip 을 DEFLATED 로 생성, parametrize ids 지정(바이트 ID 로 로그 4.8MB 폭증) | round 2: 100 passed |

## 첨부 / Logs

- `logs/make-test.r1.tail.txt`, `logs/make-test.r2.txt`, `logs/e6-live-gate.txt`
