/** Centralized React Query cache keys. */

export const queryKeys = {
  all: ["codeatlas"] as const,
  health: () => [...queryKeys.all, "health"] as const,
  status: () => [...queryKeys.all, "status"] as const,
  graph: (repositoryPath: string) =>
    [...queryKeys.all, "graph", repositoryPath] as const,
  report: (repositoryPath: string) =>
    [...queryKeys.all, "report", repositoryPath] as const,
} as const;
