import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { dict } from "../i18n";
import { match, query } from "../router";
import { parseFrames } from "../sse";

describe("SSE 파서 (AG-UI 프레임)", () => {
  it("완결 프레임만 파싱하고 나머지는 보존", () => {
    const { events, rest } = parseFrames('data: {"type":"RUN_STARTED"}\n\ndata: {"type":"TEXT_MESSAGE_CONTENT","delta":"안"}\n\ndata: {"ty');
    expect(events.map((e) => e.type)).toEqual(["RUN_STARTED", "TEXT_MESSAGE_CONTENT"]);
    expect(rest).toBe('data: {"ty');
  });
  it("SSE id 를 __seq 로(재연결 커서, NFR-P4)", () => {
    const { events } = parseFrames('id: 7\ndata: {"type":"RUN_STARTED"}\n\ndata: {"type":"CUSTOM"}\n\n');
    expect(events).toEqual([{ type: "RUN_STARTED", __seq: 7 }, { type: "CUSTOM" }]);
  });
  it("[DONE]·깨진 JSON·CRLF 처리", () => {
    const { events } = parseFrames('data: [DONE]\r\n\r\ndata: {bad\n\ndata: {"type":"RUN_FINISHED"}\r\n\r\n');
    expect(events).toEqual([{ type: "RUN_FINISHED" }]);
  });
});

describe("라우터", () => {
  it("경로 파라미터·쿼리", () => {
    expect(match("/agents/:id", "/agents/board?x=1")).toEqual({ id: "board" });
    expect(match("/agents/:id", "/agents")).toBeNull();
    expect(query("/chat?scope=calc").get("scope")).toBe("calc");
  });
});

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return f === "__tests__" ? [] : sources(p);
    return /\.tsx?$/.test(f) ? [p] : [];
  });
}

describe("i18n (NFR-U3: 키 커버리지 100%)", () => {
  it("ko 와 en 키 집합이 같다", () => {
    expect(Object.keys(dict.en).sort()).toEqual(Object.keys(dict.ko).sort());
  });
  it("소스의 t(\"…\") 리터럴 키가 모두 사전에 있다(화면에 키 이름 노출 금지)", () => {
    const used = new Set<string>();
    for (const f of sources(join(__dirname, ".."))) {
      for (const m of readFileSync(f, "utf8").matchAll(/\bt\("([a-z_.]+)"\)/g)) used.add(m[1]);
    }
    const missing = [...used].filter((k) => !(k in dict.ko));
    expect(missing).toEqual([]);
    expect(used.size).toBeGreaterThan(80);
  });
  it("동적 키(dash.*·profile.*)도 사전에 있다", () => {
    for (const k of ["agents", "approvals", "llm", "installs", "sessions", "runtime"]) expect(dict.ko[`dash.${k}`]).toBeTruthy();
    for (const k of ["light", "dark", "system"]) expect(dict.en[`profile.${k}`]).toBeTruthy();
  });
});
