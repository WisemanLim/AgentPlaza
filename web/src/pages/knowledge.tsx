// G01 지식 컬렉션 · G02 문서 업로드·인덱싱(D3-06) · C04 메모리·맞춤지침(D3-05, 삭제권)
import { type FormEvent, useState } from "react";
import type { Me } from "../App";
import { api } from "../api";
import { Badge, errorText, fmtTime, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

export type Collection = { id: string; name: string; description: string | null; owner: string; shared: boolean;
  data_class: string; documents: number };
type Doc = { id: string; filename: string; mime: string; bytes: number; status: string; error: string | null; chunks: number; created_at: string };
type Hit = { n: number; score: number; text: string; document: string; collection: string };

const isAdmin = (me: Me) => me.role === "admin" || me.role === "supervisor";

export function KnowledgePage({ me }: { me: Me }) {
  const cols = useApi<Collection[]>("/api/kb/collections");
  const toast = useToast();
  const [sel, setSel] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", shared: false, data_class: "L2" });
  const create = async (e: FormEvent) => {
    e.preventDefault();
    try { const c = await api<Collection>("/api/kb/collections", { body: form }); setForm({ ...form, name: "" }); cols.reload(); setSel(c.id); }
    catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <h1>{t("kb.title")}</h1>
      <form className="row card" onSubmit={create}>
        <input required placeholder={t("kb.name")} aria-label={t("kb.name")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ maxWidth: 260 }} />
        <label className="row sub">{t("chat.data_class")}
          <select value={form.data_class} onChange={(e) => setForm({ ...form, data_class: e.target.value })} style={{ width: "auto" }}>
            {["L0", "L1", "L2", "L3"].map((l) => <option key={l}>{l}</option>)}</select></label>
        {isAdmin(me) && <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={form.shared} onChange={(e) => setForm({ ...form, shared: e.target.checked })} />{t("kb.shared")}</label>}
        <button className="btn primary">{t("kb.create")}</button>
      </form>
      <StateView q={cols} empty={(d) => !d.length}>{(d) => (
        <div className="grid">{d.map((c) => (
          <button key={c.id} className="card stack" style={{ textAlign: "left", borderColor: sel === c.id ? "var(--primary)" : undefined }}
            aria-pressed={sel === c.id} onClick={() => setSel(c.id)}>
            <b>{c.name}</b>
            <span className="row">{c.shared && <Badge value="info" label={t("kb.shared")} />}<Badge value="ok" label={c.data_class} />
              <span className="sub">{t("kb.documents")} {c.documents}</span></span>
          </button>))}</div>)}</StateView>
      {sel && <CollectionDetail id={sel} onChange={cols.reload} onDeleted={() => { setSel(null); cols.reload(); }} />}
    </div>
  );
}

function CollectionDetail({ id, onChange, onDeleted }: { id: string; onChange: () => void; onDeleted: () => void }) {
  const docs = useApi<Doc[]>(`/api/kb/collections/${id}/documents`);
  const toast = useToast();
  const [files, setFiles] = useState<FileList | null>(null);
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[] | null>(null);
  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!files?.length) return;
    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f));
    setBusy(true);
    try { const r = await api<Doc[]>(`/api/kb/collections/${id}/documents`, { form, method: "POST" });
      r.filter((d) => d.status !== "ready").forEach((d) => toast(`${d.filename}: ${d.error}`, "error")); docs.reload(); onChange(); }
    catch (x) { toast(errorText(x), "error"); }
    setBusy(false);
  };
  const search = async (e: FormEvent) => {
    e.preventDefault();
    try { setHits((await api<{ results: Hit[] }>("/api/kb/search", { body: { collections: [id], query: q } })).results); }
    catch (x) { toast(errorText(x), "error"); }
  };
  const remove = async () => {
    if (!window.confirm(t("kb.delete_confirm"))) return;
    try { await api(`/api/kb/collections/${id}`, { method: "DELETE" }); onDeleted(); } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <section className="card stack">
      <div className="row"><h2 style={{ marginRight: "auto" }}>{t("kb.documents")}</h2><button className="btn danger" onClick={remove}>{t("common.delete")}</button></div>
      <form className="row" onSubmit={upload}>
        <label className="sr-only" htmlFor="kbfiles">{t("kb.upload")}</label>
        <input id="kbfiles" type="file" multiple accept=".txt,.md,.csv,.json,.html,.pdf" onChange={(e) => setFiles(e.target.files)} style={{ maxWidth: 360 }} />
        <button className="btn primary" disabled={busy || !files?.length}>{busy ? t("common.loading") : t("kb.upload")}</button>
      </form>
      <StateView q={docs} empty={(d) => !d.length}>{(d) => (
        <table className="responsive"><thead><tr><th>{t("kb.file")}</th><th>{t("common.status")}</th><th>{t("kb.chunks")}</th><th /></tr></thead>
          <tbody>{d.map((x) => (
            <tr key={x.id}><td>{x.filename}<div className="sub">{fmtTime(x.created_at)} · {Math.ceil(x.bytes / 1024)}KB</div></td>
              <td><Badge value={x.status === "ready" ? "ok" : "failed"} label={x.status} />{x.error && <div className="sub">{x.error}</div>}</td>
              <td className="mono">{x.chunks}</td>
              <td><button className="btn" onClick={() => api(`/api/kb/collections/${id}/documents/${x.id}`, { method: "DELETE" }).then(() => { docs.reload(); onChange(); })}>{t("common.delete")}</button></td></tr>))}
          </tbody></table>)}</StateView>
      <form className="row" onSubmit={search} role="search">
        <label className="sr-only" htmlFor="kbq">{t("kb.search")}</label>
        <input id="kbq" placeholder={t("kb.search")} value={q} onChange={(e) => setQ(e.target.value)} style={{ flex: 1, width: "auto" }} />
        <button className="btn" disabled={!q.trim()}>{t("common.search")}</button>
      </form>
      {hits && <ol className="stack" style={{ margin: 0 }}>{hits.map((h) => (
        <li key={h.n} className="citation"><b>[{h.n}] {h.document}</b> <span className="sub mono">{h.score.toFixed(3)}</span><div className="sub">{h.text.slice(0, 300)}</div></li>))}</ol>}
    </section>
  );
}

type Mem = { id: number; kind: string; content: string; source: string; created_at: string };

export function MemoryPage() {
  const q = useApi<{ enabled: boolean; items: Mem[] }>("/api/me/memories");
  const toast = useToast();
  const [text, setText] = useState("");
  const [kind, setKind] = useState("fact");
  const add = async (e: FormEvent) => {
    e.preventDefault();
    try { await api("/api/me/memories", { body: { kind, content: text } }); setText(""); q.reload(); } catch (x) { toast(errorText(x), "error"); }
  };
  const act = async (f: () => Promise<unknown>) => { try { await f(); q.reload(); } catch (x) { toast(errorText(x), "error"); } };
  return (
    <StateView q={q}>{(m) => (
      <div className="stack" style={{ maxWidth: 760 }}>
        <h1>{t("mem.title")}</h1>
        <p className="sub">{t("mem.hint")}</p>
        <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={m.enabled}
          onChange={() => act(() => api("/api/me/memory-settings", { method: "PUT", body: { memory_enabled: !m.enabled } }))} />{t("mem.enabled")}</label>
        <form className="card stack" onSubmit={add}>
          <div className="row">
            <select aria-label={t("mem.kind")} value={kind} onChange={(e) => setKind(e.target.value)} style={{ width: "auto" }}>
              <option value="instruction">{t("mem.instruction")}</option><option value="fact">{t("mem.fact")}</option></select>
            <input required aria-label={t("mem.content")} placeholder={t("mem.content")} value={text} onChange={(e) => setText(e.target.value)} style={{ flex: 1, width: "auto" }} />
            <button className="btn primary">{t("mem.add")}</button>
          </div>
        </form>
        <section className="card"><StateView q={q} empty={(d) => !d.items.length}>{(d) => (
          <ul className="stack" style={{ margin: 0, paddingLeft: 18 }}>{d.items.map((x) => (
            <li key={x.id} className="row"><Badge value={x.kind === "instruction" ? "info" : "ok"} label={t(`mem.${x.kind}`)} />
              <span style={{ flex: 1 }}>{x.content}</span><span className="sub">{x.source} · {fmtTime(x.created_at)}</span>
              <button className="btn" onClick={() => act(() => api(`/api/me/memories/${x.id}`, { method: "DELETE" }))}>{t("common.delete")}</button></li>))}</ul>
        )}</StateView></section>
        <div><button className="btn danger" onClick={() => window.confirm(t("mem.purge_confirm")) && act(() => api("/api/me/memories", { method: "DELETE" }))}>{t("mem.purge")}</button></div>
      </div>
    )}</StateView>
  );
}
