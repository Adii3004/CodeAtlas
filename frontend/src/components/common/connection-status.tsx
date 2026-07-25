import { Link } from "react-router-dom";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useHealth } from "@/hooks/use-api";
import { getApiBaseUrl } from "@/lib/env";
import { cn } from "@/lib/utils";

/** Small backend reachability indicator shown in the header. */
export function ConnectionStatus() {
  const { data, isPending, isError } = useHealth({ refetchInterval: 30_000 });

  const state = isPending
    ? { label: "Connecting", dot: "bg-muted-foreground", pulse: true }
    : isError
      ? { label: "Backend offline", dot: "bg-destructive", pulse: false }
      : { label: `Connected · v${data?.version ?? "?"}`, dot: "bg-success", pulse: false };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          to="/settings"
          className="hover:bg-accent flex items-center gap-2 rounded-md px-2 py-1.5 text-xs transition-colors"
        >
          <span
            className={cn(
              "size-2 rounded-full",
              state.dot,
              state.pulse && "animate-pulse",
            )}
            aria-hidden
          />
          <span className="text-muted-foreground hidden sm:inline">
            {state.label}
          </span>
          <span className="sr-only">API status: {state.label}</span>
        </Link>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{state.label}</p>
        <p className="text-muted-foreground font-mono">{getApiBaseUrl()}</p>
      </TooltipContent>
    </Tooltip>
  );
}
