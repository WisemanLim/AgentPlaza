// C07 채널·임베드 설정(D3-07): 웹 위젯 · Slack · Telegram · 카카오 i 오픈빌더 → AI Assistant
import { type FormEvent, useState } from "react";
import { api } from "../api";
import { Badge, errorText, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

type Chan = { id: string; kind: string; name: string; enabled: boolean; endpoint: string | null; embed: string | null;
  config: { agent_scope?: string; data_class?: string; allowed_origins?: string[]; greeting?: string };
  secrets: Record<string, boolean>; threads: number; generated?: Record<string, string> };
type AgentRow = { id: string; name: string; builtin: boolean };

const ENTER: Record<string, string[]> = { slack: ["SIGNING_SECRET", "BOT_TOKEN"], telegram: ["BOT_TOKEN"], kakao: [], web: [] };
const lines = (v: string) => v.split(/[\n,]/).map((s) => s.trim()).filter(Boolean);

export function ChannelsPage() {
  const q = useApi<Chan[]>("/api/channels");
  const agents = useApi<AgentRow[]>("/api/agents");
  const toast = useToast();
  const [shown, setShown] = useState<Record<string, Record<string, string>>>({});  // 생성 비밀값(1회 표시)
  const [f, setF] = useState({ id: "", kind: "web", name: "", agent_scope: "", data_class: "L2", origins: "", greeting: "" });
  const run = async (fn: () => Promise<unknown>) => { try { await fn(); toast("OK", "ok"); q.reload(); } catch (x) { toast(errorText(x), "error"); } };
  const create = (e: FormEvent) => {
    e.preventDefault();
    const config: Chan["config"] = { data_class: f.data_class, ...(f.agent_scope ? { agent_scope: f.agent_scope } : {}),
      ...(f.greeting ? { greeting: f.greeting } : {}), ...(f.kind === "web" ? { allowed_origins: lines(f.origins) } : {}) };
    run(async () => {
      const r = await api<Chan>("/api/channels", { body: { id: f.id, kind: f.kind, name: f.name, config } });
      if (r.generated && Object.keys(r.generated).length) setShown({ ...shown, [r.id]: r.generated });
      setF({ ...f, id: "", name: "", origins: "", greeting: "" });
    });
  };
  const saveSecrets = (e: FormEvent<HTMLFormElement>, c: Chan) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const secrets = Object.fromEntries(ENTER[c.kind].map((k) => [k, String(fd.get(k) ?? "")]).filter(([, v]) => v));
    run(() => api(`/api/channels/${c.id}`, { method: "PATCH", body: { secrets } }));
  };
  return (
    <div className="stack">
      <h1>{t("ch.title")}</h1>
      <p className="sub">{t("ch.hint")}</p>
      <StateView q={q} empty={(d) => !d.length}>{(d) => (<div className="stack">{d.map((c) => (
        <section key={c.id} className="card stack" aria-labelledby={`ch-${c.id}`}>
          <div className="row"><h2 id={`ch-${c.id}`} style={{ margin: 0, marginRight: "auto" }}>{c.name} <span className="mono sub">{c.id}</span></h2>
            <Badge value="info" label={t(`ch.kind.${c.kind}`)} /><Badge value={c.enabled ? "ok" : "disabled"} label={c.enabled ? t("ch.on") : t("ch.off")} />
            <span className="sub">{t("ch.threads")} {c.threads}</span></div>
          <div className="sub">{t("ch.scope")}: {c.config.agent_scope ?? t("ch.all_agents")} · {c.config.data_class ?? "L2"}
            {c.kind === "web" && <> · {t("ch.origins")}: {(c.config.allowed_origins ?? []).join(", ") || "—"}</>}</div>
          {c.endpoint && <div className="row"><span className="sub">{t("ch.endpoint")}</span><code className="mono">{c.endpoint}</code>
            <button className="btn" onClick={() => navigator.clipboard?.writeText(c.endpoint ?? "")}>{t("reg.copy")}</button></div>}
          {c.embed && <div className="row"><span className="sub">{t("ch.embed")}</span><code className="mono">{c.embed}</code>
            <button className="btn" onClick={() => navigator.clipboard?.writeText(c.embed ?? "")}>{t("reg.copy")}</button></div>}
          {shown[c.id] && <div role="alert" className="card" style={{ borderColor: "var(--warn)" }}>
            <b>{t("ch.generated")}</b>{Object.entries(shown[c.id]).map(([k, v]) => <div key={k} className="row"><span className="mono">{k}</span><code className="mono">{v}</code></div>)}
            <p className="sub">{c.kind === "kakao" ? t("ch.kakao_hint") : t("ch.telegram_hint")}</p></div>}
          <div className="row">{Object.entries(c.secrets).map(([k, ok]) => <Badge key={k} value={ok ? "ok" : "warn"} label={`${k} ${ok ? "✓" : "—"}`} />)}</div>
          {ENTER[c.kind].length > 0 && <form className="row" onSubmit={(e) => saveSecrets(e, c)}>
            {ENTER[c.kind].map((k) => <label key={k} className="field" style={{ flex: 1, minWidth: 200 }}><span>{k} ({t("status.write_only")})</span>
              <input name={k} type="password" autoComplete="off" /></label>)}
            <button className="btn primary">{t("common.save")}</button></form>}
          <div className="row">
            <button className="btn" onClick={() => run(() => api(`/api/channels/${c.id}`, { method: "PATCH", body: { enabled: !c.enabled } }))}>{c.enabled ? t("ch.disable") : t("ch.enable")}</button>
            {(c.kind === "telegram" || c.kind === "kakao") && <button className="btn" onClick={() => run(async () => {
              const r = await api<{ generated: Record<string, string> }>(`/api/channels/${c.id}/rotate`, { method: "POST" });
              setShown({ ...shown, [c.id]: r.generated });
            })}>{t("ch.rotate")}</button>}
            <button className="btn danger" onClick={() => run(() => api(`/api/channels/${c.id}`, { method: "DELETE" }))}>{t("common.delete")}</button>
          </div>
        </section>))}</div>)}</StateView>
      <form className="card stack" onSubmit={create}>
        <h2>{t("ch.add")}</h2>
        <div className="row">
          <label className="field"><span>{t("ch.kind")}</span><select value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>
            {["web", "slack", "telegram", "kakao"].map((k) => <option key={k} value={k}>{t(`ch.kind.${k}`)}</option>)}</select></label>
          <label className="field"><span>ID</span><input required pattern="[a-z0-9][a-z0-9-]{1,39}" value={f.id} onChange={(e) => setF({ ...f, id: e.target.value })} /></label>
          <label className="field" style={{ flex: 1 }}><span>{t("pubs.name")}</span><input required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></label>
        </div>
        <div className="row">
          <label className="field"><span>{t("ch.scope")}</span><select value={f.agent_scope} onChange={(e) => setF({ ...f, agent_scope: e.target.value })}>
            <option value="">{t("ch.all_agents")}</option>{(agents.data ?? []).filter((a) => !a.builtin).map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
          <label className="field"><span>{t("ch.data_class")}</span><select value={f.data_class} onChange={(e) => setF({ ...f, data_class: e.target.value })}>
            {["L0", "L1", "L2", "L3"].map((l) => <option key={l} value={l}>{l}</option>)}</select></label>
          <label className="field" style={{ flex: 1 }}><span>{t("ch.greeting")}</span><input value={f.greeting} onChange={(e) => setF({ ...f, greeting: e.target.value })} /></label>
        </div>
        {f.kind === "web" && <label className="field"><span>{t("ch.origins")} ({t("ch.origins_hint")})</span>
          <textarea rows={2} className="mono" required value={f.origins} onChange={(e) => setF({ ...f, origins: e.target.value })} placeholder="https://www.example.com" /></label>}
        <div><button className="btn primary">{t("ch.add")}</button></div>
      </form>
    </div>
  );
}
