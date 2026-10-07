"""CLI 에이전트 브리지 — Claude Code·Codex·Gemini CLI·OpenClaw 같은 에이전트형 CLI 를 OpenAI 호환 /v1 로 노출한다.

플랫폼은 이 서비스를 'OpenAI 호환 서버'(D1-02)로 등록해 별칭·폴백·데이터 등급·계량을 그대로 적용한다.
CLI 는 공급사 클라우드로 나가므로 등록 시 local=false — L2 이상 데이터는 정책상 이 백엔드로 가지 않는다.

프로토콜
  ndjson  한 줄 하나의 JSON 이벤트(claude -p --output-format stream-json · codex exec --json · gemini --output-format stream-json)
  acp     Agent Client Protocol(JSON-RPC 2.0, stdio): initialize → session/new → session/prompt, session/update 알림으로 조각 수신.
          권한 요청(session/request_permission)·파일/터미널 요청은 모두 거절한다(브리지는 대화만 중계).
설정: CLI_BRIDGE_BACKENDS='{"claude": {"cmd": ["claude","-p","{prompt}","--output-format","stream-json","--verbose"],
                             "protocol": "ndjson"}, "gemini": {"cmd": ["gemini","--experimental-acp"], "protocol": "acp"}}'
      BRIDGE_TOKEN(필수, 플랫폼만 호출) · BRIDGE_TIMEOUT(초, 기본 300). 표준 라이브러리만 쓴다.
"""
import hmac
import json
import os
import queue
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ.get("BRIDGE_TOKEN", "")
TIMEOUT = float(os.environ.get("BRIDGE_TIMEOUT", "300"))


class BridgeError(Exception):
    pass


def backends() -> dict:
    return json.loads(os.environ.get("CLI_BRIDGE_BACKENDS", "{}") or "{}")


def prompt_of(messages: list[dict]) -> str:
    """OpenAI messages → CLI 한 번 호출할 프롬프트(시스템·이전 대화 포함)."""
    def text(c):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict)) if isinstance(c, list) else str(c or "")
    parts = [f"[{m['role']}]\n{text(m.get('content'))}" for m in messages if m.get("role") in ("system", "user", "assistant")]
    return "\n\n".join(parts)


def text_from_event(ev: dict) -> tuple[str, str | None]:
    """NDJSON 이벤트 → (증분 텍스트, 최종 텍스트|None). 알려진 CLI 형식을 모두 받아들인다."""
    t = ev.get("type")
    if t == "stream_event":  # claude --include-partial-messages
        d = (ev.get("event") or {}).get("delta") or {}
        return (d.get("text", "") if d.get("type") == "text_delta" else ""), None
    if t == "assistant" and isinstance(ev.get("message"), dict):  # claude stream-json
        return "".join(c.get("text", "") for c in ev["message"].get("content", []) if c.get("type") == "text"), None
    if t == "result":  # claude·gemini 최종
        r = ev.get("result")
        if ev.get("is_error"):
            raise BridgeError(str(r or ev.get("error") or "cli error"))
        return "", (r if isinstance(r, str) else None)
    if t in ("item.completed", "item.updated") and (ev.get("item") or {}).get("type") in ("agent_message", "assistant_message"):
        return (ev["item"].get("text") or ""), None  # codex exec --json
    if isinstance(ev.get("msg"), dict) and ev["msg"].get("type") == "agent_message":
        return ev["msg"].get("message", ""), None  # codex 구형
    if t == "message" and ev.get("role") == "assistant":  # gemini stream-json
        return str(ev.get("content") or ""), None
    if isinstance(ev.get("text"), str) and t in (None, "text", "delta"):
        return ev["text"], None
    return "", None


def _argv(cmd: list[str], prompt: str) -> tuple[list[str], bool]:
    if any("{prompt}" in a for a in cmd):
        return [a.replace("{prompt}", prompt) for a in cmd], False
    return list(cmd), True  # 자리표시자가 없으면 stdin 으로


def run_ndjson(cmd: list[str], prompt: str, timeout: float = TIMEOUT) -> Iterator[str]:
    argv, use_stdin = _argv(cmd, prompt)
    with tempfile.TemporaryDirectory() as cwd:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        if use_stdin:
            proc.stdin.write(prompt)
        proc.stdin.close()
        deadline, streamed, final = time.monotonic() + timeout, [], None
        for line in proc.stdout:
            if time.monotonic() > deadline:
                proc.kill()
                raise BridgeError("timeout")
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            delta, fin = text_from_event(ev)
            if delta:
                streamed.append(delta)
                yield delta
            final = fin if fin is not None else final
        rc = proc.wait(timeout=10)
        if rc != 0 and not streamed and final is None:
            raise BridgeError(f"exit {rc}: {proc.stderr.read()[-300:]}")
        if final and not streamed:  # 증분 없이 결과만 주는 CLI
            yield final


def run_acp(cmd: list[str], prompt: str, timeout: float = TIMEOUT) -> Iterator[str]:
    """ACP 클라이언트(브리지) — 에이전트 프로세스와 JSON-RPC 를 주고받는다."""
    with tempfile.TemporaryDirectory() as cwd:
        proc = subprocess.Popen(list(cmd), cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, bufsize=1)
        lines: queue.Queue = queue.Queue()
        threading.Thread(target=lambda: [lines.put(ln) for ln in proc.stdout] + [lines.put(None)], daemon=True).start()
        seq = [0]

        def send(method: str | None, params: dict | None = None, *, reply_to=None, result=None, error=None) -> int:
            if reply_to is not None:
                msg = {"jsonrpc": "2.0", "id": reply_to, **({"error": error} if error else {"result": result})}
            else:
                seq[0] += 1
                msg = {"jsonrpc": "2.0", "id": seq[0], "method": method, "params": params or {}}
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
            return seq[0]

        deadline = time.monotonic() + timeout

        def until(rid: int) -> Iterator[dict | str]:
            while True:
                line = lines.get(timeout=max(0.1, deadline - time.monotonic()))
                if line is None:
                    raise BridgeError("acp agent exited")
                msg = json.loads(line)
                if msg.get("id") == rid and "method" not in msg:
                    if msg.get("error"):
                        raise BridgeError(f"acp error: {msg['error'].get('message')}")
                    yield msg.get("result") or {}
                    return
                if msg.get("method") == "session/update":
                    upd = (msg.get("params") or {}).get("update") or {}
                    if upd.get("sessionUpdate") == "agent_message_chunk" and (upd.get("content") or {}).get("type") == "text":
                        yield upd["content"]["text"]
                elif "method" in msg and "id" in msg:  # 에이전트 → 클라이언트 요청: 모두 거절
                    if msg["method"] == "session/request_permission":
                        send(None, reply_to=msg["id"], result={"outcome": {"outcome": "cancelled"}})
                    else:
                        send(None, reply_to=msg["id"], error={"code": -32601, "message": "not supported by bridge"})
        try:
            list(until(send("initialize", {"protocolVersion": 1, "clientCapabilities": {
                "fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False}})))
            sid = next(r for r in until(send("session/new", {"cwd": cwd, "mcpServers": []})) if isinstance(r, dict))["sessionId"]
            for item in until(send("session/prompt", {"sessionId": sid, "prompt": [{"type": "text", "text": prompt}]})):
                if isinstance(item, str):
                    yield item
        except queue.Empty:
            raise BridgeError("timeout") from None
        finally:
            proc.kill()


def run(backend: dict, prompt: str) -> Iterator[str]:
    proto = backend.get("protocol", "ndjson")
    if proto == "acp":
        return run_acp(backend["cmd"], prompt)
    if proto == "ndjson":
        return run_ndjson(backend["cmd"], prompt)
    raise BridgeError(f"unknown protocol {proto}")


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth(self) -> bool:
        got = self.headers.get("authorization", "").removeprefix("Bearer ").strip()
        return bool(TOKEN) and hmac.compare_digest(got, TOKEN)

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            return self._json(200, {"status": "ok", "backends": sorted(backends())})
        if not self._auth():
            return self._json(401, {"error": {"message": "unauthorized"}})
        if self.path == "/v1/models":
            return self._json(200, {"object": "list", "data": [{"id": n, "object": "model", "owned_by": "cli-bridge"}
                                                              for n in sorted(backends())]})
        self._json(404, {"error": {"message": "not found"}})

    def do_POST(self):  # noqa: N802
        if not self._auth():
            return self._json(401, {"error": {"message": "unauthorized"}})
        if self.path != "/v1/chat/completions":
            return self._json(404, {"error": {"message": "not found"}})
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", "0") or 0)) or b"{}")
        backend = backends().get(body.get("model", ""))
        if backend is None:
            return self._json(404, {"error": {"message": f"unknown model {body.get('model')}"}})
        prompt = prompt_of(body.get("messages") or [])
        rid, created = f"chatcmpl-{uuid.uuid4().hex[:20]}", int(time.time())
        try:
            if not body.get("stream"):
                text = "".join(run(backend, prompt))
                return self._json(200, {"id": rid, "object": "chat.completion", "created": created, "model": body["model"],
                                        "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                                                     "finish_reason": "stop"}],
                                        "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(text) // 4}})
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()

            def frame(delta: dict, finish=None) -> bytes:
                return ("data: " + json.dumps({"id": rid, "object": "chat.completion.chunk", "created": created,
                                               "model": body["model"], "choices": [{"index": 0, "delta": delta,
                                                                                    "finish_reason": finish}]},
                                              ensure_ascii=False) + "\n\n").encode()
            self.wfile.write(frame({"role": "assistant"}))
            for piece in run(backend, prompt):
                self.wfile.write(frame({"content": piece}))
                self.wfile.flush()
            self.wfile.write(frame({}, "stop") + b"data: [DONE]\n\n")
        except BridgeError as exc:
            if not body.get("stream"):
                return self._json(502, {"error": {"message": str(exc)}})
            self.wfile.write(b"data: " + json.dumps({"error": {"message": str(exc)}}).encode() + b"\n\n")

    def log_message(self, fmt, *args):
        print(f"bridge {self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)


def serve(port: int = 8787) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("BRIDGE_TOKEN 필요 / required")
    serve(int(os.environ.get("PORT", "8787"))).serve_forever()
