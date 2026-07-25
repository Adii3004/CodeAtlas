import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { AnimatedNumber } from "@/components/common/animated-number";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface StatCardProps {
  label: string;
  /** Pass a number to animate the count-up; anything else renders as-is. */
  value: ReactNode | number;
  hint?: string;
  icon?: LucideIcon;
  format?: (value: number) => string;
  className?: string;
}

/** Compact metric tile used across the overview and insights pages. */
export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  format,
  className,
}: StatCardProps) {
  return (
    <Card className={cn("hover-lift h-full p-5", className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1.5">
          <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            {label}
          </p>
          <p className="truncate text-[1.75rem] leading-none font-semibold tracking-tight tabular-nums">
            {typeof value === "number" ? (
              <AnimatedNumber value={value} format={format} />
            ) : (
              value
            )}
          </p>
          {hint ? (
            <p className="text-muted-foreground truncate text-xs">{hint}</p>
          ) : null}
        </div>
        {Icon ? (
          <div
            className="bg-accent-soft text-accent flex size-9 shrink-0 items-center justify-center rounded-lg"
            aria-hidden
          >
            <Icon className="size-4" />
          </div>
        ) : null}
      </div>
    </Card>
  );
}
