// 거버넌스(D9-05·D9-06·D2-05·D7-07): 정책 문서 편집 + 가드레일 점검 · 시크릿(D9-04): 목록·등록/회전·삭제(값은 다시 보이지 않음)
import { type FormEvent, useState } from "react";
import { api } from "../api";
import { Badge, errorText, fmtTime, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

const LEVELS = ["L0", "L1", "L2", "L3"];
type Policy = {
  data: { model_locality: Record<string, string>; external_tool_max_level: string; confidential_requires_cleared_agent: boolean;
    approval_at_levels: string[]; export_max_level: string; audit_level_min: string };
  guardrails: { injection: string; pii_mask_public: boolean; scan_tool_results: boolean; tool_allowlist: string[]; tool_denylist: string[] };
  reviewer: { mode: string; agent: string | null };
  gateway: { rate_per_minute: Record<string, number>; tool_rules: { tool: string; min_role: string }[] };
};
const list = (v: FormDataEntryValue | null) => String(v ?? "").split(",").map((s) => s.trim()).filter(Boolean);

export function GovernancePage() {
  const q = useApi<Policy>("/api/policy");
  const toast = useToast();
  const [check, setCheck] = useState("");
  const [result, setResult] = useState<{ injection: { level: string; score: number }; pii: { masked: string; found: Record<string, number> } } | null>(null);
  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      const rules = JSON.parse(String(f.get("rules") || "[]"));
      await api("/api/policy", { method: "PUT", body: {
        data: { model_locality: Object.fromEntries(LEVELS.map((l) => [l, f.get(`loc_${l}`)])),
          external_tool_max_level: f.get("ext"), confidential_requires_cleared_agent: f.get("clr") === "on",
          approval_at_levels: f.getAll("appr").map(String), export_max_level: f.get("exp"), audit_level_min: f.get("aud") },
        guardrails: { injection: f.get("inj"), pii_mask_public: f.get("pii") === "on", scan_tool_results: f.get("scan") === "on",
          tool_allowlist: list(f.get("allow")), tool_denylist: list(f.get("deny")) },
        reviewer: { mode: f.get("rev"), agent: String(f.get("revagent") || "") || null },
        gateway: { rate_per_minute: { user: Number(f.get("r_user")), service: Number(f.get("r_service")), anonymous: Number(f.get("r_anon")) },
          tool_rules: rules } } });
      toast("OK", "ok"); q.reload();
    } catch (x) { toast(x instanceof SyntaxError ? `tool_rules JSON: ${x.message}` : errorText(x), "error"); }
  };
  const runCheck = async (e: FormEvent) => {
    e.preventDefault();
    try { setResult(await api("/api/guardrails/check", { body: { text: check } })); } catch (x) { toast(errorText(x), "error"); }
  };
  const sel = (name: string, value: string, options: string[]) => (
    <select name={name} defaultValue={value}>{options.map((o) => <option key={o}>{o}</option>)}</select>);
  return (
    <div className="stack">
      <h1>{t("gov.title")}</h1>
      <StateView q={q}>{(p) => (
        <form className="stack" onSubmit={save}>
          <section className="card stack"><h2>{t("gov.data")}</h2>
            <fieldset className="row" style={{ border: 0, padding: 0 }}><legend className="sub">{t("gov.model_locality")}</legend>
              {LEVELS.map((l) => <label key={l} className="row">{l} {sel(`loc_${l}`, p.data.model_locality[l], ["any", "local"])}</label>)}</fieldset>
            <div className="row">
              <label className="field"><span>{t("gov.external_max")}</span>{sel("ext", p.data.external_tool_max_level, LEVELS)}</label>
              <label className="field"><span>{t("gov.export_max")}</span>{sel("exp", p.data.export_max_level, LEVELS)}</label>
              <label className="field"><span>{t("gov.audit_min")}</span>{sel("aud", p.data.audit_level_min, ["minimal", "standard", "full"])}</label>
            </div>
            <label className="row"><input type="checkbox" name="clr" style={{ width: "auto" }} defaultChecked={p.data.confidential_requires_cleared_agent} />{t("gov.cleared")}</label>
            <fieldset className="row" style={{ border: 0, padding: 0 }}><legend className="sub">{t("gov.approval_at")}</legend>
              {LEVELS.map((l) => <label key={l} className="row"><input type="checkbox" name="appr" value={l} style={{ width: "auto" }} defaultChecked={p.data.approval_at_levels.includes(l)} />{l}</label>)}</fieldset>
          </section>
          <section className="card stack"><h2>{t("gov.guardrails")}</h2>
            <label className="field"><span>{t("gov.injection")}</span>{sel("inj", p.guardrails.injection, ["block", "flag", "off"])}</label>
            <label className="row"><input type="checkbox" name="pii" style={{ width: "auto" }} defaultChecked={p.guardrails.pii_mask_public} />{t("gov.pii_public")}</label>
            <label className="row"><input type="checkbox" name="scan" style={{ width: "auto" }} defaultChecked={p.guardrails.scan_tool_results} />{t("gov.scan_results")}</label>
            <label className="field"><span>{t("gov.allow")}</span><input name="allow" className="mono" defaultValue={p.guardrails.tool_allowlist.join(", ")} /></label>
            <label className="field"><span>{t("gov.deny")}</span><input name="deny" className="mono" defaultValue={p.guardrails.tool_denylist.join(", ")} /></label>
          </section>
          <section className="card stack"><h2>{t("gov.reviewer")}</h2>
            <div className="row">
              <label className="field"><span>{t("gov.reviewer_mode")}</span>{sel("rev", p.reviewer.mode, ["off", "auto", "always"])}</label>
              <label className="field" style={{ flex: 1 }}><span>{t("gov.reviewer_agent")}</span><input name="revagent" className="mono" defaultValue={p.reviewer.agent ?? ""} /></label>
            </div>
          </section>
          <section className="card stack"><h2>{t("gov.gateway")}</h2>
            <div className="row">{(["user", "service", "anonymous"] as const).map((k) => (
              <label key={k} className="field"><span>{t("gov.rate")} · {k}</span>
                <input type="number" min={1} name={k === "anonymous" ? "r_anon" : `r_${k}`} defaultValue={p.gateway.rate_per_minute[k]} /></label>))}</div>
            <label className="field"><span>{t("gov.tool_rules")}</span>
              <textarea name="rules" rows={3} className="mono" defaultValue={JSON.stringify(p.gateway.tool_rules)} /></label>
          </section>
          <div><button className="btn primary">{t("common.save")}</button></div>
        </form>)}</StateView>
      <form className="card stack" onSubmit={runCheck}>
        <h2>{t("gov.check")}</h2>
        <label className="field"><span>{t("gov.check_text")}</span><textarea rows={3} value={check} onChange={(e) => setCheck(e.target.value)} /></label>
        <div><button className="btn" disabled={!check.trim()}>{t("gov.check_run")}</button></div>
        {result && <div className="stack">
          <div className="row"><Badge value={result.injection.level === "none" ? "ok" : result.injection.level === "injection" ? "failed" : "pending"}
            label={`${t("gov.injection")}: ${result.injection.level} (${result.injection.score})`} />
            {Object.entries(result.pii.found).map(([k, n]) => <Badge key={k} value="pending" label={`${k}×${n}`} />)}</div>
          <p className="mono">{result.pii.masked}</p></div>}
      </form>
    </div>
  );
}

type SecretRow = { scope: string; name: string; version: number; updated_at: string; created_by: string };

export function SecretsPage() {
  const q = useApi<SecretRow[]>("/api/secrets");
  const toast = useToast();
  const [form, setForm] = useState({ scope: "global", name: "", value: "" });
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api(`/api/secrets/${encodeURIComponent(form.scope)}/${form.name}`, { method: "PUT", body: { value: form.value } });
      setForm({ ...form, name: "", value: "" }); q.reload(); toast("OK", "ok");
    } catch (x) { toast(errorText(x), "error"); }
  };
  const remove = async (s: SecretRow) => {
    try { await api(`/api/secrets/${encodeURIComponent(s.scope)}/${s.name}`, { method: "DELETE" }); q.reload(); } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <h1>{t("secrets.title")}</h1>
      <p className="sub">{t("secrets.hint")}</p>
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <table className="card responsive"><thead><tr><th>scope</th><th>{t("secrets.name")}</th><th>{t("common.version")}</th><th /></tr></thead>
          <tbody>{d.map((s) => (
            <tr key={`${s.scope}/${s.name}`}><td className="mono">{s.scope}</td><td className="mono">{s.name}</td>
              <td>v{s.version} <span className="sub">{fmtTime(s.updated_at)}</span></td>
              <td className="row"><button className="btn" onClick={() => setForm({ scope: s.scope, name: s.name, value: "" })}>{t("secrets.rotate")}</button>
                <button className="btn danger" onClick={() => remove(s)}>{t("common.delete")}</button></td></tr>))}</tbody></table>)}</StateView>
      <form className="card stack" onSubmit={submit} style={{ maxWidth: 640 }}>
        <div className="row">
          <label className="field"><span>scope</span><input required className="mono" placeholder="global | agent:<id>" value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })} /></label>
          <label className="field"><span>{t("secrets.name")}</span><input required className="mono" pattern="[A-Z][A-Z0-9_]*" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        </div>
        <label className="field"><span>{t("secrets.value")}</span><input required type="password" autoComplete="off" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} /></label>
        <div><button className="btn primary">{t("secrets.save")}</button></div>
      </form>
    </div>
  );
}
