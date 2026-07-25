import { FolderGit2 } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export interface RepositoryPathFieldProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  label?: string;
  hint?: string;
  disabled?: boolean;
  className?: string;
}

/**
 * Repository path input. The backend reads repositories from the local
 * filesystem, so this is a plain path field rather than a file picker.
 */
export function RepositoryPathField({
  id = "repository-path",
  value,
  onChange,
  label = "Repository path",
  hint = "Absolute path on the machine running the backend.",
  disabled,
  className,
}: RepositoryPathFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <FolderGit2
          className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
          aria-hidden
        />
        <Input
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="C:/projects/my-repo"
          disabled={disabled}
          spellCheck={false}
          autoComplete="off"
          className="pl-9 font-mono text-xs"
          aria-describedby={hint ? `${id}-hint` : undefined}
        />
      </div>
      {hint ? (
        <p id={`${id}-hint`} className="text-muted-foreground text-xs">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
