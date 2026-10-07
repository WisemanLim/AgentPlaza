# 시험 결과 / Test Result — impl 10th (Epic 10 콘솔 API·셋업 위저드·OTel)

- 일자 Date: 2026-10-06
- 대상 Target(profile): `python-fastapi` · OpenTelemetry SDK 1.45 · otel/opentelemetry-collector(debug exporter)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 9, 통과 Pass: 9, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 144 passed (E10 6 + 회귀) · 실 스택 3건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E10-01 | PASS | |
| E10-02 | PASS | |
| E10-03 | PASS | |
| E10-04 | PASS | 보존 기간·HITL TTL 은 설정값(DB) 우선 |
| E10-05 | PASS | |
| E10-06 | PASS | |
| E10-07 | PASS | |
| E10-08 | PASS | input/output 토큰 Int 로 수집 |
| E10-09 | PASS (round 2) | |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | `make test` 300초 초과(멈춘 듯 보임), 단독 실행 87s | 시험 컨테이너에 수집기가 없는데 OTEL_EXPORTER_OTLP_ENDPOINT 로 플랫폼·라이브러리 내보내기가 DNS 실패 재시도 | conftest 에서 OTLP 내보내기 비활성(OTEL_*_EXPORTER=none), 스팬은 인메모리로 검증 | 144 passed in 10s |
| 1 | 실 스택: api 재생성 후 설치 에이전트 호출 DNS 실패 | runtime 이 연결한 에이전트 전용 네트워크 연결이 새 api 컨테이너에는 없음 | runtime 10초 주기 reconcile + api 기동 시 /reconcile 요청 | 강제 분리 후 13초 내 재연결, 호출 성공 |

## 첨부 / Logs

- `logs/make-test.r1~r3.txt`, `logs/e10-live.txt`, `logs/e10-live-reconcile.txt`
