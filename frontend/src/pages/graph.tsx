import type { Edge } from "@xyflow/react";
import { Network, Search, X } from "lucide-react";
import { useCallback, useDeferredValue, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { RepositorySelector } from "@/components/common/repository-selector";
import {
  CATEGORY_LABELS,
  categoryColor,
} from "@/components/graph/category-colors";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import {
  NODE_HANDLES,
  NODE_SIZE,
  type FileFlowNode,
} from "@/components/graph/file-node";
import { NodeDetailsPanel } from "@/components/graph/node-details-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useGraph } from "@/hooks/use-api";
import { useActiveRepository } from "@/hooks/use-active-repository";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";
import { formatNumber } from "@/lib/format";
import type { FileCategory, GraphResponse } from "@/types/api";

/** Files immediately connected to `id`, in both directions. */
function neighborsOf(graph: GraphResponse | undefined, id: string | null) {
  if (!graph || !id) {
    return { dependencies: [], dependents: [], all: new Set<string>() };
  }
  const dependencies = graph.edges
    .filter((edge) => edge.source === id)
    .map((edge) => edge.target);
  const dependents = graph.edges
    .filter((edge) => edge.target === id)
    .map((edge) => edge.source);
  return {
    dependencies: dependencies.sort(),
    dependents: dependents.sort(),
    all: new Set([...dependencies, ...dependents]),
  };
}

function Legend({ categories }: { categories: FileCategory[] }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
      {categories.map((category) => (
        <li
          key={category}
          className="text-muted-foreground flex items-center gap-1.5 text-xs"
        >
          <span
            className="size-2 rounded-full"
            style={{ backgroundColor: categoryColor(category) }}
            aria-hidden
          />
          {CATEGORY_LABELS[category]}
        </li>
      ))}
    </ul>
  );
}

export default function GraphPage() {
  const { active, repositories } = useActiveRepository();
  const { data, isPending, isError, error, refetch, isFetching } = useGraph(
    active?.path,
  );

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const searchRef = useRef<HTMLInputElement>(null);

  // "/" jumps to search; Escape clears the current focus or selection.
  useKeyboardShortcut("/", (event) => {
    event.preventDefault();
    searchRef.current?.focus();
  });
  useKeyboardShortcut(
    "Escape",
    () => {
      if (search) {
        setSearch("");
        searchRef.current?.blur();
      } else {
        setSelectedId(null);
      }
    },
    { allowInFields: true },
  );

  const handleNodeClick = useCallback(
    (_: unknown, node: FileFlowNode) => setSelectedId(node.id),
    [],
  );
  const handlePaneClick = useCallback(() => setSelectedId(null), []);

  const { dependencies, dependents, all: neighborIds } = useMemo(
    () => neighborsOf(data, selectedId),
    [data, selectedId],
  );

  const matchedIds = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    if (!query || !data) return null;
    return new Set(
      data.nodes
        .filter((node) => node.relative_path.toLowerCase().includes(query))
        .map((node) => node.id),
    );
  }, [data, deferredSearch]);

  const flowNodes = useMemo<FileFlowNode[]>(() => {
    if (!data) return [];
    return data.nodes.map((node) => {
      const isSelected = node.id === selectedId;
      const isNeighbor = neighborIds.has(node.id);
      const isMatch = matchedIds?.has(node.id) ?? false;
      const dimmed = matchedIds
        ? !isMatch
        : selectedId !== null && !isSelected && !isNeighbor;

      return {
        id: node.id,
        type: "file" as const,
        position: { x: node.x, y: node.y },
        // Explicit size and handles: React Flow can place nodes and edges
        // without a DOM measurement pass.
        width: NODE_SIZE,
        height: NODE_SIZE,
        handles: NODE_HANDLES,
        data: { ...node, dimmed, neighbor: isNeighbor, selected: isSelected },
        draggable: false,
      };
    });
  }, [data, selectedId, neighborIds, matchedIds]);

  const flowEdges = useMemo<Edge[]>(() => {
    if (!data) return [];
    return data.edges.map((edge) => {
      const connected =
        selectedId !== null &&
        (edge.source === selectedId || edge.target === selectedId);
      return {
        id: `${edge.source}->${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: connected,
        style: {
          stroke: connected ? "var(--accent)" : "var(--border)",
          strokeWidth: connected ? 1.6 : 0.8,
          opacity: selectedId !== null && !connected ? 0.15 : 0.7,
        },
      };
    });
  }, [data, selectedId]);

  const categories = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.nodes.map((node) => node.category))].sort();
  }, [data]);

  const selectedNode = data?.nodes.find((node) => node.id === selectedId);
  const matchCount = matchedIds?.size ?? 0;

  return (
    <div className="flex h-full flex-col gap-5 p-5 lg:p-8">
      <PageHeader
        eyebrow="How it all connects"
        title="Dependency Map"
        description="Every file is a node; every import is an edge. Select a file to trace what it relies on and what relies on it."
        actions={<RepositorySelector />}
      />

      {repositories.length === 0 ? (
        <EmptyState
          icon={Network}
          title="Nothing to map yet."
          description="Scan a repository and its dependency map appears here — files, imports, and the shape of the architecture."
          action={
            <Button asChild>
              <Link to="/repositories">Scan a repository</Link>
            </Button>
          }
          className="flex-1"
        />
      ) : isError ? (
        <ErrorState
          error={error}
          onRetry={() => void refetch()}
          title="Could not build the map"
        />
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full sm:w-72">
              <Search
                className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-3.5 -translate-y-1/2"
                aria-hidden
              />
              <Input
                ref={searchRef}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Find a file…  /"
                aria-label="Search files"
                className="h-9 pr-8 pl-9 font-mono text-xs"
              />
              {search ? (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  aria-label="Clear search"
                  className="text-muted-foreground hover:text-foreground absolute top-1/2 right-2 -translate-y-1/2 rounded p-0.5"
                >
                  <X className="size-3.5" />
                </button>
              ) : null}
            </div>

            {search ? (
              <Badge variant={matchCount > 0 ? "muted" : "warning"}>
                {matchCount} match{matchCount === 1 ? "" : "es"}
              </Badge>
            ) : null}

            {data ? (
              <div className="text-muted-foreground ml-auto flex items-center gap-4 text-xs tabular-nums">
                <span>{formatNumber(data.statistics.nodes)} files</span>
                <span>{formatNumber(data.statistics.edges)} imports</span>
                <span>
                  {data.statistics.cycles === 0
                    ? "No cycles"
                    : `${data.statistics.cycles} cycles`}
                </span>
              </div>
            ) : null}
          </div>

          <div className="flex min-h-0 flex-1 gap-4">
            {isPending ? (
              <Skeleton className="flex-1 rounded-2xl" />
            ) : (
              <GraphCanvas
                nodes={flowNodes}
                edges={flowEdges}
                onNodeClick={handleNodeClick}
                onPaneClick={handlePaneClick}
                className="flex-1"
                overlay={
                  isFetching ? (
                    <Badge variant="muted">Refreshing…</Badge>
                  ) : data && data.nodes.length === 0 ? (
                    <EmptyState
                      icon={Network}
                      title="This repository has no files to map."
                      className="bg-card/90 border-solid backdrop-blur-sm"
                    />
                  ) : undefined
                }
              />
            )}

            {selectedNode ? (
              <div className="hidden lg:block">
                <NodeDetailsPanel
                  node={selectedNode}
                  dependencies={dependencies}
                  dependents={dependents}
                  onClose={() => setSelectedId(null)}
                  onSelectFile={setSelectedId}
                />
              </div>
            ) : null}
          </div>

          {categories.length > 0 ? <Legend categories={categories} /> : null}
        </>
      )}
    </div>
  );
}
