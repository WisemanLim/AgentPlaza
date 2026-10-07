// 공용 UI: 상태(로딩 300ms 이하 미표시·빈·오류·권한 없음), 토스트(aria-live, 최대 3), 모달(<dialog>: 포커스 트랩·Esc), 배지.
import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { t } from "../i18n";
import { navigate } from "../router";

export function Link({ to, children, className, current }: { to: string; children: ReactNode; className?: string; current?: boolean }) {
  return (
    <a href={to} className={className} aria-current={current ? "page" : undefined}
       onClick={(e) => { if (e.metaKey || e.ctrlKey || e.button !== 0) return; e.preventDefault(); navigate(to); }}>
      {children}
    </a>
  );
}

const TONE: Record<string, string> = {
  healthy: "ok", succeeded: "ok", approved: "ok", ok: "ok", official: "info", partner: "info", "publisher:verified": "ok",
  registered: "info", running: "info", queued: "info", pending: "warn", waiting_approval: "warn", degraded: "warn",
  "signature:unverified": "warn", "signature:verified": "ok", "signature:invalid": "danger", warn: "warn", community: "warn", external: "warn", unhealthy: "danger", failed: "danger",
  rolled_back: "danger", rejected: "danger", expired: "danger", disabled: "danger",
  info: "info", published: "ok", blocked: "danger", featured: "info", validated: "ok", auth_failed: "danger", error: "danger",
};
const BADGE_KEY: Record<string, string> = { official: "badge.official", partner: "badge.partner", community: "badge.community",
  external: "badge.external", "signature:unverified": "badge.unverified", "signature:verified": "badge.verified",
  "publisher:verified": "badge.publisher_verified", featured: "badge.featured", validated: "badge.validated" };
export function Badge({ value, label }: { value: string; label?: string }) {
  return <span className={`badge ${TONE[value] ?? ""}`}>{label ?? (BADGE_KEY[value] ? t(BADGE_KEY[value]) : value)}</span>;
}
export function Dot({ value }: { value: string }) {
  return <span className={`dot ${TONE[value] ?? ""}`} aria-hidden="true" />;
}

export function useApi<T>(path: string | null, deps: unknown[] = []) {
  const [state, setState] = useState<{ data?: T; error?: ApiError; loading: boolean }>({ loading: true });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!path) return;
    const ctrl = new AbortController();
    setState((s) => ({ ...s, loading: true }));
    api<T>(path, { signal: ctrl.signal })
      .then((data) => setState({ data, loading: false }))
      .catch((error) => { if (error.name !== "AbortError") setState({ error, loading: false }); });
    return () => ctrl.abort();
  }, [path, n, ...deps]);
  return { ...state, reload: useCallback(() => setN((x) => x + 1), []) };
}

export function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 0) return t("common.offline");
    if (e.status === 403) return `${t("common.forbidden")} — ${e.message}`;
    return e.message;
  }
  return (e as Error)?.message ?? t("common.error");
}

/** ST-01~03: 300ms 이하 로딩은 표시하지 않고 그 이상은 스켈레톤, 빈 상태 문구, 오류 + 다시 시도. */
export function StateView<T>({ q, empty, children }: { q: { data?: T; error?: unknown; loading: boolean; reload: () => void };
  empty?: (d: T) => boolean; children: (d: T) => ReactNode }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => { if (!q.loading) return; const h = setTimeout(() => setSlow(true), 300); return () => { clearTimeout(h); setSlow(false); }; }, [q.loading]);
  if (q.error) return <div className="alert" role="alert">{errorText(q.error)} <button className="btn" onClick={q.reload}>{t("common.retry")}</button></div>;
  if (q.data === undefined) return slow ? <div className="stack" aria-busy="true"><span className="sr-only">{t("common.loading")}</span><div className="skeleton" /><div className="skeleton" /></div> : null;
  if (empty?.(q.data)) return <p className="sub">{t("common.empty")}</p>;
  return <>{children(q.data)}</>;
}

type Toast = { id: number; text: string; tone: "ok" | "error" | "info" };
const ToastCtx = createContext<(text: string, tone?: Toast["tone"]) => void>(() => {});
export function useToast() { return useContext(ToastCtx); }
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((text: string, tone: Toast["tone"] = "info") => {
    const id = Date.now() + Math.random();
    setItems((xs) => [...xs.slice(-2), { id, text, tone }]);
    if (tone !== "error") setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), 4000); // 오류는 수동으로 닫는다
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" aria-live="polite" role="status">
        {items.map((x) => (
          <div key={x.id} className={`toast ${x.tone}`}>
            <span>{x.text}</span>{" "}
            {x.tone === "error" && <button className="btn" onClick={() => setItems((xs) => xs.filter((y) => y.id !== x.id))}>{t("common.close")}</button>}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function Modal({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="modal-title" className="card" style={{ maxWidth: 560, width: "90vw" }}>
      <h2 id="modal-title" style={{ marginTop: 0 }}>{title}</h2>
      {children}
    </dialog>
  );
}

export function Stepper({ steps, current, done }: { steps: string[]; current: number; done: boolean[] }) {
  return (
    <ol className="stepper">
      {steps.map((s, i) => <li key={s} aria-current={i === current ? "step" : undefined} className={done[i] ? "done" : ""}>{i + 1}. {s}</li>)}
    </ol>
  );
}

export function fmtTime(v: unknown): string {
  if (!v) return "";
  const d = new Date(String(v).endsWith("Z") || String(v).includes("+") ? String(v) : `${v}Z`);
  return isNaN(d.getTime()) ? String(v) : d.toLocaleString();
}
