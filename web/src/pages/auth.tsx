// A01 로그인 · A02 설치 위저드(관리자 → LLM 연결 → 모델 → 기본 에이전트 → 완료, 진행은 서버에 저장)
import { type FormEvent, useEffect, useState } from "react";
import { api, ApiError, setToken } from "../api";
import { errorText, Stepper, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

type Token = { access_token: string };

function centered(children: React.ReactNode) {
  return <main style={{ display: "grid", placeItems: "center", minHeight: "100vh" }}><div className="card stack" style={{ width: "min(400px, 92vw)" }}>{children}</div></main>;
}

export function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      const r = await api<Token>("/api/auth/login", { body: { email, password } });
      setToken(r.access_token); onLogin();
    } catch (x) {
      setErr(x instanceof ApiError && x.status === 423 ? t("auth.locked") : x instanceof ApiError && x.status === 401 ? t("auth.invalid") : errorText(x));
    }
    setBusy(false);
  };
  return centered(
    <form className="stack" onSubmit={submit} aria-labelledby="login-title">
      <h1 id="login-title">◈ {t("app.title")}</h1>
      <label className="field"><span>{t("auth.email")}</span><input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      <label className="field"><span>{t("auth.password")}</span><input type="password" autoComplete="current-password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
      {err && <p className="alert" role="alert">{err}</p>}
      <button className="btn primary" disabled={busy}>{t("auth.login")}</button>
    </form>,
  );
}

type Progress = { steps: { id: string; done: boolean; skipped?: boolean; pulls?: Record<string, { state: string }> }[]; completed: boolean };
type LlmStatus = { ollama: { reachable: boolean; models: string[]; recommended: string[] }; public: Record<string, boolean>; hint: string };
type Listing = { id: string; name: { ko: string; en: string }; source: { type: string }; required_env: string[] };

export function SetupPage({ onDone, signedIn = false }: { onDone: () => void; signedIn?: boolean }) {
  const toast = useToast();
  const [authed, setAuthed] = useState(signedIn);
  const [progress, setProgress] = useState<Progress | null>(null);
  const reload = () => api<Progress>("/api/setup/progress").then(setProgress).catch(() => {});
  useEffect(() => { if (authed) reload(); }, [authed]);
  const labels = [t("setup.admin"), t("setup.llm"), t("setup.models"), t("setup.agents"), t("setup.complete")];
  const done = progress ? progress.steps.map((s) => s.done) : [authed, false, false, false, false];
  const current = authed ? done.findIndex((d) => !d) : 0;

  return (
    <main style={{ padding: 24 }}>
      <div className="content stack" style={{ maxWidth: 720 }}>
        <h1>{t("setup.title")}</h1>
        <Stepper steps={labels} current={current} done={done} />
        {!authed && <AdminStep onDone={() => setAuthed(true)} />}
        {authed && current === 1 && <LlmStep onDone={reload} />}
        {authed && current === 2 && <ModelsStep progress={progress} onDone={reload} />}
        {authed && current === 3 && <AgentsStep onDone={reload} />}
        {authed && current === 4 && (
          <button className="btn primary" onClick={async () => {
            try { await api("/api/setup/complete", { method: "POST" }); onDone(); } catch (e) { toast(errorText(e), "error"); }
          }}>{t("setup.finish")}</button>
        )}
        {authed && current === -1 && <button className="btn primary" onClick={onDone}>{t("setup.finish")}</button>}
      </div>
    </main>
  );
}

function AdminStep({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  return (
    <form className="card stack" onSubmit={async (e) => {
      e.preventDefault();
      try { const r = await api<Token>("/api/setup/admin", { body: { email, password } }); setToken(r.access_token); onDone(); }
      catch (x) { setErr(errorText(x)); }
    }}>
      <label className="field"><span>{t("auth.email")}</span><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      <label className="field"><span>{t("auth.password")}</span><input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
      {err && <p className="alert" role="alert">{err}</p>}
      <button className="btn primary">{t("setup.create_admin")}</button>
    </form>
  );
}

function LlmStep({ onDone }: { onDone: () => void }) {
  const toast = useToast();
  const st = useApi<LlmStatus>("/api/setup/llm");
  const [chat, setChat] = useState("granite4.1:3b");
  const [reason, setReason] = useState("qwen3:8b");
  if (!st.data) return <p className="sub">{t("common.loading")}</p>;
  const models = st.data.ollama.recommended.length ? st.data.ollama.recommended : [chat, reason];
  const save = async () => {
    try {
      const r = await api<{ warnings: string[] }>("/api/setup/llm", { body: { chat_model: chat, reasoning_model: reason } });
      r.warnings.forEach((w) => toast(w, "info"));
      onDone();
    } catch (e) { toast(errorText(e), "error"); }
  };
  return (
    <section className="card stack" aria-labelledby="llm-h">
      <h2 id="llm-h">{t("setup.llm")}</h2>
      <p className={`badge ${st.data.ollama.reachable ? "ok" : "warn"}`}>{st.data.ollama.reachable ? t("setup.ollama_ok") : t("setup.ollama_ng")}</p>
      <label className="field"><span>{t("setup.chat_model")}</span>
        <select value={chat} onChange={(e) => setChat(e.target.value)}>{models.map((m) => <option key={m}>{m}</option>)}</select></label>
      <label className="field"><span>{t("setup.reasoning_model")}</span>
        <select value={reason} onChange={(e) => setReason(e.target.value)}>{models.map((m) => <option key={m}>{m}</option>)}</select></label>
      <p className="sub">{t("setup.public_keys")} — {Object.entries(st.data.public).map(([k, v]) => `${k}: ${v ? "✓" : "–"}`).join(" · ")}</p>
      <div className="row">
        <button className="btn primary" onClick={save}>{t("setup.save")}</button>
        <button className="btn" onClick={() => api("/api/setup/skip", { body: { step: "llm" } }).then(onDone)}>{t("setup.skip")}</button>
      </div>
    </section>
  );
}

function ModelsStep({ progress, onDone }: { progress: Progress | null; onDone: () => void }) {
  const [model, setModel] = useState("granite4.1:3b");
  const pulls = progress?.steps.find((s) => s.id === "models")?.pulls ?? {};
  useEffect(() => {
    if (!Object.values(pulls).some((p) => p.state === "queued" || p.state === "pulling")) return;
    const h = setInterval(onDone, 3000);
    return () => clearInterval(h);
  }, [pulls, onDone]);
  return (
    <section className="card stack">
      <h2>{t("setup.models")}</h2>
      <div className="row">
        <input aria-label={t("setup.chat_model")} value={model} onChange={(e) => setModel(e.target.value)} style={{ maxWidth: 260 }} />
        <button className="btn" onClick={() => api("/api/setup/models/pull", { body: { model } }).then(onDone)}>{t("setup.pull")}</button>
        <button className="btn" onClick={() => api("/api/setup/skip", { body: { step: "models" } }).then(onDone)}>{t("setup.skip")}</button>
      </div>
      <ul aria-live="polite">{Object.entries(pulls).map(([m, p]) => <li key={m}>{m}: {p.state}</li>)}</ul>
    </section>
  );
}

function AgentsStep({ onDone }: { onDone: () => void }) {
  const toast = useToast();
  const listings = useApi<Listing[]>("/api/market/listings");
  const [picked, setPicked] = useState<string[]>(["knowledge-rag"]);
  const ok = (listings.data ?? []).filter((x) => x.source.type === "zip" && !x.required_env.length);
  return (
    <section className="card stack">
      <h2>{t("setup.agents")}</h2>
      <fieldset className="stack" style={{ border: 0, padding: 0 }}>
        <legend className="sub">Orchestrator · AI Assistant ✓</legend>
        {ok.map((x) => (
          <label key={x.id} className="row"><input type="checkbox" style={{ width: "auto" }} checked={picked.includes(x.id)}
            onChange={(e) => setPicked(e.target.checked ? [...picked, x.id] : picked.filter((p) => p !== x.id))} />{x.name.ko} <span className="sub mono">{x.id}</span></label>
        ))}
      </fieldset>
      <div className="row">
        <button className="btn primary" onClick={async () => {
          try { await api("/api/setup/agents", { body: { listings: picked } }); onDone(); } catch (e) { toast(errorText(e), "error"); }
        }}>{t("setup.install_selected")}</button>
        <button className="btn" onClick={() => api("/api/setup/skip", { body: { step: "agents" } }).then(onDone)}>{t("setup.skip")}</button>
      </div>
    </section>
  );
}
