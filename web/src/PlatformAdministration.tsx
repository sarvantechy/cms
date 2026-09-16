import { useEffect, useState } from "react";
import { Building2, CheckCircle2, LogOut, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import {
  getPlatformErrorMessage,
  getPlatformTenants,
  platformLogin,
  platformLogout,
  restorePlatformSession,
  updatePlatformTenantStatus,
  type PlatformActor,
  type PlatformTenant,
} from "./platformApi";

const PLATFORM_DEMO_EMAIL = "platform@4by4.demo";
const DEMO_PASSWORD = "";

/** Own isolated Platform Administrator authentication and tenant lifecycle views. */
export default function PlatformAdministration() {
  const [actor, setActor] = useState<PlatformActor | null>(null);
  const [tenants, setTenants] = useState<PlatformTenant[]>([]);
  const [restoring, setRestoring] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    restorePlatformSession().then((authentication) => {
      if (active) setActor(authentication?.actor ?? null);
    }).finally(() => {
      if (active) setRestoring(false);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!actor) return;
    let active = true;
    getPlatformTenants().then((records) => {
      if (active) setTenants(records);
    }).catch((loadError) => {
      if (active) setError(getPlatformErrorMessage(loadError));
    });
    return () => { active = false; };
  }, [actor]);

  /** Authenticate a platform administrator without creating a tenant session. */
  async function submitLogin(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const authentication = await platformLogin(
        String(form.get("email") ?? "").trim(),
        String(form.get("password") ?? ""),
      );
      setActor(authentication.actor);
    } catch (loginError) {
      setError(getPlatformErrorMessage(loginError));
    } finally {
      setBusy(false);
    }
  }

  /** End the isolated platform session and return to its login screen. */
  async function signOut(): Promise<void> {
    setBusy(true);
    try {
      await platformLogout();
    } finally {
      setActor(null);
      setTenants([]);
      setBusy(false);
    }
  }

  /** Apply a tenant lifecycle transition and refresh the directory. */
  async function changeStatus(tenant: PlatformTenant, status: "active" | "suspended" | "closed"): Promise<void> {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await updatePlatformTenantStatus(tenant.id, status);
      setTenants(await getPlatformTenants());
      setNotice(`${tenant.short_name} is ${result.status}. ${result.revoked_sessions} sessions revoked.`);
    } catch (statusError) {
      setError(getPlatformErrorMessage(statusError));
    } finally {
      setBusy(false);
    }
  }

  if (restoring) return <main className="portal-loading">Restoring platform session...</main>;
  if (!actor) return <PlatformLogin busy={busy} error={error} onSubmit={submitLogin} />;

  return (
    <main className="platform-workspace">
      <header className="platform-header"><div><span>4B4</span><div><p>PLATFORM CONTROL</p><h1>Tenant directory</h1></div></div><button type="button" disabled={busy} onClick={signOut}><LogOut aria-hidden /> Sign out</button></header>
      <section className="platform-summary"><div><ShieldCheck aria-hidden /><span><strong>Platform Administrator</strong><small>{actor.permissions.length} effective permissions</small></span></div><p>Platform access is isolated from college memberships and operational records.</p></section>
      {notice && <p className="workspace-banner success" role="status">{notice}</p>}
      {error && <p className="workspace-banner error" role="alert">{error}</p>}
      <section className="platform-tenant-list" aria-label="Tenant lifecycle directory">
        <header><div><p>COLLEGE TENANTS</p><h2>{tenants.length} institutions</h2></div><span>Global directory · no tenant data access</span></header>
        {tenants.map((tenant) => <article key={tenant.id}><span className="tenant-color" style={{ background: tenant.primary_color }}><Building2 aria-hidden /></span><div><strong>{tenant.display_name}</strong><p>{tenant.key} · {tenant.timezone}</p></div><span className={`platform-status ${tenant.status}`}>{tenant.status}</span><div className="inline-actions">{tenant.status !== "active" && <button className="row-action" type="button" disabled={busy} onClick={() => changeStatus(tenant, "active")}>Activate</button>}{tenant.status === "active" && <button className="row-action secondary" type="button" disabled={busy} onClick={() => changeStatus(tenant, "suspended")}>Suspend</button>}{tenant.status !== "closed" && <button className="row-action danger" type="button" disabled={busy} onClick={() => changeStatus(tenant, "closed")}>Close</button>}</div></article>)}
      </section>
    </main>
  );
}

/** Render the distinct Platform Administrator login journey. */
function PlatformLogin({ busy, error, onSubmit }: Readonly<{ busy: boolean; error: string; onSubmit: (event: React.SubmitEvent<HTMLFormElement>) => Promise<void> }>) {
  return <main className="platform-login"><section><span className="platform-monogram">4B4</span><p>COLLEGE PLATFORM</p><h1>Tenant operations,<br />kept separate.</h1><small>Platform audience · no college operational access</small></section><section><div className="platform-login-card"><ShieldCheck aria-hidden /><h2>Platform Administrator</h2><p>Authenticate to review tenant lifecycle state.</p><form onSubmit={onSubmit}><label>Email<input name="email" type="email" defaultValue={PLATFORM_DEMO_EMAIL} required /></label><label>Password<input name="password" type="password" defaultValue={DEMO_PASSWORD} required /></label>{error && <p className="login-error" role="alert">{error}</p>}<button type="submit" disabled={busy}>{busy ? "Authenticating..." : "Enter platform control"}<CheckCircle2 aria-hidden /></button></form><Link to="/login">College portal login</Link></div></section></main>;
}