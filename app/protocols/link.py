"""원격 에이전트 연동 — 경로 C (D6-04) · MCP 클라이언트·서버 등록 (D7-02) · A2A 클라이언트 (D7-04) · OpenAPI→도구 (D7-05).

코드를 설치하지 않고 A2A Agent Card URL 또는 MCP 서버 URL 을 등록한다:
  1) 계약 시험(카드 해석 / server/discover→tools/list)  2) capability 생성  3) 카탈로그 편입(source=link, trust=external)
도구·스킬 목록은 해시로 고정(pin)하고 재검증 시 바뀌면 비활성화한다(rug-pull 방어, PRD 13.1).
원격 인증 값은 시크릿 저장소(D9-04, AES-GCM 암호문)에 scope link:{id} 로 둔다. 예전 data/secrets/{id}.json 은 읽으면 옮긴다.
"""
import hashlib
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx
import httpx2
from a2a.client import ClientConfig, ClientFactory
from a2a.helpers import get_data_parts, get_text_parts, new_data_part, new_text_part
from a2a.types import Message, Part, Role, SendMessageRequest
from agentplaza_sdk.protocols import CARD_PATH, load_card
from google.protobuf.json_format import MessageToDict
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from sqlalchemy.orm import Session

from app.agentspec.validate import validate_manifest
from app.core.config import settings
from app.db import SessionLocal
from app.models import Agent
from app.orchestrator import executor
from app.protocols import card as cards
from app.protocols import openapi
from app.services import audit, registry

SAFE = re.compile(r"[^a-z0-9_]")


class LinkError(Exception):
    pass


def _base(url: str) -> str:
    u = urlparse(url)
    return f"{u.scheme}://{u.netloc}"


def _secret_path(agent_id: str) -> Path:
    return Path(settings.data_dir) / "secrets" / f"{agent_id}.json"  # P0 형식(이관 전용)


def save_secret(agent_id: str, header: str | None, value: str | None) -> None:
    from app.db import SessionLocal
    from app.services import secrets as store
    _secret_path(agent_id).unlink(missing_ok=True)
    with SessionLocal() as db:
        if not header or not value:
            store.delete(db, f"link:{agent_id}")
            return
        store.put(db, f"link:{agent_id}", "AUTH", json.dumps({"header": header, "value": value}), "system")


def _auth_headers(agent_id: str) -> dict:
    from app.db import SessionLocal
    from app.services import secrets as store
    legacy = _secret_path(agent_id)
    if legacy.is_file():  # P0 평문 파일 → 암호화 저장소로 이관
        old = json.loads(legacy.read_text())
        save_secret(agent_id, old["header"], old["value"])
    with SessionLocal() as db:
        raw = store.get(db, f"link:{agent_id}", "AUTH")
    if not raw:
        return {}
    s = json.loads(raw)
    store.remember(s["value"])
    return {s["header"]: s["value"]}


def _verb(name: str) -> str:
    v = SAFE.sub("_", name.lower()).strip("_") or "tool"
    return v if v[0].isalpha() else f"t_{v}"[:41]


def _pin(items: list[dict]) -> str:
    return hashlib.sha256(json.dumps(items, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _http(base: str, headers: dict) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=executor.TRANSPORTS.get(base), headers=headers, timeout=30)


def _http2(base: str, headers: dict) -> httpx2.AsyncClient:
    app = executor.APPS.get(base)
    return httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app) if app else None, headers=headers, timeout=30)


# ---------- A2A ----------

async def fetch_card(url: str, headers: dict) -> tuple[dict, object, str]:
    card_url = url if url.endswith(".json") else url.rstrip("/") + CARD_PATH
    async with _http(_base(card_url), headers) as c:
        res = await c.get(card_url)
    if res.status_code != 200:
        raise LinkError(f"Agent Card 조회 실패 HTTP {res.status_code}")
    data = res.json()
    card = load_card(data)
    if not card.supported_interfaces:
        raise LinkError("Agent Card 에 supportedInterfaces 없음")
    sig = "absent"
    if card.signatures:
        try:
            cards.verify(card)
            sig = "valid-platform"
        except Exception:  # noqa: BLE001 — 외부 키 서명은 jku 신뢰 정책(P1) 전까지 미검증으로 표시
            sig = "present-unverified"
    return data, card, sig


async def a2a_call(rpc_url: str, skill: str, args: dict, headers: dict) -> dict:
    async with _http(_base(rpc_url), headers) as hc:
        factory = ClientFactory(ClientConfig(httpx_client=hc, streaming=False))
        client = await factory.create_from_url(rpc_url.rsplit("/a2a", 1)[0] if rpc_url.endswith("/a2a") else rpc_url)
        msg = Message(role=Role.ROLE_USER, message_id=str(uuid.uuid4()),
                      parts=[new_data_part({"capability": skill, "args": args}),
                             new_text_part(json.dumps(args, ensure_ascii=False))])
        final = None
        async for ev in client.send_message(SendMessageRequest(message=msg)):
            final = ev
    if final is None:
        raise LinkError("A2A 응답 없음")
    kind = final.WhichOneof("payload")
    if kind == "task":
        task = final.task
        state = MessageToDict(task.status).get("state", "")
        if state != "TASK_STATE_COMPLETED":
            text = " ".join(get_text_parts(list(task.status.message.parts))) if task.status.message else state
            raise LinkError(f"A2A task {state}: {text}")
        for art in task.artifacts:
            data = get_data_parts(list(art.parts))
            if data:
                return data[0]
            texts = get_text_parts(list(art.parts))
            if texts:
                return {"text": " ".join(texts)}
        return {"state": state}
    if kind == "message":
        data = get_data_parts(list(final.message.parts))
        return data[0] if data else {"text": " ".join(get_text_parts(list(final.message.parts)))}
    raise LinkError(f"예상하지 못한 A2A 응답: {kind}")


# ---------- MCP ----------

async def mcp_tools(url: str, headers: dict, mode: str | None = None) -> list[dict]:
    """mode = discover(2026-07-28) | initialize(2025-11-25) 를 그 핸드셰이크로만 시험(계약 시험, NFR-P1).
    None 이면 discover 를 먼저, 안 되면 initialize(원격 연동)."""
    async with _http2(_base(url), headers) as http, streamable_http_client(url, http_client=http) as (r, w):
        async with ClientSession(r, w) as s:
            if mode == "discover":
                await s.discover()
            elif mode == "initialize":
                init = await s.initialize()
                if init.protocol_version != "2025-11-25":
                    raise LinkError(f"initialize protocolVersion {init.protocol_version} != 2025-11-25")
            else:
                try:
                    await s.discover()
                except Exception:  # noqa: BLE001 — 2025-11-25 서버면 initialize 핸드셰이크로
                    await s.initialize()
            tools = await s.list_tools()
    return [{"name": t.name, "description": t.description or "", "inputSchema": t.input_schema or {"type": "object"}}
            for t in tools.tools]


async def mcp_call(url: str, tool: str, args: dict, headers: dict) -> dict:
    async with _http2(_base(url), headers) as http, streamable_http_client(url, http_client=http) as (r, w):
        async with ClientSession(r, w) as s:
            try:
                await s.discover()
            except Exception:  # noqa: BLE001
                await s.initialize()
            res = await s.call_tool(tool, args)
    if res.is_error:
        raise LinkError(" ".join(getattr(c, "text", "") for c in res.content) or "tool error")
    if res.structured_content is not None:
        return dict(res.structured_content)
    return {"text": " ".join(getattr(c, "text", "") for c in res.content)}


# ---------- 등록·호출·재검증 ----------

def _manifest(agent_id: str, name: str, version: str, description: str, kind: str, url: str, caps: list[dict],
              names: dict, pin: str, signature: str) -> dict:
    return {
        "apiVersion": "agentplaza/v1", "kind": "Agent",
        "metadata": {"id": agent_id, "name": name[:80] or agent_id, "version": version, "license": "external",
                     "description": description or name, "publisher": {"id": "external"}},
        "spec": {"type": "federation", "capabilities": caps,
                 "federation": {"kind": kind, "url": url, "names": names, "pin": pin, "signature": signature},
                 "governance": {"dataClassification": "internal", "humanApprovalRequired": False},
                 "permissions": {"docker": False}},
    }


async def discover(kind: str, url: str, agent_id: str | None, headers: dict, base_url: str | None = None) -> dict:
    if kind == "a2a":
        data, card, sig = await fetch_card(url, headers)
        rpc = card.supported_interfaces[0].url
        skills = [{"id": s.id, "name": s.name, "description": s.description} for s in card.skills]
        aid = agent_id or SAFE.sub("-", card.name.lower()).strip("-")[:40] or "remote"
        names = {_verb(s["id"]): s["id"] for s in skills}
        caps = [{"verb": _verb(s["id"]), "domain": f"remote.{aid.replace('-', '_')}", "description": s["description"] or s["name"],
                 "inputSchema": {"type": "object"}} for s in skills]
        return _manifest(aid, card.name, card.version or "0.0.0", card.description, "a2a", rpc, caps, names, _pin(skills), sig)
    if kind == "mcp":
        tools = await mcp_tools(url, headers)
        aid = agent_id or SAFE.sub("-", urlparse(url).netloc.split(":")[0].lower()).strip("-")[:40] or "remote-mcp"
        names = {_verb(t["name"]): t["name"] for t in tools}
        caps = [{"verb": _verb(t["name"]), "domain": f"remote.{aid.replace('-', '_')}", "description": t["description"] or t["name"],
                 "inputSchema": t["inputSchema"]} for t in tools]
        return _manifest(aid, aid, "0.0.0", f"MCP server {url}", "mcp", url, caps, names, _pin(tools), "n/a")
    if kind == "openapi":
        async with _http(_base(url), headers) as c:
            res = await c.get(url)
        if res.status_code != 200:
            raise LinkError(f"OpenAPI 문서 조회 실패 HTTP {res.status_code}")
        try:
            spec = openapi.parse(res.content)
            ops = openapi.operations(spec)
        except openapi.OpenApiError as exc:
            raise LinkError(str(exc)) from None
        title = (spec.get("info") or {}).get("title") or urlparse(url).netloc
        aid = agent_id or SAFE.sub("-", title.lower()).strip("-")[:40] or "rest-api"
        caps = [{"verb": o["verb"], "domain": f"rest.{aid.replace('-', '_')}", "description": o["description"][:500],
                 "inputSchema": o["inputSchema"]} for o in ops]
        m = _manifest(aid, title, str((spec.get("info") or {}).get("version") or "0.0.0"),
                      (spec.get("info") or {}).get("description") or f"OpenAPI {url}", "openapi", url, caps,
                      {o["verb"]: o["operationId"] for o in ops}, _pin(ops), "n/a")
        m["spec"]["federation"].update(base=openapi.server_of(spec, url, base_url),
                                       ops={o["verb"]: {k: o[k] for k in ("method", "path", "params", "body")} for o in ops})
        return m
    raise LinkError("kind ∈ a2a | mcp | openapi")


async def link(db: Session, *, kind: str, url: str, agent_id: str | None, header: str | None, value: str | None,
               actor: str, base_url: str | None = None) -> Agent:
    headers = {header: value} if header and value else {}
    try:
        manifest = await discover(kind, url, agent_id, headers, base_url)
    except (httpx.HTTPError, httpx2.HTTPError, LinkError, ValueError) as exc:
        raise LinkError(f"계약 시험 실패 / contract test failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — SDK 예외 그룹 등
        raise LinkError(f"계약 시험 실패 / contract test failed: {type(exc).__name__}: {exc}") from exc
    errs = validate_manifest(manifest)
    if errs:
        raise LinkError("; ".join(errs))
    aid = manifest["metadata"]["id"]
    existing = db.get(Agent, aid)
    if existing is not None and existing.source != "link":
        raise LinkError(f"id 충돌: {aid} (설치 에이전트)")
    save_secret(aid, header, value)
    a = registry.register(db, manifest, endpoint=manifest["spec"]["federation"]["url"], source="link", trust="external",
                          status="healthy")
    audit.record(db, actor=actor, actor_type="user", agent_id=aid, action="agent.linked",
                 detail={"kind": kind, "url": url, "pin": manifest["spec"]["federation"]["pin"],
                         "signature": manifest["spec"]["federation"]["signature"], "capabilities": len(manifest["spec"]["capabilities"])})
    return a


async def revalidate(db: Session, agent_id: str, actor: str) -> dict:
    a = db.get(Agent, agent_id)
    fed = a.manifest["spec"]["federation"]
    try:
        url = fed["url"] if fed["kind"] in ("mcp", "openapi") else _base(fed["url"]) + _card_prefix(fed["url"])
        fresh = await discover(fed["kind"], url, agent_id, _auth_headers(agent_id), fed.get("base"))
    except Exception as exc:  # noqa: BLE001
        a.status = "unhealthy"
        db.commit()
        return {"ok": False, "status": a.status, "error": f"{type(exc).__name__}: {exc}"}
    changed = fresh["spec"]["federation"]["pin"] != fed["pin"]
    a.status = "unhealthy" if changed else "healthy"
    audit.record(db, actor=actor, actor_type="user", agent_id=agent_id,
                 action="agent.rug_pull_suspected" if changed else "agent.revalidated", outcome="denied" if changed else "ok",
                 detail={"old_pin": fed["pin"], "new_pin": fresh["spec"]["federation"]["pin"]})
    return {"ok": not changed, "status": a.status, "changed": changed}


def _card_prefix(rpc_url: str) -> str:
    path = urlparse(rpc_url).path
    return path.rsplit("/a2a", 1)[0] if path.endswith("/a2a") else path.rstrip("/")


async def call_linked(cap: dict, args: dict, _headers: dict) -> dict:
    """executor.REMOTE['link'] — 원격 capability 실행(A2A 클라이언트·MCP 클라이언트)."""
    with SessionLocal() as db:
        a = db.get(Agent, cap["agent"])
        fed = a.manifest["spec"]["federation"]
    original = fed.get("names", {}).get(cap["verb"], cap["verb"])
    headers = _auth_headers(cap["agent"])
    try:
        if fed["kind"] == "mcp":
            return await mcp_call(fed["url"], original, args, headers)
        if fed["kind"] == "openapi":
            async with _http(_base(fed["base"]), headers) as c:
                return await openapi.call(c, fed["base"], fed["ops"][cap["verb"]], args)
        return await a2a_call(fed["url"], original, args, headers)
    except LinkError as exc:
        raise RuntimeError(str(exc)) from None
    except Exception as exc:  # noqa: BLE001 — 원격 장애를 도구 오류로 정규화
        raise RuntimeError(f"remote {fed['kind']} error: {type(exc).__name__}: {exc}") from None


executor.REMOTE["link"] = call_linked
