import axios, { AxiosError } from "axios";

export type PlatformActor = {
  account_id: string;
  role_keys: string[];
  permissions: string[];
};

export type PlatformAuthentication = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  actor: PlatformActor;
};

export type PlatformTenant = {
  id: string;
  key: string;
  display_name: string;
  short_name: string;
  status: string;
  timezone: string;
  primary_color: string;
  accent_color: string;
};

const PLATFORM_REFRESH_KEY = "cms.platform.refresh-token";
const platformApi = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? "" });
let platformAccessToken: string | null = null;

platformApi.interceptors.request.use((config) => {
  if (platformAccessToken) config.headers.Authorization = `Bearer ${platformAccessToken}`;
  return config;
});

/** Authenticate against the isolated platform audience. */
export async function platformLogin(email: string, password: string): Promise<PlatformAuthentication> {
  const { data } = await platformApi.post<PlatformAuthentication>("/api/v1/platform/auth/login", {
    email,
    password,
  });
  storeAuthentication(data);
  return data;
}

/** Restore a platform session by rotating its tab-scoped refresh token. */
export async function restorePlatformSession(): Promise<PlatformAuthentication | null> {
  const refreshToken = sessionStorage.getItem(PLATFORM_REFRESH_KEY);
  if (!refreshToken) return null;
  try {
    const { data } = await platformApi.post<PlatformAuthentication>("/api/v1/platform/auth/refresh", {
      refresh_token: refreshToken,
    });
    storeAuthentication(data);
    return data;
  } catch {
    clearPlatformSession();
    return null;
  }
}

/** Revoke the current platform refresh session and clear platform credentials. */
export async function platformLogout(): Promise<void> {
  const refreshToken = sessionStorage.getItem(PLATFORM_REFRESH_KEY);
  try {
    if (refreshToken) {
      await platformApi.post("/api/v1/platform/auth/logout", { refresh_token: refreshToken });
    }
  } finally {
    clearPlatformSession();
  }
}

/** Fetch the global tenant directory through platform authorization. */
export async function getPlatformTenants(): Promise<PlatformTenant[]> {
  const { data } = await platformApi.get<PlatformTenant[]>("/api/v1/platform/tenants");
  return data;
}

/** Apply one audited tenant lifecycle transition. */
export async function updatePlatformTenantStatus(
  tenantId: string,
  status: "active" | "suspended" | "closed",
): Promise<{ tenant_id: string; status: string; revoked_sessions: number }> {
  const { data } = await platformApi.patch(`/api/v1/platform/tenants/${tenantId}/status`, { status });
  return data;
}

/** Convert platform API failures into bounded user-facing messages. */
export function getPlatformErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Platform administration is unavailable. Please try again.";
}

/** Retain a rotated platform credential pair for the current browser tab. */
function storeAuthentication(authentication: PlatformAuthentication): void {
  platformAccessToken = authentication.access_token;
  sessionStorage.setItem(PLATFORM_REFRESH_KEY, authentication.refresh_token);
}

/** Remove all browser-held platform credentials. */
function clearPlatformSession(): void {
  platformAccessToken = null;
  sessionStorage.removeItem(PLATFORM_REFRESH_KEY);
}