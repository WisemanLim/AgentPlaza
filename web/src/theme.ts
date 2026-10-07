// 테마: light | dark | system — 프로필에 저장되고, Addon 에는 postMessage(plaza:context)로 전파된다.
export function applyTheme(theme: string) {
  const root = document.documentElement;
  if (theme === "system") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", theme);
  try { sessionStorage.setItem("plaza.theme", theme); } catch { /* 무시 */ }
}
