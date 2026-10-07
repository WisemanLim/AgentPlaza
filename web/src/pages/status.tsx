// D10-07 알림·상태: B03 알림 센터 · 상단바 벨 · 헬스 대시보드(구성요소·LLM·에이전트) · 알림 채널(Slack·Telegram·메일) · 사용량 리포트
import { type FormEvent, useEffect, useState } from "react";
import type { Me } from "../App";
import { api } from "../api";
import { Badge, errorText, fmtTime, Link, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

type Note = { id: number; kind: string; severity: string; title: string; body: string; resource: string | null;
  created_at: string; read: boolean; deliveries: Record<string, string> | null };
type Probe = { ok: boolean; detail: string; name?: string; version?: string };
type Snapshot = { at: string; ok: boolean; components: Record<string, Probe>; llm: Record<string, Probe>; agents: Record<string, Probe> };
type Channel = Record<string, unknown> & { enabled: boolean; min_severity: string; has_secret: boolean };
type Report = { days: number; markdown: string; settings: { weekly: boolean; last_sent: string | null } };

const TONE: Record<string, string> = { info: "info", warn: "warn", error: "failed" };

export function Bell() {
  const [n, setN] = useState(0);
  useEffect(() => {
    let alive = true;
    const tick = () => api<{ unread: number }>("/api/notifications/unread-count").then((r) => alive && setN(r.unread)).catch(() => {});
    tick();
    const h = setInterval(tick, 30_000);
    return () => { alive = false; clearInterval(h); };
  }, []);
  return <Link to="/notifications" className="btn"><span aria-hidden="true">🔔</span><span className="sr-only">{t("note.title")} </span>
    <span className={n > 0 ? "badge danger" : "sr-only"} style={{ marginLeft: 4 }}>{n}</span></Link>;
}

export function NotificationsPage() {
  const [unread, setUnread] = useState(false);
  const q = useApi<Note[]>(`/api/notifications${unread ? "?unread=true" : ""}`, [unread]);
  const toast = useToast();
  const read = async (ids?: number[]) => {
    try { await api("/api/notifications/read", { body: { ids } }); q.reload(); } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("note.title")}</h1>
        <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={unread} onChange={(e) => setUnread(e.target.checked)} />{t("note.unread_only")}</label>
        <button className="btn" onClick={() => read()}>{t("note.read_all")}</button></div>
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <ul className="stack" style={{ listStyle: "none", padding: 0 }}>{d.map((n) => (
          <li key={n.id} className="card stack">
            <div className="row"><Badge value={TONE[n.severity] ?? "info"} label={t(`note.sev.${n.severity}`)} />
              <b style={{ marginRight: "auto" }}>{n.title}</b><span className="sub">{fmtTime(n.created_at)}</span>
              {!n.read && <button className="btn" onClick={() => read([n.id])}>{t("note.mark_read")}</button>}</div>
            {n.body && <pre className="mono sub" style={{ whiteSpace: "pre-wrap", margin: 0 }}>{n.body}</pre>}
            {n.deliveries && Object.keys(n.deliveries).length > 0 && <div className="row sub">{Object.entries(n.deliveries).map(([k, v]) => (
              <Badge key={k} value={v === "ok" ? "ok" : "warn"} label={`${k}: ${v}`} />))}</div>}
          </li>))}</ul>)}</StateView>
    </div>
  );
}

function ProbeTable({ rows, label }: { rows: Record<string, Probe>; label: string }) {
  return (
    <table className="responsive"><thead><tr><th>{label}</th><th>{t("status.state")}</th><th>{t("status.detail")}</th></tr></thead>
      <tbody>{Object.entries(rows).map(([k, v]) => (
        <tr key={k}><td><b>{v.name ?? k}</b>{v.name && <span className="mono sub"> {k} v{v.version}</span>}</td>
          <td><Badge value={v.ok ? "healthy" : "unhealthy"} label={v.ok ? t("status.up") : t("status.down")} /></td>
          <td className="mono sub">{v.detail}</td></tr>))}</tbody></table>
  );
}

export function StatusPage({ me }: { me: Me }) {
  const snap = useApi<Snapshot>("/api/status");
  const toast = useToast();
  const check = async () => {
    try { const r = await api<{ changes: unknown[]; dispatched: number }>("/api/status/check", { method: "POST" });
      toast(`${t("status.changes")} ${r.changes.length} · ${t("status.dispatched")} ${r.dispatched}`, "ok"); snap.reload(); }
    catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("status.title")}</h1>
        <button className="btn primary" onClick={check}>{t("status.check")}</button></div>
      <StateView q={snap}>{(s) => (<>
        <div className="row"><Badge value={s.ok ? "healthy" : "unhealthy"} label={s.ok ? t("status.all_ok") : t("status.degraded")} />
          <span className="sub">{fmtTime(s.at)}</span></div>
        <section className="card"><h2>{t("status.components")}</h2><ProbeTable rows={s.components} label={t("status.component")} /></section>
        <section className="card"><h2>{t("status.llm")}</h2><ProbeTable rows={s.llm} label={t("status.component")} /></section>
        <section className="card"><h2>{t("status.agents")}</h2>
          {Object.keys(s.agents).length ? <ProbeTable rows={s.agents} label={t("nav.agents")} /> : <p className="sub">—</p>}</section>
      </>)}</StateView>
      {me.role === "supervisor" && <ChannelsSection />}
      <ReportSection me={me} />
    </div>
  );
}

const FIELDS: Record<string, [string, string][]> = {
  slack: [], telegram: [["chat_id", "Chat ID"]],
  email: [["host", "SMTP host"], ["port", "Port"], ["tls", "TLS (starttls|ssl|none)"], ["from", "From"], ["to", "To (,)"], ["username", "Username"]],
};
const SECRET_LABEL: Record<string, string> = { slack: "Incoming Webhook URL", telegram: "Bot token", email: "SMTP password" };

function ChannelsSection() {
  const q = useApi<Record<string, Channel>>("/api/notifications/channels");
  const toast = useToast();
  const save = async (e: FormEvent<HTMLFormElement>, name: string) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const config: Record<string, unknown> = { enabled: f.get("enabled") === "on", min_severity: String(f.get("min_severity")) };
    for (const [k] of FIELDS[name]) {
      const v = String(f.get(k) ?? "");
      config[k] = k === "to" ? v.split(",").map((x) => x.trim()).filter(Boolean) : k === "port" ? Number(v) || 0 : v;
    }
    const secret = String(f.get("secret") ?? "") || undefined;
    try { await api(`/api/notifications/channels/${name}`, { method: "PUT", body: { config, secret } }); toast("OK", "ok"); q.reload(); }
    catch (x) { toast(errorText(x), "error"); }
  };
  const test = async (name: string) => {
    try { const r = await api<{ result: string }>(`/api/notifications/channels/${name}/test`, { method: "POST" });
      toast(`${name}: ${r.result}`, r.result === "ok" ? "ok" : "error"); }
    catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <section className="card stack"><h2>{t("status.channels")}</h2>
      <StateView q={q}>{(d) => (<div className="stack">{Object.entries(d).map(([name, c]) => (
        <form key={name} className="stack" onSubmit={(e) => save(e, name)} style={{ borderTop: "1px solid var(--border)", paddingTop: 8 }}>
          <div className="row"><b style={{ minWidth: 80 }}>{name}</b>
            <label className="row"><input type="checkbox" name="enabled" style={{ width: "auto" }} defaultChecked={c.enabled} />{t("status.enabled")}</label>
            <label className="row sub">{t("status.min_severity")}<select name="min_severity" defaultValue={c.min_severity} style={{ width: "auto" }}>
              {["info", "warn", "error"].map((s) => <option key={s} value={s}>{t(`note.sev.${s}`)}</option>)}</select></label>
            {c.has_secret && <Badge value="ok" label={t("status.secret_set")} />}</div>
          <div className="row">{FIELDS[name].map(([k, label]) => (
            <label key={k} className="field" style={{ flex: 1, minWidth: 140 }}><span>{label}</span>
              <input name={k} defaultValue={Array.isArray(c[k]) ? (c[k] as string[]).join(", ") : String(c[k] ?? "")} /></label>))}
            <label className="field" style={{ flex: 2, minWidth: 220 }}><span>{SECRET_LABEL[name]} ({t("status.write_only")})</span>
              <input name="secret" type="password" autoComplete="off" /></label></div>
          <div className="row"><button className="btn primary">{t("common.save")}</button>
            <button type="button" className="btn" onClick={() => test(name)}>{t("status.test")}</button></div>
        </form>))}</div>)}</StateView>
    </section>
  );
}

function ReportSection({ me }: { me: Me }) {
  const q = useApi<Report>("/api/status/report?days=7");
  const toast = useToast();
  const run = async (f: () => Promise<unknown>) => { try { await f(); toast("OK", "ok"); q.reload(); } catch (x) { toast(errorText(x), "error"); } };
  return (
    <section className="card stack"><h2>{t("status.report")}</h2>
      <StateView q={q}>{(r) => (<>
        <pre className="mono" style={{ whiteSpace: "pre-wrap", margin: 0 }}>{r.markdown}</pre>
        {me.role === "supervisor" && <div className="row">
          <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={r.settings.weekly}
            onChange={(e) => run(() => api("/api/status/report/settings", { method: "PUT", body: { weekly: e.target.checked } }))} />{t("status.weekly")}</label>
          <span className="sub">{t("status.last_sent")}: {r.settings.last_sent ? fmtTime(r.settings.last_sent) : "—"}</span>
          <button className="btn" onClick={() => run(() => api("/api/status/report/send?days=7", { method: "POST" }))}>{t("status.send_now")}</button>
        </div>}
      </>)}</StateView>
    </section>
  );
}
