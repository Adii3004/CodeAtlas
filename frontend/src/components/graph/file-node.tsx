import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { memo } from "react";

import { categoryColor } from "@/components/graph/category-colors";
import { cn } from "@/lib/utils";
import type { GraphNode } from "@/types/api";

/**
 * Fixed node box.
 *
 * Declaring explicit dimensions lets React Flow lay out and connect nodes
 * without waiting on DOM measurement, which keeps a 300+ node graph fast
 * and edges present from the first paint.
 */
export const NODE_SIZE = 24;

/**
 * Handles declared on the node object rather than measured from the DOM.
 *
 * React Flow normally discovers handle positions with a ResizeObserver pass
 * per node; declaring them up front skips that work entirely, which keeps a
 * several-hundred-node graph responsive and makes edges render on first
 * paint.
 */
export const NODE_HANDLES = [
  {
    id: null,
    type: "target" as const,
    position: Position.Top,
    x: NODE_SIZE / 2,
    y: 0,
    width: 1,
    height: 1,
  },
  {
    id: null,
    type: "source" as const,
    position: Position.Bottom,
    x: NODE_SIZE / 2,
    y: NODE_SIZE,
    width: 1,
    height: 1,
  },
];

/**
 * React Flow requires node data to be index-signature compatible, hence the
 * intersection with `Record<string, unknown>`.
 */
export type FileNodeData = GraphNode & {
  /** Dimmed when a search or selection is active elsewhere. */
  dimmed: boolean;
  /** Directly connected to the selected node. */
  neighbor: boolean;
  selected: boolean;
} & Record<string, unknown>;

export type FileFlowNode = Node<FileNodeData, "file">;

/** Dot size scales gently with how many files depend on this one. */
function dotSize(fanIn: number): number {
  return Math.min(10 + fanIn * 1.1, 20);
}

function FileNodeComponent({ data }: NodeProps<FileFlowNode>) {
  const color = categoryColor(data.category);
  const size = dotSize(data.fan_in);
  const emphasized = data.selected || data.neighbor;

  return (
    <div
      className={cn(
        "group relative flex items-center justify-center transition-opacity duration-300",
        data.dimmed ? "opacity-15" : "opacity-100",
      )}
      style={{ width: NODE_SIZE, height: NODE_SIZE }}
      title={data.relative_path}
    >
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={false}
        className="!size-0 !min-h-0 !min-w-0 !border-0 !bg-transparent"
      />

      <span
        className={cn(
          "block rounded-full transition-transform duration-200",
          data.selected && "ring-foreground ring-2 ring-offset-1",
        )}
        style={{
          width: size,
          height: size,
          backgroundColor: color,
          transform: data.selected ? "scale(1.35)" : undefined,
        }}
      />

      {/* Absolutely positioned so the label never affects node bounds. */}
      <span
        className={cn(
          "text-foreground/80 pointer-events-none absolute top-full left-1/2 mt-0.5 max-w-32 -translate-x-1/2 truncate",
          "text-[9px] leading-tight font-medium whitespace-nowrap transition-opacity",
          emphasized ? "opacity-100" : "opacity-0 group-hover:opacity-100",
        )}
      >
        {data.label}
      </span>

      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={false}
        className="!size-0 !min-h-0 !min-w-0 !border-0 !bg-transparent"
      />
    </div>
  );
}

export const FileNode = memo(FileNodeComponent);
