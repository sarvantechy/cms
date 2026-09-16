import axios, { AxiosError, type AxiosRequestConfig } from "axios";

export type ActorScope = {
  scope_type: string;
  scope_reference_id: string | null;
};

export type ActorSummary = {
  account_id: string;
  tenant_id: string;
  membership_id: string;
  role_keys: string[];
  permissions: string[];
  scopes: ActorScope[];
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  actor: ActorSummary;
};

export type SessionIdentity = {
  tenantKey: string;
  email: string;
};

export type SelectableMembership = {
  id: string;
  status: string;
  tenant: {
    id: string;
    key: string;
    display_name: string;
    short_name: string;
    status: string;
    timezone: string;
    primary_color: string;
    accent_color: string;
  };
  roles: { id: string; key: string; display_name: string; description: string }[];
};

export type AcademicsOverview = {
  campuses: number;
  academic_years: number;
  terms: number;
  departments: number;
  programs: number;
  subjects: number;
  batches: number;
  sections: number;
  rooms: number;
};

export type CampusSummary = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  address: string | null;
  status: string;
};

export type ProgramSummary = {
  id: string;
  tenant_id: string;
  department_id: string;
  code: string;
  name: string;
  degree_level: string;
  duration_years: number;
  status: string;
};

export type DepartmentSummary = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  status: string;
};

export type ProgramCreate = {
  department_id: string;
  code: string;
  name: string;
  degree_level: string;
  duration_years: number;
  status: "active" | "inactive" | "discontinued";
};

const REFRESH_TOKEN_KEY = "indus.portal.refresh-token";
const SESSION_IDENTITY_KEY = "indus.portal.identity";
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? "" });
let accessToken: string | null = null;
let restoration: Promise<{ authentication: TokenResponse; identity: SessionIdentity } | null> | null = null;

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

/** Run one authenticated API request through the shared Axios client. */
export async function apiRequest<TResponse>(config: AxiosRequestConfig): Promise<TResponse> {
  const { data } = await api.request<TResponse>(config);
  return data;
}

/** Authenticate a tenant member and retain only the refresh credential across page reloads. */
export async function login(
  identity: SessionIdentity,
  password: string,
): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/login", {
    tenant_key: identity.tenantKey,
    email: identity.email,
    password,
  });
  accessToken = data.access_token;
  sessionStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  sessionStorage.setItem(SESSION_IDENTITY_KEY, JSON.stringify(identity));
  restoration = null;
  return data;
}

/** List active tenant memberships available to the current authenticated account. */
export async function getSelectableMemberships(): Promise<SelectableMembership[]> {
  const { data } = await api.get<SelectableMembership[]>("/api/v1/auth/memberships");
  return data;
}

/** Rotate credentials into another active tenant membership for the current account. */
export async function switchTenant(identity: SessionIdentity): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/switch-tenant", {
    tenant_key: identity.tenantKey,
  });
  accessToken = data.access_token;
  sessionStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  sessionStorage.setItem(SESSION_IDENTITY_KEY, JSON.stringify(identity));
  restoration = null;
  return data;
}

/** Rotate the tab-scoped refresh credential and restore an authenticated browser session once. */
export function restoreSession(): Promise<{
  authentication: TokenResponse;
  identity: SessionIdentity;
} | null> {
  restoration ??= restoreStoredSession();
  return restoration;
}

/** Revoke the current refresh session and clear all browser-held credentials. */
export async function logout(): Promise<void> {
  const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
  try {
    if (refreshToken) {
      await api.post("/api/v1/auth/logout", { refresh_token: refreshToken });
    }
  } finally {
    clearSession();
  }
}

/** Convert an API failure into a bounded message suitable for the login form. */
export function authenticationErrorMessage(error: unknown): string {
  if (error instanceof AxiosError && error.response?.status === 401) {
    return "The college, email, or password is incorrect.";
  }
  return "The college portal is unavailable. Please try again.";
}

/** Clear credentials after rejected restoration or explicit logout. */
export function clearSession(): void {
  accessToken = null;
  restoration = null;
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(SESSION_IDENTITY_KEY);
}

/** Read, rotate, and replace a previously stored refresh credential. */
async function restoreStoredSession(): Promise<{
  authentication: TokenResponse;
  identity: SessionIdentity;
} | null> {
  const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
  const identityValue = sessionStorage.getItem(SESSION_IDENTITY_KEY);
  if (!refreshToken || !identityValue) {
    clearSession();
    return null;
  }

  try {
    const identity = JSON.parse(identityValue) as SessionIdentity;
    if (!identity.tenantKey || !identity.email) {
      throw new Error("Stored session identity is incomplete");
    }
    const { data } = await api.post<TokenResponse>("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    accessToken = data.access_token;
    sessionStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    return { authentication: data, identity };
  } catch {
    clearSession();
    return null;
  }
}

/** Fetch academics overview with counts of configured structures. */
export async function getAcademicsOverview(): Promise<AcademicsOverview> {
  const { data } = await api.get<AcademicsOverview>("/api/v1/academics/overview");
  return data;
}

/** Fetch list of programs for the authenticated tenant. */
export async function getPrograms(): Promise<{ items: ProgramSummary[]; total: number }> {
  const { data } = await api.get<{ items: ProgramSummary[]; total: number }>(
    "/api/v1/academics/programs"
  );
  return data;
}

/** Create a program within a department visible to the authenticated tenant actor. */
export async function createProgram(payload: ProgramCreate): Promise<ProgramSummary> {
  const { data } = await api.post<ProgramSummary>("/api/v1/academics/programs", payload);
  return data;
}

/** Fetch list of departments for the authenticated tenant. */
export async function getDepartments(): Promise<{ items: DepartmentSummary[]; total: number }> {
  const { data } = await api.get<{ items: DepartmentSummary[]; total: number }>(
    "/api/v1/academics/departments"
  );
  return data;
}

/** Fetch list of campuses for the authenticated tenant. */
export async function getCampuses(): Promise<{ items: CampusSummary[]; total: number }> {
  const { data } = await api.get<{ items: CampusSummary[]; total: number }>(
    "/api/v1/academics/campuses"
  );
  return data;
}
