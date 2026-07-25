/** One typed function per backend endpoint. */

import { apiClient } from "@/lib/api/client";
import type {
  AskRequest,
  AskResponse,
  GraphResponse,
  HealthResponse,
  IndexRequest,
  IndexResponse,
  RepositoryReport,
  RootResponse,
  ScanRequest,
  ScanResponse,
  StatusResponse,
} from "@/types/api";

export const api = {
  root: (signal?: AbortSignal) => apiClient.get<RootResponse>("/", { signal }),

  health: (signal?: AbortSignal) =>
    apiClient.get<HealthResponse>("/health", { signal, timeoutMs: 10_000 }),

  status: (signal?: AbortSignal) =>
    apiClient.get<StatusResponse>("/status", { signal, timeoutMs: 15_000 }),

  scan: (payload: ScanRequest, signal?: AbortSignal) =>
    apiClient.post<ScanResponse>("/scan", payload, { signal }),

  index: (payload: IndexRequest, signal?: AbortSignal) =>
    apiClient.post<IndexResponse>("/index", payload, {
      signal,
      timeoutMs: 600_000,
    }),

  graph: (repositoryPath: string, signal?: AbortSignal) =>
    apiClient.get<GraphResponse>("/graph", {
      searchParams: { repository_path: repositoryPath },
      signal,
    }),

  report: (repositoryPath: string, signal?: AbortSignal) =>
    apiClient.get<RepositoryReport>("/report", {
      searchParams: { repository_path: repositoryPath },
      signal,
    }),

  ask: (payload: AskRequest, signal?: AbortSignal) =>
    apiClient.post<AskResponse>("/ask", payload, {
      signal,
      timeoutMs: 300_000,
    }),
};
