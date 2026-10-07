"""시험 헬퍼 (conftest 와 시험 모듈이 공유)."""

SUPERVISOR = {"email": "root@example.test", "password": "supervisor-pass-1"}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_user(client, token: str, email: str, role: str = "user") -> tuple[dict, str]:
    """사용자 생성 후 임시 비밀번호로 로그인한 토큰까지 돌려준다."""
    res = client.post("/api/users", json={"email": email, "role": role}, headers=auth(token))
    assert res.status_code == 201, res.text
    body = res.json()
    login = client.post("/api/auth/login", json={"email": email, "password": body["temporary_password"]})
    assert login.status_code == 200, login.text
    return body, login.json()["access_token"]


def load_template_app(tmp_path, type_: str, agent_id: str, monkeypatch, api_key: str = "", signed: bool = True,
                      public_url: str | None = None):
    """템플릿으로 에이전트를 생성하고 backend/main.py 를 import 해 ASGI app 을 돌려준다.
    signed=True 면 설치 파이프라인처럼 플랫폼 서명 Agent Card 를 a2a/agent-card.json 에 넣는다."""
    import importlib.util
    import json

    from app.agentspec import generator as gen

    root = tmp_path / agent_id
    for rel, data in gen.scaffold(agent_id, agent_id.replace("-", " ").title(), type_).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
    if signed:
        from app.protocols import card as cards
        m = gen.manifest_of({"agent.yaml": (root / "agent.yaml").read_bytes()})
        url = f"{public_url}/a2a" if public_url else None
        (root / "a2a" / "agent-card.json").write_text(json.dumps(cards.signed_card_json(m, url)))
    monkeypatch.setenv("AGENT_CARD_FILE", str(root / "a2a" / "agent-card.json"))
    if public_url:
        monkeypatch.setenv("AGENT_PUBLIC_URL", public_url)
    monkeypatch.setenv("AGENT_MANIFEST", str(root / "agent.yaml"))
    monkeypatch.setenv("AGENT_MIGRATIONS", str(root / "database" / "migrations"))
    monkeypatch.setenv("AGENT_DATA_DIR", str(tmp_path / f"data-{agent_id}"))
    monkeypatch.setenv("AGENT_API_KEY", api_key)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    spec = importlib.util.spec_from_file_location(f"agent_{agent_id.replace('-', '_')}", root / "backend" / "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app, gen.manifest_of({"agent.yaml": (root / "agent.yaml").read_bytes()})
