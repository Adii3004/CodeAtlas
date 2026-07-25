import { ArrowDownRight, ArrowUpRight, FileCode2, X } from "lucide-react";

import {
  CATEGORY_LABELS,
  categoryColor,
} from "@/components/graph/category-colors";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatNumber, humanize } from "@/lib/format";
import type { GraphNode } from "@/types/api";

export interface NodeDetailsPanelProps {
  node: GraphNode;
  dependencies: string[];
  dependents: string[];
  onClose: () => void;
  onSelectFile: (id: string) => void;
}

function FileList({
  title,
  icon: Icon,
  files,
  onSelect,
}: {
  title: string;
  icon: typeof ArrowUpRight;
  files: string[];
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <p className="text-muted-foreground flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase">
        <Icon className="size-3" aria-hidden />
        {title} ({files.length})
      </p>
      {files.length === 0 ? (
        <p className="text-muted-foreground text-xs">None</p>
      ) : (
        <ul className="space-y-0.5">
          {files.map((file) => (
            <li key={file}>
              <button
                type="button"
                onClick={() => onSelect(file)}
                className="hover:bg-accent-soft w-full truncate rounded px-1.5 py-1 text-left font-mono text-[11px] transition-colors"
                title={file}
              >
                {file}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Slide-in inspector for the selected file. */
export function NodeDetailsPanel({
  node,
  dependencies,
  dependents,
  onClose,
  onSelectFile,
}: NodeDetailsPanelProps) {
  return (
    <div className="bg-card/95 flex h-full w-72 flex-col rounded-xl border shadow-lift backdrop-blur-sm">
      <div className="flex items-start justify-between gap-2 border-b p-4">
        <div className="flex min-w-0 items-start gap-2.5">
          <span
            className="mt-1 size-2.5 shrink-0 rounded-full"
            style={{ backgroundColor: categoryColor(node.category) }}
            aria-hidden
          />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{node.label}</p>
            <p className="text-muted-foreground truncate font-mono text-[11px]">
              {node.relative_path}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onClose}
          aria-label="Close file details"
          className="size-7 shrink-0"
        >
          <X className="size-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-5 p-4">
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="muted">{CATEGORY_LABELS[node.category]}</Badge>
            <Badge variant="outline">{humanize(node.language)}</Badge>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Symbols", value: node.symbol_count },
              { label: "Imports", value: node.import_count },
              { label: "Imported by", value: node.fan_in },
              { label: "Depends on", value: node.fan_out },
            ].map((metric) => (
              <div key={metric.label} className="space-y-0.5">
                <p className="text-muted-foreground text-[11px] tracking-wide uppercase">
                  {metric.label}
                </p>
                <p className="text-base font-semibold tabular-nums">
                  {formatNumber(metric.value)}
                </p>
              </div>
            ))}
          </div>

          <div className="space-y-0.5">
            <p className="text-muted-foreground text-[11px] tracking-wide uppercase">
              Folder
            </p>
            <p className="truncate font-mono text-xs">{node.group}</p>
          </div>

          <FileList
            title="Depends on"
            icon={ArrowUpRight}
            files={dependencies}
            onSelect={onSelectFile}
          />
          <FileList
            title="Imported by"
            icon={ArrowDownRight}
            files={dependents}
            onSelect={onSelectFile}
          />
        </div>
      </ScrollArea>

      <div className="text-muted-foreground flex items-center gap-1.5 border-t p-3 text-[11px]">
        <FileCode2 className="size-3" aria-hidden />
        Click a connected file to inspect it.
      </div>
    </div>
  );
}
