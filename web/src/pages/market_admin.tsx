// 마켓 운영(Epic 18): E06 자산 게시 · E07 퍼블리셔·심사·운영 배지 · E11 설치됨·업데이트·라이선스 · E13 원격 레지스트리·번들
import { type FormEvent, Fragment, useState } from "react";
import type { Me } from "../App";
import { api, ApiError, download } from "../api";
import { Badge, errorText, fmtTime, Link, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";
import { InstallProgress } from "./agents";

type Key = { kid: string; name: string; revoked_at: string | null };
type Publisher = { id: string; name: string; url: string | null; verified: boolean; members: string[]; assets: string[];
  downloads: number; installs: number; pending: number; keys: Key[]; active_keys: number };
type Gate = { sha256?: string; structure?: { ok: boolean; files: number }; supply_chain?: Record<string, unknown>;
  license?: Record<string, unknown>; errors?: string[]; warnings?: string[] };
type Release = { id: string; listing_id: string; version: string; publisher_id: string; status: string; gate: Gate;
  submitted_by: string; reason: string | null; created_at: string };
type Diff = { version: string; needs_consent: boolean; paid: boolean; licensed: boolean | null; data_class_raised: boolean } & Record<string, unknown>;
type Installed = { agent_id: string; name: string; source: string; version: string; status: string; is_active: boolean;
  latest: string | null; origin: string | null; installed_by: string | null; installed_at: string | null; update: Diff | null;
  auto_update: boolean; versions: { version: string; current: boolean; installed_at: string }[] };
type Lic = { id: string; listing_id: string; seats: number; seats_used: number; holders: string[]; expires_at: string | null;
  versions: string; valid: boolean; status: string };
type Purchase = { id: string; listing_id: string; version: string; amount: number; currency: string; seats: number; months: number;
  adapter_ref: string; created_at: string };
type Registry = { name: string; url: string; status?: string; error?: string | null; last_sync?: string; count?: number;
  interval_minutes: number; has_token: boolean };

const csv = (v: string) => v.split(",").map((s) => s.trim()).filter(Boolean);
const DIFF_KEYS = ["egress_added", "secretRefs_added", "required_env_added", "approval_added", "capabilities_added"];

function GateReport({ gate, status }: { gate: Gate; status?: string }) {
  const sc = gate.supply_chain ?? {};
  const vulns = sc.vulns as { status?: string; critical?: number; high?: number } | undefined;
  return (
    <section className="card stack" aria-live="polite"><h2>{t("pub.gate")} {status && <Badge value={status} />}</h2>
      <table><tbody>
        <tr><th>structure</th><td><Badge value={gate.structure?.ok ? "ok" : "failed"} /> {gate.structure?.files ?? 0} files</td></tr>
        <tr><th>{t("supply.signature")}</th><td>{String(sc.signature ?? "—")} <span className="mono sub">{String(sc.signer ?? "")}</span></td></tr>
        <tr><th>{t("supply.vulns")}</th><td>{vulns ? `${vulns.status} · C${vulns.critical ?? 0} H${vulns.high ?? 0}` : "—"}</td></tr>
        <tr><th>{t("supply.license")}</th><td>{String(gate.license?.license ?? "—")} · {String(gate.license?.effective ?? "")}</td></tr>
        <tr><th>sha256</th><td className="mono sub">{gate.sha256?.slice(0, 16)}</td></tr>
      </tbody></table>
      {!!gate.errors?.length && <div><b>{t("pub.errors")}</b><ul>{gate.errors.map((e) => <li key={e} className="badge danger">{e}</li>)}</ul></div>}
      {!!gate.warnings?.length && <details><summary>{t("pub.warnings")} ({gate.warnings.length})</summary><ul>{gate.warnings.map((w) => <li key={w} className="sub">{w}</li>)}</ul></details>}
    </section>
  );
}

// ---- E06 자산 게시 ----
export function PublishPage({ me }: { me: Me }) {
  const pubs = useApi<Publisher[]>("/api/market/publishers");
  const toast = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [f, setF] = useState({ publisher: "", name_ko: "", name_en: "", tags: "", categories: "", model: "free", price: "0", currency: "KRW", overwrite: false });
  const [res, setRes] = useState<{ rel?: Release; gate?: Gate; error?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    const listing = { ...(f.name_ko || f.name_en ? { name: { ko: f.name_ko || f.name_en, en: f.name_en || f.name_ko } } : {}),
      ...(f.tags ? { tags: csv(f.tags) } : {}), ...(f.categories ? { categories: csv(f.categories) } : {}),
      pricing: f.model === "free" ? "free" : { model: f.model, price: Number(f.price) || 0, currency: f.currency } };
    const form = new FormData();
    form.append("file", file);
    form.append("publisher", f.publisher);
    form.append("listing", JSON.stringify(listing));
    form.append("overwrite", String(f.overwrite));
    setBusy(true);
    try {
      const rel = await api<Release>("/api/market/releases", { form });
      setRes({ rel, gate: rel.gate });
      toast(`${rel.listing_id}@${rel.version} ${rel.status}`, "ok");
    } catch (x) {
      const d = x instanceof ApiError ? (x.detail as { message?: string; gate?: Gate }) : null;
      setRes({ error: errorText(x), gate: d?.gate ?? undefined });
    }
    setBusy(false);
  };
  return (
    <div className="stack">
      <h1>{t("pub.title")}</h1>
      <p className="sub">{t("pub.hint")}</p>
      <form className="card stack" onSubmit={submit}>
        <label className="field"><span>{t("pub.file")}</span><input type="file" accept=".zip" required onChange={(e) => setFile(e.target.files?.[0] ?? null)} /></label>
        <label className="field"><span>{t("pub.publisher")}</span>
          <input required list="pubs" pattern="[a-z0-9][a-z0-9-]{1,63}" value={f.publisher} onChange={(e) => setF({ ...f, publisher: e.target.value })} />
          <datalist id="pubs">{(pubs.data ?? []).filter((p) => me.role === "supervisor" || p.members.includes(me.email ?? "")).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</datalist></label>
        <div className="row">
          <label className="field" style={{ flex: 1 }}><span>{t("pub.name_ko")}</span><input value={f.name_ko} onChange={(e) => setF({ ...f, name_ko: e.target.value })} /></label>
          <label className="field" style={{ flex: 1 }}><span>{t("pub.name_en")}</span><input value={f.name_en} onChange={(e) => setF({ ...f, name_en: e.target.value })} /></label>
        </div>
        <div className="row">
          <label className="field" style={{ flex: 1 }}><span>{t("pub.tags")}</span><input value={f.tags} onChange={(e) => setF({ ...f, tags: e.target.value })} /></label>
          <label className="field" style={{ flex: 1 }}><span>{t("pub.categories")}</span><input value={f.categories} onChange={(e) => setF({ ...f, categories: e.target.value })} /></label>
        </div>
        <div className="row">
          <label className="field"><span>{t("pub.pricing")}</span>
            <select value={f.model} onChange={(e) => setF({ ...f, model: e.target.value })}>
              {["free", "subscription", "per_seat", "per_call"].map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
          {f.model !== "free" && <>
            <label className="field"><span>{t("pub.price")}</span><input type="number" min={0} value={f.price} onChange={(e) => setF({ ...f, price: e.target.value })} style={{ width: 140 }} /></label>
            <label className="field"><span>{t("pub.currency")}</span><input pattern="[A-Z]{3}" value={f.currency} onChange={(e) => setF({ ...f, currency: e.target.value })} style={{ width: 90 }} /></label>
          </>}
        </div>
        <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={f.overwrite} onChange={(e) => setF({ ...f, overwrite: e.target.checked })} />{t("pub.overwrite")}</label>
        <div><button className="btn primary" disabled={busy || !file}>{t("pub.submit")}</button></div>
      </form>
      {res?.error && <p role="alert" className="badge danger">{res.error}</p>}
      {res?.gate && <GateReport gate={res.gate} status={res.rel?.status ?? "blocked"} />}
      {res?.rel?.status === "published" && <Link className="btn" to={`/market/${res.rel.listing_id}`}>{res.rel.listing_id} →</Link>}
    </div>
  );
}

// ---- E07 퍼블리셔·심사·운영 배지 ----
export function PublishersPage() {
  const pubs = useApi<Publisher[]>("/api/market/publishers");
  const pending = useApi<Release[]>("/api/market/releases?status=pending");
  const toast = useToast();
  const [np, setNp] = useState({ id: "", name: "", url: "", members: "" });
  const [open, setOpen] = useState<string | null>(null);
  const [key, setKey] = useState({ name: "", public_key: "", rotate: false });
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [ops, setOps] = useState({ listing: "", featured_until: "", validated_ref: "", hidden: false });
  const run = async (f: () => Promise<unknown>, after?: () => void) => {
    try { await f(); toast("OK", "ok"); after?.(); } catch (x) { toast(errorText(x), "error"); }
  };
  const create = (e: FormEvent) => { e.preventDefault(); run(() => api("/api/market/publishers", { body: { ...np, url: np.url || undefined, members: csv(np.members) } }), () => { setNp({ id: "", name: "", url: "", members: "" }); pubs.reload(); }); };
  return (
    <div className="stack">
      <h1>{t("pubs.title")}</h1>
      <section className="card stack"><h2>{t("pubs.pending")}</h2>
        <StateView q={pending} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><tbody>{d.map((r) => (
            <tr key={r.id}><td><b>{r.listing_id}@{r.version}</b> <span className="sub">{r.publisher_id} · {r.submitted_by} · {fmtTime(r.created_at)}</span>
              <div className="sub mono">{String(r.gate.supply_chain?.signature)} · {String(r.gate.license?.effective)} · {(r.gate.warnings ?? []).length} warn</div></td>
              <td className="row"><button className="btn primary" onClick={() => run(() => api(`/api/market/releases/${r.id}/approve`, { method: "POST" }), pending.reload)}>{t("pubs.approve")}</button>
                <input aria-label={t("pubs.reason")} placeholder={t("pubs.reason")} value={reasons[r.id] ?? ""} onChange={(e) => setReasons({ ...reasons, [r.id]: e.target.value })} style={{ maxWidth: 200 }} />
                <button className="btn danger" disabled={(reasons[r.id] ?? "").trim().length < 2} onClick={() => run(() => api(`/api/market/releases/${r.id}/reject`, { body: { reason: reasons[r.id] } }), pending.reload)}>{t("pubs.reject")}</button></td></tr>))}
          </tbody></table>)}</StateView>
      </section>
      <section className="card stack"><h2>{t("pubs.title")}</h2>
        <StateView q={pubs} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><thead><tr><th>{t("pubs.name")}</th><th>{t("pubs.assets")}</th><th>{t("mk.stats")}</th><th>{t("pubs.keys")}</th><th /></tr></thead>
            <tbody>{d.map((p) => (<Fragment key={p.id}>
              <tr key={p.id}><td><b>{p.name}</b> <span className="mono sub">{p.id}</span> {p.verified && <Badge value="publisher:verified" />}</td>
                <td>{p.assets.length}</td><td>{p.downloads} / {p.installs}</td><td>{p.active_keys} / {p.keys.length}</td>
                <td className="row"><button className="btn" aria-expanded={open === p.id} onClick={() => setOpen(open === p.id ? null : p.id)}>{t("obs.detail")}</button>
                  <button className="btn" onClick={() => run(() => api(`/api/market/publishers/${p.id}`, { method: "PATCH", body: { verified: !p.verified } }), pubs.reload)}>{p.verified ? t("pubs.unverify") : t("pubs.verify")}</button></td></tr>
              {open === p.id && <tr key={`${p.id}-d`}><td colSpan={5}><div className="stack">
                <div className="sub">{t("pubs.members")}: {p.members.join(", ") || "—"} · {t("pubs.assets")}: {p.assets.join(", ") || "—"}</div>
                <ul>{p.keys.map((k) => <li key={k.kid} className="row"><span className="mono">{k.kid}</span> {k.name}
                  {k.revoked_at ? <Badge value="rejected" label={t("trust.revoked")} /> : <button className="btn" onClick={() => run(() => api(`/api/trust/keys/${k.kid}`, { method: "DELETE" }), pubs.reload)}>{t("trust.revoke")}</button>}</li>)}</ul>
                <form className="stack" onSubmit={(e) => { e.preventDefault(); run(() => api(`/api/market/publishers/${p.id}/keys`, { body: key }), () => { setKey({ name: "", public_key: "", rotate: false }); pubs.reload(); }); }}>
                  <input required placeholder={t("trust.key_name")} aria-label={t("trust.key_name")} value={key.name} onChange={(e) => setKey({ ...key, name: e.target.value })} />
                  <textarea required rows={3} className="mono" aria-label={t("trust.public_key")} placeholder="-----BEGIN PUBLIC KEY-----" value={key.public_key} onChange={(e) => setKey({ ...key, public_key: e.target.value })} />
                  <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={key.rotate} onChange={(e) => setKey({ ...key, rotate: e.target.checked })} />{t("pubs.rotate")}</label>
                  <div><button className="btn primary">{t("pubs.add_key")}</button></div>
                </form></div></td></tr>}
            </Fragment>))}</tbody></table>)}</StateView>
        <form className="row" onSubmit={create}>
          <input required placeholder={t("pubs.id")} aria-label={t("pubs.id")} pattern="[a-z0-9][a-z0-9-]{1,63}" value={np.id} onChange={(e) => setNp({ ...np, id: e.target.value })} style={{ maxWidth: 160 }} />
          <input required placeholder={t("pubs.name")} aria-label={t("pubs.name")} value={np.name} onChange={(e) => setNp({ ...np, name: e.target.value })} style={{ maxWidth: 180 }} />
          <input placeholder={t("pubs.url")} aria-label={t("pubs.url")} value={np.url} onChange={(e) => setNp({ ...np, url: e.target.value })} style={{ maxWidth: 220 }} />
          <input placeholder={t("pubs.members")} aria-label={t("pubs.members")} value={np.members} onChange={(e) => setNp({ ...np, members: e.target.value })} style={{ maxWidth: 260 }} />
          <button className="btn primary">{t("pubs.add")}</button>
        </form>
      </section>
      <form className="card stack" onSubmit={(e) => { e.preventDefault(); run(() => api(`/api/market/listings/${ops.listing}/ops`, { method: "PATCH", body: { hidden: ops.hidden, featured_until: ops.featured_until, validated_ref: ops.validated_ref || undefined } })); }}>
        <h2>{t("pubs.ops")}</h2>
        <div className="row">
          <input required placeholder={t("pubs.listing")} aria-label={t("pubs.listing")} value={ops.listing} onChange={(e) => setOps({ ...ops, listing: e.target.value })} style={{ maxWidth: 180 }} />
          <label className="row sub">{t("pubs.featured_until")}<input type="date" value={ops.featured_until} onChange={(e) => setOps({ ...ops, featured_until: e.target.value })} style={{ width: "auto" }} /></label>
          <input placeholder={t("pubs.validated_ref")} aria-label={t("pubs.validated_ref")} value={ops.validated_ref} onChange={(e) => setOps({ ...ops, validated_ref: e.target.value })} style={{ maxWidth: 180 }} />
          <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={ops.hidden} onChange={(e) => setOps({ ...ops, hidden: e.target.checked })} />{t("pubs.hidden")}</label>
          <button className="btn primary">{t("pubs.save")}</button>
        </div>
      </form>
    </div>
  );
}

// ---- E11 설치됨·업데이트·라이선스 ----
export function InstalledPage({ me }: { me: Me }) {
  const q = useApi<Installed[]>("/api/market/installed");
  const lics = useApi<Lic[]>("/api/licenses");
  const buys = useApi<Purchase[]>("/api/market/purchases");
  const toast = useToast();
  const [only, setOnly] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [rb, setRb] = useState("");
  const [installId, setInstallId] = useState<string | null>(null);
  const run = async (f: () => Promise<unknown>, after?: () => void) => {
    try { await f(); after?.(); } catch (x) { toast(errorText(x), "error"); }
  };
  const check = () => run(async () => {
    const r = await api<{ new: string[]; updates: unknown[] }>("/api/market/updates/check", { method: "POST" });
    toast(`${t("inst.new")}: ${r.new.length} · ${t("inst.update")}: ${r.updates.length}`, "ok");
  }, q.reload);
  const update = (a: Installed) => run(async () => setInstallId((await api<{ install_id: string }>(`/api/market/updates/${a.agent_id}`, { body: { consent } })).install_id));
  const rollback = (a: Installed) => run(async () => setInstallId((await api<{ install_id: string }>(`/api/agents/${a.agent_id}/rollback`, { body: { version: rb } })).install_id));
  return (
    <div className="stack">
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("inst.title")}</h1>
        <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={only} onChange={(e) => setOnly(e.target.checked)} />{t("inst.only_updates")}</label>
        <button className="btn primary" onClick={check}>{t("inst.check")}</button></div>
      {installId && <InstallProgress id={installId} onDone={() => { q.reload(); }} />}
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <table className="card responsive"><thead><tr><th>{t("pubs.name")}</th><th>{t("inst.latest")}</th><th>{t("market.installed")}</th><th>{t("inst.auto")}</th><th /></tr></thead>
          <tbody>{d.filter((a) => !only || a.update).map((a) => (<Fragment key={a.agent_id}>
            <tr key={a.agent_id}><td><b>{a.name}</b> <span className="mono sub">{a.agent_id}</span> <Badge value={a.status} />{!a.is_active && <Badge value="disabled" />}</td>
              <td className="mono">v{a.version}{a.update ? <> → <Badge value="warn" label={`v${a.update.version}`} /></> : a.latest ? "" : " · —"}</td>
              <td className="sub">{a.installed_by ?? "—"} · {fmtTime(a.installed_at)} · {a.origin ?? a.source}</td>
              <td><input type="checkbox" style={{ width: "auto" }} aria-label={`${t("inst.auto")} ${a.agent_id}`} checked={a.auto_update} onChange={(e) => run(() => api(`/api/market/auto-update/${a.agent_id}`, { method: "PUT", body: { enabled: e.target.checked } }), q.reload)} /></td>
              <td><button className="btn" aria-expanded={open === a.agent_id} onClick={() => { setOpen(open === a.agent_id ? null : a.agent_id); setConsent(false); setRb(""); }}>{a.update ? t("inst.update") : t("inst.rollback")}</button></td></tr>
            {open === a.agent_id && <tr key={`${a.agent_id}-x`}><td colSpan={5}><div className="stack">
              {a.update && <div className="stack"><b>{t("inst.diff")}</b>
                {DIFF_KEYS.some((k) => (a.update?.[k] as string[] | undefined)?.length) || a.update.data_class_raised
                  ? <ul>{DIFF_KEYS.filter((k) => (a.update?.[k] as string[]).length).map((k) => <li key={k} className="mono">{k}: {(a.update?.[k] as string[]).join(", ")}</li>)}
                    {a.update.data_class_raised && <li>dataClassification ↑</li>}</ul>
                  : <span className="sub">{t("inst.no_change")}</span>}
                {a.update.paid && !a.update.licensed && <Badge value="failed" label={t("inst.needs_license")} />}
                {a.update.needs_consent && <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={consent} onChange={(e) => setConsent(e.target.checked)} />{t("inst.consent")}</label>}
                <div><button className="btn primary" disabled={(a.update.needs_consent && !consent) || (a.update.paid && !a.update.licensed)} onClick={() => update(a)}>{t("inst.update")} → v{a.update.version}</button></div></div>}
              <div className="row"><b>{t("inst.rollback")}</b>
                <select aria-label={t("inst.rollback")} value={rb} onChange={(e) => setRb(e.target.value)} style={{ width: "auto" }}>
                  <option value="">—</option>{a.versions.filter((v) => !v.current).map((v) => <option key={v.version} value={v.version}>v{v.version} · {fmtTime(v.installed_at)}</option>)}</select>
                <button className="btn" disabled={!rb} onClick={() => rollback(a)}>{t("inst.rollback")}</button></div>
            </div></td></tr>}
          </Fragment>))}</tbody></table>)}</StateView>
      <section className="card stack"><h2>{t("lic.licenses")}</h2>
        <StateView q={lics} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><tbody>{d.map((l) => (
            <tr key={l.id}><td><b>{l.listing_id}</b> <span className="mono sub">{l.id} · {l.versions}</span></td>
              <td>{l.seats_used}/{l.seats} {t("lic.seats")} <div className="sub">{l.holders.map((h) => <span key={h} className="row">{h}
                <button className="btn" onClick={() => run(() => api(`/api/licenses/${l.id}/seats/${encodeURIComponent(h)}`, { method: "DELETE" }), lics.reload)}>{t("lic.release")}</button></span>)}</div></td>
              <td>{t("lic.expires")} {l.expires_at ? fmtTime(l.expires_at) : "∞"}</td>
              <td><Badge value={l.valid ? "ok" : "failed"} label={l.valid ? t("lic.valid") : t("lic.invalid")} />
                {me.role === "supervisor" && l.status === "active" && <button className="btn danger" onClick={() => run(() => api(`/api/licenses/${l.id}`, { method: "DELETE" }), lics.reload)}>{t("lic.revoke")}</button>}</td></tr>))}
          </tbody></table>)}</StateView>
      </section>
      <section className="card stack"><h2>{t("lic.purchases")}</h2>
        <StateView q={buys} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><tbody>{d.map((p) => (
            <tr key={p.id}><td><b>{p.listing_id}@{p.version}</b> <span className="sub">{fmtTime(p.created_at)}</span></td>
              <td>{p.amount.toLocaleString()} {p.currency} · {p.seats}×{p.months}</td><td className="mono sub">{p.adapter_ref}</td>
              <td><button className="btn" onClick={() => run(() => download(`/api/market/purchases/${p.id}/receipt`, `receipt-${p.id.slice(0, 8)}.json`, undefined, "GET"))}>{t("lic.receipt")}</button></td></tr>))}
          </tbody></table>)}</StateView>
      </section>
    </div>
  );
}

// ---- E13 원격 레지스트리·호스트 공개·오프라인 번들 ----
export function RegistriesPage() {
  const regs = useApi<Registry[]>("/api/market/registries");
  const expo = useApi<{ public: boolean; url: string }>("/api/market/registry-exposure");
  const toast = useToast();
  const [f, setF] = useState({ name: "", url: "https://", token: "", license_key: "", interval_minutes: "60" });
  const [ids, setIds] = useState("");
  const [bundle, setBundle] = useState<File | null>(null);
  const [overwrite, setOverwrite] = useState(false);
  const [report, setReport] = useState<unknown>(null);
  const run = async (f2: () => Promise<unknown>, after?: () => void) => {
    try { const r = await f2(); after?.(); return r; } catch (x) { toast(errorText(x), "error"); }
  };
  const save = (e: FormEvent) => {
    e.preventDefault();
    run(async () => {
      const r = await api<Registry>(`/api/market/registries/${f.name}`, { method: "PUT", body: { url: f.url, token: f.token || undefined,
        license_key: f.license_key || undefined, interval_minutes: Number(f.interval_minutes) || 0 } });
      toast(`${r.name}: ${r.status}`, r.status === "ok" ? "ok" : "error");
      setF({ ...f, token: "", license_key: "" });
    }, regs.reload);
  };
  const imp = (e: FormEvent) => {
    e.preventDefault();
    if (!bundle) return;
    const form = new FormData();
    form.append("file", bundle);
    form.append("overwrite", String(overwrite));
    run(async () => setReport(await api("/api/market/bundle", { form })));
  };
  return (
    <div className="stack">
      <h1>{t("reg.title")}</h1>
      <section className="card stack">
        <StateView q={regs} empty={(d) => !d.length}>{(d) => (
          <table className="responsive"><thead><tr><th>{t("reg.name")}</th><th>{t("pub.status")}</th><th>{t("reg.last")}</th><th>{t("reg.count")}</th><th /></tr></thead>
            <tbody>{d.map((r) => (
              <tr key={r.name}><td><b>{r.name}</b><div className="mono sub">{r.url}</div></td>
                <td><Badge value={r.status ?? "registered"} />{r.error && <div className="sub">{r.error}</div>}</td>
                <td>{r.last_sync ? fmtTime(r.last_sync) : "—"} <span className="sub">· {r.interval_minutes}m</span></td><td>{r.count ?? 0}</td>
                <td className="row"><button className="btn primary" onClick={() => run(async () => setReport(await api(`/api/market/registries/${r.name}/sync`, { body: {} })), regs.reload)}>{t("reg.sync")}</button>
                  <button className="btn danger" onClick={() => run(() => api(`/api/market/registries/${r.name}`, { method: "DELETE" }), regs.reload)}>{t("common.delete")}</button></td></tr>))}
            </tbody></table>)}</StateView>
        <form className="stack" onSubmit={save}>
          <div className="row">
            <label className="field"><span>{t("reg.name")}</span><input required pattern="[a-z0-9][a-z0-9-]{1,39}" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} style={{ width: 160 }} /></label>
            <label className="field" style={{ flex: 1 }}><span>{t("reg.url")}</span><input required value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })} /></label>
            <label className="field"><span>{t("reg.interval")}</span><input type="number" min={0} value={f.interval_minutes} onChange={(e) => setF({ ...f, interval_minutes: e.target.value })} style={{ width: 120 }} /></label>
          </div>
          <label className="field"><span>{t("reg.token")}</span><input type="password" autoComplete="off" value={f.token} onChange={(e) => setF({ ...f, token: e.target.value })} /></label>
          <label className="field"><span>{t("reg.license_key")}</span><textarea rows={3} className="mono" value={f.license_key} onChange={(e) => setF({ ...f, license_key: e.target.value })} /></label>
          <div><button className="btn primary">{t("reg.add")}</button></div>
        </form>
      </section>
      <StateView q={expo}>{(x) => (
        <section className="card stack">
          <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={x.public} onChange={(e) => run(() => api("/api/market/registry-exposure", { method: "PUT", body: { public: e.target.checked } }), expo.reload)} />{t("reg.expose")}</label>
          <div className="row"><code className="mono">{x.url}</code><button className="btn" onClick={() => navigator.clipboard?.writeText(x.url)}>{t("reg.copy")}</button></div>
        </section>)}</StateView>
      <section className="card stack"><h2>{t("reg.bundle")}</h2>
        <div className="row">
          <input placeholder={t("reg.export_ids")} aria-label={t("reg.export_ids")} value={ids} onChange={(e) => setIds(e.target.value)} style={{ maxWidth: 320 }} />
          <button className="btn" onClick={() => run(() => download(`/api/market/bundle${ids ? `?ids=${encodeURIComponent(ids)}` : ""}`, "agentplaza-market-bundle.tar.gz", undefined, "GET"))}>{t("reg.export")}</button>
        </div>
        <form className="row" onSubmit={imp}>
          <input type="file" accept=".gz,.tgz,.tar.gz" aria-label={t("reg.import")} onChange={(e) => setBundle(e.target.files?.[0] ?? null)} />
          <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={overwrite} onChange={(e) => setOverwrite(e.target.checked)} />{t("pub.overwrite")}</label>
          <button className="btn primary" disabled={!bundle}>{t("reg.import")}</button>
        </form>
      </section>
      {report != null && <section className="card" aria-live="polite"><h2>{t("reg.report")}</h2><pre className="mono" style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(report, null, 2)}</pre></section>}
    </div>
  );
}
