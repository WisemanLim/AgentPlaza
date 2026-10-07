// C01 채팅(AG-UI SSE) · C02 세션 · C05 스코프 채팅. 도구 호출·승인 카드는 대화 안에 인라인(DP6), 승인은 1급(DP8).
// P1: C03 첨부(문서·이미지, D3-04) · C06 지식 선택 + 인용 카드(D3-06) · 기억 명령(D3-05)
import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { api, authHeaders } from "../api";
import type { Collection } from "./knowledge";
import { errorText, fmtTime, useApi, useToast } from "../components/ui";
import { t } from "../i18n";
import { navigate, query, usePath } from "../router";
import { type AgEvent, readEvents } from "../sse";

type Session = { id: string; title: string; agent_scope: string | null; updated_at: string; messages?: number };
type Pending = { approval_id: string; capability: string; agent: string; args: unknown; expires_at: string };
type Item =
  | { kind: "user"; text: string; id: string }
  | { kind: "assistant"; text: string; id: string }
  | { kind: "tool"; id: string; name: string; args: string; result?: string; ok?: boolean }
  | { kind: "approval"; id: string; pending: Pending; state?: "approved" | "rejected" | "busy" }
  | { kind: "note"; id: string; text: string; tone: "warn" | "info" | "danger" }
  | { kind: "citations"; id: string; sources: { n: number; document: string; collection: string; score: number; snippet: string }[] };
type Attachment = { id: string; filename: string; kind: string };

let seq = 0;
const uid = () => `i${++seq}`;

function fromHistory(messages: { role: string; kind: string; content: string; meta: { pending?: Pending } }[]): Item[] {
  return messages.flatMap((m): Item[] => {
    if (m.kind === "approval" && m.meta?.pending) return [{ kind: "approval", id: uid(), pending: m.meta.pending }];
    if (m.kind === "error") return [{ kind: "note", id: uid(), text: m.content, tone: "danger" }];
    return [m.role === "user" ? { kind: "user", id: uid(), text: m.content } : { kind: "assistant", id: uid(), text: m.content }];
  });
}

export function ChatPage() {
  const path = usePath();
  const params = query(path);
  const scope = params.get("scope");
  const toast = useToast();
  const sessions = useApi<Session[]>("/api/sessions");
  const [sid, setSid] = useState<string | null>(params.get("session"));
  const [items, setItems] = useState<Item[]>([]);
  const [text, setText] = useState("");
  const [dataClass, setDataClass] = useState("L2");
  const [busy, setBusy] = useState(false);
  const [files, setFiles] = useState<Attachment[]>([]);
  const [kbSel, setKbSel] = useState<string[]>([]);
  const collections = useApi<Collection[]>("/api/kb/collections");
  const abort = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const fromStream = useRef(false); // 스트림이 만든 세션으로 전환할 때는 이력을 다시 불러오지 않는다(진행 중 항목 보존)

  useEffect(() => {
    if (fromStream.current) { fromStream.current = false; return; }
    if (!sid) { setItems([]); return; }
    api<{ messages: Parameters<typeof fromHistory>[0] }>(`/api/sessions/${sid}`)
      .then((s) => setItems(fromHistory(s.messages))).catch((e) => toast(errorText(e), "error"));
  }, [sid, toast]);
  useEffect(() => { bottom.current?.scrollIntoView({ block: "end" }); }, [items]);

  const apply = (ev: AgEvent, assistantId: { current: string | null }) => {
    // 부수효과(세션 전환·ID 생성)는 업데이터 밖에서 — 업데이터는 순수 함수로 유지(StrictMode 이중 호출 안전)
    const v = (ev.value ?? {}) as Record<string, unknown>;
    if (ev.type === "CUSTOM" && ev.name === "session") {
      if (String(v.id) !== sid) { fromStream.current = true; setSid(String(v.id)); }
      sessions.reload();
      return;
    }
    const newId = uid();
    if (ev.type === "TEXT_MESSAGE_START") assistantId.current = newId;
    const target = assistantId.current;
    setItems((xs) => {
      const next = [...xs];
      const find = (id: string) => next.findIndex((x) => x.id === id);
      switch (ev.type) {
        case "CUSTOM":
          if (ev.name === "degraded") next.push({ kind: "note", id: newId, text: `${t("chat.degraded")} (${v.model})`, tone: "warn" });
          if (ev.name === "registry_miss") next.push({ kind: "note", id: newId, text: `${t("chat.miss")}: ${v.agent}.${v.capability}`, tone: "info" });
          if (ev.name === "mode" && ev.value === "llm-only") next.push({ kind: "note", id: newId, text: t("chat.llm_only"), tone: "info" });
          if (ev.name === "approval_required") next.push({ kind: "approval", id: newId, pending: v as unknown as Pending });
          if (ev.name === "guardrail") next.push({ kind: "note", id: newId, tone: v.action === "blocked" ? "danger" : "warn",
            text: `${t("chat.guardrail")}: ${String(v.input ?? v.result)}${v.action ? ` (${v.action})` : ""}` });
          if (ev.name === "review") next.push({ kind: "note", id: newId, tone: v.verdict === "pass" ? "info" : v.verdict === "block" ? "danger" : "warn",
            text: `${t("chat.review")}: ${String(v.verdict)} · ${String(v.reviewer ?? "")}` });
          if (ev.name === "policy_blocked") next.push({ kind: "note", id: newId, tone: "danger", text: `${t("chat.policy")}: ${String(v.reason)}` });
          if (ev.name === "citations") next.push({ kind: "citations", id: newId, sources: ev.value as Extract<Item, { kind: "citations" }>["sources"] });
          if (ev.name === "retry") next.push({ kind: "note", id: newId, tone: "warn", text: `${t("chat.retry")} ${String(v.step)} #${String(v.attempt)}` });
          if (ev.name === "compensation") next.push({ kind: "note", id: newId, tone: v.ok ? "info" : "danger",
            text: `${t("chat.compensation")}: ${String(v.step)} → ${String(v.capability)} ${v.ok ? "✓" : "✕"}` });
          break;
        case "TOOL_CALL_START": next.push({ kind: "tool", id: String(ev.toolCallId), name: String(ev.toolCallName), args: "" }); break;
        case "TOOL_CALL_ARGS": { const i = find(String(ev.toolCallId)); if (i >= 0) next[i] = { ...(next[i] as Extract<Item, { kind: "tool" }>), args: String(ev.delta) }; break; }
        case "TOOL_CALL_RESULT": {
          const i = find(String(ev.toolCallId));
          const r = JSON.parse(String(ev.content)) as { ok: boolean; result?: unknown; error?: unknown };
          if (i >= 0) next[i] = { ...(next[i] as Extract<Item, { kind: "tool" }>), ok: r.ok, result: JSON.stringify(r.ok ? r.result : r.error) };
          break;
        }
        case "TEXT_MESSAGE_START": next.push({ kind: "assistant", id: newId, text: "" }); break;
        case "TEXT_MESSAGE_CONTENT": {
          const i = target ? find(target) : -1;
          if (i >= 0) next[i] = { ...(next[i] as Extract<Item, { kind: "assistant" }>), text: (next[i] as { text: string }).text + String(ev.delta) };
          break;
        }
        case "RUN_ERROR": next.push({ kind: "note", id: newId, text: String(ev.message), tone: "danger" }); break;
      }
      return next;
    });
  };

  const send = async () => {
    const message = text.trim();
    if (!message || busy) return;
    setText(""); setBusy(true);
    const label = files.length ? `${message}\n📎 ${files.map((f) => f.filename).join(", ")}` : message;
    setItems((xs) => [...xs, { kind: "user", id: uid(), text: label }]);
    abort.current = new AbortController();
    const assistantId = { current: null as string | null };
    const cursor = { stream: "", seq: 0 }; // 재연결(NFR-P4): 마지막으로 받은 이벤트 번호
    const consume = async (res: Response) => {
      for await (const ev of readEvents(res)) {
        if (typeof ev.__seq === "number") cursor.seq = ev.__seq as number;
        if (ev.type === "CUSTOM" && ev.name === "stream") cursor.stream = String((ev.value as { id: string }).id);
        if (ev.type === "CUSTOM" && ev.name === "stream_end") return true;
        apply(ev, assistantId);
      }
      return false;
    };
    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST", signal: abort.current.signal,
        headers: authHeaders({ "content-type": "application/json", accept: "text/event-stream" }),
        body: JSON.stringify({ message, session_id: sid, agent_scope: scope, data_class: dataClass,
          attachments: files.map((f) => f.id), knowledge: kbSel }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? `HTTP ${res.status}`);
      let done = await consume(res);
      for (let tries = 0; !done && cursor.stream && tries < 5; tries++) { // 끊김 → 마지막 번호 다음부터 이어 받기
        setItems((xs) => [...xs, { kind: "note", id: uid(), text: t("chat.reconnecting"), tone: "info" }]);
        await new Promise((r) => setTimeout(r, 1000 * (tries + 1)));
        try {
          const again = await fetch(`/api/chat/streams/${cursor.stream}?after=${cursor.seq}`, { headers: authHeaders(), signal: abort.current.signal });
          if (again.ok) done = await consume(again);
        } catch (e) { if ((e as Error).name === "AbortError") throw e; }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") setItems((xs) => [...xs, { kind: "note", id: uid(), text: errorText(e), tone: "danger" }]);
    }
    setFiles([]);
    setBusy(false);
  };

  const attach = async (list: FileList | null) => {
    for (const f of Array.from(list ?? [])) {
      const form = new FormData();
      form.append("file", f);
      if (sid) form.append("session_id", sid);
      try { const r = await api<Attachment>("/api/files", { form, method: "POST" }); setFiles((xs) => [...xs, r]); }
      catch (e) { toast(`${f.name}: ${errorText(e)}`, "error"); }
    }
  };

  const decide = async (item: Extract<Item, { kind: "approval" }>, approve: boolean) => {
    setItems((xs) => xs.map((x) => (x.id === item.id ? { ...item, state: "busy" } : x)));
    try {
      const r = await api<{ answer: string | null; state: string }>(
        `/api/approvals/${item.pending.approval_id}/${approve ? "approve" : "reject"}`, { method: "POST", body: {} });
      setItems((xs) => [...xs.map((x) => (x.id === item.id ? { ...item, state: approve ? "approved" as const : "rejected" as const } : x)),
        { kind: "assistant" as const, id: uid(), text: r.answer ?? r.state }]);
    } catch (e) {
      toast(errorText(e), "error");
      setItems((xs) => xs.map((x) => (x.id === item.id ? { ...item, state: undefined } : x)));
    }
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); } // IME 조합 중 Enter 무시
  };

  return (
    <div className="chat">
      <aside className="sessions card stack" aria-label={t("chat.sessions")} style={{ overflowY: "auto" }}>
        <button className="btn primary" onClick={() => { setSid(null); navigate(scope ? `/chat?scope=${scope}` : "/chat"); }}>{t("chat.new")}</button>
        {(sessions.data ?? []).map((s) => (
          <button key={s.id} className="btn" aria-current={s.id === sid ? "true" : undefined}
            style={{ textAlign: "left", borderColor: s.id === sid ? "var(--primary)" : undefined }} onClick={() => setSid(s.id)}>
            <div>{s.title}</div><div className="sub" style={{ fontSize: 12 }}>{fmtTime(s.updated_at)}{s.agent_scope ? ` · ${s.agent_scope}` : ""}</div>
          </button>
        ))}
      </aside>
      <section className="thread card" aria-label={t("chat.title")}>
        <div className="row" style={{ paddingBottom: 8 }}>
          <h1 style={{ margin: 0, fontSize: 18 }}>{t("chat.title")}</h1>
          {scope && <span className="badge info">{t("chat.scope")}: {scope}</span>}
          <label className="row sub" style={{ marginLeft: "auto" }}>{t("chat.data_class")}
            <select value={dataClass} onChange={(e) => setDataClass(e.target.value)} style={{ width: "auto" }}>
              {["L0", "L1", "L2", "L3"].map((l) => <option key={l}>{l}</option>)}
            </select></label>
        </div>
        <div className="messages" aria-live="polite" aria-busy={busy}>
          {items.map((x) => {
            if (x.kind === "user" || x.kind === "assistant") return <div key={x.id} className={`msg ${x.kind}`}>{x.text || "…"}</div>;
            if (x.kind === "note") return <div key={x.id} className={`badge ${x.tone}`} style={{ justifySelf: "start" }}>{x.text}</div>;
            if (x.kind === "citations") return (
              <div key={x.id} className="citations" role="group" aria-label={t("chat.sources")}>
                {x.sources.map((c) => <div key={c.n} className="citation"><b>[{c.n}] {c.document}</b> <span className="sub">{c.collection}</span>
                  <div className="sub">{c.snippet}</div></div>)}</div>);
            if (x.kind === "tool") return (
              <details key={x.id} className="toolcard">
                <summary>{t("chat.tool")}: <b>{x.name}</b> {x.ok === undefined ? "…" : x.ok ? "✓" : "✕"}</summary>
                <div className="mono">args {x.args}</div>{x.result && <div className="mono">→ {x.result.slice(0, 600)}</div>}
              </details>
            );
            return (
              <div key={x.id} className="approvalcard stack" role="group" aria-label={t("chat.approval")}>
                <b>⚠ {t("chat.approval")}: {x.pending.agent}.{x.pending.capability}</b>
                <span className="mono">{JSON.stringify(x.pending.args)}</span>
                <span className="sub">{t("approvals.expires")} {fmtTime(x.pending.expires_at)}</span>
                {x.state === "approved" || x.state === "rejected" ? <span className={`badge ${x.state === "approved" ? "ok" : "danger"}`}>{x.state}</span> : (
                  <div className="row">
                    <button className="btn primary" disabled={x.state === "busy"} onClick={() => decide(x, true)}>{t("chat.approve")}</button>
                    <button className="btn" disabled={x.state === "busy"} onClick={() => decide(x, false)}>{t("chat.reject")}</button>
                  </div>
                )}
              </div>
            );
          })}
          <div ref={bottom} />
        </div>
        {(files.length > 0 || (collections.data ?? []).length > 0) && <div className="row" style={{ paddingTop: 6 }}>
          {files.map((f) => <span key={f.id} className="badge info">{f.kind === "image" ? "🖼" : "📄"} {f.filename}
            <button type="button" className="btn" aria-label={`${t("common.delete")} ${f.filename}`} style={{ padding: "0 6px", marginLeft: 4 }}
              onClick={() => setFiles((xs) => xs.filter((y) => y.id !== f.id))}>×</button></span>)}
          {(collections.data ?? []).length > 0 && <details className="kbpick"><summary>{t("chat.knowledge")} {kbSel.length ? `(${kbSel.length})` : ""}</summary>
            {(collections.data ?? []).map((c) => <label key={c.id} className="row"><input type="checkbox" style={{ width: "auto" }} checked={kbSel.includes(c.id)}
              onChange={() => setKbSel((xs) => xs.includes(c.id) ? xs.filter((y) => y !== c.id) : [...xs, c.id])} />{c.name}</label>)}</details>}
        </div>}
        <form className="composer" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <label className="btn" style={{ alignSelf: "stretch", display: "grid", placeItems: "center" }}>📎<span className="sr-only">{t("chat.attach")}</span>
            <input type="file" multiple hidden accept=".txt,.md,.csv,.json,.html,.pdf,.png,.jpg,.jpeg,.webp,.gif" onChange={(e) => { attach(e.target.files); e.target.value = ""; }} /></label>
          <label className="sr-only" htmlFor="composer">{t("chat.placeholder")}</label>
          <textarea id="composer" rows={2} placeholder={t("chat.placeholder")} value={text} onChange={(e) => setText(e.target.value)} onKeyDown={onKey} />
          {busy ? <button type="button" className="btn" onClick={() => abort.current?.abort()}>{t("chat.stop")}</button>
            : <button className="btn primary" disabled={!text.trim()}>{t("chat.send")}</button>}
        </form>
      </section>
    </div>
  );
}
