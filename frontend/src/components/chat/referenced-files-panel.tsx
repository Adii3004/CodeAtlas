import { FileCode2 } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { fileName } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface ReferencedFilesPanelProps {
  files: string[];
  className?: string;
}

/** Files the latest answer actually cited from the retrieved context. */
export function ReferencedFilesPanel({
  files,
  className,
}: ReferencedFilesPanelProps) {
  return (
    <aside
      aria-label="Referenced files"
      className={cn("flex h-full flex-col border-l", className)}
    >
      <div className="flex h-12 shrink-0 items-center justify-between border-b px-4">
        <h2 className="text-sm font-medium">Referenced files</h2>
        {files.length > 0 ? (
          <span className="text-muted-foreground text-xs tabular-nums">
            {files.length}
          </span>
        ) : null}
      </div>

      {files.length === 0 ? (
        <div className="p-4">
          <EmptyState
            icon={FileCode2}
            title="No references yet"
            description="Files cited by the assistant will appear here."
            className="border-0 px-2 py-10"
          />
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <ul className="space-y-0.5 p-2">
            {files.map((file) => (
              <li key={file}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="hover:bg-accent flex items-start gap-2 rounded-md px-2 py-1.5 text-left transition-colors">
                      <FileCode2
                        className="text-muted-foreground mt-0.5 size-3.5 shrink-0"
                        aria-hidden
                      />
                      <div className="min-w-0">
                        <p className="truncate text-xs font-medium">
                          {fileName(file)}
                        </p>
                        <p className="text-muted-foreground truncate font-mono text-[11px]">
                          {file}
                        </p>
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="left" className="max-w-xs">
                    <span className="font-mono break-all">{file}</span>
                  </TooltipContent>
                </Tooltip>
              </li>
            ))}
          </ul>
        </ScrollArea>
      )}
    </aside>
  );
}
