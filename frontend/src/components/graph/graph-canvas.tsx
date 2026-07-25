import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type NodeMouseHandler,
} from "@xyflow/react";
import { motion } from "framer-motion";
import { useEffect, type ReactNode } from "react";

import { categoryColor } from "@/components/graph/category-colors";
import { FileNode, type FileFlowNode } from "@/components/graph/file-node";
import { cn } from "@/lib/utils";
import type { FileCategory } from "@/types/api";

import "@xyflow/react/dist/style.css";

const NODE_TYPES = { file: FileNode };

/**
 * Frames the graph whenever the node set changes.
 *
 * Nodes declare their own dimensions instead of being measured, so React
 * Flow's measurement-driven `fitView` never fires. The bounds are computed
 * from the layout positions and applied with `fitBounds`, which only needs
 * the container size.
 */
function FitViewOnData({ nodes }: { nodes: FileFlowNode[] }) {
  const { fitView } = useReactFlow();
  // Re-fit when the graph itself changes, not on every highlight update.
  const signature = `${nodes.length}:${nodes[0]?.id ?? ""}`;

  useEffect(() => {
    if (nodes.length === 0) return;
    const frame = requestAnimationFrame(() => {
      void fitView({ padding: 0.12, duration: 400 });
    });
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, fitView]);

  return null;
}

export interface GraphCanvasProps {
  nodes: FileFlowNode[];
  edges: Edge[];
  onNodeClick?: NodeMouseHandler<FileFlowNode>;
  onPaneClick?: () => void;
  /** Rendered above the canvas — used for empty and loading states. */
  overlay?: ReactNode;
  showMiniMap?: boolean;
  className?: string;
}

/**
 * React Flow canvas for the dependency map.
 *
 * Node positions come from the backend layout, so the canvas is
 * presentation-only: no simulation runs in the browser.
 */
export function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
  onPaneClick,
  overlay,
  showMiniMap = true,
  className,
}: GraphCanvasProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "bg-surface relative h-full w-full overflow-hidden rounded-2xl border",
        className,
      )}
    >
      <ReactFlowProvider>
        <ReactFlow<FileFlowNode>
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.05}
          maxZoom={4}
          nodesDraggable={false}
          nodesConnectable={false}
          edgesFocusable={false}
          elementsSelectable
          // Large graphs only paint what is inside the viewport.
          onlyRenderVisibleElements={nodes.length > 200}
          proOptions={{ hideAttribution: true }}
          aria-label="Repository dependency graph"
        >
          <FitViewOnData nodes={nodes} />
          <Background
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1}
            color="var(--border)"
          />
          <Controls
            showInteractive={false}
            className={cn(
              "overflow-hidden rounded-lg border shadow-soft",
              "[&_button]:!border-border [&_button]:!bg-card [&_button]:!fill-foreground",
              "[&_button:hover]:!bg-accent-soft",
            )}
          />
          {showMiniMap ? (
            <MiniMap
              pannable
              zoomable
              nodeColor={(node) =>
                categoryColor(node.data.category as FileCategory)
              }
              maskColor="var(--background)"
              className="!bg-card overflow-hidden rounded-lg border shadow-soft"
            />
          ) : null}
        </ReactFlow>
      </ReactFlowProvider>

      {overlay ? (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-6">
          <div className="pointer-events-auto">{overlay}</div>
        </div>
      ) : null}
    </motion.div>
  );
}
