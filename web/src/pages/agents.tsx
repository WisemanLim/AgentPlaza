// D01 목록 · D02 상세 · D04 업로드 · D05 설치 진행(8단계) · D11 원격 등록 · N01 Addon iframe 마운트(postMessage v1)
import { type FormEvent, useEffect, useRef, useState } from "react";
import type { Me } from "../App";
import { api, download } from "../api";
import { Badge, Dot, errorText, fmtTime, Link, Modal, StateView, useApi, useToast } from "../components/ui";
import { getLocale, t } from "../i18n";
import { navigate } from "../router";
import { type Scope, ScopeSection } from "./orgs";

export type AgentRow = { id: string; name: string; type: string; version: string; status: string; is_active: boolean;
  builtin: boolean; source: string; trust: string; has_frontend: boolean; nav_visible: boolean;
  capabilities: { verb: string; domain: string; description: string; approval: boolean }[] };
type AgentDetail = AgentRow & { endpoint: string | null; manifest: Record<string, any>;
  deploy_scope?: Scope | null;
  versions: { version: string; current: boolean; sha256: string; installed_at: string; signature: string; signer: string | null;
    license_grade: string | null; vulns: { status: string; critical: number; high: number } | null; sbom: boolean }[] };
type Install = { id: string; agent_id: string | null; status: string; step: number; error: string | null; warnings: string[];
  steps: { n: number; name: string; status: string; detail?: unknown }[] };

const isAdmin = (me: Me) => me.role === "admin" || me.role === "supervisor";

export function AgentsPage({ me }: { me: Me }) {
  const q = useApi<AgentRow[]>("/api/agents");
  return (
    <>
      <div className="row"><h1 style={{ marginRight: "auto" }}>{t("agents.title")}</h1>
        {isAdmin(me) && <><Link className="btn" to="/agents/link">{t("agents.link")}</Link><Link className="btn primary" to="/agents/upload">{t("agents.upload")}</Link></>}
      </div>
      <StateView q={q} empty={(d) => !d.length}>{(d) => (
        <table className="responsive card">
          <thead><tr><th>ID</th><th>{t("common.status")}</th><th>{t("common.version")}</th><th>{t("agents.capabilities")}</th><th /></tr></thead>
          <tbody>{d.map((a) => (
            <tr key={a.id}>
              <td><Link to={`/agents/${a.id}`}><b>{a.name}</b></Link> <span className="sub mono">{a.id}</span><div className="row" style={{ marginTop: 4 }}>
                {a.builtin && <Badge value="official" label={t("agents.builtin")} />}<Badge value={a.trust} /><Badge value={a.source} label={a.source} /></div></td>
              <td><Dot value={a.is_active ? a.status : "disabled"} /> {a.is_active ? a.status : "disabled"}</td>
              <td className="mono">{a.version}</td>
              <td>{a.capabilities.map((c) => <span key={c.verb} className="badge" style={{ marginRight: 4 }}>{c.verb}{c.approval ? " ⚠" : ""}</span>)}</td>
              <td className="row">{a.nav_visible && <Link className="btn" to={`/addon/${a.id}`}>{t("agents.open_ui")}</Link>}
                {!a.builtin && <Link className="btn" to={`/chat?scope=${a.id}`}>{t("agents.chat")}</Link>}</td>
            </tr>))}
          </tbody>
        </table>
      )}</StateView>
    </>
  );
}

export function AgentDetailPage({ id, me }: { id: string; me: Me }) {
  const q = useApi<AgentDetail>(`/api/agents/${id}`);
  const toast = useToast();
  const [confirm, setConfirm] = useState(false);
  const [typed, setTyped] = useState("");
  const run = async (f: () => Promise<unknown>, ok: string) => { try { await f(); toast(ok, "ok"); q.reload(); } catch (e) { toast(errorText(e), "error"); } };
  return (
    <StateView q={q}>{(a) => {
      const fed = a.manifest?.spec?.federation;
      const base = window.location.origin;
      return (
        <div className="stack">
          <div className="row"><h1 style={{ marginRight: "auto" }}>{a.name} <span className="sub mono">{a.id}</span></h1>
            <Badge value={a.status} /><Badge value={a.trust} /></div>
          <div className="row">
            {a.nav_visible && <Link className="btn" to={`/addon/${a.id}`}>{t("agents.open_ui")}</Link>}
            {!a.builtin && <Link className="btn" to={`/chat?scope=${a.id}`}>{t("agents.chat")}</Link>}
            {isAdmin(me) && !a.builtin && <>
              <button className="btn" onClick={() => run(() => api(`/api/agents/${a.id}`, { method: "PATCH", body: { is_active: !a.is_active } }), "OK")}>
                {a.is_active ? t("agents.deactivate") : t("agents.activate")}</button>
              {a.source !== "link" && <button className="btn" onClick={() => run(() => download(`/api/agents/${a.id}/export-standalone`, `${a.id}-${a.version}-standalone.zip`), "OK")}>{t("agents.export")}</button>}
              {a.source === "link" && <button className="btn" onClick={() => run(() => api(`/api/agents/${a.id}/revalidate`, { method: "POST" }), "OK")}>{t("agents.revalidate")}</button>}
              {a.source !== "link" && <button className="btn" onClick={() => run(() => api(`/api/agents/${a.id}/rotate-key`, { method: "POST" }), "OK")}>{t("agents.rotate_key")}</button>}
              <button className="btn danger" onClick={() => setConfirm(true)}>{t("common.delete")}</button>
            </>}
          </div>
          <section className="card"><h2>{t("agents.capabilities")}</h2>
            <ul>{a.capabilities.map((c) => <li key={c.verb}><b>{c.verb}</b> <span className="mono sub">{c.domain}</span> — {c.description}{c.approval && <> <Badge value="pending" label="approval" /></>}</li>)}</ul>
          </section>
          <section className="card"><h2>{t("agents.protocols")}</h2>
            <table><tbody>
              {!a.builtin && a.source !== "link" && <>
                <tr><th>MCP</th><td className="mono">{base}/mcp/{a.id}</td></tr>
                <tr><th>A2A card</th><td className="mono"><a href={`/a/${a.id}/.well-known/agent-card.json`} target="_blank" rel="noreferrer">{base}/a/{a.id}/.well-known/agent-card.json</a></td></tr>
                <tr><th>REST</th><td className="mono">{base}/a/{a.id}/api/invoke/&lt;verb&gt;</td></tr>
              </>}
              {fed && <tr><th>{fed.kind}</th><td className="mono">{fed.url} · pin {String(fed.pin).slice(0, 12)} · {fed.signature}</td></tr>}
              {a.builtin && <tr><th>MCP</th><td className="mono">{a.id === "orchestrator" ? `${base}/mcp/orchestrator` : "—"}</td></tr>}
            </tbody></table>
          </section>
          {a.versions.length > 0 && <section className="card"><h2>{t("agents.versions")}</h2>
            <table><tbody>{a.versions.map((v) => (
              <tr key={v.version}><td className="mono">{v.version}{v.current && " ✓"}</td><td>{fmtTime(v.installed_at)}</td>
                <td className="row"><Badge value={`signature:${v.signature}`} />{v.signer && <span className="mono sub">{v.signer}</span>}
                  {v.license_grade && <Badge value={["G4", "G5"].includes(v.license_grade) ? "warn" : "ok"} label={`${t("supply.license")} ${v.license_grade}`} />}
                  {v.vulns && <Badge value={v.vulns.status !== "scanned" ? "pending" : v.vulns.critical || v.vulns.high ? "warn" : "ok"}
                    label={`${t("supply.vulns")} ${v.vulns.status === "scanned" ? `C${v.vulns.critical}·H${v.vulns.high}` : t("supply.unscanned")}`} />}
                  {v.sbom && v.current && <button className="btn" onClick={() => run(() => download(`/api/agents/${a.id}/sbom`, `${a.id}-${v.version}.cdx.json`, undefined, "GET"), "OK")}>{t("supply.sbom")}</button>}</td>
                <td>{!v.current && isAdmin(me) && <button className="btn" onClick={() => run(async () => {
                  const r = await api<{ install_id: string }>(`/api/agents/${a.id}/rollback`, { body: { version: v.version } });
                  navigate(`/agents/upload?install=${r.install_id}`);
                }, "OK")}>{t("agents.rollback")}</button>}</td></tr>))}</tbody></table>
          </section>}
          {isAdmin(me) && !a.builtin && <ScopeSection id={a.id} current={a.deploy_scope ? { org_id: a.deploy_scope.org_id, kind: a.deploy_scope.kind, ids: a.deploy_scope.ids } : null} />}
          {isAdmin(me) && !a.builtin && a.source !== "link" && <BackupsSection id={a.id} />}
          <Modal open={confirm} title={t("common.delete")} onClose={() => setConfirm(false)}>
            <form className="stack" onSubmit={async (e) => { e.preventDefault(); await run(() => api(`/api/agents/${a.id}`, { method: "DELETE" }), "OK"); setConfirm(false); navigate("/agents"); }}>
              <label className="field"><span>{t("agents.delete_confirm")}: <b className="mono">{a.id}</b></span><input value={typed} onChange={(e) => setTyped(e.target.value)} autoFocus /></label>
              <div className="row"><button className="btn danger" disabled={typed !== a.id}>{t("common.delete")}</button>
                <button type="button" className="btn" onClick={() => setConfirm(false)}>{t("common.cancel")}</button></div>
            </form>
          </Modal>
        </div>
      );
    }}</StateView>
  );
}

// 3·4단계 판정 요지(서명·취약점·라이선스 등급)를 한 줄로
function stepFacts(d: unknown) {
  if (!d || typeof d !== "object") return null;
  const x = d as { signature?: string; vulns?: { status: string; critical: number; high: number }; grade?: string; effective?: string };
  return (<>
    {x.signature && <Badge value={`signature:${x.signature}`} />}
    {x.vulns && <span className="sub">{t("supply.vulns")} {x.vulns.status === "scanned" ? `C${x.vulns.critical}·H${x.vulns.high}` : t("supply.unscanned")}</span>}
    {x.effective && <span className="sub">{t("supply.license")} {x.effective}</span>}
  </>);
}

type Backup = { backup: string; volumes?: { volume: string; bytes?: number }[] };

// D8-06: 볼륨 백업(일시정지 스냅숏)·복원. 업그레이드는 자동으로 사전 백업한다(NFR-O4).
function BackupsSection({ id }: { id: string }) {
  const q = useApi<{ backups: Backup[] }>(`/api/agents/${id}/backups`);
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const act = async (f: () => Promise<unknown>) => {
    setBusy(true);
    try { await f(); toast("OK", "ok"); q.reload(); } catch (e) { toast(errorText(e), "error"); }
    setBusy(false);
  };
  return (
    <section className="card stack"><div className="row"><h2 style={{ marginRight: "auto" }}>{t("backup.title")}</h2>
      <button className="btn" disabled={busy} onClick={() => act(() => api(`/api/agents/${id}/backup`, { method: "POST" }))}>{t("backup.now")}</button></div>
      <StateView q={q} empty={(d) => !d.backups.length}>{(d) => (
        <table><tbody>{d.backups.slice(0, 10).map((b) => (
          <tr key={b.backup}><td className="mono">{b.backup}</td>
            <td className="sub">{(b.volumes ?? []).map((v) => `${v.volume}${v.bytes ? ` ${Math.ceil(v.bytes / 1024)}KB` : ""}`).join(", ")}</td>
            <td><button className="btn" disabled={busy} onClick={() => window.confirm(t("backup.confirm")) &&
              act(() => api(`/api/agents/${id}/restore`, { body: { backup: b.backup } }))}>{t("backup.restore")}</button></td></tr>))}
        </tbody></table>)}</StateView>
    </section>
  );
}

export function InstallProgress({ id, onDone }: { id: string; onDone?: (i: Install) => void }) {
  const [inst, setInst] = useState<Install | null>(null);
  const done = useRef(onDone);
  done.current = onDone; // 렌더마다 바뀌는 콜백이 폴링을 재시작하지 않게
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      const i = await api<Install>(`/api/agents/installs/${id}`).catch(() => null);
      if (!alive || !i) return;
      setInst(i);
      if (["succeeded", "failed", "rolled_back"].includes(i.status)) done.current?.(i); else setTimeout(tick, 1500);
    };
    tick();
    return () => { alive = false; };
  }, [id]);
  if (!inst) return <p className="sub">{t("common.loading")}</p>;
  return (
    <section className="card stack" aria-live="polite" aria-label={t("agents.install_progress")}>
      <div className="row"><b>{inst.agent_id ?? id}</b><Badge value={inst.status} /></div>
      <ol className="stack" style={{ margin: 0 }}>{inst.steps.map((s) => (
        <li key={s.n} className="row"><Dot value={s.status === "ok" ? "ok" : s.status === "failed" ? "failed" : s.status === "skipped" || s.status === "warn" ? "pending" : "registered"} />
          {s.name} <span className="sub">{s.status}</span>{stepFacts(s.detail)}</li>))}</ol>
      {inst.error && <p className="alert" role="alert">{inst.error}</p>}
      {inst.warnings.map((w) => <p key={w} className="alert warn">{w}</p>)}
      {inst.status === "succeeded" && inst.agent_id && <Link className="btn primary" to={`/agents/${inst.agent_id}`}>{inst.agent_id} →</Link>}
    </section>
  );
}

export function UploadPage() {
  const toast = useToast();
  const [files, setFiles] = useState<FileList | null>(null);
  const [env, setEnv] = useState("");
  const [installs, setInstalls] = useState<string[]>(() => {
    const p = new URLSearchParams(window.location.search).get("install");
    return p ? [p] : [];
  });
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!files?.length) return;
    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f));
    const envObj = Object.fromEntries(env.split("\n").map((l) => l.trim()).filter((l) => l.includes("=")).map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1)]));
    form.append("env", JSON.stringify(envObj));
    try {
      const r = await api<{ filename: string; install_id?: string; error?: string }[]>("/api/agents/upload", { form, method: "POST" });
      r.filter((x) => x.error).forEach((x) => toast(`${x.filename}: ${x.error}`, "error"));
      setInstalls(r.filter((x) => x.install_id).map((x) => x.install_id!));
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <div className="stack">
      <h1>{t("agents.upload")}</h1>
      <form className="card stack" onSubmit={submit}>
        <label className="field"><span>{t("agents.files")}</span><input type="file" accept=".zip" multiple onChange={(e) => setFiles(e.target.files)} /></label>
        <label className="field"><span>{t("market.required_env")} (KEY=VALUE)</span><textarea rows={3} className="mono" value={env} onChange={(e) => setEnv(e.target.value)} /></label>
        <button className="btn primary" disabled={!files?.length}>{t("agents.upload")}</button>
      </form>
      {installs.map((id) => <InstallProgress key={id} id={id} />)}
    </div>
  );
}

export function LinkPage() {
  const toast = useToast();
  const [f, setF] = useState({ kind: "a2a", url: "", id: "", auth_header: "x-api-key", auth_value: "", base_url: "" });
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const a = await api<{ id: string }>("/api/agents/link", { body: { ...f, id: f.id || undefined, auth_value: f.auth_value || undefined,
        base_url: f.kind === "openapi" && f.base_url ? f.base_url : undefined } });
      toast(`${a.id} OK`, "ok"); navigate(`/agents/${a.id}`);
    } catch (x) { toast(errorText(x), "error"); }
  };
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  return (
    <form className="card stack" onSubmit={submit} style={{ maxWidth: 640 }}>
      <h1>{t("agents.link")}</h1>
      <label className="field"><span>{t("agents.kind")}</span><select value={f.kind} onChange={set("kind")}><option value="a2a">A2A Agent Card</option><option value="mcp">MCP server</option><option value="openapi">OpenAPI (REST)</option></select></label>
      <label className="field"><span>{t("agents.url")}</span><input type="url" required value={f.url} onChange={set("url")} /></label>
      {f.kind === "openapi" && <label className="field"><span>{t("agents.base_url")}</span><input type="url" value={f.base_url} onChange={set("base_url")} /></label>}
      <label className="field"><span>ID</span><input pattern="[a-z][a-z0-9-]{1,40}" value={f.id} onChange={set("id")} /></label>
      <label className="field"><span>{t("agents.auth_header")}</span><input value={f.auth_header} onChange={set("auth_header")} /></label>
      <label className="field"><span>{t("agents.auth_value")}</span><input type="password" autoComplete="off" value={f.auth_value} onChange={set("auth_value")} /></label>
      <button className="btn primary">{t("agents.register")}</button>
    </form>
  );
}

type UiMount = { mount: string; src: string | null; origin: string; fallback_chat: string; sandbox: string };

export function AddonPage({ id }: { id: string }) {
  const q = useApi<UiMount>(`/api/agents/${id}/ui`);
  const toast = useToast();
  const frame = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(600);
  useEffect(() => {
    if (q.data && q.data.mount !== "iframe") navigate(`/chat?scope=${id}`, true); // 화면 없는 에이전트 → 스코프 채팅(NFR-U5)
  }, [q.data, id]);
  useEffect(() => {
    const origin = q.data?.origin;
    if (!origin) return;
    const onMsg = (e: MessageEvent) => {
      if (e.origin !== origin || e.source !== frame.current?.contentWindow) return; // 출처 화이트리스트
      const m = e.data as { type?: string; height?: number; text?: string; path?: string };
      if (m.type === "plaza:resize" && m.height) setHeight(Math.min(Math.max(m.height + 24, 200), 4000));
      if (m.type === "plaza:notify" && m.text) toast(String(m.text).slice(0, 200), "info");
      if (m.type === "plaza:navigate" && m.path?.startsWith("/")) navigate(m.path);
    };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, [q.data, toast]);
  return (
    <StateView q={q}>{(u) => u.mount !== "iframe" || !u.src ? null : (
      <iframe ref={frame} className="addon" title={`${id} UI`} src={u.src} sandbox={u.sandbox} style={{ height }}
        onLoad={() => frame.current?.contentWindow?.postMessage({ type: "plaza:context", version: 1, locale: getLocale(),
          theme: document.documentElement.dataset.theme ?? "system" }, u.origin)} />
    )}</StateView>
  );
}
