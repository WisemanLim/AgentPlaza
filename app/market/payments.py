"""결제 어댑터(D6-05, PRD Q6): mock(즉시 결제, 시험·폐쇄망) + 호스티드 결제 Stripe Checkout · Polar Checkout · Lago 청구.

호스티드 흐름: 구매 → 결제 페이지(어댑터가 만든 URL)로 이동 → 결제대행이 서명한 웹훅 → 금액·통화 대조 → 라이선스 발급.
플랫폼은 카드·계좌 정보를 받지 않는다(호스티드 결제). 정산·세금·환불은 범위 밖(X12, NFR-C4).
PAYMENT_ADAPTER = none(키 직접 입력만) | mock | stripe | polar | lago. 키·웹훅 비밀은 env 로만 주입한다.

가격 모델(리스팅 pricing): free · subscription(price/월) · per_seat(price/좌석·월) · per_call(표시만 — 사용량 정산은 X12)
"""
import base64
import hashlib
import hmac
import json
import time
import uuid

import httpx

from app.core.config import settings
from app.db import utcnow

ZERO_DECIMAL = {"KRW", "JPY", "VND", "CLP", "ISK", "UGX", "XAF", "XOF", "PYG", "RWF", "KMF", "GNF", "MGA", "VUV", "XPF",
                "BIF", "DJF"}  # 최소 단위 = 주 단위인 통화(그 밖은 ×100)
TOLERANCE = 300  # 웹훅 타임스탬프 허용 오차(초) — 재전송 공격 방지
TRANSPORTS: dict[str, httpx.AsyncBaseTransport] = {}  # 시험용: API 기준 URL → 가짜 서버(ASGI)


class PaymentError(Exception):
    pass


class WebhookRejected(PaymentError):
    """서명·형식이 맞지 않는 웹훅(401)."""


def minor(amount: int, currency: str) -> int:
    return amount if currency.upper() in ZERO_DECIMAL else amount * 100


def _client(base: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=20, transport=TRANSPORTS.get(base.rstrip("/")))


def _check(res: httpx.Response, who: str) -> dict:
    if res.status_code >= 400:
        raise PaymentError(f"{who}: HTTP {res.status_code} {res.text[:200]}")
    return res.json()


def _fresh(ts: str) -> None:
    try:
        if abs(time.time() - int(ts)) > TOLERANCE:
            raise WebhookRejected("웹훅 시각이 허용 범위를 벗어남 / stale webhook")
    except ValueError:
        raise WebhookRejected("웹훅 시각 형식 오류") from None


class MockPayment:
    name, hosted = "mock", False

    def charge(self, *, amount: int, currency: str, description: str, buyer: str) -> dict:
        return {"ref": f"mock_{uuid.uuid4().hex[:16]}", "status": "paid", "amount": amount, "currency": currency,
                "description": description, "paid_at": utcnow().isoformat()}


class StripePayment:
    """Stripe Checkout Session(mode=payment) + 'Stripe-Signature: t=…,v1=hex(HMAC-SHA256(secret, "t.body"))'."""
    name, hosted = "stripe", True

    def __init__(self, secret_key: str, webhook_secret: str, api_base: str = "https://api.stripe.com"):
        self.key, self.whsec, self.base = secret_key, webhook_secret, api_base.rstrip("/")

    async def checkout(self, *, purchase_id: str, amount: int, currency: str, description: str, buyer: str,
                       success_url: str, cancel_url: str) -> dict:
        form = {"mode": "payment", "success_url": success_url, "cancel_url": cancel_url,
                "client_reference_id": purchase_id, "metadata[purchase_id]": purchase_id,
                "line_items[0][quantity]": "1", "line_items[0][price_data][currency]": currency.lower(),
                "line_items[0][price_data][unit_amount]": str(minor(amount, currency)),
                "line_items[0][price_data][product_data][name]": description[:250]}
        async with _client(self.base) as c:
            data = _check(await c.post(f"{self.base}/v1/checkout/sessions", data=form,
                                       headers={"Authorization": f"Bearer {self.key}"}), "stripe")
        return {"ref": data["id"], "url": data["url"]}

    def parse(self, headers: dict, body: bytes) -> dict | None:
        items = [p.strip().split("=", 1) for p in headers.get("stripe-signature", "").split(",") if "=" in p]
        ts, sigs = next((v for k, v in items if k == "t"), None), [v for k, v in items if k == "v1"]
        if not ts or not sigs:
            raise WebhookRejected("Stripe-Signature 없음")
        _fresh(ts)
        want = hmac.new(self.whsec.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(want, s) for s in sigs):
            raise WebhookRejected("Stripe 서명 불일치")
        ev = json.loads(body)
        obj = ev.get("data", {}).get("object", {})
        status = {"checkout.session.completed": "paid" if obj.get("payment_status") == "paid" else "pending",
                  "checkout.session.async_payment_succeeded": "paid",
                  "checkout.session.async_payment_failed": "failed",
                  "checkout.session.expired": "expired"}.get(ev.get("type"))
        if status is None:
            return None
        return {"ref": obj.get("id"), "purchase_id": obj.get("client_reference_id"), "status": status,
                "amount_minor": obj.get("amount_total"), "currency": (obj.get("currency") or "").upper()}


class PolarPayment:
    """Polar Checkout(MoR, 상품의 custom price + amount) + Standard Webhooks('webhook-signature: v1,<base64>')."""
    name, hosted = "polar", True

    def __init__(self, token: str, webhook_secret: str, product_id: str, api_base: str = "https://api.polar.sh"):
        self.token, self.whsec, self.product, self.base = token, webhook_secret, product_id, api_base.rstrip("/")

    async def checkout(self, *, purchase_id: str, amount: int, currency: str, description: str, buyer: str,
                       success_url: str, cancel_url: str) -> dict:
        body = {"products": [self.product], "amount": minor(amount, currency), "success_url": success_url,
                "metadata": {"purchase_id": purchase_id, "description": description[:400]}, "external_customer_id": buyer}
        async with _client(self.base) as c:
            data = _check(await c.post(f"{self.base}/v1/checkouts/", json=body,
                                       headers={"Authorization": f"Bearer {self.token}"}), "polar")
        return {"ref": data["id"], "url": data["url"]}

    def _key(self) -> bytes:
        s = self.whsec
        return base64.b64decode(s.removeprefix("whsec_")) if s.startswith("whsec_") else s.encode()

    def parse(self, headers: dict, body: bytes) -> dict | None:
        mid, ts, sig = headers.get("webhook-id"), headers.get("webhook-timestamp"), headers.get("webhook-signature", "")
        if not mid or not ts or not sig:
            raise WebhookRejected("Standard Webhooks 헤더 없음")
        _fresh(ts)
        want = base64.b64encode(hmac.new(self._key(), f"{mid}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
        if not any(hmac.compare_digest(want, s.split(",", 1)[1]) for s in sig.split() if s.startswith("v1,")):
            raise WebhookRejected("Polar 서명 불일치")
        ev = json.loads(body)
        data = ev.get("data", {})
        if ev.get("type") == "order.paid":
            status = "paid"
        elif ev.get("type") == "checkout.updated" and data.get("status") in ("failed", "expired"):
            status = data["status"]
        else:
            return None
        return {"ref": data.get("checkout_id") or data.get("id"), "purchase_id": (data.get("metadata") or {}).get("purchase_id"),
                "status": status, "amount_minor": data.get("total_amount", data.get("amount")),
                "currency": (data.get("currency") or "").upper()}


class LagoPayment:
    """Lago 일회성 청구(add-on 수수료 → 인보이스 → payment_url) + 'X-Lago-Signature: base64(HMAC-SHA256(key, body))'.
    실제 결제는 Lago 에 연결된 결제대행(Stripe·GoCardless·Adyen)이 처리한다."""
    name, hosted = "lago", True

    def __init__(self, api_url: str, api_key: str, hmac_key: str, add_on_code: str):
        self.base, self.key, self.hmac, self.code = api_url.rstrip("/"), api_key, hmac_key, add_on_code

    async def checkout(self, *, purchase_id: str, amount: int, currency: str, description: str, buyer: str,
                       success_url: str, cancel_url: str) -> dict:
        h = {"Authorization": f"Bearer {self.key}"}
        cust = "plaza-" + hashlib.sha256(buyer.encode()).hexdigest()[:16]  # 구매자 식별자(이메일 원문은 보내지 않음)
        async with _client(self.base) as c:
            _check(await c.post(f"{self.base}/api/v1/customers", json={"customer": {"external_id": cust, "name": cust,
                                                                                  "currency": currency.upper()}}, headers=h),
                   "lago customers")
            inv = _check(await c.post(f"{self.base}/api/v1/invoices", json={"invoice": {
                "external_customer_id": cust, "currency": currency.upper(),
                "fees": [{"add_on_code": self.code, "units": 1, "unit_amount_cents": minor(amount, currency),
                          "description": f"{description[:200]} [{purchase_id}]"}]}}, headers=h), "lago invoices")["invoice"]
            url = _check(await c.post(f"{self.base}/api/v1/invoices/{inv['lago_id']}/payment_url", headers=h),
                         "lago payment_url")["invoice_payment_details"]["payment_url"]
        return {"ref": inv["lago_id"], "url": url}

    def parse(self, headers: dict, body: bytes) -> dict | None:
        sig = headers.get("x-lago-signature", "")
        if headers.get("x-lago-signature-algorithm", "hmac") != "hmac" or not sig:
            raise WebhookRejected("X-Lago-Signature(hmac) 없음")
        want = base64.b64encode(hmac.new(self.hmac.encode(), body, hashlib.sha256).digest()).decode()
        if not hmac.compare_digest(want, sig):
            raise WebhookRejected("Lago 서명 불일치")
        ev = json.loads(body)
        if ev.get("webhook_type") != "invoice.payment_status_updated":
            return None
        inv = ev.get("invoice", {})
        status = {"succeeded": "paid", "failed": "failed"}.get(inv.get("payment_status"))
        if status is None:
            return None
        return {"ref": inv.get("lago_id"), "purchase_id": None, "status": status,
                "amount_minor": inv.get("total_amount_cents"), "currency": (inv.get("currency") or "").upper()}


def adapter():
    s = settings
    if s.payment_adapter == "mock":
        return MockPayment()
    if s.payment_adapter == "stripe" and s.stripe_secret_key and s.stripe_webhook_secret:
        return StripePayment(s.stripe_secret_key, s.stripe_webhook_secret, s.stripe_api_base)
    if s.payment_adapter == "polar" and s.polar_access_token and s.polar_webhook_secret and s.polar_product_id:
        return PolarPayment(s.polar_access_token, s.polar_webhook_secret, s.polar_product_id, s.polar_api_url)
    if s.payment_adapter == "lago" and s.lago_api_url and s.lago_api_key and s.lago_webhook_hmac_key:
        return LagoPayment(s.lago_api_url, s.lago_api_key, s.lago_webhook_hmac_key, s.lago_add_on_code)
    return None  # none 이거나 키가 빠짐 — 구매는 끄고 키 직접 입력만


def pricing_of(x: dict) -> dict:
    p = x.get("pricing") or "free"
    return dict(p) if isinstance(p, dict) else {"model": str(p)}


def is_paid(x: dict) -> bool:
    return pricing_of(x).get("model", "free") != "free"


def quote(pricing: dict, seats: int, months: int) -> int:
    price = int(pricing.get("price") or 0)
    return {"per_seat": price * seats * months, "subscription": price * months}.get(pricing.get("model"), 0)
