"""BaseAgent: handle(capability, input) -> output 하나가 코어다(PRD 7.4)."""
import inspect
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from agentplaza_sdk.llm import LLMClient
from agentplaza_sdk.secrets import SecretStore

Handler = Callable[[dict, "Context"], Any | Awaitable[Any]]


class CapabilityError(Exception):
    """핸들러가 사용자에게 보여 줄 오류(4xx)를 낼 때 사용한다."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


@dataclass
class Context:
    agent_id: str
    data_dir: Path
    llm: LLMClient
    caller: dict = field(default_factory=dict)  # 게이트웨이가 넘긴 호출자 정보(X-Plaza-* 헤더)
    migrations_dir: Path | None = None
    secret: Callable[..., str | None] | None = None  # ctx.secret("API_TOKEN") — agent.yaml env.secretRefs


class Agent:
    def __init__(self, manifest: dict, base_dir: Path | str = "."):
        self.manifest = manifest
        self.base_dir = Path(base_dir)
        self._handlers: dict[str, Handler] = {}
        # 경로는 생성 시점에 고정한다(한 프로세스에 에이전트가 여럿이어도 섞이지 않게).
        self.data_dir = Path(os.environ.get("AGENT_DATA_DIR", "/data"))
        self.migrations_dir = Path(os.environ.get("AGENT_MIGRATIONS", self.base_dir / "database" / "migrations"))
        self._secrets: SecretStore | None = None

    @classmethod
    def from_manifest(cls, path: str | Path = "agent.yaml") -> "Agent":
        p = Path(path)
        if not p.is_absolute() and not p.exists():
            p = Path(os.environ.get("AGENT_MANIFEST", p))
        return cls(yaml.safe_load(p.read_text(encoding="utf-8")), p.parent)

    # --- 메타 ---
    @property
    def id(self) -> str:
        return self.manifest["metadata"]["id"]

    @property
    def name(self) -> str:
        return self.manifest["metadata"].get("name", self.id)

    @property
    def version(self) -> str:
        return self.manifest["metadata"]["version"]

    @property
    def spec(self) -> dict:
        return self.manifest.get("spec", {})

    @property
    def capabilities(self) -> list[dict]:
        return self.spec.get("capabilities", [])

    def capability_spec(self, verb: str) -> dict | None:
        return next((c for c in self.capabilities if c["verb"] == verb), None)

    # --- 등록 ---
    def capability(self, verb: str) -> Callable[[Handler], Handler]:
        def deco(fn: Handler) -> Handler:
            self._handlers[verb] = fn
            return fn
        return deco

    def coherence(self) -> list[str]:
        """선언(agent.yaml) vs 실제(핸들러) 불일치 목록. plaza validate --strict 와 기동 시 검사."""
        declared = {c["verb"] for c in self.capabilities}
        implemented = set(self._handlers)
        errs = [f"declared but not implemented: {v}" for v in sorted(declared - implemented)]
        errs += [f"implemented but not declared: {v}" for v in sorted(implemented - declared)]
        return errs

    def secret(self, name: str, default: str | None = None) -> str | None:
        """시크릿(D9-04): env 우선, 없으면 플랫폼 pull(캐시 30초)."""
        if self._secrets is None:
            self._secrets = SecretStore(self.id)
        return self._secrets.get(name, default)

    def context(self, caller: dict | None = None) -> Context:
        llm = LLMClient(alias=self.spec.get("llm", {}).get("alias", "plaza/chat"))
        return Context(agent_id=self.id, data_dir=self.data_dir, llm=llm, caller=caller or {},
                       migrations_dir=self.migrations_dir, secret=self.secret)

    async def invoke(self, verb: str, payload: dict, ctx: Context) -> Any:
        spec = self.capability_spec(verb)
        if spec is None or verb not in self._handlers:
            raise CapabilityError(f"unknown capability: {verb}", status=404)
        schema = spec.get("inputSchema")
        if isinstance(schema, dict) and "$ref" not in schema:
            errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda e: e.path)
            if errors:
                raise CapabilityError(f"invalid input: {errors[0].message}", status=422)
        out = self._handlers[verb](payload, ctx)
        return await out if inspect.isawaitable(out) else out
