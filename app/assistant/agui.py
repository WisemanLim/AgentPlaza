"""AG-UI 이벤트 검사 (D7-06, NFR-P4): 우리가 내보내는 이벤트가 표준 이름·필수 필드·순서를 지키는지 확인한다.

AG-UI 1.0 의 이벤트 가운데 플랫폼이 쓰는 부분집합을 검사한다(SUBAGENT_*·THINKING_* 등은 내보내지 않는다).
순서 규칙: 실행(run)은 RUN_STARTED 로 시작해 RUN_FINISHED|RUN_ERROR 로 끝난다 · 텍스트는 START→CONTENT*→END ·
도구는 START→ARGS*→END→RESULT · CONTENT 의 delta 는 비어 있지 않다. 실행 밖 CUSTOM(session·stream·stream_end)은 허용.
"""
REQUIRED = {
    "RUN_STARTED": {"threadId", "runId"}, "RUN_FINISHED": {"threadId", "runId"}, "RUN_ERROR": {"message"},
    "STEP_STARTED": {"stepName"}, "STEP_FINISHED": {"stepName"},
    "TEXT_MESSAGE_START": {"messageId", "role"}, "TEXT_MESSAGE_CONTENT": {"messageId", "delta"},
    "TEXT_MESSAGE_END": {"messageId"},
    "TOOL_CALL_START": {"toolCallId", "toolCallName"}, "TOOL_CALL_ARGS": {"toolCallId", "delta"},
    "TOOL_CALL_END": {"toolCallId"}, "TOOL_CALL_RESULT": {"toolCallId", "messageId", "content"},
    "STATE_SNAPSHOT": {"snapshot"}, "STATE_DELTA": {"delta"}, "MESSAGES_SNAPSHOT": {"messages"},
    "CUSTOM": {"name"}, "RAW": {"event"},
}


def check(events: list[dict]) -> list[str]:
    errs: list[str] = []
    in_run = False
    texts: dict[str, str] = {}
    tools: dict[str, str] = {}
    for i, ev in enumerate(events):
        t = ev.get("type")
        if t not in REQUIRED:
            errs.append(f"#{i} 알 수 없는 type {t}")
            continue
        missing = REQUIRED[t] - set(ev)
        if missing:
            errs.append(f"#{i} {t} 필수 필드 없음 {sorted(missing)}")
        if t == "RUN_STARTED":
            if in_run:
                errs.append(f"#{i} RUN_STARTED 중첩")
            in_run = True
            continue
        if t in ("RUN_FINISHED", "RUN_ERROR"):
            if not in_run and t == "RUN_FINISHED":
                errs.append(f"#{i} RUN_FINISHED 가 RUN_STARTED 없이")
            open_msgs = [m for m, s in texts.items() if s != "end"]
            open_tools = [c for c, s in tools.items() if s in ("start", "args")]
            if t == "RUN_FINISHED" and (open_msgs or open_tools):
                errs.append(f"#{i} 닫히지 않은 메시지·도구 {open_msgs + open_tools}")
            in_run = False
            continue
        if not in_run and t != "CUSTOM":
            errs.append(f"#{i} {t} 가 실행 밖에서")
        if t == "TEXT_MESSAGE_START":
            texts[ev["messageId"]] = "start"
        elif t == "TEXT_MESSAGE_CONTENT":
            if texts.get(ev.get("messageId")) not in ("start", "content"):
                errs.append(f"#{i} CONTENT 가 START 없이")
            if not ev.get("delta"):
                errs.append(f"#{i} 빈 delta")
            texts[ev.get("messageId")] = "content"
        elif t == "TEXT_MESSAGE_END":
            if texts.get(ev.get("messageId")) not in ("start", "content"):
                errs.append(f"#{i} END 가 START 없이")
            texts[ev.get("messageId")] = "end"
        elif t == "TOOL_CALL_START":
            tools[ev["toolCallId"]] = "start"
        elif t == "TOOL_CALL_ARGS":
            if tools.get(ev.get("toolCallId")) not in ("start", "args"):
                errs.append(f"#{i} TOOL_CALL_ARGS 순서")
            tools[ev.get("toolCallId")] = "args"
        elif t == "TOOL_CALL_END":
            if tools.get(ev.get("toolCallId")) not in ("start", "args"):
                errs.append(f"#{i} TOOL_CALL_END 순서")
            tools[ev.get("toolCallId")] = "end"
        elif t == "TOOL_CALL_RESULT":
            if tools.get(ev.get("toolCallId")) != "end":
                errs.append(f"#{i} TOOL_CALL_RESULT 가 END 전에")
            tools[ev.get("toolCallId")] = "result"
    return errs
