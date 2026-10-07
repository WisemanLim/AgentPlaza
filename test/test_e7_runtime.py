"""Epic 7 — 런타임·compose·라우팅·격리 (D8-02/03/04/05, NFR-I3·I4·I5).

실 Docker 기동(runtime 서비스·Traefik·네트워크 격리)은 impl 시나리오에서 확인하고, 여기서는
린트 게이트·federated compose 규칙·forwardAuth·include 생성을 결정적으로 시험한다.
"""
import copy
from pathlib import Path

import pytest
import yaml

from app.agentspec import generator as gen
from app.core.config import settings
from app.registry import pipeline
from app.runtime.lint import lint
from app.services import registry
from helpers import auth, make_user


def federated(type_="app", **spec):
    m = gen.build_manifest("board", "Board", type_)
    m["spec"].update(spec)
    return gen.compose_for(m, federated=True, network="plaza-test-net-board")


def test_e7_01_generated_federated_compose_passes_lint():
    for t in ("app", "service", "rag", "tool-proxy", "reviewer", "execution", "hitl", "memory"):
        m = gen.build_manifest(f"x-{t}", "X", t)
        assert lint(gen.compose_for(m, federated=True, network="n")) == [], t


@pytest.mark.parametrize("mutate,needle", [
    (lambda s: s.update(privileged=True), "privileged"),
    (lambda s: s.update(network_mode="host"), "network_mode=host"),
    (lambda s: s.update(pid="host"), "pid=host"),
    (lambda s: s.update(cap_add=["SYS_ADMIN"]), "cap_add"),
    (lambda s: s.update(cap_drop=[]), "cap_drop"),
    (lambda s: s.update(read_only=False), "read_only"),
    (lambda s: s["volumes"].append("/var/run/docker.sock:/var/run/docker.sock"), "docker.sock"),
    (lambda s: s["volumes"].append({"type": "bind", "source": "/etc", "target": "/host-etc"}), "bind"),
    (lambda s: s.update(ports=["8000:8000"]), "포트 publish"),
    (lambda s: s["deploy"]["resources"]["limits"].pop("memory"), "limits.memory"),
    (lambda s: s["deploy"]["resources"].update(reservations={"devices": [{"capabilities": ["gpu"]}]}), "GPU"),
    (lambda s: s.update(runtime="sysbox"), "runtime"),
    (lambda s: s.update(security_opt=[]), "no-new-privileges"),
], ids=["privileged", "host-net", "host-pid", "cap-add", "cap-drop", "rw-root", "docker-sock", "bind", "ports",
        "no-mem-limit", "gpu", "runtime", "no-new-priv"])
def test_e7_02_lint_rejects_escape_vectors(mutate, needle):
    """NFR-I3·I5·D8-04·D8-05: 컨테이너 탈출·호스트 접근·무제한 자원·GPU 남용을 기동 전에 거부."""
    doc = copy.deepcopy(federated())
    mutate(doc["services"]["board-be"])
    errs = lint(doc)
    assert any(needle in e for e in errs), errs


def test_e7_03_isolated_network_and_egress_policy():
    """NFR-I4: 에이전트 전용 외부 네트워크 + egress 미선언이면 내부 네트워크 internal."""
    doc = federated()
    assert doc["networks"]["plaza-test-net-board"] == {"external": True, "name": "plaza-test-net-board"}
    assert doc["networks"]["board-internal"] == {"internal": True}
    assert "plaza-shared" not in doc["networks"]
    egress = federated("tool-proxy")
    assert egress["networks"]["board-internal"] == {}  # egress 선언 시 내부망도 외부 통신 허용
    labels = doc["services"]["board-be"]["labels"]
    assert labels["agentplaza.project"] == "${PLAZA_PROJECT:-plaza}"
    assert labels["traefik.http.routers.board-api.middlewares"].startswith("plaza-auth@docker")
    assert doc["services"]["board-fe"]["labels"]["traefik.http.routers.board-ui.middlewares"].startswith("plaza-auth@docker")


def test_e7_04_forward_auth(client, sup_token, tmp_path, monkeypatch):
    """D8-03: Traefik forwardAuth — 쿠키/Bearer/키 확인 후 에이전트 내부 키 주입. 비활성·범위 밖·무인증 거부."""
    from app import db as appdb
    with appdb.SessionLocal() as s:
        registry.register(s, gen.build_manifest("board", "Board", "app"), endpoint="http://board-be:8000", status="healthy")
    fwd = lambda headers: client.get("/api/auth/forward", headers={"X-Forwarded-Uri": "/a/board/ui/", **headers})  # noqa: E731
    client.cookies.clear()  # 셋업 응답이 남긴 세션 쿠키 제거
    assert fwd({}).status_code == 401
    ok = fwd(auth(sup_token))
    assert ok.status_code == 200 and ok.headers["x-api-key"] == registry.agent_key("board")
    assert ok.headers["x-plaza-user"] == "root@example.test"
    login = client.post("/api/auth/login", json={"email": "root@example.test", "password": "supervisor-pass-1"})
    assert "plaza_session" in login.cookies and "httponly" in login.headers["set-cookie"].lower()
    client.cookies.set("plaza_session", login.cookies["plaza_session"])
    assert fwd({}).status_code == 200  # 쿠키로 통과(콘솔 iframe)
    client.cookies.clear()
    key = client.post("/api/api-keys", json={"name": "scoped", "agents": ["other"]}, headers=auth(sup_token)).json()["key"]
    assert fwd({"x-api-key": key}).status_code == 403  # 키 범위 밖
    client.patch("/api/agents/board", json={"is_active": False}, headers=auth(sup_token))
    assert fwd(auth(sup_token)).status_code == 403  # 비활성
    assert client.get("/api/auth/forward", headers={"X-Forwarded-Uri": "/etc", **auth(sup_token)}).status_code == 403


def test_e7_05_include_file_and_remote_driver_contract(tmp_path, monkeypatch):
    """D8-02: 설치 현재 버전 목록 → 루트 include."""
    from app import db as appdb
    from app.models import AgentVersion
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    with appdb.SessionLocal() as s:
        s.add(AgentVersion(agent_id="board", version="1.0.0", sha256="x", artifact="a", current=True, installed_by="t"))
        s.add(AgentVersion(agent_id="board", version="0.9.0", sha256="y", artifact="b", current=False, installed_by="t"))
        s.commit()
        out = pipeline.write_include(s)
    inc = yaml.safe_load(Path(out).read_text())["include"]
    assert inc == [{"path": "board/1.0.0/compose.plaza.yaml", "project_directory": "board/1.0.0",
                    "env_file": "board/1.0.0/.env"}]


def test_e7_06_optional_overlays_and_platform_compose_policy():
    """D8-05: GPU 예약은 LLM 공급자(ollama 오버레이)만. 플랫폼 api 는 docker.sock 을 갖지 않는다(NFR-I3)."""
    root = Path(__file__).resolve().parents[1]
    base = yaml.safe_load((root / "docker-compose.yml").read_text())
    assert not any("docker.sock" in str(v) for v in base["services"]["api"].get("volumes", []))
    assert any("docker.sock" in str(v) for v in base["services"]["runtime"]["volumes"])
    assert all(str(v).endswith(":ro") for v in base["services"]["traefik"]["volumes"] if "docker.sock" in str(v))
    gpu = yaml.safe_load((root / "compose-optional" / "ollama-gpu.yml").read_text())
    assert gpu["services"]["ollama"]["deploy"]["resources"]["reservations"]["devices"][0]["capabilities"] == ["gpu"]


def test_e7_07_runtime_service_lint_module_is_stdlib_only():
    """runtime 이미지는 표준 라이브러리만으로 lint 를 실행한다(공격 표면 최소화)."""
    root = Path(__file__).resolve().parents[1]
    src = (root / "app" / "runtime" / "lint.py").read_text() + (root / "runtime" / "service.py").read_text()
    imports = {line.split()[1].split(".")[0] for line in src.splitlines() if line.startswith(("import ", "from "))}
    assert imports <= {"hmac", "json", "os", "re", "subprocess", "threading", "time", "http", "pathlib", "lint"}, imports
