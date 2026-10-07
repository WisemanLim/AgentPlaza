// 최소 라우터(History API). 외부 의존성 없이 경로 매칭·이동만 한다.
import { useSyncExternalStore } from "react";

const EVT = "plaza:nav";
function subscribe(f: () => void) {
  window.addEventListener("popstate", f);
  window.addEventListener(EVT, f);
  return () => { window.removeEventListener("popstate", f); window.removeEventListener(EVT, f); };
}
export function usePath(): string {
  return useSyncExternalStore(subscribe, () => window.location.pathname + window.location.search);
}
export function navigate(to: string, replace = false) {
  if (replace) history.replaceState({}, "", to); else history.pushState({}, "", to);
  window.dispatchEvent(new Event(EVT));
}
export function match(pattern: string, path: string): Record<string, string> | null {
  const [p] = path.split("?");
  const a = pattern.split("/").filter(Boolean);
  const b = p.split("/").filter(Boolean);
  if (a.length !== b.length) return null;
  const params: Record<string, string> = {};
  for (let i = 0; i < a.length; i++) {
    if (a[i].startsWith(":")) params[a[i].slice(1)] = decodeURIComponent(b[i]);
    else if (a[i] !== b[i]) return null;
  }
  return params;
}
export function query(path: string): URLSearchParams {
  return new URLSearchParams(path.split("?")[1] ?? "");
}
