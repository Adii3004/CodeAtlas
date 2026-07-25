/**
 * Typed HTTP client for the CodeAtlas backend.
 *
 * Unwraps the shared `{ success, data, error, message }` envelope, applies a
 * request timeout, and normalizes every failure into an `ApiError`.
 */

import { env, getApiBaseUrl } from "@/lib/env";
import type { ApiErrorCode, ApiResponse } from "@/types/api";

export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;

  constructor(message: string, code: ApiErrorCode, status = 0) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }

  /** True for failures worth retrying (network blips, timeouts, 5xx). */
  get isRetryable(): boolean {
    return (
      this.code === "network_error" ||
      this.code === "timeout" ||
      this.status >= 500
    );
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  searchParams?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  timeoutMs?: number;
}

function buildUrl(
  path: string,
  searchParams?: RequestOptions["searchParams"],
): string {
  const url = new URL(
    path.startsWith("/") ? path : `/${path}`,
    `${getApiBaseUrl()}/`,
  );
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

function toApiError(payload: unknown, status: number): ApiError {
  const envelope = payload as Partial<ApiResponse<unknown>> | null;
  const code = (envelope?.error ?? "http_error") as ApiErrorCode;
  const message =
    envelope?.message && envelope.message.length > 0
      ? envelope.message
      : `Request failed with status ${status}.`;
  return new ApiError(message, code, status);
}

/**
 * Perform a request and return the unwrapped `data` payload.
 *
 * @throws {ApiError} for network failures, timeouts, and error responses.
 */
export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, searchParams, signal, timeoutMs } = options;

  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(new DOMException("Timeout", "TimeoutError")),
    timeoutMs ?? env.apiTimeoutMs,
  );
  // Let callers (e.g. React Query cancellation) abort us too.
  signal?.addEventListener("abort", () => controller.abort(signal.reason), {
    once: true,
  });

  let response: Response;
  try {
    response = await fetch(buildUrl(path, searchParams), {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new ApiError(
        "The request timed out. The backend may still be working.",
        "timeout",
      );
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The request was cancelled.", "network_error");
    }
    throw new ApiError(
      `Cannot reach the API at ${getApiBaseUrl()}. Is the backend running?`,
      "network_error",
    );
  } finally {
    window.clearTimeout(timeout);
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    if (!response.ok) throw toApiError(null, response.status);
    throw new ApiError("The API returned an invalid response.", "unknown_error");
  }

  if (!response.ok) throw toApiError(payload, response.status);

  const envelope = payload as ApiResponse<T>;
  if (!envelope.success || envelope.data === null) {
    throw toApiError(payload, response.status);
  }
  return envelope.data;
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => request<T>(path, { ...options, method: "POST", body }),
};
