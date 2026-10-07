// 콘솔 셸(B01) + 라우팅 + 인증 게이트(셋업 전 → 위저드, 토큰 없음 → 로그인).
import { type ReactNode, useEffect, useState, useSyncExternalStore } from "react";
import { api, getToken, setToken, setUnauthorizedHandler } from "./api";
import { Link, ToastProvider, useApi } from "./components/ui";
import { getLocale, onLocale, setLocale, t } from "./i18n";
import { match, navigate, usePath } from "./router";
import { applyTheme } from "./theme";
import { LoginPage, SetupPage } from "./pages/auth";
import { DashboardPage } from "./pages/dashboard";
import { ChatPage } from "./pages/chat";
import { AddonPage, AgentDetailPage, AgentsPage, LinkPage, UploadPage } from "./pages/agents";
import { MarketDetailPage, MarketPage } from "./pages/market";
import { ApprovalsPage, AuditPage, KeysPage, LlmPage, ProfilePage, SettingsPage, UsersPage } from "./pages/admin";
import { TrustPage } from "./pages/trust";
import { GovernancePage, SecretsPage } from "./pages/governance";
import { KnowledgePage, MemoryPage } from "./pages/knowledge";
import { InstalledPage, PublishersPage, PublishPage, RegistriesPage } from "./pages/market_admin";
import { EvalsPage, ObservePage } from "./pages/observe";
import { OrgsPage } from "./pages/orgs";
import { ChannelsPage } from "./pages/channels";
import { Bell, NotificationsPage, StatusPage } from "./pages/status";

export type Me = { id: number | string; email?: string; role: string; locale?: string; type?: string };

function useLocaleRender() {
  return useSyncExternalStore(onLocale, getLocale);
}

const ROUTES: [string, (p: Record<string, string>, me: Me) => ReactNode][] = [
  ["/", (_p, me) => <DashboardPage me={me} />],
  ["/chat", () => <ChatPage />],
  ["/agents", (_p, me) => <AgentsPage me={me} />],
  ["/agents/upload", () => <UploadPage />],
  ["/agents/link", () => <LinkPage />],
  ["/agents/:id", (p, me) => <AgentDetailPage id={p.id} me={me} />],
  ["/addon/:id", (p) => <AddonPage id={p.id} />],
  ["/market", (_p, me) => <MarketPage me={me} />],
  ["/market/publish", (_p, me) => <PublishPage me={me} />],
  ["/market/publishers", () => <PublishersPage />],
  ["/market/installed", (_p, me) => <InstalledPage me={me} />],
  ["/market/:id", (p, me) => <MarketDetailPage id={p.id} me={me} />],
  ["/approvals", (_p, me) => <ApprovalsPage me={me} />],
  ["/llm", (_p, me) => <LlmPage me={me} />],
  ["/users", (_p, me) => <UsersPage me={me} />],
  ["/orgs", (_p, me) => <OrgsPage me={me} />],
  ["/keys", () => <KeysPage />],
  ["/trust", () => <TrustPage />],
  ["/governance", () => <GovernancePage />],
  ["/secrets", () => <SecretsPage />],
  ["/settings", (_p, me) => <SettingsPage me={me} />],
  ["/settings/registries", () => <RegistriesPage />],
  ["/settings/channels", () => <ChannelsPage />],
  ["/profile", () => <ProfilePage />],
  ["/profile/memory", () => <MemoryPage />],
  ["/knowledge", (_p, me) => <KnowledgePage me={me} />],
  ["/audit", () => <AuditPage />],
  ["/observe", () => <ObservePage />],
  ["/status", (_p, me) => <StatusPage me={me} />],
  ["/notifications", () => <NotificationsPage />],
  ["/evals", () => <EvalsPage />],
];

function Router({ me }: { me: Me }) {
  const path = usePath();
  for (const [pattern, render] of ROUTES) {
    const p = match(pattern, path);
    if (p) return <>{render(p, me)}</>;
  }
  return <p>404 — <Link to="/">{t("nav.dashboard")}</Link></p>;
}

type NavAgent = { id: string; name: string; nav_visible: boolean };

function Shell({ me, onLogout }: { me: Me; onLogout: () => void }) {
  const path = usePath().split("?")[0];
  const [open, setOpen] = useState(false);
  const agents = useApi<NavAgent[]>("/api/agents", [path === "/agents"]);
  const admin = me.role === "admin" || me.role === "supervisor";
  const item = (to: string, key: string) => (
    <Link to={to} current={to === "/" ? path === "/" : path.startsWith(to)}>{t(key)}</Link>
  );
  useEffect(() => setOpen(false), [path]);
  return (
    <div className="shell">
      <header className="topbar">
        <button className="btn menu-btn" aria-expanded={open} aria-controls="nav" onClick={() => setOpen(!open)}>{t("nav.menu")}</button>
        <span className="brand"><span aria-hidden="true">◈</span>{t("app.title")}</span>
        <Bell />
        <select aria-label={t("profile.locale")} value={getLocale()} onChange={(e) => setLocale(e.target.value as "ko" | "en")} style={{ width: "auto" }}>
          <option value="ko">한국어</option><option value="en">English</option>
        </select>
        <span className="sub who">{me.email} · {me.role}</span>
        <button className="btn" onClick={onLogout}>{t("auth.logout")}</button>
      </header>
      <nav id="nav" className={`nav ${open ? "open" : ""}`} aria-label={t("nav.main")}>
        {item("/", "nav.dashboard")}
        {item("/chat", "nav.chat")}
        {item("/market", "nav.market")}
        {item("/agents", "nav.agents")}
        {item("/approvals", "nav.approvals")}
        {item("/knowledge", "nav.knowledge")}
        {(agents.data ?? []).some((a) => a.nav_visible) && <h2>{t("nav.addons")}</h2>}
        {(agents.data ?? []).filter((a) => a.nav_visible).map((a) => (
          <Link key={a.id} to={`/addon/${a.id}`} current={path === `/addon/${a.id}`}>{a.name}</Link>
        ))}
        {admin && <h2>{t("nav.manage")}</h2>}
        {admin && item("/llm", "nav.llm")}
        {admin && item("/users", "nav.users")}
        {item("/orgs", "nav.orgs")}
        {admin && item("/keys", "nav.keys")}
        {admin && item("/trust", "nav.trust")}
        {admin && item("/governance", "nav.governance")}
        {admin && item("/secrets", "nav.secrets")}
        {admin && item("/market/installed", "nav.installed")}
        {me.role === "supervisor" && item("/settings/registries", "nav.registries")}
        {admin && item("/settings/channels", "nav.channels")}
        {admin && item("/settings", "nav.settings")}
        {admin && <h2>{t("nav.ops")}</h2>}
        {admin && item("/status", "nav.status")}
        {admin && item("/observe", "nav.observe")}
        {admin && item("/evals", "nav.evals")}
        {admin && item("/audit", "nav.audit")}
        {item("/profile", "nav.profile")}
        {item("/profile/memory", "nav.memory")}
      </nav>
      <main><div className="content"><Router me={me} /></div></main>
    </div>
  );
}

export function App() {
  useLocaleRender();
  const [status, setStatus] = useState<{ initialized: boolean } | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [checking, setChecking] = useState(true);

  const loadMe = async () => {
    if (!getToken()) { setMe(null); setChecking(false); return; }
    try {
      const m = await api<Me>("/api/auth/me");
      setMe(m);
      if (m.locale === "en" || m.locale === "ko") setLocale(m.locale);
      const prof = await api<{ theme: string }>("/api/me/profile").catch(() => ({ theme: "system" }));
      applyTheme(prof.theme);
    } catch { setToken(null); setMe(null); }
    setChecking(false);
  };
  useEffect(() => {
    try { applyTheme(sessionStorage.getItem("plaza.theme") ?? "system"); } catch { /* 무시 */ }
    setUnauthorizedHandler(() => { setToken(null); setMe(null); });
    api<{ initialized: boolean }>("/api/setup/status").then(setStatus).catch(() => setStatus({ initialized: true }));
    loadMe();
  }, []);
  const logout = async () => {
    await api("/api/auth/logout", { method: "POST" }).catch(() => {});
    setToken(null); setMe(null); navigate("/");
  };

  let body: ReactNode = null;
  if (status && !status.initialized) body = <SetupPage onDone={() => { setStatus({ initialized: true }); loadMe(); }} />;
  else if (!checking && !me) body = <LoginPage onLogin={loadMe} />;
  else if (me && match("/setup", usePathSafe())) body = <SetupPage signedIn onDone={() => navigate("/")} />;
  else if (me) body = <Shell me={me} onLogout={logout} />;
  return <ToastProvider>{body}</ToastProvider>;
}

function usePathSafe() {
  return typeof window === "undefined" ? "/" : window.location.pathname;
}
