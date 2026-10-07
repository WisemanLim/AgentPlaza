// I04 승인함 · J01/J02/J04 LLM · K01 사용자 · K04 API 키 · L01 설정 · L02 프로필 · M03 감사 원장
import { type FormEvent, useState } from "react";
import type { Me } from "../App";
import { applyTheme } from "../theme";
import { api } from "../api";
import { Badge, errorText, fmtTime, Modal, StateView, useApi, useToast } from "../components/ui";
import { setLocale, t } from "../i18n";

const isAdmin = (me: Me) => me.role === "admin" || me.role === "supervisor";

type Approval = { id: string; agent_id: string; capability: string; args: unknown; requester: string; status: string; expires_at: string };

export function ApprovalsPage({ me }: { me: Me }) {
  const q = useApi<Approval[]>("/api/approvals");
  const toast = useToast();
  const decide = async (a: Approval, approve: boolean) => {
    try {
      const r = await api<{ state: string; answer: string | null }>(`/api/approvals/${a.id}/${approve ? "approve" : "reject"}`, { body: {} });
      toast(`${a.agent_id}.${a.capability}: ${r.state}`, r.state === "succeeded" ? "ok" : "info");
    } catch (e) { toast(errorText(e), "error"); }
    q.reload();
  };
  return (
    <div className="stack">
      <h1>{t("approvals.title")}</h1>
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <table className="card responsive"><thead><tr><th>{t("nav.agents")}</th><th>{t("approvals.args")}</th><th>{t("approvals.requester")}</th><th>{t("approvals.expires")}</th><th /></tr></thead>
          <tbody>{d.map((a) => (
            <tr key={a.id}><td><b>{a.agent_id}.{a.capability}</b></td><td className="mono">{JSON.stringify(a.args)}</td><td>{a.requester}</td><td>{fmtTime(a.expires_at)}</td>
              <td className="row">{isAdmin(me) ? <>
                <button className="btn primary" onClick={() => decide(a, true)}>{t("chat.approve")}</button>
                <button className="btn" onClick={() => decide(a, false)}>{t("chat.reject")}</button></> : <Badge value={a.status} />}</td></tr>))}
          </tbody></table>
      )}</StateView>
    </div>
  );
}

type Model = { id: string; provider: string; local: boolean; context: number; tool_call: boolean; vision: boolean; license: string; commercial_use: string; enabled: boolean };
type Route = { alias: string; targets: string[]; description: string | null };
type Provider = { name: string; reachable: boolean | null; models?: string[]; via?: string; fallbacks?: number };
type Budget = { monthly: number; ratio: number; currency: string; month: string; spent: number; used: number | null; forced: boolean };

export function LlmPage({ me }: { me: Me }) {
  const models = useApi<Model[]>("/api/llm/models");
  const routes = useApi<Route[]>("/api/llm/routes");
  const providers = useApi<Provider[]>("/api/llm/providers");
  const toast = useToast();
  const toggle = async (m: Model) => {
    let ack = false;
    if (!m.enabled && m.commercial_use === "conditional") ack = window.confirm(`${m.id}: ${m.license} — ${t("llm.license")} OK?`);
    try { await api(`/api/llm/models/${m.id}`, { method: "PATCH", body: { enabled: !m.enabled, acknowledge_license: ack } }); }
    catch (e) { toast(errorText(e), "error"); }
    models.reload();
  };
  const saveRoute = async (r: Route, value: string) => {
    try { await api(`/api/llm/routes/${r.alias}`, { method: "PUT", body: { targets: value.split(",").map((s) => s.trim()).filter(Boolean), description: r.description } }); toast("OK", "ok"); }
    catch (e) { toast(errorText(e), "error"); }
    routes.reload();
  };
  return (
    <div className="stack">
      <h1>{t("llm.title")}</h1>
      <section className="card"><h2>{t("llm.providers")}</h2>
        <StateView q={providers}>{(d) => <div className="row">{d.map((p) => <Badge key={p.name} value={p.reachable === false ? "unhealthy" : "healthy"}
          label={`${p.name}${p.models ? ` (${p.models.length})` : ""}${p.via === "bifrost" ? " · via Bifrost" : ""}${p.name === "bifrost" ? ` · ${t("llm.direct_fallbacks")} ${p.fallbacks ?? 0}` : ""}`} />)}</div>}</StateView>
      </section>
      {isAdmin(me) && <BudgetSection me={me} />}
      <section className="card"><h2>{t("llm.models")}</h2>
        <StateView q={models}>{(d) => (
          <table className="responsive"><thead><tr><th>ID</th><th>{t("llm.license")}</th><th>ctx</th><th /></tr></thead>
            <tbody>{d.map((m) => (
              <tr key={m.id}><td className="mono">{m.id} <Badge value={m.local ? "ok" : "warn"} label={m.local ? t("llm.local") : t("llm.public")} /></td>
                <td>{m.license} <Badge value={m.commercial_use === "allowed" ? "ok" : "pending"} label={m.commercial_use} /></td><td className="mono">{m.context}</td>
                <td><label className="row"><input type="checkbox" style={{ width: "auto" }} checked={m.enabled} disabled={!isAdmin(me)} onChange={() => toggle(m)} />{t("llm.enabled")}</label></td></tr>))}
            </tbody></table>)}</StateView>
      </section>
      {isAdmin(me) && <ServersSection onModels={models.reload} />}
      <section className="card"><h2>{t("llm.routes")}</h2>
        <StateView q={routes}>{(d) => (
          <div className="stack">{d.map((r) => (
            <form key={r.alias} className="row" onSubmit={(e) => { e.preventDefault(); saveRoute(r, (e.currentTarget.elements.namedItem("t") as HTMLInputElement).value); }}>
              <b className="mono" style={{ minWidth: 160 }}>{r.alias}</b>
              <input name="t" className="mono" defaultValue={r.targets.join(", ")} aria-label={r.alias} disabled={!isAdmin(me)} style={{ flex: 1, width: "auto" }} />
              {isAdmin(me) && <button className="btn">{t("common.save")}</button>}
            </form>))}</div>)}</StateView>
      </section>
    </div>
  );
}

// J05: 월 예산 — 기준 비율(기본 80%) 도달 시 퍼블릭 대상을 빼고 로컬만(CMP-10 사용량 바: 85% 황색·95% 적색). 편집은 supervisor
function BudgetSection({ me }: { me: Me }) {
  const q = useApi<Budget>("/api/llm/budget");
  const toast = useToast();
  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api("/api/llm/budget", { method: "PUT", body: { monthly: Number(f.get("monthly")) || 0, ratio: Number(f.get("ratio")) / 100 } });
      toast("OK", "ok"); q.reload();
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <section className="card stack"><h2>{t("llm.budget")}</h2>
      <StateView q={q}>{(b) => (<>
        <div className="row">
          <meter min={0} max={1} low={0.85} high={0.95} optimum={0} value={Math.min(b.used ?? 0, 1)} aria-label={t("llm.budget_used")} style={{ width: 240 }} />
          <span className="mono">{b.spent.toFixed(4)} / {b.monthly ? b.monthly.toFixed(2) : "∞"} {b.currency} · {b.month}</span>
          {b.forced ? <Badge value="warn" label={t("llm.budget_forced")} /> : b.monthly ? <Badge value="ok" label={`${Math.round((b.used ?? 0) * 100)}%`} /> : <Badge value="info" label={t("llm.budget_off")} />}
        </div>
        <p className="sub">{t("llm.budget_hint")}</p>
        {me.role === "supervisor" && <form className="row" onSubmit={save}>
          <label className="field"><span>{t("llm.budget_monthly")} ({b.currency}, 0 = {t("llm.budget_off")})</span><input name="monthly" type="number" min={0} step="0.01" defaultValue={b.monthly} style={{ width: 160 }} /></label>
          <label className="field"><span>{t("llm.budget_ratio")} (%)</span><input name="ratio" type="number" min={50} max={100} defaultValue={Math.round(b.ratio * 100)} style={{ width: 120 }} /></label>
          <button className="btn primary">{t("common.save")}</button>
        </form>}
      </>)}</StateView>
    </section>
  );
}

type Server = { name: string; base_url: string; local: boolean; has_key: boolean };

// D1-02: OpenAI 호환 서버(vLLM·llama-server·CLI 브리지 등) 등록 → 서빙 모델 조회 → 카탈로그 추가
function ServersSection({ onModels }: { onModels: () => void }) {
  const q = useApi<Server[]>("/api/llm/servers");
  const toast = useToast();
  const [f, setF] = useState({ name: "", base_url: "", local: true, api_key: "" });
  const [served, setServed] = useState<{ server: string; models: string[] } | null>(null);
  const act = async (fn: () => Promise<unknown>) => { try { await fn(); q.reload(); } catch (x) { toast(errorText(x), "error"); } };
  const addModel = (server: Server, id: string) => act(async () => {
    await api("/api/llm/models", { body: { provider: server.name, model_id: id, local: server.local, context: 32768, tool_call: false,
      vision: false, license: "unknown", commercial_use: "conditional", enabled: false } });
    toast(`${server.name}/${id} OK`, "ok"); onModels();
  });
  return (
    <section className="card stack"><h2>{t("llm.servers")}</h2>
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <table className="responsive"><tbody>{d.map((s) => (
          <tr key={s.name}><td className="mono"><b>{s.name}</b> {s.base_url}</td>
            <td><Badge value={s.local ? "ok" : "warn"} label={s.local ? t("llm.local") : t("llm.public")} /></td>
            <td className="row"><button className="btn" onClick={() => act(async () => setServed(await api(`/api/llm/servers/${s.name}/models`)))}>{t("llm.discover")}</button>
              <button className="btn danger" onClick={() => act(() => api(`/api/llm/servers/${s.name}`, { method: "DELETE" }))}>{t("common.delete")}</button></td></tr>))}
        </tbody></table>)}</StateView>
      {served && <div className="row">{served.models.map((m) => (
        <button key={m} className="btn" onClick={() => addModel((q.data ?? []).find((s) => s.name === served.server)!, m)}>+ {served.server}/{m}</button>))}</div>}
      <form className="row" onSubmit={(e) => { e.preventDefault(); act(async () => { await api(`/api/llm/servers/${f.name}`, { method: "PUT",
        body: { base_url: f.base_url, local: f.local, api_key: f.api_key || undefined } }); setF({ name: "", base_url: "", local: true, api_key: "" }); }); }}>
        <input required placeholder="name" aria-label={t("llm.server_name")} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} style={{ maxWidth: 140 }} />
        <input required type="url" placeholder="http://vllm:8000/v1" aria-label="base_url" value={f.base_url} onChange={(e) => setF({ ...f, base_url: e.target.value })} style={{ flex: 1, width: "auto" }} />
        <input type="password" autoComplete="off" placeholder="API key" aria-label="API key" value={f.api_key} onChange={(e) => setF({ ...f, api_key: e.target.value })} style={{ maxWidth: 160 }} />
        <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={f.local} onChange={(e) => setF({ ...f, local: e.target.checked })} />{t("llm.local")}</label>
        <button className="btn primary">{t("llm.add_server")}</button>
      </form>
    </section>
  );
}

type User = { id: number; email: string; role: string; is_active: boolean };

export function UsersPage({ me }: { me: Me }) {
  const q = useApi<User[]>("/api/users");
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("user");
  const [temp, setTemp] = useState<string | null>(null);
  const add = async (e: FormEvent) => {
    e.preventDefault();
    try { const r = await api<{ temporary_password: string }>("/api/users", { body: { email, role } }); setTemp(r.temporary_password); setEmail(""); q.reload(); }
    catch (x) { toast(errorText(x), "error"); }
  };
  const patch = async (u: User, body: object) => { try { await api(`/api/users/${u.id}`, { method: "PATCH", body }); } catch (x) { toast(errorText(x), "error"); } q.reload(); };
  return (
    <div className="stack">
      <h1>{t("users.title")}</h1>
      <form className="row card" onSubmit={add}>
        <input type="email" required placeholder={t("auth.email")} aria-label={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} style={{ maxWidth: 280 }} />
        <select aria-label={t("users.role")} value={role} onChange={(e) => setRole(e.target.value)} style={{ width: "auto" }}>
          <option value="user">user</option>{me.role === "supervisor" && <option value="admin">admin</option>}</select>
        <button className="btn primary">{t("users.add")}</button>
      </form>
      <StateView q={q}>{(d) => (
        <table className="card responsive"><thead><tr><th>{t("auth.email")}</th><th>{t("users.role")}</th><th>{t("users.active")}</th></tr></thead>
          <tbody>{d.map((u) => <tr key={u.id}><td>{u.email}</td><td>{u.role}</td>
            <td><label className="row"><input type="checkbox" style={{ width: "auto" }} checked={u.is_active} disabled={String(u.id) === String(me.id)} onChange={() => patch(u, { is_active: !u.is_active })} />{u.is_active ? "✓" : "✕"}</label></td></tr>)}</tbody></table>
      )}</StateView>
      <Modal open={!!temp} title={t("users.temp_pw")} onClose={() => setTemp(null)}>
        <p className="alert warn">{t("common.copy_once")}</p><p className="mono" style={{ fontSize: 18 }}>{temp}</p>
        <button className="btn primary" onClick={() => setTemp(null)}>{t("common.close")}</button>
      </Modal>
    </div>
  );
}

type Key = { id: number; name: string; prefix: string; role: string; scopes: { agents: string[] }; revoked: boolean; last_used_at: string | null };

export function KeysPage() {
  const q = useApi<Key[]>("/api/api-keys");
  const toast = useToast();
  const [name, setName] = useState("");
  const [agents, setAgents] = useState("*");
  const [raw, setRaw] = useState<string | null>(null);
  const add = async (e: FormEvent) => {
    e.preventDefault();
    try { const r = await api<{ key: string }>("/api/api-keys", { body: { name, agents: agents.split(",").map((s) => s.trim()).filter(Boolean) } }); setRaw(r.key); setName(""); q.reload(); }
    catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <h1>{t("keys.title")}</h1>
      <form className="row card" onSubmit={add}>
        <input required placeholder={t("keys.name")} aria-label={t("keys.name")} value={name} onChange={(e) => setName(e.target.value)} style={{ maxWidth: 220 }} />
        <input placeholder={t("keys.agents")} aria-label={t("keys.agents")} value={agents} onChange={(e) => setAgents(e.target.value)} style={{ maxWidth: 280 }} />
        <button className="btn primary">{t("keys.add")}</button>
      </form>
      <StateView q={q}>{(d) => (
        <table className="card responsive"><thead><tr><th>{t("keys.name")}</th><th>prefix</th><th>agents</th><th /></tr></thead>
          <tbody>{d.map((k) => <tr key={k.id}><td>{k.name}</td><td className="mono">{k.prefix}…</td><td className="mono">{k.scopes.agents.join(", ")}</td>
            <td>{k.revoked ? <Badge value="rejected" label="revoked" /> : <button className="btn" onClick={() => api(`/api/api-keys/${k.id}`, { method: "DELETE" }).then(q.reload)}>{t("keys.revoke")}</button>}</td></tr>)}</tbody></table>
      )}</StateView>
      <Modal open={!!raw} title={t("keys.title")} onClose={() => setRaw(null)}>
        <p className="alert warn">{t("common.copy_once")}</p><p className="mono" style={{ wordBreak: "break-all" }}>{raw}</p>
        <button className="btn primary" onClick={() => setRaw(null)}>{t("common.close")}</button>
      </Modal>
    </div>
  );
}

type Sys = { retention_chat_days: number; hitl_ttl_minutes: number; default_data_class: string; site_name: string };

export function SettingsPage({ me }: { me: Me }) {
  const q = useApi<Sys>("/api/settings");
  const toast = useToast();
  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api("/api/settings", { method: "PUT", body: { retention_chat_days: Number(f.get("r")), hitl_ttl_minutes: Number(f.get("h")),
        default_data_class: f.get("d"), site_name: f.get("s") } });
      toast("OK", "ok"); q.reload();
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <StateView q={q}>{(s) => (
      <form className="card stack" onSubmit={save} style={{ maxWidth: 560 }}>
        <h1>{t("settings.title")}</h1>
        <label className="field"><span>{t("settings.site_name")}</span><input name="s" defaultValue={s.site_name} /></label>
        <label className="field"><span>{t("settings.retention")}</span><input name="r" type="number" min={1} max={3650} defaultValue={s.retention_chat_days} /></label>
        <label className="field"><span>{t("settings.hitl_ttl")}</span><input name="h" type="number" min={1} defaultValue={s.hitl_ttl_minutes} /></label>
        <label className="field"><span>{t("settings.default_data_class")}</span>
          <select name="d" defaultValue={s.default_data_class}>{["L0", "L1", "L2", "L3"].map((l) => <option key={l}>{l}</option>)}</select></label>
        <button className="btn primary" disabled={me.role !== "supervisor"}>{t("common.save")}</button>
        {me.role === "supervisor" && <button type="button" className="btn" onClick={async () => {
          try { const r = await api<{ platform: { backup: string } }>("/api/admin/backup", { method: "POST" }); toast(`${t("backup.done")} ${r.platform.backup}`, "ok"); }
          catch (x) { toast(errorText(x), "error"); } }}>{t("backup.all")}</button>}
      </form>
    )}</StateView>
  );
}

export function ProfilePage() {
  const q = useApi<{ email: string; role: string; locale: string; theme: string }>("/api/me/profile");
  const toast = useToast();
  const update = async (body: { locale?: string; theme?: string }) => {
    try {
      const p = await api<{ locale: string; theme: string }>("/api/me/profile", { method: "PATCH", body });
      if (body.locale) setLocale(p.locale as "ko" | "en");
      if (body.theme) applyTheme(p.theme);
      q.reload();
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <StateView q={q}>{(p) => (
      <div className="card stack" style={{ maxWidth: 480 }}>
        <h1>{t("profile.title")}</h1>
        <p>{p.email} · {p.role}</p>
        <label className="field"><span>{t("profile.locale")}</span>
          <select value={p.locale} onChange={(e) => update({ locale: e.target.value })}><option value="ko">한국어</option><option value="en">English</option></select></label>
        <fieldset className="row" style={{ border: 0, padding: 0 }}><legend className="sub">{t("profile.theme")}</legend>
          {["light", "dark", "system"].map((th) => (
            <label key={th} className="row"><input type="radio" name="theme" style={{ width: "auto" }} checked={p.theme === th} onChange={() => update({ theme: th })} />{t(`profile.${th}`)}</label>))}
        </fieldset>
      </div>
    )}</StateView>
  );
}

type Ev = { id: number; ts: string; actor: string; agent_id: string | null; action: string; resource: string | null; outcome: string; hash: string };

export function AuditPage() {
  const [action, setAction] = useState("");
  const q = useApi<Ev[]>(`/api/audit?limit=200${action ? `&action=${encodeURIComponent(action)}` : ""}`);
  const [verdict, setVerdict] = useState<{ ok: boolean; checked: number; broken_at?: number } | null>(null);
  return (
    <div className="stack">
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("audit.title")}</h1>
        <input placeholder="action" aria-label="action" value={action} onChange={(e) => setAction(e.target.value)} style={{ maxWidth: 220 }} />
        <button className="btn" onClick={() => api<{ ok: boolean; checked: number }>("/api/audit/verify").then(setVerdict)}>{t("audit.verify")}</button></div>
      {verdict && <p className={`alert ${verdict.ok ? "info" : ""}`} role="status">{verdict.ok ? t("audit.ok") : `${t("audit.broken")} #${verdict.broken_at}`} ({verdict.checked})</p>}
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <table className="card responsive"><thead><tr><th>#</th><th>ts</th><th>actor</th><th>action</th><th>resource</th><th>hash</th></tr></thead>
          <tbody>{d.map((e) => <tr key={e.id}><td>{e.id}</td><td>{fmtTime(e.ts)}</td><td>{e.actor}</td><td><Badge value={e.outcome === "ok" ? "ok" : "failed"} label={e.action} /></td>
            <td className="mono">{e.agent_id ?? ""} {e.resource ?? ""}</td><td className="mono sub">{e.hash.slice(0, 12)}</td></tr>)}</tbody></table>
      )}</StateView>
    </div>
  );
}
