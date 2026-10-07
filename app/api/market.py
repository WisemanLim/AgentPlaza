"""마켓플레이스 API — 스토어(D6-01) · 경로 A 다운로드·설치(D6-02) · 경로 C 연동(D6-04). 경로 B 는 /api/agents/upload·install-url·install-git."""
import zipfile
from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import Principal, require_admin, require_user
from app.db import get_db
from app.market import catalog, licensing, payments, remote, taxonomy
from app.models import Agent
from app.registry import fetch, pipeline
from app.services import orgs

router = APIRouter(prefix="/api/market", tags=["market"], dependencies=[Depends(require_user)])


class InstallIn(BaseModel):
    env: dict[str, str] = Field(default_factory=dict)  # required_env 입력 폼(UI E04)
    force: bool = False
    auth_header: str | None = None  # 원격 연동 리스팅용
    auth_value: str | None = None
    deploy_scope: dict | None = None  # 조직 도입(FL-07): {org_id, kind: org|group|user, ids}


@router.get("/categories")
def categories():
    return {"industries": taxonomy.tree(), "work": taxonomy.WORK, "domains": taxonomy.DOMAIN}


@router.get("/listings")
def listings(q: str | None = None, category: str | None = None, industry: str | None = None, work: str | None = None,
             domain: str | None = None, type: str | None = None, trust: str | None = None, db: Session = Depends(get_db)):
    return catalog.search(db, q=q, category=category, industry=industry, work=work, domain=domain, type_=type, trust=trust)


@router.get("/listings/{listing_id}")
async def listing(listing_id: str, db: Session = Depends(get_db)):
    x = catalog.get(listing_id, db)
    if x is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "리스팅 없음 / not found")
    out = catalog.decorate(x, db.get(Agent, listing_id), catalog.trusted_kids(db), db)
    if x["source"]["type"] in ("zip", "release"):  # 상세: README·버전 이력(UI E03)
        with zipfile.ZipFile(BytesIO(await catalog.artifact(x))) as z:
            out["readme"] = z.read("README.md").decode() if "README.md" in z.namelist() else ""
            out["changelog"] = z.read("CHANGELOG.md").decode() if "CHANGELOG.md" in z.namelist() else ""
    return out


@router.post("/install/{listing_id}", status_code=202)
async def install(listing_id: str, body: InstallIn, background: BackgroundTasks, p: Principal = Depends(require_admin),
                  db: Session = Depends(get_db)):
    x = catalog.get(listing_id, db)
    if x is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "리스팅 없음 / not found")
    if body.deploy_scope:  # 배치 대상(E04 2단계) — 설치 전에 정해 두면 기동 직후부터 범위가 적용된다
        sc = body.deploy_scope
        try:
            orgs.set_scope(db, x["id"], org_id=sc.get("org_id", orgs.DEFAULT), kind=sc.get("kind", ""),
                           ids=sc.get("ids") or [], actor=p.actor)
        except orgs.OrgError as exc:
            raise HTTPException(exc.code, str(exc)) from None
    src = x["source"]
    if src["type"] in catalog.REMOTE_TYPES:  # 경로 C: 코드 미설치 연동
        from app.protocols import link
        try:
            a = await link.link(db, kind="a2a" if src["type"] == "remote-a2a" else "mcp",
                                url=src.get("card_url") or src["url"], agent_id=x["id"], header=body.auth_header,
                                value=body.auth_value, actor=p.actor)
        except link.LinkError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
        return {"path": "C", "agent_id": a.id, "status": a.status}
    missing = [k for k in x.get("required_env", []) if not body.env.get(k)]
    if missing:  # 폼 단계에서 먼저 막는다(파이프라인도 다시 검사)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"required_env 누락: {missing}")
    if payments.is_paid(x) and not licensing.entitled(db, x["id"], x["version"]):  # NFR-C4: 라이선스 없으면 설치 거부
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "유료 에이전트 — 구매 또는 라이선스 키 등록 필요 / license required")
    try:
        data = await catalog.artifact(x, headers=remote.headers_for(db, x, x["version"]))
    except (catalog.MarketError, fetch.FetchError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    inst = pipeline.new_install(db, source="market", source_ref=f"{x['id']}@{x['version']}", created_by=p.actor,
                                env=body.env)
    catalog.count(db, x["id"], x["version"], "install", p.actor)
    background.add_task(pipeline.run, inst.id, data, force=body.force, trust=x.get("trust", "community"), env=body.env)
    return {"path": "A", "install_id": inst.id}
