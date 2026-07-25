import { FolderGit2 } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useActiveRepository } from "@/hooks/use-active-repository";
import { cn } from "@/lib/utils";

export interface RepositorySelectorProps {
  className?: string;
  /** Only offer repositories that have been indexed into a collection. */
  indexedOnly?: boolean;
}

/** Chooses which tracked repository the current page operates on. */
export function RepositorySelector({
  className,
  indexedOnly = false,
}: RepositorySelectorProps) {
  const { repositories, activeId, setActive } = useActiveRepository();
  const options = indexedOnly
    ? repositories.filter((repository) => repository.collectionName)
    : repositories;

  if (options.length === 0) return null;

  return (
    <Select value={activeId ?? undefined} onValueChange={setActive}>
      <SelectTrigger
        aria-label="Active repository"
        className={cn("w-[16rem] max-w-full", className)}
      >
        <FolderGit2 className="text-muted-foreground size-4 shrink-0" />
        <SelectValue placeholder="Choose a repository" />
      </SelectTrigger>
      <SelectContent>
        {options.map((repository) => (
          <SelectItem key={repository.id} value={repository.id}>
            {repository.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
