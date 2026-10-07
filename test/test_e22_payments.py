"""Epic 22 — 결제 어댑터 Stripe·Polar·Lago (D6-05, PRD Q6, NFR-C4).

호스티드 결제(결제 페이지 URL) → 결제대행 서명 웹훅 → 금액·통화 대조 → 라이선스 발급. 각 결제대행 API 는 가짜 ASGI 서버.
실 테스트 모드 키 검증은 사용자가 키를 넣고 수행(MANUAL, test/impl 결과에 절차).
"""
import base64
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs

import httpx
import pytest
from fastapi import FastAPI, Request

from app.core.config import settings
from app.market import payments
from helpers import auth
from test_e18_market_commerce import PAID, acme, pkg, submit  # noqa: F401 — acme 는 픽스처


def fake_provider(seen: list):
    app = FastAPI()

    @app.post("/v1/checkout/sessions")  # Stripe(form)
    async def stripe(request: Request):
        form = {k: v[0] for k, v in parse_qs((await request.body()).decode()).items()}
        seen.append(("stripe", request.headers.get("authorization"), form))
        return {"id": f"cs_test_{form['client_reference_id'][:8]}", "url": "https://checkout.stripe.test/c/pay"}

    @app.post("/v1/checkouts/")  # Polar(JSON)
    async def polar(request: Request):
        body = await request.json()
        seen.append(("polar", request.headers.get("authorization"), body))
        return {"id": "chk_" + body["metadata"]["purchase_id"][:8], "url": "https://polar.test/checkout/x", "status": "open"}

    @app.post("/api/v1/customers")  # Lago
    async def customers(request: Request):
        seen.append(("lago-customer", request.headers.get("authorization"), await request.json()))
        return {"customer": {"lago_id": "cus_1"}}

    @app.post("/api/v1/invoices")
    async def invoices(request: Request):
        seen.append(("lago-invoice", request.headers.get("authorization"), await request.json()))
        return {"invoice": {"lago_id": "inv_1", "payment_status": "pending"}}

    @app.post("/api/v1/invoices/{lid}/payment_url")
    async def payment_url(lid: str):
        return {"invoice_payment_details": {"lago_customer_id": "cus_1", "payment_url": f"https://pay.lago.test/{lid}"}}
    return app


@pytest.fixture
def paid_listing(client, sup_token, acme):  # noqa: F811
    assert submit(client, sup_token, pkg("acme-pay", "1.0.0", acme["priv"]), "acme", PAID).json()["status"] == "published"
    return "acme-pay"


@pytest.fixture
def provider(monkeypatch):
    seen: list = []
    app = fake_provider(seen)
    for base in ("https://stripe.test", "https://polar.test", "https://lago.test"):
        monkeypatch.setitem(payments.TRANSPORTS, base, httpx.ASGITransport(app=app))
    return seen


def configure(monkeypatch, name: str):
    vals = {"stripe": {"stripe_secret_key": "sk_test_fake", "stripe_webhook_secret": "whsec_fake_stripe",
                       "stripe_api_base": "https://stripe.test"},
            "polar": {"polar_access_token": "polar_oat_fake", "polar_product_id": "prod-1",
                      "polar_webhook_secret": "whsec_" + base64.b64encode(b"polar-fake-secret").decode(),
                      "polar_api_url": "https://polar.test"},
            "lago": {"lago_api_url": "https://lago.test", "lago_api_key": "lago_fake", "lago_webhook_hmac_key": "lago-hmac"}}
    monkeypatch.setattr(settings, "payment_adapter", name)
    for k, v in vals[name].items():
        monkeypatch.setattr(settings, k, v)


def stripe_hook(client, payload: dict, *, secret="whsec_fake_stripe", ts=None):
    body = json.dumps(payload).encode()
    t = str(ts or int(time.time()))
    sig = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post("/api/market/payments/stripe/webhook", content=body,
                       headers={"stripe-signature": f"t={t},v1={sig}", "content-type": "application/json"})


def buy(client, token, lid, seats=2, months=3):
    r = client.post(f"/api/market/purchase/{lid}", json={"seats": seats, "months": months}, headers=auth(token))
    assert r.status_code == 202, r.text
    return r.json()


def test_e22_01_stripe_checkout_webhook_issues_license(client, sup_token, paid_listing, provider, monkeypatch):
    configure(monkeypatch, "stripe")
    h = auth(sup_token)
    r = buy(client, sup_token, paid_listing)
    pu = r["purchase"]
    assert r["checkout_url"] == "https://checkout.stripe.test/c/pay" and pu["status"] == "pending"
    who, authz, form = provider[0]
    assert who == "stripe" and authz == "Bearer sk_test_fake" and form["mode"] == "payment"
    assert form["line_items[0][price_data][unit_amount]"] == "60000" and form["line_items[0][price_data][currency]"] == "krw"
    assert form["client_reference_id"] == pu["id"] and not any("card" in k for k in form)  # 카드 정보 미취급
    assert client.get(f"/api/market/purchases/{pu['id']}", headers=h).json()["checkout_url"] == r["checkout_url"]
    assert client.get(f"/api/licenses?listing={paid_listing}", headers=h).json() == []
    event = {"type": "checkout.session.completed", "data": {"object": {
        "id": pu["adapter_ref"], "client_reference_id": pu["id"], "payment_status": "paid", "amount_total": 60000,
        "currency": "krw"}}}
    assert stripe_hook(client, event, secret="whsec_wrong").status_code == 401
    assert stripe_hook(client, event, ts=int(time.time()) - 3600).status_code == 401  # 재전송 공격
    ok = stripe_hook(client, event)
    assert ok.status_code == 200 and ok.json()["status"] == "paid"
    assert stripe_hook(client, event).json()["status"] == "paid"  # 재전송 — 한 번만 발급
    lics = client.get(f"/api/licenses?listing={paid_listing}", headers=h).json()
    assert len(lics) == 1 and lics[0]["seats"] == 2 and lics[0]["valid"] is True
    rc = client.get(f"/api/market/purchases/{pu['id']}/receipt", headers=h).json()
    assert rc["payment"] == {"adapter": "stripe", "ref": pu["adapter_ref"], "status": "paid"}
    assert client.get(f"/api/market/listings/{paid_listing}", headers=h).json()["licensed"] is True
    assert client.get("/api/audit?action=market.webhook_rejected", headers=h).json()


def test_e22_02_amount_mismatch_and_failure(client, sup_token, paid_listing, provider, monkeypatch):
    configure(monkeypatch, "stripe")
    h = auth(sup_token)
    pu = buy(client, sup_token, paid_listing)["purchase"]
    bad = {"type": "checkout.session.completed", "data": {"object": {
        "id": pu["adapter_ref"], "client_reference_id": pu["id"], "payment_status": "paid", "amount_total": 100,
        "currency": "krw"}}}
    assert stripe_hook(client, bad).json()["status"] == "mismatch"
    assert client.get(f"/api/licenses?listing={paid_listing}", headers=h).json() == []
    pu2 = buy(client, sup_token, paid_listing)["purchase"]
    exp = {"type": "checkout.session.expired", "data": {"object": {"id": pu2["adapter_ref"], "client_reference_id": pu2["id"]}}}
    assert stripe_hook(client, exp).json()["status"] == "expired"
    other = {"type": "customer.created", "data": {"object": {"id": "cus_1"}}}
    assert stripe_hook(client, other).json() == {"ok": True, "ignored": True}


def test_e22_03_polar_standard_webhooks(client, sup_token, paid_listing, provider, monkeypatch):
    configure(monkeypatch, "polar")
    h = auth(sup_token)
    r = buy(client, sup_token, paid_listing, seats=1, months=1)
    pu = r["purchase"]
    who, authz, body = provider[0]
    assert who == "polar" and body["products"] == ["prod-1"] and body["amount"] == 10000 and authz == "Bearer polar_oat_fake"
    payload = json.dumps({"type": "order.paid", "data": {"id": "ord_1", "status": "paid", "checkout_id": pu["adapter_ref"],
                                                          "total_amount": 10000, "currency": "krw",
                                                          "metadata": {"purchase_id": pu["id"]}}}).encode()
    mid, ts = "msg_1", str(int(time.time()))
    key = base64.b64decode(settings.polar_webhook_secret.removeprefix("whsec_"))
    sig = base64.b64encode(hmac.new(key, f"{mid}.{ts}.".encode() + payload, hashlib.sha256).digest()).decode()
    hdr = {"webhook-id": mid, "webhook-timestamp": ts, "content-type": "application/json"}
    assert client.post("/api/market/payments/polar/webhook", content=payload,
                       headers=hdr | {"webhook-signature": "v1,AAAA"}).status_code == 401
    ok = client.post("/api/market/payments/polar/webhook", content=payload, headers=hdr | {"webhook-signature": f"v1,{sig}"})
    assert ok.json()["status"] == "paid"
    assert client.get(f"/api/licenses?listing={paid_listing}", headers=h).json()[0]["seats"] == 1
    # 다른 어댑터 이름으로 오면 거부
    assert client.post("/api/market/payments/stripe/webhook", content=payload, headers=hdr).status_code == 401


def test_e22_04_lago_invoice_payment_url_and_hmac(client, sup_token, paid_listing, provider, monkeypatch):
    configure(monkeypatch, "lago")
    h = auth(sup_token)
    r = buy(client, sup_token, paid_listing, seats=1, months=2)
    assert r["checkout_url"] == "https://pay.lago.test/inv_1" and r["purchase"]["adapter_ref"] == "inv_1"
    cust = next(b for w, _, b in provider if w == "lago-customer")["customer"]["external_id"]
    inv = next(b for w, _, b in provider if w == "lago-invoice")["invoice"]
    assert cust.startswith("plaza-") and "@" not in json.dumps(provider)  # 구매자 이메일 원문을 보내지 않음
    assert inv["fees"][0]["unit_amount_cents"] == 20000 and inv["currency"] == "KRW"

    def hook(payment_status, key="lago-hmac"):
        body = json.dumps({"webhook_type": "invoice.payment_status_updated", "object_type": "invoice", "invoice": {
            "lago_id": "inv_1", "payment_status": payment_status, "total_amount_cents": 20000, "currency": "KRW"}}).encode()
        sig = base64.b64encode(hmac.new(key.encode(), body, hashlib.sha256).digest()).decode()
        return client.post("/api/market/payments/lago/webhook", content=body,
                           headers={"x-lago-signature": sig, "x-lago-signature-algorithm": "hmac"})
    assert hook("succeeded", key="wrong").status_code == 401
    assert hook("pending").json() == {"ok": True, "ignored": True}
    assert hook("succeeded").json()["status"] == "paid"
    assert len(client.get(f"/api/licenses?listing={paid_listing}", headers=h).json()) == 1


def test_e22_05_adapter_selection_and_minor_units(client, sup_token, paid_listing, monkeypatch):
    monkeypatch.setattr(settings, "payment_adapter", "stripe")
    monkeypatch.setattr(settings, "stripe_secret_key", "")  # 키가 없으면 꺼짐 → 키 직접 입력만
    assert payments.adapter() is None
    assert client.post(f"/api/market/purchase/{paid_listing}", json={}, headers=auth(sup_token)).status_code == 409
    assert payments.minor(9900, "KRW") == 9900 and payments.minor(12, "USD") == 1200
    assert client.post("/api/market/payments/stripe/webhook", content=b"{}").status_code == 401
