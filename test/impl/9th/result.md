# 시험 결과 / Test Result — impl 9th (Epic 9 마켓플레이스 설치 3경로)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · 정적 카탈로그 `market/catalog.json`(8 리스팅) · git 포함 이미지
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 11, 통과 Pass: 11, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 138 passed (E9 10 + 회귀) · 실 스택 US2 17s

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E9-01 | PASS | |
| E9-02 | PASS | |
| E9-03 | PASS | |
| E9-04 | PASS | |
| E9-05 | PASS | |
| E9-06 | PASS | |
| E9-07 | PASS | file:// 은 비운영 환경에서만 허용 |
| E9-08 | PASS | 경로 C 엔진은 Epic 8(link) 재사용 |
| E9-09 | PASS | |
| E9-10 | PASS | |
| E9-11 | PASS | 17s (에이전트 이미지·빌드 캐시 삭제, python 베이스 이미지는 캐시 상태) |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 0 (설계) | 동기 zip 다운로드가 시험용 ASGI 전송을 못 씀 | httpx 동기 클라이언트 | zip URL·artifact 를 async 로, git 은 스레드 실행 | round 1 통과 |

## 범위 메모

- 경로 B 의 OCI 아티팩트(ORAS)·사설 미러는 미구현 — 레지스트리 클라이언트 필요(계획표 가정). zip 업로드·zip URL·Git 은 구현.

## 첨부 / Logs

- `logs/make-test.r1.txt`, `logs/e9-live-us2.txt`
