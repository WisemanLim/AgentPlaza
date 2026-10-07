# impl 22nd — Epic 22 결제 어댑터 Lago·Polar·Stripe

FR: D6-05 · PRD Q6(Lago/Polar/Stripe) · NFR-C4(영수증·라이선스 증적) · COMPLIANCE: 결제 정보 미저장(호스티드), 비운영 실결제 금지

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E22-01 | Stripe Checkout + 웹훅 | 유료 리스팅 구매(2좌석·3개월) → checkout.session.completed | 202 + 결제 URL · pending · 카드 필드 없음 · 서명 틀림/오래됨 401 · 정상 → paid·라이선스·영수증 · 재전송 1회만 | P0 |
| E22-02 | 금액 대조·실패 | amount_total 불일치 · expired · 무관한 이벤트 | mismatch(발급 안 함) · expired · ignored | P0 |
| E22-03 | Polar(Standard Webhooks) | 체크아웃(products·amount·metadata) → order.paid | 서명 v1(base64) 검증, 다른 어댑터 경로 401, paid·좌석 1 | P0 |
| E22-04 | Lago 청구 | 고객·인보이스(add-on 수수료)·payment_url → invoice.payment_status_updated | X-Lago-Signature(HMAC base64), pending 무시, succeeded → paid, 구매자 이메일 미전송 | P0 |
| E22-05 | 선택·단위 | 키 없는 어댑터 · KRW/USD | 어댑터 꺼짐 409 · 최소 단위(KRW 그대로, USD ×100) · 웹훅 401 | P1 |
| E22-06 | Stripe API 적합 | stripe/stripe-mock(공식 OpenAPI 검증 서버) | 체크아웃 세션 생성 성공, 잘못된 파라미터 400 | P1 |
| E22-07 | 실 스택 | Traefik 경유 웹훅(서명 없음) · mock 구매 | 401 ×3 · 201 | P0 |
| E22-08 | 회귀·콘솔 | make test · 결제 복귀 화면 | 전체 통과 · "결제 확인 중"·"결제 취소됨"·"결제 완료"+영수증 | P0 |
| E22-09 | 실 테스트 모드 키 | 사용자가 Stripe/Polar 샌드박스·Lago 키를 넣고 결제 | MANUAL(아래 절차) | P2 |

> MANUAL 절차(E22-09): `.env.local` 에 `PAYMENT_ADAPTER=stripe` + `STRIPE_SECRET_KEY=sk_test_…` + `STRIPE_WEBHOOK_SECRET=whsec_…`(stripe CLI `stripe listen --forward-to http://127.0.0.1:8090/api/market/payments/stripe/webhook` 이 출력) → `make local-restart SVC=api` → 콘솔 유료 리스팅에서 "결제로 발급" → 시험 카드 4242… 로 결제 → 복귀 화면 "결제 완료". Polar 는 sandbox(POLAR_API_URL=https://sandbox-api.polar.sh, custom price 상품 id), Lago 는 자체 호스팅 + add-on 코드 + HMAC 웹훅.
