# 시험 결과 / Test Result — impl 22nd (Epic 22 결제 어댑터 Lago·Polar·Stripe)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · 가짜 결제대행 서버(ASGI) · stripe/stripe-mock · local 스택 · 콘솔
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 9, 통과 Pass: 8, 실패 Fail: 0, MANUAL 1, 최종 Verdict: **PASS** (E22-09 는 실 테스트 키가 필요해 사용자 수행 항목)
- pytest 267 passed (E22 5 + 회귀 262) · stripe-mock 1건 · 실 스택 4건 · 콘솔 E2E 1건

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E22-01 | PASS | unit_amount 60000 krw · client_reference_id = 구매 id · 서명 틀림·1시간 전 401 · paid → 라이선스 1건(좌석 2) · 재전송에도 1건 · 영수증 payment {adapter: stripe, status: paid} |
| E22-02 | PASS | amount_total 100 → mismatch(발급 0) · expired · customer.created 무시 |
| E22-03 | PASS | Polar 본문 products [prod-1]·amount 10000 · v1,AAAA 401 · 정상 서명 paid · 다른 어댑터 경로 401 |
| E22-04 | PASS | payment_url https://pay.lago.test/inv_1 · unit_amount_cents 20000 · external_id plaza-<해시>(이메일 없음) · 틀린 키 401 · pending 무시 · succeeded paid |
| E22-05 | PASS | 키 없음 → 어댑터 None·구매 409 · minor(9900,KRW)=9900·minor(12,USD)=1200 |
| E22-06 | PASS | stripe-mock: checkout.session 생성(cs_test_…, checkout.stripe.com URL) · unit_amount "abc" → 400 Request validation error |
| E22-07 | PASS | /api/market/payments/{stripe,polar,lago}/webhook 서명 없음 401 ×3 · mock 구매 201 |
| E22-08 | PASS | make test 267 · NFR-S5 무인증 경로 시험 통과(웹훅은 서명 없으면 401) · 복귀 화면 3상태 |
| E22-09 | MANUAL | 실 결제대행 테스트 모드 키 필요 — scenario.md 절차 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | (설계) 웹훅이 무인증 허용목록(NFR-S5)을 깰 위험 | 결제대행은 플랫폼 자격증명을 보낼 수 없음 | 인증 = 결제대행 서명, 서명·어댑터가 맞지 않으면 401 | e1_10 PASS |
| 1 | (예방) 웹훅 재전송·금액 변조 | 결제대행은 같은 이벤트를 여러 번 보낼 수 있음 | pending 일 때만 발급(멱등), 금액·통화가 구매 기록과 다르면 mismatch | E22-01·02 |
| 1 | (시험 환경) 실 스택 mock 구매가 E18 화면 시험 전제(acme-pro 미라이선스)를 바꿈 | 라이브 데이터 공유 | 시험용 라이선스 철회·UI 시험용 구매 행 제거 | E18 전제 복구 |

## 첨부 / Logs

- `logs/make-test.txt`(267) · `logs/stripe-mock.txt` · `logs/e22-live.txt` · `logs/e2e.txt` · `logs/e2e/screens/p1-22-*.png`
