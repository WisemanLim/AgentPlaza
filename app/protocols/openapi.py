"""OpenAPI → 도구 (D7-05): 기존 REST 서비스의 OpenAPI 3 문서를 등록하면 operation 마다 capability 가 된다.
MCP 게이트웨이(/mcp/{id})·Orchestrator·A2A 가 그대로 도구로 쓴다 — 서비스 코드는 바꾸지 않는다.

- 입력 스키마 = path·query 매개변수 + JSON 요청 본문(object 면 속성 병합, 아니면 body 속성)
- 호출: path 치환 → query → 나머지 인자는 JSON 본문. 응답은 JSON(아니면 text)
- 로컬 $ref(#/components/…)만 따라간다(깊이 제한). operation 은 최대 50개
"""
import json
import re
from urllib.parse import quote, urljoin

import httpx
import yaml

METHODS = ("get", "post", "put", "patch", "delete")
MAX_OPS = 50
SAFE = re.compile(r"[^a-z0-9_]+")


class OpenApiError(ValueError):
    pass


def _resolve(spec: dict, node, depth: int = 0):
    if depth > 8:
        return {}
    if isinstance(node, dict) and isinstance(node.get("$ref"), str):
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return {}
        cur = spec
        for part in ref[2:].split("/"):
            cur = cur.get(part, {}) if isinstance(cur, dict) else {}
        return _resolve(spec, cur, depth + 1)
    if isinstance(node, dict):
        return {k: _resolve(spec, v, depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(spec, v, depth + 1) for v in node]
    return node


def verb_of(op_id: str) -> str:
    v = SAFE.sub("_", re.sub(r"(?<!^)(?=[A-Z])", "_", op_id).lower()).strip("_") or "op"
    return (v if v[0].isalpha() else f"op_{v}")[:41]


def operations(spec: dict) -> list[dict]:
    if not str(spec.get("openapi", "")).startswith("3"):
        raise OpenApiError("OpenAPI 3.x 문서만 / only OpenAPI 3.x")
    ops = []
    for path, item in (spec.get("paths") or {}).items():
        shared = item.get("parameters", [])
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId") or f"{method}_{path}"
            props, required, params = {}, [], {"path": [], "query": []}
            for p in [*shared, *op.get("parameters", [])]:
                p = _resolve(spec, p)
                if p.get("in") not in ("path", "query"):
                    continue
                props[p["name"]] = {**(p.get("schema") or {"type": "string"}),
                                    **({"description": p["description"]} if p.get("description") else {})}
                params[p["in"]].append(p["name"])
                if p.get("required") or p["in"] == "path":
                    required.append(p["name"])
            body = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema")
            body_mode = None
            if body:
                body = _resolve(spec, body)
                if body.get("type") == "object" and body.get("properties"):
                    props.update(body["properties"])
                    required += body.get("required", [])
                    body_mode = "merge"
                else:
                    props["body"] = body
                    body_mode = "field"
                    if (op.get("requestBody") or {}).get("required"):
                        required.append("body")
            ops.append({"verb": verb_of(op_id), "operationId": op_id, "method": method.upper(), "path": path,
                        "description": op.get("summary") or op.get("description") or f"{method.upper()} {path}",
                        "params": params, "body": body_mode,
                        "inputSchema": {"type": "object", "properties": props, "required": sorted(set(required))}})
    if not ops:
        raise OpenApiError("operation 없음 / no operations")
    if len(ops) > MAX_OPS:
        raise OpenApiError(f"operation {len(ops)}개 > {MAX_OPS} — 필요한 부분만 담은 문서로")
    if len({o["verb"] for o in ops}) != len(ops):
        raise OpenApiError("operationId 가 겹침 / duplicate operation ids")
    return ops


def server_of(spec: dict, spec_url: str, override: str | None) -> str:
    if override:
        return override.rstrip("/")
    servers = spec.get("servers") or [{"url": "/"}]
    return urljoin(spec_url, servers[0].get("url", "/")).rstrip("/")


def parse(body: bytes) -> dict:
    try:
        return json.loads(body) if body.lstrip().startswith(b"{") else yaml.safe_load(body)
    except (yaml.YAMLError, ValueError) as exc:
        raise OpenApiError(f"OpenAPI 해석 실패: {exc}") from None


async def call(client: httpx.AsyncClient, base: str, op: dict, args: dict) -> dict:
    args = dict(args)
    path = op["path"]
    for name in op["params"]["path"]:
        if name not in args:
            raise OpenApiError(f"path 매개변수 누락: {name}")
        path = path.replace("{" + name + "}", quote(str(args.pop(name)), safe=""))
    query = {k: args.pop(k) for k in op["params"]["query"] if k in args}
    body = None
    if op["body"] == "field":
        body = args.pop("body", None)
    elif op["body"] == "merge":
        body, args = args, {}
    res = await client.request(op["method"], base + path, params=query, json=body)
    try:
        data = res.json()
    except ValueError:
        data = {"text": res.text[:4000]}
    if res.status_code >= 400:
        raise OpenApiError(f"HTTP {res.status_code}: {str(data)[:300]}")
    return data if isinstance(data, dict) else {"result": data}
