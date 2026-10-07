// K02 조직·그룹·구성원 · FL-07 조직 도입(배치 범위 deploy_scope) — PRD Q7·Q12. 데이터 분리(X09)가 아니라 노출 범위 통제
import { type FormEvent, useState } from "react";
import type { Me } from "../App";
import { api } from "../api";
import { Badge, errorText, StateView, useApi, useToast } from "../components/ui";
import { t } from "../i18n";

type OrgRow = { id: string; name: string; members: number; groups: number; my_role: string | null };
type Member = { user_id: number; email: string; role: string };
type Group = { id: string; name: string; members: { user_id: number; email: string }[] };
type OrgDetail = { id: string; name: string; members: Member[]; groups: Group[]; can_manage: boolean;
  agents: { agent_id: string; kind: string; ids: (string | number)[] }[] };
export type Scope = { org_id: string; kind: "org" | "group" | "user"; ids: (string | number)[] };

export function OrgsPage({ me }: { me: Me }) {
  const list = useApi<OrgRow[]>("/api/orgs");
  const toast = useToast();
  const [sel, setSel] = useState("default");
  const detail = useApi<OrgDetail>(`/api/orgs/${sel}`, [sel]);
  const [nOrg, setNOrg] = useState({ id: "", name: "" });
  const [member, setMember] = useState({ email: "", role: "member" });
  const [group, setGroup] = useState("");
  const [gm, setGm] = useState<Record<string, string>>({});
  const run = async (f: () => Promise<unknown>, after: () => void = detail.reload) => {
    try { await f(); toast("OK", "ok"); after(); list.reload(); } catch (x) { toast(errorText(x), "error"); }
  };
  const addOrg = (e: FormEvent) => { e.preventDefault(); run(() => api("/api/orgs", { body: nOrg }), () => { setSel(nOrg.id); setNOrg({ id: "", name: "" }); }); };
  return (
    <div className="stack">
      <h1>{t("org.title")}</h1>
      <p className="sub">{t("org.hint")}</p>
      <StateView q={list} empty={(d) => !d.length}>{(d) => (
        <div className="row" role="tablist" aria-label={t("org.title")}>{d.map((o) => (
          <button key={o.id} role="tab" aria-selected={sel === o.id} className={`btn${sel === o.id ? " primary" : ""}`} onClick={() => setSel(o.id)}>
            {o.name} ({o.members}·{o.groups}){o.my_role === "admin" && " ★"}</button>))}</div>)}</StateView>
      {me.role === "supervisor" && <form className="row card" onSubmit={addOrg}>
        <input required placeholder={t("pubs.id")} aria-label={t("pubs.id")} pattern="[a-z0-9][a-z0-9-]{1,63}" value={nOrg.id} onChange={(e) => setNOrg({ ...nOrg, id: e.target.value })} style={{ maxWidth: 160 }} />
        <input required placeholder={t("org.name")} aria-label={t("org.name")} value={nOrg.name} onChange={(e) => setNOrg({ ...nOrg, name: e.target.value })} style={{ maxWidth: 220 }} />
        <button className="btn">{t("org.add")}</button>
      </form>}
      <StateView q={detail}>{(o) => (<>
        <section className="card stack"><h2>{t("org.members")} <span className="sub">{o.name}</span></h2>
          <table className="responsive"><tbody>{o.members.map((m) => (
            <tr key={m.user_id}><td>{m.email}</td>
              <td>{o.can_manage
                ? <select aria-label={`${t("org.role")} ${m.email}`} value={m.role} style={{ width: "auto" }}
                    onChange={(e) => run(() => api(`/api/orgs/${o.id}/members`, { method: "PUT", body: { email: m.email, role: e.target.value } }))}>
                    <option value="member">{t("org.member")}</option><option value="admin">{t("org.admin")}</option></select>
                : <Badge value={m.role === "admin" ? "info" : "ok"} label={m.role === "admin" ? t("org.admin") : t("org.member")} />}</td>
              <td>{o.can_manage && <button className="btn" onClick={() => run(() => api(`/api/orgs/${o.id}/members/${m.user_id}`, { method: "DELETE" }))}>{t("org.remove")}</button>}</td></tr>))}
          </tbody></table>
          {o.can_manage && <form className="row" onSubmit={(e) => { e.preventDefault(); run(() => api(`/api/orgs/${o.id}/members`, { method: "PUT", body: member }), () => { setMember({ email: "", role: "member" }); detail.reload(); }); }}>
            <input required type="email" placeholder="email" aria-label={t("org.member_email")} value={member.email} onChange={(e) => setMember({ ...member, email: e.target.value })} style={{ maxWidth: 260 }} />
            <select aria-label={t("org.role")} value={member.role} onChange={(e) => setMember({ ...member, role: e.target.value })} style={{ width: "auto" }}>
              <option value="member">{t("org.member")}</option><option value="admin">{t("org.admin")}</option></select>
            <button className="btn primary">{t("org.add_member")}</button>
          </form>}
        </section>
        <section className="card stack"><h2>{t("org.groups")}</h2>
          {o.groups.length === 0 && <p className="sub">—</p>}
          {o.groups.map((g) => (
            <div key={g.id} className="stack" style={{ borderTop: "1px solid var(--border)", paddingTop: 8 }}>
              <div className="row"><b>{g.name}</b> <span className="sub">{g.members.length}</span>
                {o.can_manage && <button className="btn danger" style={{ marginLeft: "auto" }} onClick={() => run(() => api(`/api/orgs/${o.id}/groups/${g.id}`, { method: "DELETE" }))}>{t("common.delete")}</button>}</div>
              <div className="row">{g.members.map((m) => <span key={m.user_id} className="badge">{m.email}
                {o.can_manage && <button className="btn" aria-label={`${t("org.remove")} ${m.email}`} style={{ padding: "0 6px" }} onClick={() => run(() => api(`/api/orgs/${o.id}/groups/${g.id}/members/${m.user_id}`, { method: "DELETE" }))}>×</button>}</span>)}</div>
              {o.can_manage && <form className="row" onSubmit={(e) => { e.preventDefault(); run(() => api(`/api/orgs/${o.id}/groups/${g.id}/members`, { method: "PUT", body: { email: gm[g.id] ?? "" } }), () => { setGm({ ...gm, [g.id]: "" }); detail.reload(); }); }}>
                <select aria-label={`${t("org.add_to_group")} ${g.name}`} value={gm[g.id] ?? ""} onChange={(e) => setGm({ ...gm, [g.id]: e.target.value })} style={{ width: "auto" }}>
                  <option value="">—</option>{o.members.filter((m) => !g.members.some((x) => x.user_id === m.user_id)).map((m) => <option key={m.user_id} value={m.email}>{m.email}</option>)}</select>
                <button className="btn" disabled={!gm[g.id]}>{t("org.add_to_group")}</button>
              </form>}
            </div>))}
          {o.can_manage && <form className="row" onSubmit={(e) => { e.preventDefault(); run(() => api(`/api/orgs/${o.id}/groups`, { body: { name: group } }), () => { setGroup(""); detail.reload(); }); }}>
            <input required placeholder={t("org.group_name")} aria-label={t("org.group_name")} value={group} onChange={(e) => setGroup(e.target.value)} style={{ maxWidth: 220 }} />
            <button className="btn primary">{t("org.add_group")}</button>
          </form>}
        </section>
        {o.agents.length > 0 && <section className="card"><h2>{t("org.deployed")}</h2>
          <ul>{o.agents.map((a) => <li key={a.agent_id}><b className="mono">{a.agent_id}</b> · {t(`org.kind.${a.kind}`)}{a.ids.length ? ` (${a.ids.length})` : ""}</li>)}</ul></section>}
      </>)}</StateView>
    </div>
  );
}

// 배치 범위 선택(E04 2단계·D02): 전체(범위 없음) | 조직 전체 | 그룹 | 사용자
export function ScopePicker({ value, onChange }: { value: Scope | null; onChange: (s: Scope | null) => void }) {
  const orgsQ = useApi<OrgRow[]>("/api/orgs");
  const org = value?.org_id ?? "default";
  const detail = useApi<OrgDetail>(`/api/orgs/${org}`, [org]);
  const kind = value?.kind ?? "all";
  const toggle = (id: string | number) => {
    if (!value) return;
    onChange({ ...value, ids: value.ids.includes(id) ? value.ids.filter((x) => x !== id) : [...value.ids, id] });
  };
  return (
    <fieldset className="stack" style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-ctl)", padding: 12 }}>
      <legend>{t("org.scope")}</legend>
      <div className="row" role="radiogroup">
        {(["all", "org", "group", "user"] as const).map((k) => (
          <label key={k} className="row"><input type="radio" style={{ width: "auto" }} name="scope-kind" checked={kind === k}
            onChange={() => onChange(k === "all" ? null : { org_id: org, kind: k, ids: [] })} />{t(`org.kind.${k}`)}</label>))}
        {value && <select aria-label={t("org.title")} value={org} style={{ width: "auto" }} onChange={(e) => onChange({ ...value, org_id: e.target.value, ids: [] })}>
          {(orgsQ.data ?? []).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select>}
      </div>
      {value?.kind === "group" && <div className="row">{(detail.data?.groups ?? []).map((g) => (
        <label key={g.id} className="row"><input type="checkbox" style={{ width: "auto" }} checked={value.ids.includes(g.id)} onChange={() => toggle(g.id)} />{g.name}</label>))}</div>}
      {value?.kind === "user" && <div className="row">{(detail.data?.members ?? []).map((m) => (
        <label key={m.user_id} className="row"><input type="checkbox" style={{ width: "auto" }} checked={value.ids.includes(m.user_id)} onChange={() => toggle(m.user_id)} />{m.email}</label>))}</div>}
    </fieldset>
  );
}

// D02 에이전트 상세: 배치 범위 편집(플랫폼 admin 이상)
export function ScopeSection({ id, current }: { id: string; current: Scope | null }) {
  const toast = useToast();
  const [scope, setScope] = useState<Scope | null>(current);
  const save = async () => {
    try {
      if (scope) await api(`/api/agents/${id}/scope`, { method: "PUT", body: scope });
      else await api(`/api/agents/${id}/scope`, { method: "DELETE" });
      toast("OK", "ok");
    } catch (x) { toast(errorText(x), "error"); }
  };
  return (
    <section className="card stack"><h2>{t("org.scope")}</h2>
      <ScopePicker value={scope} onChange={setScope} />
      <div><button className="btn primary" onClick={save}>{t("common.save")}</button></div>
    </section>
  );
}
