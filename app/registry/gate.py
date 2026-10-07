"""등록 2단계 — 구조 검증 게이트 (D5-02, NFR-S1).

zip-slip·심볼릭 링크·압축 폭탄·중첩 아카이브·암호화 항목을 거부하고, agent.yaml 스키마·필수 파일·
Python 문법·SQL(DDL 만)·금지 API(docker.sock 등)를 검사한다. 거부 사유는 목록으로 돌려준다.
"""
import ast
import io
import re
import stat
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import sqlglot
from sqlglot import exp

from app.agentspec.validate import validate_text
from app.core.config import settings

NESTED = (".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar", ".jar", ".war", ".whl")
FTS5 = re.compile(r"^\s*CREATE\s+VIRTUAL\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?\w+\s+USING\s+fts5\s*\(", re.I)
DDL = (exp.Create, exp.Alter, exp.Drop)
# 차단: 컨테이너 탈출·호스트 제어 수단(NFR-I3). 경고: 감사 대상이지만 유형에 따라 정당할 수 있는 API.
BLOCK = {r"/var/run/docker\.sock": "docker.sock 참조", r"\bprivileged\s*:\s*true": "privileged 컨테이너",
         r"network_mode\s*:\s*['\"]?host": "host 네트워크", r"\bpid\s*:\s*['\"]?host": "host pid"}
WARN = {r"\bsubprocess\b": "subprocess 사용", r"\bos\.system\(": "os.system 사용", r"\beval\(": "eval 사용",
        r"\bexec\(": "exec 사용"}


@dataclass
class GateResult:
    files: dict[str, bytes] = field(default_factory=dict)
    meta: dict[str, bytes] = field(default_factory=dict)  # checksums.txt · signature.sig (3단계 무결성·서명)
    manifest: dict | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _safe_path(name: str) -> str | None:
    p = PurePosixPath(name.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return None
    return p.as_posix()


def extract(data: bytes) -> GateResult:
    r = GateResult()
    if len(data) > settings.upload_max_mb * 1024 * 1024:
        r.errors.append(f"업로드 크기 초과 > {settings.upload_max_mb}MB")
        return r
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        r.errors.append("zip 형식 아님 / not a zip")
        return r
    infos = [i for i in z.infolist() if not i.is_dir()]
    if len(infos) > settings.unpacked_max_files:
        r.errors.append(f"파일 수 초과 > {settings.unpacked_max_files}")
        return r
    total = 0
    for i in infos:
        mode = i.external_attr >> 16
        path = _safe_path(i.filename)
        if path is None:
            r.errors.append(f"경로 탐색(zip-slip) 차단: {i.filename}")
        elif stat.S_ISLNK(mode):
            r.errors.append(f"심볼릭 링크 차단: {i.filename}")
        elif i.flag_bits & 0x1:
            r.errors.append(f"암호화 항목 차단: {i.filename}")
        elif path.lower().endswith(NESTED):
            r.errors.append(f"중첩 아카이브 차단: {i.filename}")
        elif i.compress_size and i.file_size / max(i.compress_size, 1) > settings.unpacked_max_ratio:
            r.errors.append(f"압축 폭탄 의심(비율 {i.file_size // max(i.compress_size, 1)}): {i.filename}")
        total += i.file_size
        if path in r.files:
            r.errors.append(f"중복 경로: {path}")
    if total > settings.unpacked_max_mb * 1024 * 1024:
        r.errors.append(f"압축 해제 크기 초과 > {settings.unpacked_max_mb}MB")
    if r.errors:
        return r
    for i in infos:
        with z.open(i) as f:  # 선언 크기를 넘겨 읽지 않는다(헤더 위조 대비)
            body = f.read(i.file_size + 1)
        if len(body) > i.file_size:
            r.errors.append(f"선언 크기 불일치: {i.filename}")
            return r
        r.files[_safe_path(i.filename)] = body
    # 최상위 디렉터리 하나로 감싼 zip(디렉터리 zip)은 한 단계 벗긴다(PRD 10.6 v2.0).
    tops = {p.split("/", 1)[0] for p in r.files}
    if "agent.yaml" not in r.files and len(tops) == 1 and all("/" in p for p in r.files):
        prefix = tops.pop() + "/"
        r.files = {p.removeprefix(prefix): b for p, b in r.files.items()}
    for name in ("checksums.txt", "signature.sig"):
        if name in r.files:
            r.meta[name] = r.files.pop(name)
    return r


def check_sql(path: str, text: str) -> list[str]:
    errs = []
    for raw in filter(str.strip, text.split(";")):
        stmt = raw.strip()
        if stmt.startswith("--") and "\n" not in stmt:
            continue
        if FTS5.match(stmt):
            continue
        try:
            parsed = [s for s in sqlglot.parse(stmt, read="sqlite") if s is not None]
        except sqlglot.errors.ParseError:
            errs.append(f"{path}: 해석 불가 SQL — DDL 만 허용")
            continue
        for s in parsed:
            if not isinstance(s, DDL):
                errs.append(f"{path}: DDL 만 허용 — {type(s).__name__} 거부")
    return errs


def inspect(r: GateResult) -> GateResult:
    """추출 후 내용 검사. errors 가 하나라도 있으면 등록 거부."""
    if not r.ok:
        return r
    if "agent.yaml" not in r.files:
        if any(p.endswith("-meta.json") for p in r.files):
            r.errors.append("v1 flat zip — `plaza convert-v1` 로 agent.yaml 생성 후 재포장 필요")
        else:
            r.errors.append("agent.yaml 없음")
        return r
    m, errs = validate_text(r.files["agent.yaml"].decode("utf-8", "replace"))
    r.errors += [f"agent.yaml {e}" for e in errs]
    if m is None or errs:
        return r
    r.manifest = m
    if m["spec"]["type"] != "federation":
        for need in ("compose.yaml", "backend/Dockerfile", "backend/main.py"):
            if need not in r.files:
                r.errors.append(f"필수 파일 없음: {need}")
    for path, body in r.files.items():
        text = body.decode("utf-8", "ignore")
        if path.endswith(".py"):
            try:
                ast.parse(text, filename=path)
            except SyntaxError as exc:
                r.errors.append(f"Python 문법 오류: {path}:{exc.lineno}")
            for pat, why in WARN.items():
                if re.search(pat, text):
                    r.warnings.append(f"{why}: {path}")
        if path.endswith(".sql"):
            r.errors += check_sql(path, text)
        if path.endswith((".py", ".yaml", ".yml", ".json", ".sh", ".toml")) or path.endswith("Dockerfile"):
            for pat, why in BLOCK.items():
                if re.search(pat, text):
                    r.errors.append(f"금지 항목({why}): {path}")
    return r
