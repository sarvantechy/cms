import { useState } from "react";
import { KeyRound, LogOut, ShieldCheck, UserPlus, UsersRound } from "lucide-react";

import {
  changePassword,
  createInvitation,
  createTenantRole,
  getApiErrorMessage,
  getMembershipRoleAssignments,
  replaceMembershipRoleAssignments,
  revokeMembershipSessions,
  revokeSession,
  updateMembershipStatus,
  updateTenantRole,
  type ActorSummary,
  type InvitationResponse,
  type MembershipAdminSummary,
  type PermissionAdminSummary,
  type RoleScopeInput,
  type SessionSummary,
  type TenantRoleAdminSummary,
} from "./operationalApi";

type AccessAdministrationProps = {
  actor: ActorSummary | null;
  sessions: SessionSummary[];
  memberships: MembershipAdminSummary[];
  roles: TenantRoleAdminSummary[];
  permissions: PermissionAdminSummary[];
  onRefresh: (message: string) => void;
  onError: (message: string) => void;
  onLogout: () => Promise<void>;
};

type RoleDraft = {
  selected: boolean;
  scopes: RoleScopeInput[];
};

const scopeTypes = [
  "institution",
  "campus",
  "department",
  "program",
  "batch",
  "section",
  "subject_offering",
  "linked_student",
  "own_record",
] as const;

/** Render tenant identity administration backed by protected production APIs. */
export default function AccessAdministration({
  actor,
  sessions,
  memberships,
  roles,
  permissions,
  onRefresh,
  onError,
  onLogout,
}: Readonly<AccessAdministrationProps>) {
  const [busy, setBusy] = useState(false);
  const [showInvitation, setShowInvitation] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [roleEditor, setRoleEditor] = useState<TenantRoleAdminSummary | "new" | null>(null);
  const [assignmentMember, setAssignmentMember] = useState<MembershipAdminSummary | null>(null);
  const [assignmentDraft, setAssignmentDraft] = useState<Record<string, RoleDraft>>({});
  const [invitationResult, setInvitationResult] = useState<InvitationResponse | null>(null);

  /** Run one mutation while exposing controlled API errors. */
  async function runMutation(action: () => Promise<void>): Promise<void> {
    setBusy(true);
    try {
      await action();
    } catch (error) {
      onError(getApiErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  /** Submit a membership invitation with selected initial roles and scope. */
  async function submitInvitation(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const roleKeys = form.getAll("role_key").map(String);
    await runMutation(async () => {
      const scopeType = String(form.get("scope_type"));
      const scopeReference = String(form.get("scope_reference_id") ?? "").trim();
      const result = await createInvitation({
        email: String(form.get("email") ?? "").trim(),
        display_name: String(form.get("display_name") ?? "").trim(),
        role_keys: roleKeys,
        scope_type: scopeType,
        scope_reference_id: requiresScopeReference(scopeType) ? scopeReference : null,
      });
      setInvitationResult(result);
      onRefresh("Invitation created.");
    });
  }

  /** Submit a custom role create or update request. */
  async function submitRole(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const permissionKeys = form.getAll("permission_key").map(String);
    await runMutation(async () => {
      if (roleEditor === "new") {
        await createTenantRole({
          key: String(form.get("key") ?? "").trim(),
          display_name: String(form.get("display_name") ?? "").trim(),
          description: String(form.get("description") ?? "").trim(),
          permission_keys: permissionKeys,
        });
        onRefresh("Custom role created.");
      } else if (roleEditor) {
        await updateTenantRole(roleEditor.id, {
          display_name: String(form.get("display_name") ?? "").trim(),
          description: String(form.get("description") ?? "").trim(),
          is_active: form.get("is_active") === "on",
          permission_keys: permissionKeys,
        });
        onRefresh("Custom role updated.");
      }
      setRoleEditor(null);
    });
  }

  /** Change the current password and end the now-invalid browser session. */
  async function submitPassword(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const newPassword = String(form.get("new_password") ?? "");
    if (newPassword !== String(form.get("confirm_password") ?? "")) {
      onError("New password confirmation does not match.");
      return;
    }
    await runMutation(async () => {
      await changePassword(String(form.get("current_password") ?? ""), newPassword);
      setShowPassword(false);
      await onLogout();
    });
  }

  /** Load active role assignments before opening the assignment editor. */
  async function openAssignments(member: MembershipAdminSummary): Promise<void> {
    await runMutation(async () => {
      const assignments = await getMembershipRoleAssignments(member.id);
      const draft: Record<string, RoleDraft> = {};
      for (const role of roles) {
        const assignment = assignments.find((item) => item.role_id === role.id);
        draft[role.id] = {
          selected: Boolean(assignment),
          scopes: assignment?.scopes.length ? assignment.scopes : [emptyScope()],
        };
      }
      setAssignmentDraft(draft);
      setAssignmentMember(member);
    });
  }

  /** Persist the complete active role and scope selection for one membership. */
  async function saveAssignments(): Promise<void> {
    if (!assignmentMember) return;
    const assignments = Object.entries(assignmentDraft)
      .filter(([, value]) => value.selected)
      .map(([roleId, value]) => ({
        role_id: roleId,
        scopes: value.scopes.map((scope) => ({
          scope_type: scope.scope_type,
          scope_reference_id: requiresScopeReference(scope.scope_type)
            ? scope.scope_reference_id?.trim() || null
            : null,
        })),
      }));
    await runMutation(async () => {
      await replaceMembershipRoleAssignments(assignmentMember.id, assignments);
      setAssignmentMember(null);
      onRefresh("Membership roles and scopes updated.");
    });
  }

  /** Toggle one role in the assignment draft. */
  function toggleAssignmentRole(roleId: string, selected: boolean): void {
    setAssignmentDraft((current) => ({
      ...current,
      [roleId]: { selected, scopes: current[roleId]?.scopes ?? [emptyScope()] },
    }));
  }

  /** Add one scope row to a role assignment draft. */
  function addAssignmentScope(roleId: string): void {
    setAssignmentDraft((current) => ({
      ...current,
      [roleId]: { ...current[roleId], scopes: [...current[roleId].scopes, emptyScope()] },
    }));
  }

  /** Update one scope row without mutating existing draft state. */
  function updateAssignmentScope(roleId: string, index: number, patch: Partial<RoleScopeInput>): void {
    setAssignmentDraft((current) => ({
      ...current,
      [roleId]: {
        ...current[roleId],
        scopes: current[roleId].scopes.map((scope, scopeIndex) => (
          scopeIndex === index ? { ...scope, ...patch } : scope
        )),
      },
    }));
  }

  /** Remove one scope while retaining at least one scope per selected role. */
  function removeAssignmentScope(roleId: string, index: number): void {
    setAssignmentDraft((current) => ({
      ...current,
      [roleId]: {
        ...current[roleId],
        scopes: current[roleId].scopes.filter((_, scopeIndex) => scopeIndex !== index),
      },
    }));
  }

  if (showInvitation) {
    return <section className="workspace-stack access-workspace"><InvitationWorkspace roles={roles.filter((role) => role.is_active)} busy={busy} result={invitationResult} onClose={() => setShowInvitation(false)} onSubmit={submitInvitation} /></section>;
  }

  if (showPassword) {
    return <section className="workspace-stack access-workspace"><PasswordWorkspace busy={busy} onClose={() => setShowPassword(false)} onSubmit={submitPassword} /></section>;
  }

  if (roleEditor) {
    return <section className="workspace-stack access-workspace"><RoleWorkspace role={roleEditor} permissions={permissions} busy={busy} onClose={() => setRoleEditor(null)} onSubmit={submitRole} /></section>;
  }

  if (assignmentMember) {
    return <section className="workspace-stack access-workspace"><AssignmentWorkspace member={assignmentMember} roles={roles.filter((role) => role.is_active)} draft={assignmentDraft} busy={busy} onClose={() => setAssignmentMember(null)} onSave={saveAssignments} onToggleRole={toggleAssignmentRole} onAddScope={addAssignmentScope} onUpdateScope={updateAssignmentScope} onRemoveScope={removeAssignmentScope} /></section>;
  }

  return (
    <section className="workspace-stack access-workspace">
      <div className="access-toolbar" aria-label="Access administration actions">
        <button className="primary-action" type="button" onClick={() => { setInvitationResult(null); setShowInvitation(true); }}><UserPlus aria-hidden /> Invite member</button>
        <button className="row-action" type="button" onClick={() => setRoleEditor("new")}><ShieldCheck aria-hidden /> Create role</button>
        <button className="row-action secondary" type="button" onClick={() => setShowPassword(true)}><KeyRound aria-hidden /> Change password</button>
      </div>

      <section className="split-grid">
        <article className="sample-table-shell">
          <header><div><h2>Actor context</h2><span>Server-resolved authorization</span></div></header>
          {actor ? <div className="kv-grid"><p><strong>Account</strong><span>{shortId(actor.account_id)}</span></p><p><strong>Membership</strong><span>{shortId(actor.membership_id)}</span></p><p><strong>Tenant</strong><span>{shortId(actor.tenant_id)}</span></p><p><strong>Roles</strong><span>{actor.role_keys.join(", ") || "-"}</span></p><p><strong>Permissions</strong><span>{actor.permissions.length}</span></p><p><strong>Scopes</strong><span>{actor.scopes.length}</span></p></div> : <EmptyAccess message="No actor context found." />}
        </article>

        <article className="sample-table-shell">
          <header><div><h2>Your sessions</h2><span>{sessions.length} active or historical</span></div></header>
          {sessions.length === 0 ? <EmptyAccess message="No sessions found." /> : <div className="sample-table">{sessions.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.user_agent ?? "Unknown device"}</strong><p>Last used {formatDateTime(row.last_used_at)} · {row.ip_address ?? "No IP"}</p></div>{row.revoked_at ? <span className="row-status">Revoked</span> : <button className="row-action" type="button" disabled={busy} onClick={() => runMutation(async () => { await revokeSession(row.id); onRefresh("Session revoked."); })}>Revoke</button>}</article>)}</div>}
        </article>

        <article className="sample-table-shell span-two">
          <header><div><h2>Tenant roles</h2><span>{roles.length} configured roles · {permissions.length} available permissions</span></div></header>
          {roles.length === 0 ? <EmptyAccess message="No tenant roles found." /> : <div className="sample-table">{roles.map((role, index) => <article key={role.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{role.display_name}</strong><p>{role.key} · {role.permission_keys.length} permissions · {role.is_system_managed ? "system" : "custom"}</p></div>{role.is_system_managed ? <span className="row-status">{role.is_active ? "Active" : "Inactive"}</span> : <button className="row-action" type="button" onClick={() => setRoleEditor(role)}>Edit</button>}</article>)}</div>}
        </article>

        <article className="sample-table-shell span-two">
          <header><div><h2>Memberships</h2><span>{memberships.length} tenant memberships</span></div></header>
          {memberships.length === 0 ? <EmptyAccess message="No memberships found." /> : <div className="sample-table">{memberships.map((member, index) => {
            const isSelf = member.id === actor?.membership_id;
            return <article key={member.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{member.display_name}</strong><p>{member.email} · {member.status} · {member.role_keys.join(", ") || "No roles"}</p></div><div className="inline-actions">{!isSelf && member.status !== "ended" && <button className="row-action" type="button" disabled={busy} onClick={() => openAssignments(member)}>Roles & scopes</button>}{!isSelf && <button className="row-action secondary" type="button" disabled={busy} onClick={() => runMutation(async () => { const result = await revokeMembershipSessions(member.id); onRefresh(`${result.revoked_sessions} member sessions revoked.`); })}><LogOut aria-hidden /> Force logout</button>}{!isSelf && member.status === "active" && <button className="row-action secondary" type="button" disabled={busy} onClick={() => runMutation(async () => { await updateMembershipStatus(member.id, "suspended"); onRefresh("Membership suspended."); })}>Suspend</button>}{!isSelf && member.status === "suspended" && <button className="row-action" type="button" disabled={busy} onClick={() => runMutation(async () => { await updateMembershipStatus(member.id, "active"); onRefresh("Membership activated."); })}>Reactivate</button>}{!isSelf && member.status !== "ended" && <button className="row-action danger" type="button" disabled={busy} onClick={() => runMutation(async () => { await updateMembershipStatus(member.id, "ended"); onRefresh("Membership ended."); })}>End</button>}{isSelf && <span className="row-status">Current account</span>}</div></article>;
          })}</div>}
        </article>
      </section>

    </section>
  );
}

/** Render the invitation form and its one-time delivery token. */
function InvitationWorkspace({ roles, busy, result, onClose, onSubmit }: Readonly<{ roles: TenantRoleAdminSummary[]; busy: boolean; result: InvitationResponse | null; onClose: () => void; onSubmit: (event: React.SubmitEvent<HTMLFormElement>) => Promise<void> }>) {
  return <article className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="invite-title"><header><div><p>IDENTITY</p><h2 id="invite-title">Invite member</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close invitation form">x</button></header>{result ? <div className="screen-result"><UsersRound aria-hidden /><strong>Invitation ready for delivery</strong><p>Expires {formatDateTime(result.expires_at)}. The token is shown once until a provider is configured.</p><textarea readOnly aria-label="Invitation token" value={result.invitation_token} /><button className="primary-action" type="button" onClick={onClose}>Done</button></div> : <form className="master-form" onSubmit={onSubmit}><label>Display name<input name="display_name" required maxLength={160} /></label><label>Email<input name="email" type="email" required maxLength={320} /></label><fieldset className="choice-grid"><legend>Initial roles</legend>{roles.map((role) => <label key={role.id}><input type="checkbox" name="role_key" value={role.key} />{role.display_name}</label>)}</fieldset><div className="form-grid"><label>Scope<select name="scope_type" defaultValue="institution">{scopeTypes.map((scope) => <option key={scope} value={scope}>{scope.replaceAll("_", " ")}</option>)}</select></label><label>Scope reference<input name="scope_reference_id" placeholder="Required for referenced scopes" /></label></div><footer><button type="button" onClick={onClose}>Cancel</button><button className="primary-action" type="submit" disabled={busy}>{busy ? "Creating..." : "Create invitation"}</button></footer></form>}</article>;
}

/** Render the current-account password change form. */
function PasswordWorkspace({ busy, onClose, onSubmit }: Readonly<{ busy: boolean; onClose: () => void; onSubmit: (event: React.SubmitEvent<HTMLFormElement>) => Promise<void> }>) {
  return <article className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="password-title"><header><div><p>SECURITY</p><h2 id="password-title">Change password</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close password form">x</button></header><form className="master-form" onSubmit={onSubmit}><label>Current password<input name="current_password" type="password" autoComplete="current-password" required maxLength={72} /></label><label>New password<input name="new_password" type="password" autoComplete="new-password" required maxLength={72} /></label><label>Confirm new password<input name="confirm_password" type="password" autoComplete="new-password" required maxLength={72} /></label><footer><button type="button" onClick={onClose}>Cancel</button><button className="primary-action" type="submit" disabled={busy}>{busy ? "Changing..." : "Change and sign out"}</button></footer></form></article>;
}

/** Render a custom tenant role editor with explicit permission grants. */
function RoleWorkspace({ role, permissions, busy, onClose, onSubmit }: Readonly<{ role: TenantRoleAdminSummary | "new"; permissions: PermissionAdminSummary[]; busy: boolean; onClose: () => void; onSubmit: (event: React.SubmitEvent<HTMLFormElement>) => Promise<void> }>) {
  const isNew = role === "new";
  const selected = new Set(isNew ? [] : role.permission_keys);
  return <article className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide" aria-labelledby="role-title"><header><div><p>AUTHORIZATION</p><h2 id="role-title">{isNew ? "Create custom role" : `Edit ${role.display_name}`}</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close role form">x</button></header><form className="master-form" onSubmit={onSubmit}>{isNew && <label>Role key<input name="key" required pattern="[a-z][a-z0-9_]*" placeholder="department_coordinator" /></label>}<label>Display name<input name="display_name" required defaultValue={isNew ? "" : role.display_name} /></label><label>Description<textarea name="description" required defaultValue={isNew ? "" : role.description} rows={3} /></label>{!isNew && <label className="toggle-line"><input type="checkbox" name="is_active" defaultChecked={role.is_active} />Role is active</label>}<fieldset className="permission-grid"><legend>Permissions</legend>{permissions.map((permission) => <label key={permission.key} title={permission.description}><input type="checkbox" name="permission_key" value={permission.key} defaultChecked={selected.has(permission.key)} /><span><strong>{permission.key}</strong><small>{permission.description}</small></span></label>)}</fieldset><footer><button type="button" onClick={onClose}>Cancel</button><button className="primary-action" type="submit" disabled={busy}>{busy ? "Saving..." : "Save role"}</button></footer></form></article>;
}

/** Render effective role and scope assignment controls for one membership. */
function AssignmentWorkspace({ member, roles, draft, busy, onClose, onSave, onToggleRole, onAddScope, onUpdateScope, onRemoveScope }: Readonly<{ member: MembershipAdminSummary; roles: TenantRoleAdminSummary[]; draft: Record<string, RoleDraft>; busy: boolean; onClose: () => void; onSave: () => Promise<void>; onToggleRole: (roleId: string, selected: boolean) => void; onAddScope: (roleId: string) => void; onUpdateScope: (roleId: string, index: number, patch: Partial<RoleScopeInput>) => void; onRemoveScope: (roleId: string, index: number) => void }>) {
  return <article className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide" aria-labelledby="assignments-title"><header><div><p>ACCESS SCOPE</p><h2 id="assignments-title">Roles for {member.display_name}</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close role assignments">x</button></header><div className="assignment-editor">{roles.map((role) => { const roleDraft = draft[role.id] ?? { selected: false, scopes: [emptyScope()] }; return <section key={role.id} className={roleDraft.selected ? "assignment-role selected" : "assignment-role"}><label className="toggle-line"><input type="checkbox" checked={roleDraft.selected} onChange={(event) => onToggleRole(role.id, event.target.checked)} /><span><strong>{role.display_name}</strong><small>{role.key}</small></span></label>{roleDraft.selected && <div className="scope-list">{roleDraft.scopes.map((scope, index) => <div className="scope-row" key={`${role.id}-${index}`}><select aria-label={`${role.display_name} scope type ${index + 1}`} value={scope.scope_type} onChange={(event) => onUpdateScope(role.id, index, { scope_type: event.target.value, scope_reference_id: null })}>{scopeTypes.map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}</select>{requiresScopeReference(scope.scope_type) && <input aria-label={`${role.display_name} scope reference ${index + 1}`} value={scope.scope_reference_id ?? ""} onChange={(event) => onUpdateScope(role.id, index, { scope_reference_id: event.target.value })} placeholder="Record UUID" required />}{roleDraft.scopes.length > 1 && <button className="row-action secondary" type="button" onClick={() => onRemoveScope(role.id, index)}>Remove</button>}</div>)}<button className="row-action secondary" type="button" onClick={() => onAddScope(role.id)}>Add scope</button></div>}</section>; })}</div><footer className="screen-footer"><button type="button" onClick={onClose}>Cancel</button><button className="primary-action" type="button" disabled={busy || !Object.values(draft).some((value) => value.selected)} onClick={onSave}>{busy ? "Saving..." : "Save assignments"}</button></footer></article>;
}

/** Return whether a scope type requires a domain record UUID. */
function requiresScopeReference(scopeType: string): boolean {
  return scopeType !== "institution" && scopeType !== "own_record";
}

/** Create one default institution-wide role scope. */
function emptyScope(): RoleScopeInput {
  return { scope_type: "institution", scope_reference_id: null };
}

/** Render a compact empty state inside access panels. */
function EmptyAccess({ message }: Readonly<{ message: string }>) {
  return <div className="state-shell"><ShieldCheck className="state-icon" aria-hidden /><p>{message}</p></div>;
}

/** Format an optional timestamp for compact access records. */
function formatDateTime(value: string | null): string {
  if (!value) return "Never";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

/** Shorten UUID values while preserving recognizable context. */
function shortId(value: string): string {
  return `${value.slice(0, 8)}...`;
}