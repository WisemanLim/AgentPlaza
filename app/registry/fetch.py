"""경로 B 소스 가져오기 (D6-03): zip URL · Git URL(subdir·ref). 결과는 zip bytes → 등록 8단계로.

OCI 아티팩트(ORAS)는 레지스트리 클라이언트가 필요해 P0 범위에서 제외(계획표 가정 참조).
"""
import io
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.orchestrator import executor


class FetchError(Exception):
    pass


def _limit() -> int:
    return settings.upload_max_mb * 1024 * 1024


async def zip_url(url: str, headers: dict | None = None) -> bytes:
    u = urlparse(url)
    if u.scheme not in ("https", "http"):
        raise FetchError("zip URL 은 http(s) 만 / only http(s)")
    base = f"{u.scheme}://{u.netloc}"
    buf = bytearray()
    try:
        async with httpx.AsyncClient(transport=executor.TRANSPORTS.get(base), timeout=60, follow_redirects=True) as c, \
                c.stream("GET", url, headers=headers) as res:
            if res.status_code != 200:
                raise FetchError(f"다운로드 실패 HTTP {res.status_code}")
            async for chunk in res.aiter_bytes():
                buf += chunk
                if len(buf) > _limit():
                    raise FetchError(f"크기 초과 > {settings.upload_max_mb}MB")
    except httpx.HTTPError as exc:
        raise FetchError(f"다운로드 실패: {type(exc).__name__}") from exc
    return bytes(buf)


GIT_REF = re.compile(r"^[A-Za-z0-9._/-]{1,100}$")


def git_subdir(url: str, path: str = "", ref: str | None = None) -> bytes:
    u = urlparse(url)
    allowed = ("https", "http") if settings.app_env == "prod" else ("https", "http", "file")
    if u.scheme not in allowed:
        raise FetchError(f"Git URL scheme 허용: {allowed}")
    if ref and not GIT_REF.match(ref):
        raise FetchError("잘못된 ref")
    if ".." in Path(path).parts or path.startswith("/"):
        raise FetchError("잘못된 path")
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["git", "clone", "--depth", "1", "--quiet"] + (["--branch", ref] if ref else []) + ["--", url, tmp + "/repo"]
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)  # noqa: S603 — 고정 인자, shell 미사용
        if r.returncode != 0:
            raise FetchError(f"git clone 실패: {r.stderr.strip()[-300:]}")
        root = (Path(tmp) / "repo" / path).resolve()
        if not str(root).startswith(str((Path(tmp) / "repo").resolve())) or not (root / "agent.yaml").is_file():
            raise FetchError(f"agent.yaml 없음: {path or '/'}")
        buf = io.BytesIO()
        total = 0
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(root.rglob("*")):
                if ".git" in f.relative_to(root).parts or f.is_symlink() or not f.is_file():
                    continue
                total += f.stat().st_size
                if total > _limit():
                    raise FetchError(f"크기 초과 > {settings.upload_max_mb}MB")
                z.write(f, f.relative_to(root).as_posix())
        return buf.getvalue()
