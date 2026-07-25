import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils";

export interface ProgressProps {
  /** 0–100. Omit for an indeterminate bar. */
  value?: number;
  label?: string;
  className?: string;
}

/**
 * Determinate or indeterminate progress bar.
 *
 * The backend performs scan and index work in a single request, so
 * long-running steps use the indeterminate variant.
 */
export function Progress({ value, label, className }: ProgressProps) {
  const reduceMotion = useReducedMotion();
  const indeterminate = value === undefined;

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={indeterminate ? undefined : Math.round(value)}
      className={cn(
        "bg-muted relative h-1.5 w-full overflow-hidden rounded-full",
        className,
      )}
    >
      {indeterminate ? (
        <motion.div
          className="bg-accent absolute inset-y-0 w-1/3 rounded-full"
          animate={reduceMotion ? { x: 0 } : { x: ["-100%", "300%"] }}
          transition={{
            duration: 1.4,
            repeat: Infinity,
            ease: [0.45, 0, 0.55, 1],
          }}
        />
      ) : (
        <motion.div
          className="bg-accent h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        />
      )}
    </div>
  );
}
