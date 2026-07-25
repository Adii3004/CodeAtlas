import { AlertTriangle, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

export interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  className?: string;
}

/** Turn any thrown value into a readable message. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}

/** Inline error surface for failed queries and mutations. */
export function ErrorState({
  error,
  onRetry,
  title = "Something went wrong",
  className,
}: ErrorStateProps) {
  const code = error instanceof ApiError ? error.code : null;

  return (
    <div
      role="alert"
      className={cn(
        "border-destructive/30 bg-destructive/5 flex flex-col items-start gap-3 rounded-xl border p-5",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle
          className="text-destructive mt-0.5 size-4 shrink-0"
          aria-hidden
        />
        <div className="space-y-1">
          <p className="text-sm font-medium">{title}</p>
          <p className="text-muted-foreground text-sm">{errorMessage(error)}</p>
          {code ? (
            <p className="text-muted-foreground font-mono text-xs">{code}</p>
          ) : null}
        </div>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="size-4" />
          Try again
        </Button>
      ) : null}
    </div>
  );
}
