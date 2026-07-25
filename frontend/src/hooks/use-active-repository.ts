import { useLocalStorage } from "@/hooks/use-local-storage";
import { useRepositories, type TrackedRepository } from "@/hooks/use-repositories";

const ACTIVE_KEY = "codeatlas.active-repository";

/**
 * The repository the Chat, Graph, and Report pages operate on.
 *
 * Stored by id and resolved against the tracked list, so a removed
 * repository degrades to "none selected" rather than a dangling path.
 */
export function useActiveRepository() {
  const { repositories } = useRepositories();
  const [activeId, setActiveId] = useLocalStorage<string | null>(
    ACTIVE_KEY,
    null,
  );

  const active: TrackedRepository | null =
    repositories.find((repository) => repository.id === activeId) ??
    repositories[0] ??
    null;

  return {
    repositories,
    active,
    activeId: active?.id ?? null,
    setActive: (id: string) => setActiveId(id),
  };
}
