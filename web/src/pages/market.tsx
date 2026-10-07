// E01 카탈로그 · E02 3축 브라우즈 · E03 상세 · E04 도입(필수 env 폼 → 8단계 진행). 원격 리스팅은 경로 C 연동.
import { type FormEvent, useEffect, useRef, useState } from "react";
import type { Me } from "../App";
import { api, download } from "../api";
import { Badge, errorText, Link, StateView, useApi, useToast } from "../components/ui";
import { getLocale, t } from "../i18n";
import { InstallProgress } from "./agents";
import { type Scope, ScopePicker } from "./orgs";

type Listing = { id: string; version: string; type: string; name: { ko: string; en: string } | string;
  description: { ko: string; en: string } | string; categories: string[]; industry: string; work: string; domain: string;
  tags: string[]; publisher: { id: string; name?: string; verified?: boolean }; license: string; trust: string;
  capabilities: string[]; approval?: string[]; required_env: string[]; hasFrontend?: boolean;
  permissions?: { egress: string[]; dataClassification?: string }; source: { type: string };
  badges: string[]; installed: { version: string; status: string; update_available: boolean } | null;
  readme?: string; changelog?: string; pricing: Pricing; paid: boolean; licensed?: boolean | null; origin?: string;
  stats?: Record<string, number> };
export type Pricing = { model: string; price?: number; currency?: string };
type Check = { check: string; ok: boolean; detail: unknown };
type Cats = { industries: { industry: string; name: string; children: { slug: string; name: string }[] }[];
  work: Record<string, string>; domains: Record<string, string> };

const loc = (v: Listing["name"]) => (typeof v === "string" ? v : v[getLocale()] ?? v.ko);
const isAdmin = (me: Me) => me.role === "admin" || me.role === "supervisor";
export const priceText = (p: Pricing) =>
  p.model === "free" ? t("mk.free") : `${(p.price ?? 0).toLocaleString()} ${p.currency ?? ""}${t(`mk.${p.model}`)}`;
const quote = (p: Pricing, seats: number, months: number) =>
  p.model === "per_seat" ? (p.price ?? 0) * seats * months : p.model === "subscription" ? (p.price ?? 0) * months : 0;

export function MarketPage({ me }: { me: Me }) {
  const cats = useApi<Cats>("/api/market/categories");
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [domain, setDomain] = useState("");
  const qs = new URLSearchParams(Object.entries({ q, category, domain }).filter(([, v]) => v)).toString();
  const list = useApi<Listing[]>(`/api/market/listings${qs ? `?${qs}` : ""}`);
  return (
    <div className="stack">
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("market.title")}</h1>
        {isAdmin(me) && <Link className="btn" to="/market/installed">{t("nav.installed")}</Link>}
        {isAdmin(me) && <Link className="btn" to="/market/publish">{t("mk.publish")}</Link>}
        {me.role === "supervisor" && <Link className="btn" to="/market/publishers">{t("mk.publishers")}</Link>}</div>
      <form className="row card" role="search" onSubmit={(e) => e.preventDefault()}>
        <label className="sr-only" htmlFor="mq">{t("common.search")}</label>
        <input id="mq" placeholder={t("common.search")} value={q} onChange={(e) => setQ(e.target.value)} style={{ maxWidth: 280 }} />
        <label className="row sub">{t("market.industry")}·{t("market.work")}
          <select value={category} onChange={(e) => setCategory(e.target.value)} style={{ width: "auto" }}>
            <option value="">{t("market.all")}</option>
            {cats.data?.industries.map((i) => <optgroup key={i.industry} label={i.name}>{i.children.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</optgroup>)}
          </select></label>
        <label className="row sub">{t("market.domain")}
          <select value={domain} onChange={(e) => setDomain(e.target.value)} style={{ width: "auto" }}>
            <option value="">{t("market.all")}</option>
            {Object.entries(cats.data?.domains ?? {}).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select></label>
      </form>
      <StateView q={list} empty={(d) => !d.length}>{(d) => (
        <div className="grid">{d.map((x) => (
          <article key={x.id} className="card stack" aria-labelledby={`l-${x.id}`}>
            <div className="row"><h2 id={`l-${x.id}`} style={{ margin: 0, fontSize: 16 }}><Link to={`/market/${x.id}`}>{loc(x.name)}</Link></h2>
              <span className="sub mono" style={{ marginLeft: "auto" }}>v{x.version}</span></div>
            <p className="sub" style={{ margin: 0 }}>{loc(x.description)}</p>
            <div className="row">{x.badges.map((b) => <Badge key={b} value={b} />)}
              {x.paid && <Badge value="info" label={priceText(x.pricing)} />}</div>
            <div className="row sub" style={{ fontSize: 12 }}>{x.capabilities.join(" · ")}</div>
            <div className="row">
              {x.installed ? <Badge value="ok" label={x.installed.update_available ? t("market.update") : t("market.installed")} /> : null}
              {isAdmin(me) && (!x.installed || x.installed.update_available) && <Link className="btn primary" to={`/market/${x.id}`}>{t("market.install")}</Link>}
            </div>
          </article>))}</div>
      )}</StateView>
    </div>
  );
}

export function MarketDetailPage({ id, me }: { id: string; me: Me }) {
  const q = useApi<Listing>(`/api/market/listings/${id}`);
  const params = new URLSearchParams(typeof window === "undefined" ? "" : window.location.search);
  const returned = params.get("purchase");  // 결제 페이지에서 돌아옴 → 웹훅 확인까지 상태를 본다
  const cancelled = params.has("cancelled");
  const toast = useToast();
  const [env, setEnv] = useState<Record<string, string>>({});
  const [auth, setAuth] = useState({ auth_header: "x-api-key", auth_value: "" });
  const [scope, setScope] = useState<Scope | null>(null);  // 조직 도입(FL-07) 배치 대상
  const [installId, setInstallId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const install = async (e: FormEvent, x: Listing) => {
    e.preventDefault();
    setBusy(true);
    try {
      const remote = x.source.type.startsWith("remote-");
      const r = await api<{ path: string; install_id?: string; agent_id?: string }>(`/api/market/install/${x.id}`, {
        body: { ...(remote ? { ...auth, auth_value: auth.auth_value || undefined } : { env, force: !!x.installed }),
                deploy_scope: scope ?? undefined } });
      if (r.install_id) setInstallId(r.install_id); else { toast(`${r.agent_id} OK`, "ok"); q.reload(); }
    } catch (x2) { toast(errorText(x2), "error"); }
    setBusy(false);
  };
  return (
    <StateView q={q}>{(x) => (
      <div className="stack">
        <div className="row"><h1 style={{ marginRight: "auto" }}>{loc(x.name)} <span className="sub mono">{x.id} v{x.version}</span></h1>
          {x.badges.map((b) => <Badge key={b} value={b} />)}</div>
        <p>{loc(x.description)}</p>
        <section className="card"><table><tbody>
          <tr><th>{t("market.publisher")}</th><td>{x.publisher.name ?? x.publisher.id} {x.publisher.verified && "✓"}</td></tr>
          <tr><th>{t("market.license")}</th><td>{x.license}</td></tr>
          <tr><th>{t("agents.capabilities")}</th><td>{x.capabilities.map((c) => <span key={c} className="badge" style={{ marginRight: 4 }}>{c}{x.approval?.includes(c) ? " ⚠" : ""}</span>)}</td></tr>
          <tr><th>{t("market.permissions")}</th><td>egress: {x.permissions?.egress?.length ? x.permissions.egress.join(", ") : "—"} · data: {x.permissions?.dataClassification ?? "—"} · docker: ✕</td></tr>
          <tr><th>{t("market.industry")}/{t("market.work")}/{t("market.domain")}</th><td>{x.industry} / {x.work} / {x.domain}</td></tr>
          <tr><th>{t("mk.price")}</th><td>{priceText(x.pricing)}</td></tr>
          <tr><th>{t("mk.origin")} · {t("mk.stats")}</th><td>{x.origin ?? "static"} · {Object.entries(x.stats ?? {}).map(([k, v]) => `${k} ${v}`).join(" · ") || "—"}</td></tr>
        </tbody></table></section>
        {isAdmin(me) && returned && <PurchaseStatus id={returned} cancelled={cancelled} onPaid={() => q.reload()} />}
        {isAdmin(me) && x.paid && !x.licensed && <LicensePanel x={x} onDone={() => q.reload()} />}
        {x.installed && <div className="row card"><Badge value="ok" label={`${t("market.installed")} v${x.installed.version}`} />
          <Badge value={x.installed.status} /><Link className="btn" to={`/agents/${x.id}`}>{t("market.open")}</Link></div>}
        {isAdmin(me) && !installId && (!x.paid || x.licensed) && (!x.installed || x.installed.update_available) && (
          <form className="card stack" onSubmit={(e) => install(e, x)}>
            {x.source.type.startsWith("remote-") ? <>
              <label className="field"><span>{t("agents.auth_header")}</span><input value={auth.auth_header} onChange={(e) => setAuth({ ...auth, auth_header: e.target.value })} /></label>
              <label className="field"><span>{t("agents.auth_value")}</span><input type="password" value={auth.auth_value} onChange={(e) => setAuth({ ...auth, auth_value: e.target.value })} /></label>
            </> : x.required_env.map((k) => (
              <label key={k} className="field"><span>{t("market.required_env")}: <b className="mono">{k}</b></span>
                <input required value={env[k] ?? ""} onChange={(e) => setEnv({ ...env, [k]: e.target.value })} /></label>
            ))}
            {!x.installed && <ScopePicker value={scope} onChange={setScope} />}
            <button className="btn primary" disabled={busy}>{x.installed ? t("market.update") : t("market.install")}</button>
          </form>
        )}
        {installId && <InstallProgress id={installId} onDone={() => q.reload()} />}
        {x.readme && <section className="card"><h2>{t("market.readme")}</h2><pre className="mono" style={{ whiteSpace: "pre-wrap" }}>{x.readme}</pre></section>}
      </div>
    )}</StateView>
  );
}

// E12 구매·라이선스: 키 직접 입력(오프라인 검증 체크리스트) 또는 결제 어댑터로 발급 → 영수증. 정산·세금은 범위 밖.
function LicensePanel({ x, onDone }: { x: Listing; onDone: () => void }) {
  const inst = useApi<{ payment_adapter: string }>("/api/market/instance");
  const toast = useToast();
  const payable = inst.data?.payment_adapter !== "none" && !(x.origin ?? "").startsWith("registry:");
  const [mode, setMode] = useState<"key" | "pay">("key");
  const [key, setKey] = useState("");
  const [checks, setChecks] = useState<Check[] | null>(null);
  const [seats, setSeats] = useState(1);
  const [months, setMonths] = useState(1);
  const [receipt, setReceipt] = useState<string | null>(null);
  const run = async (f: () => Promise<void>) => { try { await f(); } catch (e) { toast(errorText(e), "error"); } };
  const verify = () => run(async () => setChecks((await api<{ checks: Check[] }>("/api/licenses/verify", { body: { key, listing: x.id } })).checks));
  const register = () => run(async () => { await api("/api/licenses", { body: { key, listing: x.id } }); toast("OK", "ok"); onDone(); });
  const buy = () => run(async () => {
    const r = await api<{ purchase: { id: string }; checkout_url?: string }>(`/api/market/purchase/${x.id}`, { body: { seats, months } });
    if (r.checkout_url) { window.location.assign(r.checkout_url); return; }  // 호스티드 결제(Stripe·Polar·Lago) — 카드 정보는 결제대행만
    setReceipt(r.purchase.id); toast("OK", "ok");
  });
  return (
    <section className="card stack" aria-labelledby="lic-h">
      <h2 id="lic-h">{t("lic.title")} <span className="sub">{priceText(x.pricing)}</span></h2>
      <p className="sub">{t("lic.note")}</p>
      <div className="row" role="radiogroup">
        <label className="row"><input type="radio" style={{ width: "auto" }} checked={mode === "key"} onChange={() => setMode("key")} />{t("lic.mode_key")}</label>
        <label className="row"><input type="radio" style={{ width: "auto" }} checked={mode === "pay"} disabled={!payable} onChange={() => setMode("pay")} />{t("lic.mode_pay")}</label>
      </div>
      {!payable && <p className="sub">{t("lic.no_adapter")}</p>}
      {mode === "key" ? <>
        <label className="field"><span>{t("lic.key")}</span>
          <textarea rows={3} className="mono" value={key} onChange={(e) => { setKey(e.target.value); setChecks(null); }} /></label>
        <div className="row"><button className="btn" disabled={!key.trim()} onClick={verify}>{t("lic.verify")}</button>
          <button className="btn primary" disabled={!checks?.every((c) => c.ok)} onClick={register}>{t("lic.register")}</button></div>
        {checks && <ul className="stack" aria-label={t("lic.verify")}>{checks.map((c) => (
          <li key={c.check}><Badge value={c.ok ? "ok" : "failed"} label={c.ok ? "✓" : "✕"} /> {t(`lic.check.${c.check}`)} <span className="sub mono">{String(c.detail ?? "")}</span></li>))}</ul>}
      </> : <>
        <div className="row">
          <label className="field"><span>{t("lic.seats")}</span><input type="number" min={1} max={1000} value={seats} onChange={(e) => setSeats(Number(e.target.value) || 1)} style={{ width: 100 }} /></label>
          <label className="field"><span>{t("lic.months")}</span><input type="number" min={1} max={36} value={months} onChange={(e) => setMonths(Number(e.target.value) || 1)} style={{ width: 100 }} /></label>
          <span><span className="sub">{t("lic.amount")}</span><div><b>{quote(x.pricing, seats, months).toLocaleString()} {x.pricing.currency}</b></div></span>
        </div>
        <div><button className="btn primary" disabled={!!receipt} onClick={buy}>{t("lic.pay")}</button></div>
      </>}
      {receipt && <div className="row"><button className="btn" onClick={() => run(() => download(`/api/market/purchases/${receipt}/receipt`, `receipt-${receipt.slice(0, 8)}.json`, undefined, "GET"))}>{t("lic.receipt")}</button>
        <button className="btn primary" onClick={onDone}>{t("market.install")} →</button></div>}
    </section>
  );
}

// 호스티드 결제 복귀(E12): 결제대행 웹훅이 오면 paid → 라이선스 발급. pending 동안 2초마다 확인
function PurchaseStatus({ id, cancelled, onPaid }: { id: string; cancelled: boolean; onPaid: () => void }) {
  const [st, setSt] = useState<{ status: string; amount: number; currency: string } | null>(null);
  const done = useRef(onPaid);
  done.current = onPaid;
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      const r = await api<{ status: string; amount: number; currency: string }>(`/api/market/purchases/${id}`).catch(() => null);
      if (!alive || !r) return;
      setSt(r);
      if (r.status === "pending" && !cancelled) setTimeout(tick, 2000); else if (r.status === "paid") done.current();
    };
    tick();
    return () => { alive = false; };
  }, [id, cancelled]);
  if (!st) return null;
  return (
    <section className="card row" aria-live="polite">
      <b>{t("lic.title")}</b>
      <Badge value={st.status === "paid" ? "ok" : st.status === "pending" ? "warn" : "failed"}
        label={cancelled && st.status === "pending" ? t("lic.cancelled") : t(`lic.status.${st.status}`)} />
      <span className="mono">{st.amount.toLocaleString()} {st.currency}</span>
      {st.status === "paid" && <button className="btn" onClick={() => download(`/api/market/purchases/${id}/receipt`, `receipt-${id.slice(0, 8)}.json`, undefined, "GET")}>{t("lic.receipt")}</button>}
    </section>
  );
}
