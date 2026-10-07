"""AgentPlaza runtime 서비스 — docker.sock 을 가진 유일한 플랫폼 컨테이너(api·에이전트는 금지, NFR-I3).

표준 라이브러리만 사용한다. 토큰(X-Runtime-Token)으로 api 만 호출할 수 있다.
  POST /build {agent_id, version}         compose build
  POST /up    {agent_id, version, egress} 린트 → 전용 네트워크 → api·traefik 연결 → up --wait
  POST /down  {agent_id, version?, volumes} down -v → 네트워크 분리·삭제
  POST /reconcile                         api·traefik 를 에이전트 네트워크에 다시 연결(10초 주기로도 수행)
  POST /backup  {agent_id}                 에이전트 볼륨 백업(일시정지 스냅숏, tar.gz) → data/backups/agents/<id>/<stamp>/
  POST /restore {agent_id, backup}         정지 → 볼륨 비우고 복원 → 시작 (D8-06·NFR-O4)
  POST /backup-db                          플랫폼 PostgreSQL pg_dump(-Fc) → data/backups/platform/
  GET  /backups/<agent_id>                 백업 목록
  GET  /status/<agent_id>                 compose ps
  GET  /health
"""
import hmac
import json
import os
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from lint import lint

TOKEN = os.environ.get("RUNTIME_TOKEN", "")
PROJECT = os.environ.get("PLAZA_PROJECT", "plaza")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))
PLATFORM_SERVICES = [s for s in os.environ.get("PLATFORM_SERVICES", "api,traefik").split(",") if s]
WAIT = int(os.environ.get("UP_WAIT_SECONDS", "180"))
RECONCILE_SECONDS = int(os.environ.get("RECONCILE_SECONDS", "10"))
HELPER_IMAGE = os.environ.get("HELPER_IMAGE", "docker:cli")  # 볼륨 tar 를 돌릴 이미지 — 이 서비스 자신의 이미지(오프라인 OK)
STAMP = re.compile(r"^\d{8}T\d{6}Z$")
ID = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
VER = re.compile(r"^[0-9A-Za-z.+-]{1,40}$")


class Fail(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def sh(*args: str, timeout: int = 900) -> str:
    r = subprocess.run(list(args), capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise Fail(f"{' '.join(args[:4])}…: {(r.stderr or r.stdout).strip()[-800:]}", 500)
    return r.stdout


def project(aid: str) -> str:
    return f"{PROJECT}-agent-{aid}"


def network(aid: str) -> str:
    return f"{PROJECT}-net-{aid}"


def workdir(aid: str, ver: str) -> Path:
    if not ID.match(aid) or not VER.match(ver):
        raise Fail("invalid agent id/version")
    w = (DATA_DIR / "installed" / aid / ver).resolve()
    if not str(w).startswith(str(DATA_DIR.resolve())) or not (w / "compose.plaza.yaml").is_file():
        raise Fail(f"workdir not found: {aid}/{ver}", 404)
    return w


def compose(aid: str, w: Path, *args: str, timeout: int = 900) -> str:
    return sh("docker", "compose", "-p", project(aid), "--project-directory", str(w), "-f", str(w / "compose.plaza.yaml"),
              "--profile", "federated", *args, timeout=timeout)


def platform_containers() -> list[tuple[str, str]]:
    out = []
    for svc in PLATFORM_SERVICES:
        ids = sh("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}",
                 "--filter", f"label=com.docker.compose.service={svc}").split()
        out += [(svc, i) for i in ids]
    return out


def ensure_network(aid: str, egress: bool) -> None:
    name = network(aid)
    if not sh("docker", "network", "ls", "-q", "--filter", f"name=^{name}$").strip():
        args = ["docker", "network", "create", "--label", f"agentplaza.project={PROJECT}", "--label", f"agentplaza.agent={aid}"]
        if not egress:  # egress 미선언 = 외부 통신 차단(PRD 13.1 egress 기본 차단)
            args.append("--internal")
        sh(*args, name)
    attached = sh("docker", "network", "inspect", name, "--format", "{{range .Containers}}{{.Name}} {{end}}").split()
    for svc, cid in platform_containers():
        cname = sh("docker", "inspect", cid, "--format", "{{.Name}}").strip().lstrip("/")
        if cname not in attached:
            sh("docker", "network", "connect", "--alias", svc, name, cid)


def reconcile() -> dict:
    """플랫폼 컨테이너(api·traefik)가 재생성되면 에이전트 전용 네트워크 연결이 사라진다 — 다시 붙인다."""
    nets = sh("docker", "network", "ls", "--filter", f"label=agentplaza.project={PROJECT}", "--format", "{{.Name}}").split()
    fixed = []
    platform = platform_containers()
    for name in nets:
        attached = sh("docker", "network", "inspect", name, "--format", "{{range .Containers}}{{.Name}} {{end}}").split()
        for svc, cid in platform:
            cname = sh("docker", "inspect", cid, "--format", "{{.Name}}").strip().lstrip("/")
            if cname not in attached:
                sh("docker", "network", "connect", "--alias", svc, name, cid)
                fixed.append(f"{svc}->{name}")
    return {"networks": len(nets), "reconnected": fixed}


def _reconcile_loop() -> None:
    while True:
        try:
            out = reconcile()
            if out["reconnected"]:
                print(f"runtime reconcile {out['reconnected']}", flush=True)
        except Fail as exc:
            print(f"runtime reconcile error {exc}", flush=True)
        time.sleep(RECONCILE_SECONDS)


def drop_network(aid: str) -> None:
    name = network(aid)
    if not sh("docker", "network", "ls", "-q", "--filter", f"name=^{name}$").strip():
        return
    for _, cid in platform_containers():
        subprocess.run(["docker", "network", "disconnect", "-f", name, cid], capture_output=True)
    subprocess.run(["docker", "network", "rm", name], capture_output=True)


def run_bytes(args: list[str], *, stdin: bytes | None = None, timeout: int = 900) -> bytes:
    r = subprocess.run(args, input=stdin, capture_output=True, timeout=timeout)
    if r.returncode != 0:
        raise Fail(f"{' '.join(args[:4])}…: {r.stderr.decode('utf-8', 'replace').strip()[-800:]}", 500)
    return r.stdout


def volumes_of(aid: str) -> list[str]:
    return sh("docker", "volume", "ls", "-q", "--filter", f"label=com.docker.compose.project={project(aid)}").split()


def backup_dir(aid: str, stamp: str | None = None) -> Path:
    if not ID.match(aid) or (stamp is not None and not STAMP.match(stamp)):
        raise Fail("invalid agent id/backup")
    base = DATA_DIR / "backups" / "agents" / aid
    return base / stamp if stamp else base


def do_backup(body: dict) -> dict:
    """일시정지(pause) 동안 볼륨을 tar.gz 로 떠서 일관된 스냅숏을 만든다(SQLite 파일 포함)."""
    import hashlib
    aid = body["agent_id"]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = backup_dir(aid, stamp)
    out.mkdir(parents=True, exist_ok=True)
    vols, paused = [], False
    try:
        if sh("docker", "compose", "-p", project(aid), "ps", "-q", "--status", "running").strip():
            sh("docker", "compose", "-p", project(aid), "pause")
            paused = True
        for v in volumes_of(aid):
            data = run_bytes(["docker", "run", "--rm", "--network", "none", "-v", f"{v}:/v:ro", "--entrypoint", "tar",
                              HELPER_IMAGE, "czf", "-", "-C", "/v", "."])
            name = v.removeprefix(f"{project(aid)}_")
            (out / f"{name}.tgz").write_bytes(data)
            vols.append({"volume": v, "file": f"{name}.tgz", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    finally:
        if paused:
            sh("docker", "compose", "-p", project(aid), "unpause")
    manifest = {"agent": aid, "backup": stamp, "volumes": vols}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def do_restore(body: dict) -> dict:
    aid, stamp = body["agent_id"], body["backup"]
    src = backup_dir(aid, stamp)
    manifest = json.loads((src / "manifest.json").read_text()) if (src / "manifest.json").is_file() else None
    if manifest is None:
        raise Fail(f"backup not found: {aid}/{stamp}", 404)
    running = bool(sh("docker", "compose", "-p", project(aid), "ps", "-q").strip())
    if running:
        sh("docker", "compose", "-p", project(aid), "stop")
    for v in manifest["volumes"]:
        sh("docker", "volume", "create", "--label", f"com.docker.compose.project={project(aid)}", v["volume"])
        run_bytes(["docker", "run", "--rm", "-i", "--network", "none", "-v", f"{v['volume']}:/v", "--entrypoint", "sh",
                   HELPER_IMAGE, "-c", "find /v -mindepth 1 -delete && tar xzf - -C /v"], stdin=(src / v["file"]).read_bytes())
    if running:
        sh("docker", "compose", "-p", project(aid), "start")
    return {"ok": True, "restored": stamp, "volumes": [v["volume"] for v in manifest["volumes"]]}


def do_backups(aid: str) -> dict:
    base = backup_dir(aid)
    items = [json.loads((d / "manifest.json").read_text()) for d in sorted(base.iterdir(), reverse=True)
             if (d / "manifest.json").is_file()] if base.is_dir() else []
    return {"agent": aid, "backups": items}


def do_backup_db(_body: dict) -> dict:
    """플랫폼 DB(PostgreSQL) 논리 백업. SQLite(local) 는 api 가 직접 백업 API 로 복사한다."""
    import hashlib
    ids = sh("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}",
             "--filter", "label=com.docker.compose.service=db").split()
    if not ids:
        raise Fail("db 서비스 없음(local=SQLite 는 api 가 백업) / no db service", 404)
    data = run_bytes(["docker", "exec", ids[0], "sh", "-c", 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc'])
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = DATA_DIR / "backups" / "platform" / f"{stamp}.dump"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {"backup": stamp, "file": str(out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def gvisor() -> bool:
    return "runsc" in sh("docker", "info", "--format", "{{json .Runtimes}}")


def do_build(body: dict) -> dict:
    aid, w = body["agent_id"], workdir(body["agent_id"], body["version"])
    compose(aid, w, "build")
    return {"ok": True}


def do_up(body: dict) -> dict:
    aid, w = body["agent_id"], workdir(body["agent_id"], body["version"])
    doc = json.loads(compose(aid, w, "config", "--format", "json"))
    errs = lint(doc, federated=True)
    if errs:
        raise Fail("compose lint: " + "; ".join(errs), 422)
    warnings = []
    if body.get("trust", "community") == "community" and not gvisor():
        warnings.append("gVisor(runsc) 미설치 — runc 로 실행 (D8-04)")
    ensure_network(aid, bool(body.get("egress")))
    compose(aid, w, "up", "-d", "--wait", "--wait-timeout", str(WAIT), "--remove-orphans", timeout=WAIT + 60)
    return {"ok": True, "warnings": warnings, "network": network(aid)}


def do_down(body: dict) -> dict:
    aid = body["agent_id"]
    if not ID.match(aid):
        raise Fail("invalid agent id")
    args = ["down", "--remove-orphans", "--rmi", "local"] + (["-v"] if body.get("volumes", True) else [])
    ver = body.get("version")
    if ver and (DATA_DIR / "installed" / aid / ver / "compose.plaza.yaml").is_file():
        compose(aid, workdir(aid, ver), *args)
    else:  # 작업 디렉터리가 없어도 프로젝트 이름으로 정리한다
        sh("docker", "compose", "-p", project(aid), *args)
    drop_network(aid)
    return {"ok": True}


def do_status(aid: str) -> dict:
    if not ID.match(aid):
        raise Fail("invalid agent id")
    out = sh("docker", "compose", "-p", project(aid), "ps", "-a", "--format", "json")
    rows = [json.loads(line) for line in out.splitlines() if line.strip().startswith("{")]
    return {"containers": [{"name": r.get("Name"), "service": r.get("Service"), "state": r.get("State"),
                            "health": r.get("Health")} for r in rows], "network": network(aid)}


ROUTES = {"/build": do_build, "/up": do_up, "/down": do_down, "/reconcile": lambda _body: reconcile(),
          "/backup": do_backup, "/restore": do_restore, "/backup-db": do_backup_db}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        return bool(TOKEN) and hmac.compare_digest(self.headers.get("x-runtime-token", ""), TOKEN)

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            return self._send(200, {"status": "ok", "project": PROJECT})
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        for prefix, fn in (("/status/", do_status), ("/backups/", do_backups)):
            if self.path.startswith(prefix):
                try:
                    return self._send(200, fn(self.path.removeprefix(prefix)))
                except Fail as exc:
                    return self._send(exc.code, {"error": str(exc)})
        self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        fn = ROUTES.get(self.path)
        if fn is None:
            return self._send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", "0") or 0)) or b"{}")
            self._send(200, fn(body))
        except Fail as exc:
            self._send(exc.code, {"error": str(exc)})
        except (KeyError, ValueError) as exc:
            self._send(400, {"error": f"bad request: {exc}"})
        except subprocess.TimeoutExpired:
            self._send(504, {"error": "timeout"})

    def log_message(self, fmt, *args):  # 요청 로그는 stdout 한 줄
        print(f"runtime {self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("RUNTIME_TOKEN 필요 / required")
    threading.Thread(target=_reconcile_loop, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 9000), Handler).serve_forever()
