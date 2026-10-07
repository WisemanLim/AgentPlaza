"""마켓 상거래·퍼블리셔·업데이트·레지스트리 API (D6-05·D6-06·D6-07, UI E06·E07·E11·E12·E13).

/api/market/*   퍼블리셔·게시·심사·운영 배지·구매·업데이트·원격 레지스트리·번들
/api/licenses   라이선스 키 검증·등록·좌석 (UI E12: POST /api/licenses {key, listing})
/registry/v0.1  MCP registry 호환 읽기 API(servers·versions) + 산출물 다운로드
"""
import json
import uuid

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, Query, Request,
                     UploadFile, status)
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Principal, current_principal, require_admin, require_supervisor, require_user
from app.db import get_db, utcnow
from app.market import catalog, licensing, payments, publishing, regapi, remote, updates
from app.models import License, LicenseSeat, MarketRelease, Publisher, Purchase
from app.registry import pipeline
from app.services import audit, sysconfig
from app.supplychain.trust import TrustError

router = APIRouter(prefix="/api/market", tags=["market"], dependencies=[Depends(require_user)])
licenses = APIRouter(prefix="/api/licenses", tags=["market"], dependencies=[Depends(require_admin)])
registry = APIRouter(prefix="/registry/v0.1", tags=["registry"])
hooks = APIRouter(prefix="/api/market/payments", tags=["market"])  # 결제대행 웹훅(자격증명 = 서명)


def _http(exc: Exception, code: int = 422) -> HTTPException:
    return HTTPException(getattr(exc, "code", code), str(exc))


@router.get("/instance")
def instance(db: Session = Depends(get_db)):
    return {"instance_id": licensing.instance_id(db), "payment_adapter": settings.payment_adapter
            if payments.adapter() else "none", "license_issuer": licensing.issuer_kid(db),
            "license_public_key": licensing.issuer_public_pem(db), "registry_public": regapi.exposed(db),
            "registry_url": f"{settings.public_base_url.rstrip('/')}/registry/v0.1"}


# ---- 퍼블리셔 (UI E07) ----

class PublisherIn(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")
    name: str = Field(min_length=1, max_length=120)
    url: str | None = None
    verified: bool = False
    members: list[str] = Field(default_factory=list)


class PublisherPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    url: str | None = None
    verified: bool | None = None
    members: list[str] | None = None


class PubKeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    public_key: str
    rotate: bool = False


@router.get("/publishers")
def list_publishers(q: str | None = None, _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(select(Publisher).order_by(Publisher.id)).scalars()
    return [publishing.publisher_out(db, p) for p in rows if not q or q.lower() in (p.id + p.name).lower()]


@router.post("/publishers", status_code=201)
def create_publisher(body: PublisherIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    if db.get(Publisher, body.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 있는 퍼블리셔 / duplicate")
    pub = Publisher(**body.model_dump(), created_by=p.actor)
    db.add(pub)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.publisher.created", resource=pub.id)
    return publishing.publisher_out(db, pub)


@router.patch("/publishers/{pid}")
def patch_publisher(pid: str, body: PublisherPatch, p: Principal = Depends(require_supervisor),
                    db: Session = Depends(get_db)):
    pub = db.get(Publisher, pid)
    if pub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "퍼블리셔 없음 / not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(pub, k, v)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.publisher.updated", resource=pid,
                 detail=body.model_dump(exclude_none=True))
    return publishing.publisher_out(db, pub)


@router.post("/publishers/{pid}/keys", status_code=201)
def add_publisher_key(pid: str, body: PubKeyIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    pub = db.get(Publisher, pid)
    if pub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "퍼블리셔 없음 / not found")
    if p.role != "supervisor" and p.actor not in (pub.members or []):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "퍼블리셔 구성원만 / members only")
    try:
        return publishing.add_publisher_key(db, pub, name=body.name, public_pem=body.public_key, rotate=body.rotate,
                                            actor=p.actor)
    except TrustError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None


# ---- 게시·심사 (UI E06·E07) ----

@router.post("/releases", status_code=201)
async def submit_release(file: UploadFile = File(...), publisher: str = Form(...), listing: str = Form("{}"),
                         overwrite: bool = Form(False), p: Principal = Depends(require_admin),
                         db: Session = Depends(get_db)):
    try:
        info = json.loads(listing or "{}")
        if not isinstance(info, dict):
            raise ValueError
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "listing 은 JSON 객체") from None
    try:
        rel = await publishing.submit(db, data=await file.read(), publisher_id=publisher, info=info, actor=p.actor,
                                      supervisor=p.role == "supervisor", overwrite=overwrite)
    except publishing.PublishError as exc:
        raise HTTPException(exc.code, {"message": str(exc), "gate": exc.gate}) from None
    return publishing.release_out(rel)


@router.get("/releases")
def list_releases(state: str | None = Query(default=None, alias="status"), listing: str | None = None,
                  _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    stmt = select(MarketRelease).order_by(MarketRelease.created_at.desc())
    if state:
        stmt = stmt.where(MarketRelease.status == state)
    if listing:
        stmt = stmt.where(MarketRelease.listing_id == listing)
    return [publishing.release_out(r) for r in db.execute(stmt.limit(200)).scalars()]


class RejectIn(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


def _release(db: Session, rid: str) -> MarketRelease:
    rel = db.get(MarketRelease, rid)
    if rel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "릴리스 없음 / not found")
    return rel


@router.post("/releases/{rid}/approve")
def approve_release(rid: str, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        return publishing.release_out(publishing.approve(db, _release(db, rid), p.actor))
    except publishing.PublishError as exc:
        raise _http(exc) from None


@router.post("/releases/{rid}/reject")
def reject_release(rid: str, body: RejectIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        return publishing.release_out(publishing.reject(db, _release(db, rid), p.actor, body.reason))
    except publishing.PublishError as exc:
        raise _http(exc) from None


class OpsIn(BaseModel):
    hidden: bool | None = None
    featured_until: str | None = Field(default=None, pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    validated_ref: str | None = Field(default=None, max_length=200)


@router.patch("/listings/{lid}/ops")
def listing_ops(lid: str, body: OpsIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    """운영 배지(Featured 기간·Validated 근거)·숨김(UI E07 5)."""
    if catalog.get(lid, db) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "리스팅 없음 / not found")
    ops = sysconfig.blob(db, catalog.OPS_KEY)
    ops[lid] = {**ops.get(lid, {}), **body.model_dump(exclude_none=True)}
    sysconfig.put_blob(db, catalog.OPS_KEY, ops)
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.listing.ops", resource=lid, detail=ops[lid])
    return ops[lid]


# ---- 구매·영수증 (UI E12, D6-05, NFR-C4) ----

class PurchaseIn(BaseModel):
    seats: int = Field(default=1, ge=1, le=1000)
    months: int = Field(default=1, ge=1, le=36)


def _range_of(version: str) -> str:
    major, minor, _ = licensing._ver(version)
    return f"^{major}.0.0" if major else f"^0.{minor}.0"


def purchase_out(pu: Purchase) -> dict:
    return {"id": pu.id, "listing_id": pu.listing_id, "version": pu.version, "buyer": pu.buyer, "seats": pu.seats,
            "months": pu.months, "amount": pu.amount, "currency": pu.currency, "adapter": pu.adapter,
            "adapter_ref": pu.adapter_ref, "status": pu.status, "license_id": pu.license_id, "created_at": pu.created_at}


@router.post("/purchase/{lid}", status_code=201)
async def purchase(lid: str, body: PurchaseIn, response: Response, p: Principal = Depends(require_admin),
                   db: Session = Depends(get_db)):
    """mock = 즉시 결제·발급(201). 호스티드(Stripe·Polar·Lago) = 결제 페이지 URL(202) → 서명 웹훅에서 발급."""
    x = catalog.get(lid, db)
    if x is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "리스팅 없음 / not found")
    if not payments.is_paid(x):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "무료 리스팅 / free listing")
    if str(x.get("origin", "")).startswith("registry:"):
        raise HTTPException(status.HTTP_409_CONFLICT, "원격 마켓 리스팅 — 그 마켓에서 구매한 키를 입력 / buy at the remote market")
    adp = payments.adapter()
    if adp is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "결제 어댑터 미연결 — 라이선스 키 직접 입력 / no payment adapter")
    pr = payments.pricing_of(x)
    amount = payments.quote(pr, body.seats, body.months)
    currency = pr.get("currency", "KRW")
    desc = f"{lid} {body.seats} seat(s) × {body.months} mo"
    pu = Purchase(id=str(uuid.uuid4()), listing_id=lid, version=x["version"], buyer=p.actor, seats=body.seats,
                  months=body.months, amount=amount, currency=currency, adapter=adp.name, adapter_ref="",
                  status="pending", receipt={})
    try:
        if adp.hosted:
            back = f"{settings.public_base_url.rstrip('/')}/market/{lid}?purchase={pu.id}"
            co = await adp.checkout(purchase_id=pu.id, amount=amount, currency=currency, description=desc, buyer=p.actor,
                                    success_url=back, cancel_url=back + "&cancelled=1")
            pu.adapter_ref, pu.receipt = co["ref"], {"checkout_url": co["url"]}
        else:
            charge = adp.charge(amount=amount, currency=currency, description=desc, buyer=p.actor)
            pu.adapter_ref = charge["ref"]
    except payments.PaymentError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"결제 연동 실패 / payment provider error: {exc}") from None
    db.add(pu)
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.purchase_started", resource=f"{lid}@{x['version']}",
                 detail={"purchase": pu.id, "amount": amount, "currency": currency, "adapter": adp.name})
    if adp.hosted:
        response.status_code = status.HTTP_202_ACCEPTED
        return {"purchase": purchase_out(pu), "checkout_url": pu.receipt["checkout_url"]}
    lic = _fulfil(db, pu, x, actor=p.actor, actor_type=p.type)
    return {"purchase": purchase_out(pu), "license": licensing.out(db, lic)}


def _fulfil(db: Session, pu: Purchase, x: dict, *, actor: str, actor_type: str) -> License:
    """결제 확인 → 라이선스 발급(Ed25519) → 영수증·원장(NFR-C4). 웹훅 재전송에도 한 번만."""
    token = licensing.issue(db, listing=pu.listing_id, publisher=(x.get("publisher") or {}).get("id", ""),
                            versions=_range_of(pu.version), seats=pu.seats, days=pu.months * 30,
                            host=licensing.instance_id(db), sub=pu.buyer)
    lic = licensing.register(db, token, pu.listing_id, pu.buyer, commit=False)
    pu.status, pu.license_id = "paid", lic.id
    pu.receipt = {"receipt_id": pu.id, "issued_at": utcnow().isoformat(), "seller": x.get("publisher"),
                  "listing": {"id": pu.listing_id, "version": pu.version, "pricing": payments.pricing_of(x)},
                  "buyer": pu.buyer, "seats": pu.seats, "months": pu.months, "amount": pu.amount, "currency": pu.currency,
                  "payment": {"adapter": pu.adapter, "ref": pu.adapter_ref, "status": "paid"},
                  "license": {"id": lic.id, "versions": lic.payload["versions"], "expires_at": lic.payload["exp"],
                              "host": lic.payload["host"], "issuer": lic.issuer, "token": token},
                  "note": "정산·세금은 X12 범위 / settlement and tax out of scope"}
    db.commit()
    audit.record(db, actor=actor, actor_type=actor_type, action="market.purchase", resource=f"{pu.listing_id}@{pu.version}",
                 detail={"purchase": pu.id, "license": lic.id, "amount": pu.amount, "currency": pu.currency,
                         "adapter": pu.adapter})
    return lic


@router.get("/purchases/{pid}")
def get_purchase(pid: str, _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    pu = db.get(Purchase, pid)
    if pu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "구매 없음 / not found")
    return purchase_out(pu) | {"checkout_url": (pu.receipt or {}).get("checkout_url") if pu.status == "pending" else None}


@router.get("/purchases")
def list_purchases(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return [purchase_out(x) for x in db.execute(select(Purchase).order_by(Purchase.created_at.desc())).scalars()]


@router.get("/purchases/{pid}/receipt")
def receipt(pid: str, _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    pu = db.get(Purchase, pid)
    if pu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "구매 없음 / not found")
    return Response(json.dumps(pu.receipt, ensure_ascii=False, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="receipt-{pu.id[:8]}.json"'})


# ---- 설치됨·업데이트 (UI E11) ----

class UpdateIn(BaseModel):
    consent: bool = False


class AutoIn(BaseModel):
    enabled: bool


@router.get("/installed")
def installed(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return updates.installed(db)


@router.post("/updates/check")
async def check_updates(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    """모두 업데이트 확인: 원격 레지스트리 동기화 → 새 버전 알림(원장)."""
    synced = [{"registry": n, **await remote.sync(db, n)} for n in remote.registries(db)]
    items = updates.installed(db)
    fresh = updates.notify(db, items)
    return {"synced": synced, "updates": [i for i in items if i["update"]], "new": [i["agent_id"] for i in fresh]}


@router.post("/updates/{agent_id}", status_code=202)
async def apply_update(agent_id: str, body: UpdateIn, background: BackgroundTasks, p: Principal = Depends(require_admin),
                       db: Session = Depends(get_db)):
    try:
        inst, data, x, env = await updates.prepare(db, agent_id, p.actor, consent=body.consent)
    except updates.UpdateError as exc:
        raise HTTPException(exc.code, {"message": str(exc), "update": exc.detail}) from None
    except catalog.MarketError as exc:
        raise _http(exc) from None
    background.add_task(pipeline.run, inst.id, data, trust=x.get("trust", "community"), env=env)
    audit.record(db, actor=p.actor, actor_type=p.type, agent_id=agent_id, action="market.update",
                 resource=f"{agent_id}@{x['version']}", detail={"consent": body.consent, "install": inst.id})
    return {"install_id": inst.id}


@router.put("/auto-update/{agent_id}")
def auto_update(agent_id: str, body: AutoIn, _: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return {"agent_id": agent_id, "enabled": updates.set_auto(db, agent_id, body.enabled).get(agent_id, False)}


# ---- 원격 레지스트리·노출·번들 (UI E13) ----

class RegistryIn(BaseModel):
    url: str = Field(min_length=8, max_length=300)
    token: str | None = None
    license_key: str | None = None
    interval_minutes: int = Field(default=60, ge=0, le=10080)


class SyncIn(BaseModel):
    overwrite: bool = False
    full: bool = False


class ExposeIn(BaseModel):
    public: bool


@router.get("/registries")
def list_registries(_: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    from app.services import secrets as secret_store
    return [{"name": n, **cfg, "has_token": "TOKEN" in secret_store.names(db, f"registry:{n}")}
            for n, cfg in remote.registries(db).items()]


@router.put("/registries/{name}")
async def put_registry(name: str, body: RegistryIn, p: Principal = Depends(require_supervisor),
                       db: Session = Depends(get_db)):
    try:
        remote.put_registry(db, name, url=body.url, token=body.token, license_key=body.license_key,
                            interval=body.interval_minutes, actor=p.actor)
    except (remote.RemoteError, TrustError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.registry.saved", resource=name,
                 detail={"url": body.url})
    return {"name": name, **await remote.test(db, name)}  # 추가 후 연결 시험 자동 수행


@router.delete("/registries/{name}")
def delete_registry(name: str, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        n = remote.delete_registry(db, name)
    except remote.RemoteError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.registry.deleted", resource=name)
    return {"removed_listings": n}


@router.post("/registries/{name}/sync")
async def sync_registry(name: str, body: SyncIn, p: Principal = Depends(require_supervisor),
                        db: Session = Depends(get_db)):
    try:
        return await remote.sync(db, name, overwrite=body.overwrite, full=body.full)
    except remote.RemoteError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None


@router.get("/registry-exposure")
def get_exposure(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return {"public": regapi.exposed(db), "url": f"{settings.public_base_url.rstrip('/')}/registry/v0.1"}


@router.put("/registry-exposure")
def put_exposure(body: ExposeIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    regapi.set_exposed(db, body.public)
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.registry.exposure", detail={"public": body.public})
    return get_exposure(p, db)


@router.get("/bundle")
def export_bundle(ids: str | None = None, _: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    data = remote.export_bundle(db, [i for i in (ids or "").split(",") if i] or None)
    return Response(data, media_type="application/gzip",
                    headers={"Content-Disposition": 'attachment; filename="agentplaza-market-bundle.tar.gz"'})


@router.post("/bundle")
async def import_bundle(file: UploadFile = File(...), overwrite: bool = Form(False),
                        p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        report = remote.import_bundle(db, await file.read(), overwrite=overwrite)
    except remote.RemoteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="market.bundle.imported",
                 detail={k: len(v) for k, v in report.items()})
    return report


# ---- 라이선스 발급자 ----

class IssuerIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    public_key: str


@router.get("/license-issuers")
def list_issuers(_: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    return [{"kid": k, "name": v["name"], "own": bool(v.get("own"))} for k, v in licensing.issuers(db).items()]


@router.post("/license-issuers", status_code=201)
def add_issuer(body: IssuerIn, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    try:
        kid = licensing.add_issuer(db, body.name, body.public_key)
    except (TrustError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="license.issuer.added", resource=kid)
    return {"kid": kid}


@router.delete("/license-issuers/{kid}")
def remove_issuer(kid: str, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    if not licensing.remove_issuer(db, kid):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "발급자 없음(자기 발급 키는 지울 수 없음) / not found")
    audit.record(db, actor=p.actor, actor_type=p.type, action="license.issuer.removed", resource=kid)
    return {"removed": kid}


# ---- /api/licenses ----

class LicenseIn(BaseModel):
    key: str = Field(min_length=10, max_length=8000)
    listing: str


@licenses.post("/verify")
def verify_license(body: LicenseIn, db: Session = Depends(get_db)):
    """저장 없이 오프라인 검증만(UI E12 '검증' 버튼). 대상 버전 = 카탈로그 현재 버전."""
    x = catalog.get(body.listing, db)
    try:
        payload, checks = licensing.verify(db, body.key, listing=body.listing, version=x["version"] if x else None)
    except licensing.LicenseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    return {"ok": all(c["ok"] for c in checks), "checks": checks, "payload": payload}


@licenses.post("", status_code=201)
def register_license(body: LicenseIn, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        lic = licensing.register(db, body.key, body.listing, p.actor)
    except licensing.LicenseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, {"message": str(exc), "checks": exc.checks}) from None
    audit.record(db, actor=p.actor, actor_type=p.type, action="license.registered", resource=body.listing,
                 detail={"license": lic.id, "seats": lic.seats, "issuer": lic.issuer})
    return licensing.out(db, lic)


@licenses.get("")
def list_licenses(listing: str | None = None, db: Session = Depends(get_db)):
    stmt = select(License).order_by(License.created_at.desc())
    if listing:
        stmt = stmt.where(License.listing_id == listing)
    return [licensing.out(db, x) for x in db.execute(stmt).scalars()]


@licenses.delete("/{lid}")
def revoke_license(lid: str, p: Principal = Depends(require_supervisor), db: Session = Depends(get_db)):
    lic = db.get(License, lid)
    if lic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "라이선스 없음 / not found")
    lic.status = "revoked"
    db.commit()
    audit.record(db, actor=p.actor, actor_type=p.type, action="license.revoked", resource=lic.listing_id,
                 detail={"license": lid})
    return licensing.out(db, lic)


@licenses.delete("/{lid}/seats/{holder}")
def release_seat(lid: str, holder: str, p: Principal = Depends(require_admin), db: Session = Depends(get_db)):
    n = db.execute(delete(LicenseSeat).where(LicenseSeat.license_id == lid, LicenseSeat.holder == holder)).rowcount
    db.commit()
    if not n:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "좌석 없음 / not found")
    audit.record(db, actor=p.actor, actor_type=p.type, action="license.seat.released", resource=lid,
                 detail={"holder": holder})
    return {"released": holder}


# ---- /registry/v0.1 (MCP registry 호환) ----

def _reader(authorization: str | None = Header(default=None), x_api_key: str | None = Header(default=None),
            db: Session = Depends(get_db)) -> str:
    """'호스트로 공개'면 익명 읽기 허용, 아니면 플랫폼 인증(사용자·API 키)."""
    if regapi.exposed(db) and not (authorization or x_api_key):
        return "anonymous"
    return current_principal(authorization=authorization, x_api_key=x_api_key, db=db).actor


@registry.get("/servers")
def reg_servers(request: Request, cursor: str | None = None, limit: int = 30, search: str | None = None,
                updated_since: str | None = None, _: str = Depends(_reader), db: Session = Depends(get_db)):
    try:
        return regapi.servers(db, str(request.base_url), cursor=cursor, limit=max(1, min(limit, 100)), search=search,
                              updated_since=updated_since)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cursor·updated_since 형식 오류") from None


@registry.get("/servers/{name:path}/versions/{version}")
def reg_version(name: str, version: str, request: Request, _: str = Depends(_reader), db: Session = Depends(get_db)):
    items = regapi.versions(db, name, str(request.base_url))
    hit = next((e for e in items if (version == "latest" and e["_meta"][regapi.OFFICIAL]["isLatest"])
                or e["server"]["version"] == version), None)
    if hit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Server not found")
    return hit


@registry.get("/servers/{name:path}/versions")
def reg_versions(name: str, request: Request, _: str = Depends(_reader), db: Session = Depends(get_db)):
    items = regapi.versions(db, name, str(request.base_url))
    if not items:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Server not found")
    return {"servers": items, "metadata": {"count": len(items)}}


@registry.get("/artifacts/{lid}/{file}")
async def reg_artifact(lid: str, file: str, request: Request, actor: str = Depends(_reader),
                       db: Session = Depends(get_db)):
    version = file.removesuffix(".zip")
    found = regapi.artifact_of(db, lid, version)
    if found is None or not file.endswith(".zip"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "산출물 없음 / not found")
    x, src = found
    why = regapi.license_ok(db, x, version, request.headers.get("x-plaza-license"))
    if why:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, why)
    try:
        data = await catalog.artifact({**x, "source": src})
    except catalog.MarketError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    catalog.count(db, lid, version, "download", actor)
    return Response(data, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{lid}-{version}.zip"'})



# ---- 결제 웹훅 (D6-05): 인증 = 결제대행 서명. 서명이 맞지 않으면 401 ----

@hooks.post("/{adapter}/webhook")
async def payment_webhook(adapter: str, request: Request, db: Session = Depends(get_db)):
    adp = payments.adapter()
    if adp is None or not adp.hosted or adp.name != adapter:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "알 수 없는 결제 어댑터 / unknown adapter")
    body = await request.body()
    try:
        ev = adp.parse({k.lower(): v for k, v in request.headers.items()}, body)
    except (payments.WebhookRejected, ValueError) as exc:
        audit.record(db, actor=f"webhook:{adapter}", actor_type="service", action="market.webhook_rejected",
                     outcome="denied", detail={"reason": str(exc)[:200]})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "웹훅 서명 검증 실패 / invalid signature") from None
    if ev is None:
        return {"ok": True, "ignored": True}
    pu = db.get(Purchase, ev["purchase_id"]) if ev.get("purchase_id") else None
    pu = pu or db.execute(select(Purchase).where(Purchase.adapter == adapter, Purchase.adapter_ref == ev["ref"])).scalars().first()
    if pu is None or pu.adapter != adapter:
        return {"ok": True, "ignored": True}
    if pu.status != "pending":  # 재전송 — 이미 처리
        return {"ok": True, "status": pu.status}
    if ev["status"] == "paid":
        if ev.get("amount_minor") is not None and (ev["amount_minor"] != payments.minor(pu.amount, pu.currency)
                                                   or (ev.get("currency") and ev["currency"] != pu.currency.upper())):
            pu.status = "mismatch"
            db.commit()
            audit.record(db, actor=f"webhook:{adapter}", actor_type="service", action="market.purchase_mismatch",
                         outcome="denied", resource=pu.listing_id, detail={"purchase": pu.id, "event": ev})
            return {"ok": True, "status": pu.status}
        x = catalog.get(pu.listing_id, db) or {"publisher": {}}
        _fulfil(db, pu, x, actor=f"webhook:{adapter}", actor_type="service")
    elif ev["status"] in ("failed", "expired"):
        pu.status = ev["status"]
        db.commit()
        audit.record(db, actor=f"webhook:{adapter}", actor_type="service", action="market.purchase_" + ev["status"],
                     resource=pu.listing_id, detail={"purchase": pu.id})
    return {"ok": True, "status": pu.status}
