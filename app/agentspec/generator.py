"""스캐폴드 생성기 (D4-01·D4-02·D4-07·D8-01).

유형 9종의 agent.yaml·compose.yaml·backend·frontend·database 를 만들어 {경로: bytes} 로 돌려준다.
템플릿 원본: agents/templates/<type>/ (토큰 {{AGENT_ID}} 등) + SDK(sdk/python/agentplaza_sdk) 벤더링.
"""
import copy
import hashlib
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import yaml

from app.agentspec.validate import validate_manifest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "agents" / "templates"
SDK_DIR = ROOT / "sdk" / "python" / "agentplaza_sdk"
TYPES = ("app", "service", "rag", "tool-proxy", "reviewer", "execution", "hitl", "memory", "federation")
AGENT_PORT = 8000
UI_PORT = 8080

_obj = {"type": "object"}
TYPE_DEFS: dict[str, dict] = {
    "app": {
        "capabilities": [{"verb": "manage", "domain": "app.{id}", "description": {"ko": "항목 생성·조회·삭제", "en": "Create, list, get, delete items"},
                          "inputSchema": {**_obj, "required": ["action"], "properties": {
                              "action": {"enum": ["create", "list", "get", "delete"]}, "title": {"type": "string"},
                              "body": {"type": "string"}, "id": {"type": "integer"}, "limit": {"type": "integer"}}}}],
        "ui": True, "llm": False,
    },
    "service": {
        "capabilities": [{"verb": "process", "domain": "text.{id}", "description": {"ko": "텍스트 변환·집계·요약", "en": "Transform, count, summarize text"},
                          "inputSchema": {**_obj, "required": ["text"], "properties": {
                              "text": {"type": "string", "maxLength": 100000},
                              "op": {"enum": ["upper", "lower", "wordcount", "summarize"]}}}}],
        "llm": True,
    },
    "rag": {
        "capabilities": [
            {"verb": "ingest", "domain": "knowledge.{id}", "description": {"ko": "문서 수집·청킹·색인", "en": "Ingest and index a document"},
             "inputSchema": {**_obj, "required": ["title", "text"], "properties": {
                 "doc_id": {"type": "string"}, "title": {"type": "string"}, "text": {"type": "string"}}}},
            {"verb": "search", "domain": "knowledge.{id}", "description": {"ko": "키워드(BM25) 검색", "en": "BM25 keyword search"},
             "inputSchema": {**_obj, "required": ["query"], "properties": {"query": {"type": "string"}, "k": {"type": "integer"}}}},
            {"verb": "ask", "domain": "knowledge.{id}", "description": {"ko": "근거·인용 포함 답변", "en": "Grounded answer with citations"},
             "inputSchema": {**_obj, "required": ["question"], "properties": {"question": {"type": "string"}, "k": {"type": "integer"}}}},
        ],
        "llm": True, "classification": "confidential",
    },
    "tool-proxy": {
        "capabilities": [{"verb": "call", "domain": "tool.{id}", "description": {"ko": "외부 REST API 호출", "en": "Call the wrapped REST API"},
                          "inputSchema": {**_obj, "properties": {"method": {"enum": ["GET", "POST"]}, "path": {"type": "string"},
                                                                 "query": _obj, "json": {}}}}],
        "env_required": ["TOOL_BASE_URL"], "egress": ["${TOOL_BASE_URL}"],
    },
    "reviewer": {
        "capabilities": [{"verb": "review", "domain": "governance.review", "description": {"ko": "PII·인젝션 검토 판정", "en": "Review for PII and injection"},
                          "inputSchema": {**_obj, "required": ["text"], "properties": {"text": {"type": "string"}}}}],
    },
    "execution": {
        "capabilities": [{"verb": "calculate", "domain": "exec.math", "description": {"ko": "안전한 산술식 계산", "en": "Safe arithmetic evaluation"},
                          "inputSchema": {**_obj, "required": ["expression"], "properties": {"expression": {"type": "string"}}}}],
    },
    "hitl": {
        "capabilities": [
            {"verb": "execute_action", "domain": "ops.{id}", "description": {"ko": "승인 후 작업 실행", "en": "Execute an action after approval"},
             "humanApprovalRequired": True,
             "inputSchema": {**_obj, "required": ["action"], "properties": {"action": {"type": "string"}, "target": {"type": "string"}}}},
            {"verb": "history", "domain": "ops.{id}", "description": {"ko": "실행 이력", "en": "Executed actions"}, "inputSchema": _obj},
        ],
    },
    "memory": {
        "capabilities": [
            {"verb": "remember", "domain": "memory.{id}", "description": {"ko": "사실·선호 기억", "en": "Remember a fact"},
             "inputSchema": {**_obj, "required": ["user", "fact"], "properties": {"user": {"type": "string"}, "fact": {"type": "string"}}}},
            {"verb": "recall", "domain": "memory.{id}", "description": {"ko": "기억 조회", "en": "Recall facts"},
             "inputSchema": {**_obj, "required": ["user"], "properties": {"user": {"type": "string"}, "query": {"type": "string"}}}},
            {"verb": "forget", "domain": "memory.{id}", "description": {"ko": "사용자 기억 삭제(삭제권)", "en": "Forget a user's facts"},
             "inputSchema": {**_obj, "required": ["user"], "properties": {"user": {"type": "string"}}}},
        ],
        "classification": "confidential",
    },
    "federation": {"capabilities": [], "backend": False},
}


def build_manifest(agent_id: str, name: str, type_: str, *, description: str = "", version: str = "0.1.0",
                   publisher: str = "local", license_: str = "MIT", llm_alias: str = "plaza/chat",
                   federation_url: str | None = None, federation_kind: str = "a2a") -> dict:
    if type_ not in TYPES:
        raise ValueError(f"type ∈ {TYPES}")
    d = TYPE_DEFS[type_]
    caps = copy.deepcopy(d["capabilities"])
    for c in caps:
        c["domain"] = c["domain"].format(id=agent_id.replace("-", "_"))
    has_backend = d.get("backend", True)
    spec: dict = {
        "type": type_,
        "platform": {"min": "0.1.0"},
        "capabilities": caps,
        "governance": {"dataClassification": d.get("classification", "internal"),
                       "humanApprovalRequired": any(c.get("humanApprovalRequired") for c in caps),
                       "auditLevel": "standard"},
        "protocols": {"rest": {"path": "/api", "openapi": True},
                      "mcp": {"enabled": has_backend, "transport": "streamable-http", "path": "/mcp"},
                      "a2a": {"enabled": has_backend, "cardPath": "/.well-known/agent-card.json"}},
        "llm": {"required": bool(d.get("llm")), "alias": llm_alias, "localOk": True},
        "env": {"required": d.get("env_required", []), "optional": [], "secretRefs": []},
        "permissions": {"network": {"egress": d.get("egress", [])},
                        "fs": {"readOnlyRoot": True, "writable": ["/data"]}, "docker": False},
        "resources": {"cpu": "500m", "memory": "512Mi", "pids": 256},
        "runtime": {"mode": "container", "healthcheck": {"path": "/health", "intervalSec": 10}},
        "ui": {"hasFrontend": bool(d.get("ui")), "mount": "iframe" if d.get("ui") else "none",
               "route": f"/addon/{agent_id}", "navVisible": bool(d.get("ui"))},
        "db": {"engine": ["sqlite"], "isolation": "file", "migrations": "database/migrations"},
        "compat": {"topologies": ["T1", "T2", "T3", "T5"]},
        "dependencies": [],
        "optionalServices": ["otel"],
    }
    if type_ == "federation":
        spec["federation"] = {"kind": federation_kind, "url": federation_url or "https://example.invalid/.well-known/agent-card.json"}
        for k in ("db", "ui", "resources", "runtime"):
            spec.pop(k)
    return {
        "apiVersion": "agentplaza/v1",
        "kind": "Agent",
        "metadata": {"id": agent_id, "name": name, "description": description or name, "version": version,
                     "publisher": {"id": publisher}, "license": license_,
                     "provenance": {"baseAgent": None}},
        "spec": spec,
    }


def _cpus(cpu: str) -> str:
    return str(int(cpu[:-1]) / 1000) if cpu.endswith("m") else cpu


def has_egress(m: dict) -> bool:
    return bool(m["spec"].get("permissions", {}).get("network", {}).get("egress"))


def compose_for(m: dict, *, federated: bool = False, network: str = "plaza-shared",
                registry: str = "${PLAZA_REGISTRY:-local}") -> dict | None:
    """agent.yaml → compose 문서.

    standalone(M1): 자체 포트 publish.
    federated(M2): 포트 0 · 에이전트 전용 외부 네트워크(api·traefik 만 함께, NFR-I4) · Traefik 라벨 + forwardAuth.
    egress 미선언이면 내부 네트워크도 internal(외부 통신 차단).
    """
    spec, meta = m["spec"], m["metadata"]
    if spec["type"] == "federation":
        return None
    aid, ver = meta["id"], meta["version"]
    res = spec.get("resources", {})
    mem = res.get("memory", "512Mi").replace("Mi", "M").replace("Gi", "G")
    internal = f"{aid}-internal"
    nets = [internal, network] if federated else [internal]
    be_env = {
        "AGENT_ID": aid, "AGENT_DATA_DIR": "/data", "AGENT_MANIFEST": "/app/agent.yaml",
        "LLM_BASE_URL": "${LLM_BASE_URL:-http://host.docker.internal:11434/v1}",
        "LLM_ALIAS": "${LLM_ALIAS:-" + spec.get("llm", {}).get("alias", "plaza/chat") + "}",
        "LLM_API_KEY": "${LLM_API_KEY:-}",
        "AGENT_API_KEY": "${AGENT_API_KEY:-}",
        "PLAZA_API_URL": "${PLAZA_API_URL:-}",  # 시크릿 pull(D9-04). M1 단독 실행은 비어 있고 env 를 쓴다
        "AGENT_DATA_CLASS": spec.get("governance", {}).get("dataClassification", "internal"),
        "OTEL_EXPORTER_OTLP_ENDPOINT": "${OTEL_EXPORTER_OTLP_ENDPOINT:-}",
    }
    for k in spec.get("env", {}).get("required", []) + spec.get("env", {}).get("optional", []):
        be_env[k] = "${" + k + ":-}"
    # pids 는 deploy.resources.limits 에만 둔다(compose v5 는 pids_limit 과 동시 지정 시 거부).
    hardening = {"read_only": True, "security_opt": ["no-new-privileges:true"], "cap_drop": ["ALL"],
                 "deploy": {"resources": {"limits": {"cpus": _cpus(res.get("cpu", "500m")), "memory": mem,
                                                     "pids": res.get("pids", 256)}}}}
    be: dict = {
        "build": {"context": ".", "dockerfile": "backend/Dockerfile"},
        "image": f"{registry}/agent-{aid}-be:{ver}",
        "environment": be_env,
        "tmpfs": ["/tmp"],
        "volumes": [f"{aid}-data:/data"],
        "networks": nets,
        "extra_hosts": ["host.docker.internal:host-gateway"],
        "healthcheck": {"test": ["CMD", "python", "-c",
                                 "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen("
                                 f"'http://127.0.0.1:{AGENT_PORT}/health').status==200 else 1)"],
                        "interval": "10s", "timeout": "3s", "retries": 6, "start_period": "20s"},
        "labels": {"agentplaza.agent": aid, "agentplaza.version": ver, "agentplaza.role": "backend",
                   **({"agentplaza.project": "${PLAZA_PROJECT:-plaza}"} if federated else {})},
        **hardening,
    }
    profile = ["federated" if federated else "standalone"]
    be["profiles"] = profile
    services: dict = {f"{aid}-be": be}
    if not federated:
        be["ports"] = ["${BIND_HOST:-127.0.0.1}:${PORT:-8001}:8000"]
        # M1 카드가 광고할 외부 주소(포트를 바꾸면 함께 바뀐다)
        be_env["AGENT_PUBLIC_URL"] = "${AGENT_PUBLIC_URL:-http://127.0.0.1:${PORT:-8001}}"
    else:
        be["labels"].update({
            "traefik.enable": "true",
            "traefik.docker.network": network,
            f"traefik.http.routers.{aid}-api.entrypoints": "web",
            f"traefik.http.routers.{aid}-api.rule": f"PathPrefix(`/a/{aid}/api`) || Path(`/a/{aid}/health`)",
            f"traefik.http.routers.{aid}-api.middlewares": f"plaza-auth@docker,{aid}-strip",
            f"traefik.http.middlewares.{aid}-strip.stripprefix.prefixes": f"/a/{aid}",
            f"traefik.http.services.{aid}-api.loadbalancer.server.port": str(AGENT_PORT),
        })
    if spec.get("ui", {}).get("hasFrontend"):
        fe: dict = {
            "build": {"context": "frontend"},
            "image": f"{registry}/agent-{aid}-fe:{ver}",
            "environment": {"AGENT_BACKEND": f"http://{aid}-be:{AGENT_PORT}", "AGENT_API_KEY": "${AGENT_API_KEY:-}",
                            # 이 화면을 iframe 으로 넣을 수 있는 오리진(CSP frame-ancestors)
                            "CONSOLE_ORIGIN": "${CONSOLE_ORIGIN:-'self'}"},
            # 비루트 nginx(uid 101)가 envsubst 결과를 쓸 수 있게 tmpfs 소유자를 맞춘다(read_only 루트).
            "tmpfs": ["/tmp", "/var/cache/nginx:uid=101,gid=101", "/etc/nginx/conf.d:uid=101,gid=101"],
            "networks": nets,
            "depends_on": {f"{aid}-be": {"condition": "service_healthy"}},
            "labels": {"agentplaza.agent": aid, "agentplaza.role": "frontend",
                       **({"agentplaza.project": "${PLAZA_PROJECT:-plaza}"} if federated else {})},
            "profiles": profile,
            **copy.deepcopy(hardening),
        }
        fe["deploy"]["resources"]["limits"] = {"cpus": "0.25", "memory": "128M", "pids": 128}
        if not federated:
            fe["ports"] = ["${BIND_HOST:-127.0.0.1}:${UI_PORT:-8081}:8080"]
        else:
            fe["labels"].update({
                "traefik.enable": "true",
                "traefik.docker.network": network,
                f"traefik.http.routers.{aid}-ui.entrypoints": "apps",  # 콘솔과 다른 오리진
                f"traefik.http.routers.{aid}-ui.rule": f"PathPrefix(`/a/{aid}/ui`)",
                f"traefik.http.routers.{aid}-ui.middlewares": f"plaza-auth@docker,{aid}-ui-strip",
                f"traefik.http.middlewares.{aid}-ui-strip.stripprefix.prefixes": f"/a/{aid}/ui",
                f"traefik.http.services.{aid}-ui.loadbalancer.server.port": str(UI_PORT),
            })
        services[f"{aid}-fe"] = fe
    doc = {
        "name": f"plaza-{aid}",
        "x-agentplaza": {"agent": aid, "version": ver, "manifest": "./agent.yaml",
                         "profile": "federated" if federated else "standalone"},
        "services": services,
        "networks": {internal: {"internal": True} if federated and not has_egress(m) else {}},
        "volumes": {f"{aid}-data": {}},
    }
    if federated:
        doc["networks"][network] = {"external": True, "name": network}
    return doc


def _render(text: str, tokens: dict[str, str]) -> str:
    for k, v in tokens.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def _dump(data: dict) -> bytes:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120).encode()


def scaffold(agent_id: str, name: str, type_: str, **kw) -> dict[str, bytes]:
    """새 에이전트 파일 묶음. 생성 직후 validate_manifest 를 통과해야 한다."""
    m = build_manifest(agent_id, name, type_, **kw)
    errs = validate_manifest(m)
    if errs:
        raise ValueError("; ".join(errs))
    return render_files(m)


def render_files(m: dict) -> dict[str, bytes]:
    meta, spec = m["metadata"], m["spec"]
    aid, type_ = meta["id"], spec["type"]
    tokens = {"AGENT_ID": aid, "AGENT_NAME": meta["name"], "VERSION": meta["version"],
              "LICENSE": meta["license"], "PUBLISHER": meta.get("publisher", {}).get("id", "local"),
              "YEAR": str(datetime.now(UTC).year)}
    files: dict[str, bytes] = {"agent.yaml": _dump(m)}
    tdir = TEMPLATES / type_
    for f in sorted(tdir.rglob("*")) if tdir.is_dir() else []:
        if f.is_file():
            files[f.relative_to(tdir).as_posix()] = _render(f.read_text(encoding="utf-8"), tokens).encode()
    common = TEMPLATES / "_common"
    if spec["type"] != "federation":
        for f in sorted((common / "backend").rglob("*")):
            if f.is_file():
                files[f"backend/{f.relative_to(common / 'backend').as_posix()}"] = f.read_bytes()
        for f in sorted(SDK_DIR.rglob("*.py")):
            files[f"backend/agentplaza_sdk/{f.relative_to(SDK_DIR).as_posix()}"] = f.read_bytes()
        files.setdefault("database/migrations/.keep", b"")
        files.setdefault("a2a/.keep", b"")  # 서명 카드 자리(PRD 7.4: 빌드 시 생성, 수정 금지)
        if spec.get("ui", {}).get("hasFrontend"):
            for f in sorted((common / "frontend").rglob("*")):
                if f.is_file():
                    files[f"frontend/{f.relative_to(common / 'frontend').as_posix()}"] = f.read_bytes()
        files["compose.yaml"] = _dump(compose_for(m))
        files[".env.example"] = _render((common / "env.example").read_text(encoding="utf-8"), tokens).encode()
    files["README.md"] = _render((common / "README.md").read_text(encoding="utf-8"), tokens).encode()
    files["LICENSE"] = _render((common / "LICENSE").read_text(encoding="utf-8"), tokens).encode()
    files["CHANGELOG.md"] = f"# Changelog\n\n## {meta['version']}\n- generated by plaza scaffold ({type_})\n".encode()
    return files


def checksums(files: dict[str, bytes]) -> bytes:
    return "".join(f"{hashlib.sha256(files[p]).hexdigest()}  {p}\n"
                   for p in sorted(files) if p != "checksums.txt").encode()


def pack(files: dict[str, bytes], extra: dict[str, bytes] | None = None) -> bytes:
    """zip 직렬화. checksums.txt 를 함께 넣는다(v2.1 규격). 타임스탬프 고정으로 같은 입력 = 같은 zip.
    extra(예: signature.sig)는 checksums 대상이 아니다 — 서명은 checksums.txt 에 대한 것이다."""
    files = {**files, "checksums.txt": checksums(files), **(extra or {})}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            info = zipfile.ZipInfo(path, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            z.writestr(info, files[path])
    return buf.getvalue()


def read_zip(data: bytes) -> dict[str, bytes]:
    """신뢰된 zip(직접 생성한 것) 전용. 업로드 zip 은 registry 게이트(Epic 6)를 거친다."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}


def manifest_of(files: dict[str, bytes]) -> dict:
    return yaml.safe_load(files["agent.yaml"])


def derive(files: dict[str, bytes], new_id: str, new_name: str | None = None, version: str = "0.1.0") -> dict[str, bytes]:
    """파생 export (D4-07, v1 F26): 새 id 로 복제하고 provenance 에 출처를 자동 기록한다(DP10)."""
    base = manifest_of(files)
    m = copy.deepcopy(base)
    m["metadata"].update({"id": new_id, "name": new_name or f"{base['metadata']['name']} (derived)", "version": version})
    m["metadata"]["provenance"] = {"baseAgent": base["metadata"]["id"], "baseVersion": base["metadata"]["version"],
                                   "derivedAt": datetime.now(UTC).replace(microsecond=0).isoformat()}
    for c in m["spec"].get("capabilities", []):
        c["domain"] = c["domain"].replace(base["metadata"]["id"].replace("-", "_"), new_id.replace("-", "_"))
    if "ui" in m["spec"]:
        m["spec"]["ui"]["route"] = f"/addon/{new_id}"
    errs = validate_manifest(m)
    if errs:
        raise ValueError("; ".join(errs))
    out = {p: b for p, b in files.items() if p not in {"checksums.txt", "signature.sig"}}
    out["agent.yaml"] = _dump(m)
    if m["spec"]["type"] != "federation":
        out["compose.yaml"] = _dump(compose_for(m))
    out["CHANGELOG.md"] = (files.get("CHANGELOG.md", b"# Changelog\n").decode()
                           + f"\n## {version}\n- derived from {base['metadata']['id']}@{base['metadata']['version']}\n").encode()
    return out


def standalone_bundle(files: dict[str, bytes]) -> dict[str, bytes]:
    """M1 독립 납품 번들 (D4-07, v1 F27): agent.zip 규격 그대로 + 실행 안내. compose 는 standalone 프로파일."""
    m = manifest_of(files)
    if m["spec"]["type"] == "federation":
        raise ValueError("federation 유형은 원격 연동 전용 — 독립 번들 없음")
    out = {p: b for p, b in files.items() if p not in {"checksums.txt", "signature.sig"}}
    out["compose.yaml"] = _dump(compose_for(m))
    out.setdefault(".env.example", (TEMPLATES / "_common" / "env.example").read_bytes())
    return out
