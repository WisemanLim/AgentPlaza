// M02 LLM 관측(D10-04, 자체 경량): 비용·사용량 · 트레이스 목록·워터폴 · H01/H02 평가·플레이그라운드(D10-05)
import { type FormEvent, useState } from "react";
import { api } from "../api";
import { Badge, errorText, fmtTime, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

type Agg = { key: string; calls: number; tokens_in: number; tokens_out: number; cost: number; errors: number; fallbacks: number; p50_ms: number; p95_ms: number };
type Usage = { days: number; total: Agg; by_day: Agg[]; by_model: Agg[]; by_alias: Agg[]; by_agent: Agg[]; by_user: Agg[] };
type Span = { trace_id: string; span_id: string; parent_id: string | null; name: string; start: string; duration_ms: number; status: string;
  attributes: Record<string, unknown> };
type TraceRow = Span & { spans: number; errors: number; tools: string[]; models: string[]; tokens: number };

function AggTable({ rows, label }: { rows: Agg[]; label: string }) {
  const max = Math.max(1, ...rows.map((r) => r.calls));
  return (
    <table className="responsive"><thead><tr><th>{label}</th><th>{t("obs.calls")}</th><th>{t("obs.tokens")}</th><th>{t("obs.cost")}</th><th>p50/p95</th><th>{t("obs.errors")}</th></tr></thead>
      <tbody>{rows.slice(0, 10).map((r) => (
        <tr key={r.key}><td className="mono">{r.key}</td>
          <td><span className="bar" style={{ width: `${(r.calls / max) * 100}%` }} aria-hidden="true" /> {r.calls}</td>
          <td className="mono">{r.tokens_in + r.tokens_out}</td><td className="mono">${r.cost.toFixed(4)}</td>
          <td className="mono">{r.p50_ms}/{r.p95_ms}ms</td><td>{r.errors ? <Badge value="failed" label={String(r.errors)} /> : 0}{r.fallbacks ? <> · <Badge value="warn" label={`fb ${r.fallbacks}`} /></> : null}</td></tr>))}
      </tbody></table>
  );
}

export function ObservePage() {
  const [days, setDays] = useState(7);
  const usage = useApi<Usage>(`/api/obs/usage?days=${days}`);
  const traces = useApi<TraceRow[]>("/api/obs/traces?limit=30");
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="stack">
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("obs.title")}</h1>
        <label className="row sub">{t("obs.days")}<select value={days} onChange={(e) => setDays(Number(e.target.value))} style={{ width: "auto" }}>
          {[1, 7, 30, 90].map((d) => <option key={d} value={d}>{d}</option>)}</select></label></div>
      <StateView q={usage}>{(u) => (
        <div className="stack">
          <div className="grid">
            {[["obs.calls", u.total.calls], ["obs.tokens", (u.total.tokens_in ?? 0) + (u.total.tokens_out ?? 0)],
              ["obs.cost", `$${(u.total.cost ?? 0).toFixed(4)}`], ["p95", `${u.total.p95_ms ?? 0}ms`]].map(([k, v]) => (
              <div key={String(k)} className="card"><div className="sub">{String(k).startsWith("obs.") ? t(String(k)) : k}</div><b style={{ fontSize: 22 }}>{String(v)}</b></div>))}
          </div>
          <section className="card"><h2>{t("obs.by_model")}</h2><AggTable rows={u.by_model} label="model" /></section>
          <section className="card"><h2>{t("obs.by_agent")}</h2><AggTable rows={u.by_agent} label="agent" /></section>
          <section className="card"><h2>{t("obs.by_user")}</h2><AggTable rows={u.by_user} label="user" /></section>
        </div>)}</StateView>
      <section className="card stack"><h2>{t("obs.traces")}</h2>
        <StateView q={traces} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><thead><tr><th>{t("obs.trace")}</th><th>{t("obs.duration")}</th><th>{t("obs.tools")}</th><th /></tr></thead>
            <tbody>{d.map((x) => (
              <tr key={x.trace_id}><td><b>{x.name}</b><div className="sub">{fmtTime(x.start)} · {x.spans} spans · {x.tokens} tok{x.errors ? ` · ${x.errors} err` : ""}</div></td>
                <td className="mono">{x.duration_ms}ms</td><td className="mono sub">{x.tools.join(", ") || "—"}<div>{x.models.join(", ")}</div></td>
                <td><button className="btn" aria-expanded={open === x.trace_id} onClick={() => setOpen(open === x.trace_id ? null : x.trace_id)}>{t("obs.detail")}</button></td></tr>))}
            </tbody></table>)}</StateView>
        {open && <TraceDetail id={open} />}
      </section>
    </div>
  );
}

function TraceDetail({ id }: { id: string }) {
  const q = useApi<{ spans: Span[] }>(`/api/obs/traces/${id}`);
  return (
    <StateView q={q}>{(d) => {
      const t0 = Math.min(...d.spans.map((s) => new Date(s.start).getTime()));
      const total = Math.max(1, ...d.spans.map((s) => new Date(s.start).getTime() - t0 + s.duration_ms));
      const depth = (s: Span): number => { const p = d.spans.find((x) => x.span_id === s.parent_id); return p ? depth(p) + 1 : 0; };
      return (
        <div className="stack waterfall" aria-label={t("obs.waterfall")}>
          {d.spans.map((s) => (
            <div key={s.span_id} className="row" style={{ paddingLeft: depth(s) * 16 }}>
              <span className="mono" style={{ minWidth: 260 }}>{s.name}</span>
              <span className="track"><span className={`span ${s.status === "error" ? "err" : ""}`} style={{
                marginLeft: `${((new Date(s.start).getTime() - t0) / total) * 100}%`, width: `${Math.max(1, (s.duration_ms / total) * 100)}%` }} /></span>
              <span className="mono sub">{s.duration_ms}ms {String(s.attributes["gen_ai.usage.input_tokens"] ?? "")}{s.attributes["plaza.model"] ? ` · ${String(s.attributes["plaza.model"])}` : ""}</span>
            </div>))}
        </div>);
    }}</StateView>
  );
}

type Suite = { id: string; name: string; agent_scope: string | null; cases: unknown[]; last_run: { id: string; status: string; passed: number; total: number; score: number; regressions: number } | null };
type Run = { id: string; status: string; passed: number; total: number; score: number; regressions: number;
  results: { id: string; input: string; answer: string; passed: boolean; score: number; regression: boolean; checks: { check: string; ok: boolean }[] }[] };
const SAMPLE = JSON.stringify([{ id: "calc", input: "6 곱하기 7", expect: { tool: "calc.calculate", contains: ["42"] } }], null, 1);

export function EvalsPage() {
  const suites = useApi<Suite[]>("/api/evals/suites");
  const toast = useToast();
  const [form, setForm] = useState({ name: "", agent_scope: "", cases: SAMPLE });
  const [run, setRun] = useState<Run | null>(null);
  const create = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/api/evals/suites", { body: { name: form.name, agent_scope: form.agent_scope || null, cases: JSON.parse(form.cases) } });
      setForm({ ...form, name: "" }); suites.reload();
    } catch (x) { toast(x instanceof SyntaxError ? `cases JSON: ${x.message}` : errorText(x), "error"); }
  };
  const start = async (s: Suite) => {
    try {
      const { run_id } = await api<{ run_id: string }>(`/api/evals/suites/${s.id}/runs`, { method: "POST" });
      const poll = async () => { const r = await api<Run>(`/api/evals/runs/${run_id}`); setRun(r); if (r.status === "running") setTimeout(poll, 2000); else suites.reload(); };
      poll();
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <h1>{t("eval.title")}</h1>
      <StateView q={suites} empty={(d) => !d.length}>{(d) => (
        <table className="card responsive"><thead><tr><th>{t("eval.suite")}</th><th>{t("eval.last")}</th><th /></tr></thead>
          <tbody>{d.map((s) => (
            <tr key={s.id}><td><b>{s.name}</b> <span className="sub">{s.cases.length} cases{s.agent_scope ? ` · ${s.agent_scope}` : ""}</span></td>
              <td>{s.last_run ? <span className="row"><Badge value={s.last_run.passed === s.last_run.total ? "ok" : "warn"} label={`${s.last_run.passed}/${s.last_run.total}`} />
                <span className="mono">{t("eval.score")} {s.last_run.score}</span>{s.last_run.regressions > 0 && <Badge value="failed" label={`${t("eval.regressions")} ${s.last_run.regressions}`} />}</span> : "—"}</td>
              <td className="row"><button className="btn primary" onClick={() => start(s)}>{t("eval.run")}</button>
                <button className="btn danger" onClick={() => api(`/api/evals/suites/${s.id}`, { method: "DELETE" }).then(suites.reload)}>{t("common.delete")}</button></td></tr>))}
          </tbody></table>)}</StateView>
      {run && <section className="card stack" aria-live="polite"><h2>{t("eval.result")} <Badge value={run.status === "done" ? "ok" : "running"} label={run.status} /></h2>
        <table className="responsive"><tbody>{run.results.map((r) => (
          <tr key={r.id}><td><Badge value={r.passed ? "ok" : "failed"} label={r.passed ? "PASS" : "FAIL"} />{r.regression && <> <Badge value="failed" label={t("eval.regressions")} /></>}</td>
            <td><b>{r.id}</b> <span className="sub">{r.input}</span><div className="sub">{r.answer.slice(0, 200)}</div></td>
            <td className="mono sub">{r.checks.map((c) => `${c.ok ? "✓" : "✕"} ${c.check}`).join("  ")}</td></tr>))}</tbody></table>
      </section>}
      <form className="card stack" onSubmit={create}>
        <h2>{t("eval.new")}</h2>
        <div className="row">
          <input required placeholder={t("eval.suite")} aria-label={t("eval.suite")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ maxWidth: 260 }} />
          <input placeholder="agent_scope" aria-label="agent_scope" value={form.agent_scope} onChange={(e) => setForm({ ...form, agent_scope: e.target.value })} style={{ maxWidth: 200 }} />
        </div>
        <label className="field"><span>{t("eval.cases")}</span><textarea rows={6} className="mono" value={form.cases} onChange={(e) => setForm({ ...form, cases: e.target.value })} /></label>
        <div><button className="btn primary">{t("eval.create")}</button></div>
      </form>
      <Compare />
    </div>
  );
}

function Compare() {
  const toast = useToast();
  const [prompt, setPrompt] = useState("");
  const [targets, setTargets] = useState("plaza/fast, plaza/chat");
  const [out, setOut] = useState<{ target: string; model?: string; answer?: string; latency_ms?: number; cost?: number; error?: string }[] | null>(null);
  const go = async (e: FormEvent) => {
    e.preventDefault();
    try { setOut((await api<{ results: typeof out }>("/api/evals/compare", { body: { prompt, targets: targets.split(",").map((s) => s.trim()).filter(Boolean) } })).results); }
    catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <form className="card stack" onSubmit={go}>
      <h2>{t("eval.playground")}</h2>
      <label className="field"><span>{t("eval.targets")}</span><input className="mono" value={targets} onChange={(e) => setTargets(e.target.value)} /></label>
      <label className="field"><span>{t("eval.prompt")}</span><textarea rows={3} value={prompt} onChange={(e) => setPrompt(e.target.value)} /></label>
      <div><button className="btn primary" disabled={!prompt.trim()}>{t("eval.compare")}</button></div>
      {out && <div className="grid">{(out ?? []).map((r) => (
        <div key={r.target} className="card stack"><b className="mono">{r.target}</b>
          {r.error ? <span className="badge danger">{r.error}</span> : <>
            <span className="sub mono">{r.model} · {r.latency_ms}ms · ${(r.cost ?? 0).toFixed(5)}</span><div>{r.answer}</div></>}</div>))}</div>}
    </form>
  );
}
