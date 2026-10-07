"""런타임 드라이버 — 빌드·기동·정지. 플랫폼 api 는 docker.sock 을 갖지 않는다(NFR-I3).

- none  : 미설정. 빌드 단계에서 명확한 오류로 실패한다.
- fake  : 시험용. 호출만 기록하고 실패를 주입할 수 있다.
- remote: 전용 runtime 서비스(docker.sock 보유)에 HTTP 로 위임한다(Epic 7).
"""
from pathlib import Path

from app.core.config import settings


class RuntimeFailure(Exception):
    pass


class NoRuntime:
    name = "none"

    async def build(self, agent_id: str, workdir: Path) -> dict:
        raise RuntimeFailure("runtime 미설정 — RUNTIME_DRIVER=remote 와 runtime 서비스 필요 / runtime not configured")

    async def up(self, agent_id: str, workdir: Path) -> dict:
        raise RuntimeFailure("runtime 미설정 / runtime not configured")

    async def down(self, agent_id: str, workdir: Path | None, volumes: bool = True) -> dict:
        return {"skipped": True}

    async def status(self, agent_id: str) -> dict:
        return {"containers": []}

    async def backup(self, agent_id: str) -> dict:
        raise RuntimeFailure("runtime 미설정 / runtime not configured")

    async def restore(self, agent_id: str, backup: str) -> dict:
        raise RuntimeFailure("runtime 미설정 / runtime not configured")

    async def backups(self, agent_id: str) -> dict:
        return {"agent": agent_id, "backups": []}


class FakeRuntime:
    name = "fake"

    def __init__(self):
        self.calls: list[tuple[str, str]] = []
        self.fail: set[tuple[str, str]] = set()  # {("build"|"up", agent_id)}
        self.running: set[str] = set()
        self.saved: dict[str, list[str]] = {}

    async def _do(self, op: str, agent_id: str) -> dict:
        self.calls.append((op, agent_id))
        if (op, agent_id) in self.fail:
            raise RuntimeFailure(f"injected {op} failure")
        return {"ok": True}

    async def build(self, agent_id: str, workdir: Path) -> dict:
        assert (workdir / "compose.plaza.yaml").is_file()
        return await self._do("build", agent_id)

    async def up(self, agent_id: str, workdir: Path) -> dict:
        out = await self._do("up", agent_id)
        self.running.add(agent_id)
        return out

    async def down(self, agent_id: str, workdir: Path | None, volumes: bool = True) -> dict:
        self.running.discard(agent_id)
        return await self._do("down", agent_id)

    async def status(self, agent_id: str) -> dict:
        return {"containers": [{"name": f"{agent_id}-be", "state": "running"}] if agent_id in self.running else []}

    async def backup(self, agent_id: str) -> dict:
        await self._do("backup", agent_id)
        stamp = f"20260101T{len(self.calls):06d}Z"
        self.saved.setdefault(agent_id, []).append(stamp)
        return {"agent": agent_id, "backup": stamp, "volumes": [{"volume": f"{agent_id}-data", "file": "data.tgz"}]}

    async def restore(self, agent_id: str, backup: str) -> dict:
        await self._do("restore", agent_id)
        if backup not in self.saved.get(agent_id, []):
            raise RuntimeFailure(f"backup not found: {backup}")
        return {"ok": True, "restored": backup}

    async def backups(self, agent_id: str) -> dict:
        return {"agent": agent_id, "backups": [{"backup": b} for b in reversed(self.saved.get(agent_id, []))]}


_runtime = None


def get_runtime():
    global _runtime
    if _runtime is None:
        if settings.runtime_driver == "fake":
            _runtime = FakeRuntime()
        elif settings.runtime_driver == "remote":
            from app.runtime.remote import RemoteRuntime
            _runtime = RemoteRuntime(settings.runtime_url, settings.runtime_token)
        else:
            _runtime = NoRuntime()
    return _runtime


def set_runtime(rt) -> None:
    """시험·운영 전환용."""
    global _runtime
    _runtime = rt
