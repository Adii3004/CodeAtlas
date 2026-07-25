import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/** Map the backend's 0–100 confidence score onto a visual band. */
function band(confidence: number) {
  if (confidence >= 75) return { variant: "success" as const, label: "High" };
  if (confidence >= 45) return { variant: "warning" as const, label: "Medium" };
  return { variant: "destructive" as const, label: "Low" };
}

export interface ConfidenceBadgeProps {
  confidence: number;
  showLabel?: boolean;
}

export function ConfidenceBadge({
  confidence,
  showLabel = true,
}: ConfidenceBadgeProps) {
  const { variant, label } = band(confidence);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant={variant} className="tabular-nums">
          {showLabel ? `${label} · ` : null}
          {confidence}/100
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        Heuristic confidence from retrieval strength, context size, grounding,
        and hallucination checks.
      </TooltipContent>
    </Tooltip>
  );
}
