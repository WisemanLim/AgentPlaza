// API 클라이언트: Bearer 토큰(세션 저장소) + 일관된 오류. 401 이면 로그인 화면으로.
const KEY = "plaza.token";
let token: string | null = (() => { try { return globalThis.sessionStorage?.getItem(KEY) ?? null; } catch { return null; } })();
let onUnauthorized: () => void = () => {};

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : (detail as { message?: string })?.message ?? `HTTP ${status}`);
  }
}

export function setToken(t: string | null) {
  token = t;
  try { if (t) sessionStorage.setItem(KEY, t); else sessionStorage.removeItem(KEY); } catch { /* 무시 */ }
}
export function getToken() { return token; }
export function setUnauthorizedHandler(f: () => void) { onUnauthorized = f; }

export function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  return token ? { ...extra, authorization: `Bearer ${token}` } : extra;
}

type Opts = { method?: string; body?: unknown; form?: FormData; signal?: AbortSignal; headers?: Record<string, string> };

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const headers = authHeaders(opts.headers);
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) { body = JSON.stringify(opts.body); headers["content-type"] = "application/json"; }
  let res: Response;
  try {
    res = await fetch(path, { method: opts.method ?? (body ? "POST" : "GET"), headers, body, signal: opts.signal, credentials: "same-origin" });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError(0, "offline");
  }
  const ctype = res.headers.get("content-type") ?? "";
  const data = ctype.includes("json") ? await res.json().catch(() => null) : await res.text();
  if (res.status === 401 && token) onUnauthorized();
  if (!res.ok) throw new ApiError(res.status, (data as { detail?: unknown })?.detail ?? data);
  return data as T;
}

export async function download(path: string, filename: string, body?: unknown, method = "POST") {
  const res = await fetch(path, { method, headers: authHeaders(body ? { "content-type": "application/json" } : {}),
    body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}
