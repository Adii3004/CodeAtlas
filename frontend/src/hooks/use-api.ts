/**
 * React Query bindings for every backend endpoint.
 *
 * Queries are enabled only when their inputs are present, so pages can call
 * them unconditionally.
 */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  AskRequest,
  AskResponse,
  IndexRequest,
  IndexResponse,
  ScanRequest,
  ScanResponse,
} from "@/types/api";

export function useHealth(options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: ({ signal }) => api.health(signal),
    refetchInterval: options?.refetchInterval,
    retry: 1,
  });
}

export function useStatus(options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.status(),
    queryFn: ({ signal }) => api.status(signal),
    refetchInterval: options?.refetchInterval,
  });
}

export function useGraph(repositoryPath: string | undefined) {
  return useQuery({
    queryKey: queryKeys.graph(repositoryPath ?? ""),
    queryFn: ({ signal }) => api.graph(repositoryPath!, signal),
    enabled: Boolean(repositoryPath),
    staleTime: 60_000,
  });
}

export function useReport(repositoryPath: string | undefined) {
  return useQuery({
    queryKey: queryKeys.report(repositoryPath ?? ""),
    queryFn: ({ signal }) => api.report(repositoryPath!, signal),
    enabled: Boolean(repositoryPath),
    staleTime: 60_000,
  });
}

export function useScanRepository() {
  return useMutation<ScanResponse, Error, ScanRequest>({
    mutationFn: (payload) => api.scan(payload),
  });
}

export function useIndexRepository() {
  return useMutation<IndexResponse, Error, IndexRequest>({
    mutationFn: (payload) => api.index(payload),
  });
}

export function useAskQuestion() {
  return useMutation<AskResponse, Error, AskRequest>({
    mutationFn: (payload) => api.ask(payload),
  });
}
