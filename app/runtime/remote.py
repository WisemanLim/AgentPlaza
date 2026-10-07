"""runtime 서비스 HTTP 클라이언트 (D8-02). api 는 docker.sock 대신 이 서비스에 위임한다(NFR-I3)."""
from pathlib import Path

import httpx

from app.runtime.driver import RuntimeFailure


class RemoteRuntime:
    name = "remote"

    def __init__(self, url: str, token: str, timeout: float = 900.0):
        self.url, self.token, self.timeout = url.rstrip("/"), token, timeout

    async def _post(self, path: str, body: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                res = await c.post(f"{self.url}{path}", json=body, headers={"x-runtime-token": self.token})
        except httpx.HTTPError as exc:
            raise RuntimeFailure(f"runtime 연결 실패: {type(exc).__name__}") from exc
        data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        if res.status_code >= 400:
            raise RuntimeFailure(data.get("error", f"HTTP {res.status_code}"))
        return data

    @staticmethod
    def _ver(workdir: Path | None) -> str | None:
        return workdir.name if workdir else None

    async def build(self, agent_id: str, workdir: Path) -> dict:
        return await self._post("/build", {"agent_id": agent_id, "version": workdir.name})

    async def up(self, agent_id: str, workdir: Path, *, egress: bool = False, trust: str = "community") -> dict:
        return await self._post("/up", {"agent_id": agent_id, "version": workdir.name, "egress": egress, "trust": trust})

    async def down(self, agent_id: str, workdir: Path | None, volumes: bool = True) -> dict:
        return await self._post("/down", {"agent_id": agent_id, "version": self._ver(workdir), "volumes": volumes})

    async def reconcile(self) -> dict:
        return await self._post("/reconcile", {})

    async def backup(self, agent_id: str) -> dict:
        return await self._post("/backup", {"agent_id": agent_id})

    async def restore(self, agent_id: str, backup: str) -> dict:
        return await self._post("/restore", {"agent_id": agent_id, "backup": backup})

    async def backup_db(self) -> dict:
        return await self._post("/backup-db", {})

    async def backups(self, agent_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                res = await c.get(f"{self.url}/backups/{agent_id}", headers={"x-runtime-token": self.token})
            return res.json()
        except httpx.HTTPError as exc:
            raise RuntimeFailure(f"runtime 연결 실패: {type(exc).__name__}") from exc

    async def status(self, agent_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                res = await c.get(f"{self.url}/status/{agent_id}", headers={"x-runtime-token": self.token})
            return res.json()
        except httpx.HTTPError as exc:
            return {"error": type(exc).__name__}
