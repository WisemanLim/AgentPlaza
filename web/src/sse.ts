// AG-UI 이벤트 SSE 파서: 'data: {json}' 프레임을 빈 줄로 구분한다. 순수 함수(parseFrames)는 시험한다.
export type AgEvent = { type: string; [k: string]: unknown };

export function parseFrames(buffer: string): { events: AgEvent[]; rest: string } {
  const events: AgEvent[] = [];
  const parts = buffer.split(/\r?\n\r?\n/);
  const rest = parts.pop() ?? "";
  for (const frame of parts) {
    const lines = frame.split(/\r?\n/);
    const data = lines.filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trimStart()).join("\n");
    if (!data || data === "[DONE]") continue;
    const id = lines.find((l) => l.startsWith("id:"))?.slice(3).trim();
    try { const ev = JSON.parse(data); if (id) ev.__seq = Number(id); events.push(ev); } catch { /* 깨진 프레임은 버린다 */ }
  }
  return { events, rest };
}

export async function* readEvents(res: Response): AsyncGenerator<AgEvent> {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseFrames(buffer);
    buffer = rest;
    yield* events;
  }
  const { events } = parseFrames(buffer + "\n\n");
  yield* events;
}
