// 공급망 신뢰(D5-03·D5-04): 신뢰 서명 키 등록·철회 + 공급망 정책(서명 필수·취약점 차단 등급·라이선스·egress)
import { type FormEvent, useState } from "react";
import { api } from "../api";
import { Badge, errorText, fmtTime, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

type TrustKey = { kid: string; name: string; publisher_id: string | null; created_at: string; revoked_at: string | null };
type Policy = { require_signature: boolean; block_unscanned: boolean; block_severity: string; license_block_grades: string[];
  license_allow: string[]; egress_allow: string[] };

const list = (v: FormDataEntryValue | null) => String(v ?? "").split(",").map((s) => s.trim()).filter(Boolean);

export function TrustPage() {
  const keys = useApi<TrustKey[]>("/api/trust/keys");
  const pol = useApi<Policy>("/api/trust/policy");
  const toast = useToast();
  const [form, setForm] = useState({ name: "", public_key: "", publisher_id: "" });
  const add = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/api/trust/keys", { body: { ...form, publisher_id: form.publisher_id || undefined } });
      setForm({ name: "", public_key: "", publisher_id: "" });
      keys.reload();
    } catch (x) { toast(errorText(x), "error"); }
  };
  const revoke = async (k: TrustKey) => {
    try { await api(`/api/trust/keys/${k.kid}`, { method: "DELETE" }); keys.reload(); } catch (x) { toast(errorText(x), "error"); }
  };
  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api("/api/trust/policy", { method: "PUT", body: {
        require_signature: f.get("rs") === "on", block_unscanned: f.get("bu") === "on", block_severity: String(f.get("sev") ?? ""),
        license_block_grades: f.getAll("lb").map(String), license_allow: list(f.get("la")), egress_allow: list(f.get("ea")) } });
      toast("OK", "ok"); pol.reload();
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <h1>{t("trust.title")}</h1>
      <section className="card stack"><h2>{t("trust.keys")}</h2>
        <p className="sub">{t("trust.hint")}</p>
        <StateView q={keys} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><thead><tr><th>kid</th><th>{t("trust.key_name")}</th><th>{t("trust.publisher")}</th><th /></tr></thead>
            <tbody>{d.map((k) => (
              <tr key={k.kid}><td className="mono">{k.kid}</td><td>{k.name}<div className="sub">{fmtTime(k.created_at)}</div></td><td>{k.publisher_id ?? "—"}</td>
                <td>{k.revoked_at ? <Badge value="rejected" label={t("trust.revoked")} /> : <button className="btn" onClick={() => revoke(k)}>{t("trust.revoke")}</button>}</td></tr>))}
            </tbody></table>)}</StateView>
        <form className="stack" onSubmit={add}>
          <div className="row">
            <label className="field" style={{ flex: 1 }}><span>{t("trust.key_name")}</span><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label className="field" style={{ flex: 1 }}><span>{t("trust.publisher")}</span><input value={form.publisher_id} onChange={(e) => setForm({ ...form, publisher_id: e.target.value })} /></label>
          </div>
          <label className="field"><span>{t("trust.public_key")}</span>
            <textarea required rows={4} className="mono" placeholder="-----BEGIN PUBLIC KEY-----" value={form.public_key} onChange={(e) => setForm({ ...form, public_key: e.target.value })} /></label>
          <div><button className="btn primary">{t("trust.add")}</button></div>
        </form>
      </section>
      <StateView q={pol}>{(p) => (
        <form className="card stack" onSubmit={save} style={{ maxWidth: 640 }}>
          <h2>{t("trust.policy")}</h2>
          <label className="row"><input type="checkbox" name="rs" style={{ width: "auto" }} defaultChecked={p.require_signature} />{t("trust.require_signature")}</label>
          <label className="row"><input type="checkbox" name="bu" style={{ width: "auto" }} defaultChecked={p.block_unscanned} />{t("trust.block_unscanned")}</label>
          <label className="field"><span>{t("trust.block_severity")}</span>
            <select name="sev" defaultValue={p.block_severity}><option value="">{t("trust.none")}</option>
              {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => <option key={s}>{s}</option>)}</select></label>
          <fieldset className="row" style={{ border: 0, padding: 0 }}><legend className="sub">{t("trust.license_block")}</legend>
            {["G3", "G4", "G5"].map((g) => <label key={g} className="row"><input type="checkbox" name="lb" value={g} style={{ width: "auto" }} defaultChecked={p.license_block_grades.includes(g)} />{g}</label>)}</fieldset>
          <label className="field"><span>{t("trust.license_allow")}</span><input name="la" className="mono" defaultValue={p.license_allow.join(", ")} /></label>
          <label className="field"><span>{t("trust.egress_allow")}</span><input name="ea" className="mono" defaultValue={p.egress_allow.join(", ")} /></label>
          <div><button className="btn primary">{t("common.save")}</button></div>
        </form>)}</StateView>
    </div>
  );
}
