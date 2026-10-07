// B02 대시보드: 상태 타일 6개, 30초 폴링.
import { useEffect } from "react";
import type { Me } from "../App";
import { Link, StateView, useApi } from "../components/ui";
import { t } from "../i18n";

type Tile = { id: string; label: string; value: number | string; total?: number; warn?: number; fallbacks?: number;
  local_ratio?: number | null; running?: number; failed?: number; ok?: boolean };
const LINK: Record<string, string> = { agents: "/agents", approvals: "/approvals", llm: "/llm", installs: "/agents",
  sessions: "/chat", runtime: "/agents" };

export function DashboardPage({ me }: { me: Me }) {
  const q = useApi<{ tiles: Tile[]; refresh_seconds: number }>("/api/console/dashboard");
  useEffect(() => { const h = setInterval(q.reload, 30_000); return () => clearInterval(h); }, [q.reload]);
  return (
    <>
      <h1>{t("dash.title")}</h1>
      <p className="sub">{me.email}</p>
      <StateView q={q}>{(d) => (
        <div className="grid">
          {d.tiles.map((x) => (
            <Link key={x.id} to={LINK[x.id] ?? "/"} className="card" >
              <div className="sub">{t(`dash.${x.id}`)}</div>
              <div style={{ fontSize: 28, fontWeight: 700 }}>{x.value}{x.total !== undefined && <span className="sub" style={{ fontSize: 16 }}> / {x.total}</span>}</div>
              <div className="row sub" style={{ fontSize: 12 }}>
                {!!x.warn && <span className="badge danger">⚠ {x.warn}</span>}
                {x.fallbacks !== undefined && <span>{t("dash.fallbacks")} {x.fallbacks}</span>}
                {x.local_ratio != null && <span>{t("dash.local")} {Math.round(x.local_ratio * 100)}%</span>}
                {!!x.running && <span className="badge info">▶ {x.running}</span>}
                {!!x.failed && <span className="badge danger">✕ {x.failed}</span>}
                {x.ok === false && <span className="badge danger">✕</span>}
              </div>
            </Link>
          ))}
        </div>
      )}</StateView>
    </>
  );
}
