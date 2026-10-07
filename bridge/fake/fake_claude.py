#!/usr/bin/env python3
"""시험용 가짜 CLI — claude -p --output-format stream-json 형식을 흉내 낸다(프롬프트의 마지막 줄을 되풀이)."""
import json
import sys

prompt = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
last = prompt.strip().splitlines()[-1] if prompt.strip() else ""
print(json.dumps({"type": "system", "subtype": "init", "session_id": "fake"}))
for word in ["fake-claude:", *last.split()]:
    print(json.dumps({"type": "stream_event", "event": {"type": "content_block_delta",
                                                          "delta": {"type": "text_delta", "text": word + " "}}}))
print(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": ""}]}}))
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": f"fake-claude: {last}"}))
