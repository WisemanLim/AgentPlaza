#!/usr/bin/env python3
"""시험용 가짜 ACP 에이전트 — initialize·session/new·session/prompt 에 답하고, 응답 전에 권한 요청을 한 번 보낸다."""
import json
import sys


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    msg = json.loads(line)
    if msg.get("method") == "initialize":
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {"protocolVersion": 1, "agentCapabilities": {}}})
    elif msg.get("method") == "session/new":
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {"sessionId": "s-1"}})
    elif msg.get("method") == "session/prompt":
        text = msg["params"]["prompt"][0]["text"].strip().splitlines()[-1]
        send({"jsonrpc": "2.0", "id": 900, "method": "session/request_permission",
              "params": {"sessionId": "s-1", "toolCall": {"title": "write file"}, "options": []}})
        decision = json.loads(sys.stdin.readline())
        denied = decision.get("result", {}).get("outcome", {}).get("outcome") == "cancelled"
        for word in ["fake-acp:", *text.split(), "(permission denied)" if denied else "(permission granted)"]:
            send({"jsonrpc": "2.0", "method": "session/update",
                  "params": {"sessionId": "s-1", "update": {"sessionUpdate": "agent_message_chunk",
                                                            "content": {"type": "text", "text": word + " "}}}})
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {"stopReason": "end_turn"}})
