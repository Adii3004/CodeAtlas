import { useLocalStorage } from "@/hooks/use-local-storage";
import { STORAGE_KEYS } from "@/lib/env";

/** A repository the user has scanned or indexed, remembered locally. */
export interface TrackedRepository {
  id: string;
  name: string;
  path: string;
  collectionName: string | null;
  lastScannedAt: string | null;
  lastIndexedAt: string | null;
  totalFiles: number | null;
  totalChunks: number | null;
}

function repositoryId(path: string): string {
  return path.replace(/\\/g, "/").toLowerCase();
}

/**
 * The repository list is client-side only — the backend is stateless and
 * takes a path per request.
 */
export function useRepositories() {
  const [repositories, setRepositories] = useLocalStorage<TrackedRepository[]>(
    STORAGE_KEYS.repositories,
    [],
  );

  const upsert = (
    path: string,
    patch: Partial<Omit<TrackedRepository, "id" | "path">>,
  ) => {
    const id = repositoryId(path);
    setRepositories((previous) => {
      const existing = previous.find((repository) => repository.id === id);
      const next: TrackedRepository = {
        id,
        path,
        name: patch.name ?? existing?.name ?? path.split(/[\\/]/).pop() ?? path,
        collectionName: patch.collectionName ?? existing?.collectionName ?? null,
        lastScannedAt: patch.lastScannedAt ?? existing?.lastScannedAt ?? null,
        lastIndexedAt: patch.lastIndexedAt ?? existing?.lastIndexedAt ?? null,
        totalFiles: patch.totalFiles ?? existing?.totalFiles ?? null,
        totalChunks: patch.totalChunks ?? existing?.totalChunks ?? null,
      };
      return existing
        ? previous.map((repository) =>
            repository.id === id ? next : repository,
          )
        : [next, ...previous];
    });
  };

  const remove = (id: string) => {
    setRepositories((previous) =>
      previous.filter((repository) => repository.id !== id),
    );
  };

  const clear = () => setRepositories([]);

  return { repositories, upsert, remove, clear };
}
