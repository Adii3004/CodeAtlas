import { Loader2 } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return (
    <Loader2
      className={cn("text-muted-foreground size-4 animate-spin", className)}
      aria-hidden
    />
  );
}

/** Full-region loading state used as a Suspense fallback. */
export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div
      className="flex min-h-[60vh] flex-col items-center justify-center gap-3"
      role="status"
      aria-live="polite"
    >
      <Spinner className="size-5" />
      <p className="text-muted-foreground text-sm">{label}…</p>
    </div>
  );
}

/** Card-shaped skeleton grid for metric tiles. */
export function StatCardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="bg-card space-y-3 rounded-xl border p-5">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-7 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
      ))}
    </div>
  );
}

/** Rectangular skeleton for tables and lists. */
export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading table">
      <Skeleton className="h-9 w-full" />
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} className="h-11 w-full" />
      ))}
    </div>
  );
}

export function ChartSkeleton({ className }: { className?: string }) {
  return <Skeleton className={cn("h-64 w-full", className)} />;
}
