import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: LucideIcon;
  /** Short editorial line, set in the serif accent face. */
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

/** Warm, editorial placeholder for "nothing here yet" moments. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "border-border/70 flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed px-6 py-16 text-center",
        className,
      )}
    >
      {Icon ? (
        <div
          className="bg-accent-soft text-accent flex size-11 items-center justify-center rounded-xl"
          aria-hidden
        >
          <Icon className="size-5" />
        </div>
      ) : null}
      <div className="space-y-2">
        <p className="font-editorial text-xl">{title}</p>
        {description ? (
          <p className="text-muted-foreground mx-auto max-w-sm text-sm leading-relaxed text-balance">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}
