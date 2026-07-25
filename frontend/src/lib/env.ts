/**
 * Typed access to build-time environment variables.
 *
 * The API base URL can be overridden at runtime from the Settings page; that
 * override is stored in localStorage and read by the API client.
 */

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TIMEOUT_MS = 120_000;

function readNumber(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export const env = {
  apiBaseUrl: (
    import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL
  ).replace(/\/+$/, ""),
  apiTimeoutMs: readNumber(
    import.meta.env.VITE_API_TIMEOUT_MS,
    DEFAULT_TIMEOUT_MS,
  ),
  isDev: import.meta.env.DEV,
} as const;

export const STORAGE_KEYS = {
  theme: "codeatlas.theme",
  apiBaseUrl: "codeatlas.api-base-url",
  preferences: "codeatlas.preferences",
  repositories: "codeatlas.repositories",
} as const;

/** Effective API base URL: runtime override if set, otherwise build-time. */
export function getApiBaseUrl(): string {
  if (typeof window === "undefined") return env.apiBaseUrl;
  const override = window.localStorage.getItem(STORAGE_KEYS.apiBaseUrl);
  return override && override.trim().length > 0
    ? override.replace(/\/+$/, "")
    : env.apiBaseUrl;
}
