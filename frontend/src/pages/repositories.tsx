import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircle2,
  Database,
  FolderGit2,
  Layers,
  MessagesSquare,
  Network,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { DataTable } from "@/components/common/data-table";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import {
  PageContainer,
  PageHeader,
  SectionHeading,
} from "@/components/common/page-header";
import { RepositoryPathField } from "@/components/common/repository-path-field";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useIndexRepository, useScanRepository } from "@/hooks/use-api";
import { useRepositories, type TrackedRepository } from "@/hooks/use-repositories";
import { formatDuration, formatNumber } from "@/lib/format";
import type { IndexResponse, ScanResponse } from "@/types/api";

function ResultMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-muted-foreground text-xs tracking-wide uppercase">
        {label}
      </p>
      <p className="text-lg font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function ScanResultCard({ result }: { result: ScanResponse }) {
  const topLanguages = Object.entries(result.languages)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      <Card className="border-success/30 bg-success/5 p-6">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="text-success mt-0.5 size-5 shrink-0" />
          <div className="min-w-0 flex-1 space-y-5">
            <div className="space-y-1">
              <p className="font-editorial text-xl">Repository Ready</p>
              <p className="text-muted-foreground text-sm">
                {result.repository_name} was mapped successfully.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
              <ResultMetric
                label="Files"
                value={formatNumber(result.total_files)}
              />
              <ResultMetric
                label="Parsed"
                value={formatNumber(result.parsed_files)}
              />
              <ResultMetric
                label="Symbols"
                value={formatNumber(result.total_symbols)}
              />
              <ResultMetric
                label="Imports"
                value={formatNumber(result.total_imports)}
              />
            </div>

            {topLanguages.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {topLanguages.map(([language, count]) => (
                  <Badge key={language} variant="muted">
                    {language} · {count}
                  </Badge>
                ))}
              </div>
            ) : null}

            {result.graph ? (
              <div className="text-muted-foreground flex flex-wrap gap-x-5 gap-y-1 text-xs">
                <span>{formatNumber(result.graph.nodes)} nodes</span>
                <span>{formatNumber(result.graph.edges)} edges</span>
                <span>
                  {result.graph.cycles === 0
                    ? "No circular dependencies"
                    : `${result.graph.cycles} cycles`}
                </span>
                <span>
                  {formatNumber(result.graph.unresolved_imports)} unresolved
                  imports
                </span>
              </div>
            ) : null}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function IndexResultCard({ result }: { result: IndexResponse }) {
  const total = Math.max(result.total_chunks, 1);
  const done = result.indexed_chunks + result.cached_chunks;
  const percent = Math.round((done / total) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      <Card className="p-6">
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <p className="font-editorial text-xl">
                {result.failed_chunks === 0
                  ? "Indexed and searchable"
                  : "Indexed with gaps"}
              </p>
              <p className="text-muted-foreground text-sm">
                <span className="font-mono">{result.collection_name}</span> ·{" "}
                {result.embedding_model} · {result.vector_dimension}d
              </p>
            </div>
            <Badge variant={result.failed_chunks === 0 ? "success" : "warning"}>
              {percent}% complete
            </Badge>
          </div>

          <Progress value={percent} label="Chunks embedded" />

          <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
            <ResultMetric
              label="Chunks"
              value={formatNumber(result.total_chunks)}
            />
            <ResultMetric
              label="Embedded"
              value={formatNumber(result.indexed_chunks)}
            />
            <ResultMetric
              label="From cache"
              value={formatNumber(result.cached_chunks)}
            />
            <ResultMetric
              label="Failed"
              value={formatNumber(result.failed_chunks)}
            />
          </div>

          <p className="text-muted-foreground text-xs">
            Finished in {formatDuration(result.elapsed_seconds)}.
            {result.failed_chunks > 0
              ? " Re-run indexing to retry the remaining chunks — completed work is cached."
              : null}
          </p>

          {result.failed_chunks === 0 ? (
            <Button asChild size="sm">
              <Link to="/chat">
                <MessagesSquare className="size-4" />
                Ask a question
              </Link>
            </Button>
          ) : null}
        </div>
      </Card>
    </motion.div>
  );
}

export default function RepositoriesPage() {
  const { repositories, upsert, remove } = useRepositories();
  const [path, setPath] = useState("");
  const [rebuild, setRebuild] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<TrackedRepository | null>(
    null,
  );

  const scan = useScanRepository();
  const index = useIndexRepository();

  const trimmedPath = path.trim();
  const busy = scan.isPending || index.isPending;

  const handleScan = () => {
    if (!trimmedPath) return;
    scan.mutate(
      { repository_path: trimmedPath, build_graph: true, build_report: true },
      {
        onSuccess: (result) => {
          upsert(trimmedPath, {
            name: result.repository_name,
            totalFiles: result.total_files,
            lastScannedAt: new Date().toISOString(),
          });
          toast.success("Repository Ready", {
            description: `${result.repository_name} · ${formatNumber(result.total_files)} files mapped.`,
          });
        },
        onError: (error) =>
          toast.error("Scan failed", { description: error.message }),
      },
    );
  };

  const handleIndex = () => {
    if (!trimmedPath) return;
    index.mutate(
      { repository_path: trimmedPath, rebuild },
      {
        onSuccess: (result) => {
          upsert(trimmedPath, {
            name: result.repository_name,
            collectionName: result.collection_name,
            totalChunks: result.total_chunks,
            lastIndexedAt: new Date().toISOString(),
          });
          if (result.failed_chunks > 0) {
            toast.warning("Indexed with gaps", {
              description: `${formatNumber(result.failed_chunks)} chunks failed. Run again to retry.`,
            });
          } else {
            toast.success("Ready for questions", {
              description: `${formatNumber(result.total_chunks)} chunks in ${result.collection_name}.`,
            });
          }
        },
        onError: (error) =>
          toast.error("Indexing failed", { description: error.message }),
      },
    );
  };

  return (
    <PageContainer className="space-y-8">
      <PageHeader
        eyebrow="Map a codebase"
        title="Repositories"
        description="Scan reads the structure and dependencies. Indexing embeds the code so you can ask questions about it."
      />

      <Card className="p-6">
        <div className="space-y-5">
          <RepositoryPathField
            value={path}
            onChange={setPath}
            disabled={busy}
            hint="Absolute path on the machine running the backend — for example C:/projects/my-repo."
          />

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={handleScan} disabled={!trimmedPath || busy}>
              <Search className="size-4" />
              {scan.isPending ? "Scanning…" : "Scan repository"}
            </Button>
            <Button
              variant="outline"
              onClick={handleIndex}
              disabled={!trimmedPath || busy}
            >
              <Layers className="size-4" />
              {index.isPending ? "Indexing…" : "Index for questions"}
            </Button>

            <div className="ml-auto flex items-center gap-2">
              <Switch
                id="rebuild"
                checked={rebuild}
                onCheckedChange={setRebuild}
                disabled={busy}
              />
              <Label htmlFor="rebuild" className="text-muted-foreground text-xs">
                Rebuild collection
              </Label>
            </div>
          </div>

          <AnimatePresence>
            {busy ? (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 overflow-hidden"
              >
                <Progress
                  label={scan.isPending ? "Scanning repository" : "Indexing chunks"}
                />
                <p className="text-muted-foreground flex items-center gap-1.5 text-xs">
                  <Sparkles className="size-3 shrink-0" aria-hidden />
                  {scan.isPending
                    ? "Walking the tree, parsing files, and building the dependency graph…"
                    : "Chunking and embedding. Cached chunks are reused, so repeat runs are fast."}
                </p>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </Card>

      {scan.isError ? (
        <ErrorState
          error={scan.error}
          onRetry={handleScan}
          title="Scan failed"
        />
      ) : null}
      {index.isError ? (
        <ErrorState
          error={index.error}
          onRetry={handleIndex}
          title="Indexing failed"
        />
      ) : null}

      <AnimatePresence mode="popLayout">
        {scan.data ? <ScanResultCard result={scan.data} /> : null}
        {index.data ? <IndexResultCard result={index.data} /> : null}
      </AnimatePresence>

      <section className="space-y-4">
        <SectionHeading
          title="History"
          description="Repositories you have mapped from this browser."
        />

        {repositories.length === 0 ? (
          <EmptyState
            icon={FolderGit2}
            title="Every great repository starts with a scan."
            description="Paste a path above and CodeAtlas will map it — no configuration, no waiting on a build."
          />
        ) : (
          <DataTable<TrackedRepository>
            rows={repositories}
            rowKey={(row) => row.id}
            columns={[
              {
                id: "name",
                header: "Repository",
                cell: (row) => (
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{row.name}</p>
                    <p className="text-muted-foreground truncate font-mono text-xs">
                      {row.path}
                    </p>
                  </div>
                ),
              },
              {
                id: "collection",
                header: "Collection",
                cell: (row) =>
                  row.collectionName ? (
                    <Badge variant="muted" className="font-mono">
                      <Database className="size-3" />
                      {row.collectionName}
                    </Badge>
                  ) : (
                    <span className="text-muted-foreground text-xs">
                      Not indexed
                    </span>
                  ),
              },
              {
                id: "files",
                header: "Files",
                align: "right",
                cell: (row) =>
                  row.totalFiles === null ? "—" : formatNumber(row.totalFiles),
              },
              {
                id: "chunks",
                header: "Chunks",
                align: "right",
                cell: (row) =>
                  row.totalChunks === null
                    ? "—"
                    : formatNumber(row.totalChunks),
              },
              {
                id: "actions",
                header: "",
                align: "right",
                className: "w-32",
                cell: (row) => (
                  <div className="flex items-center justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setPath(row.path)}
                      aria-label={`Use ${row.name}`}
                    >
                      <Search className="size-3.5" />
                    </Button>
                    <Button asChild variant="ghost" size="icon-sm">
                      <Link to="/graph" aria-label={`Map ${row.name}`}>
                        <Network className="size-3.5" />
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setPendingDelete(row)}
                      aria-label={`Forget ${row.name}`}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                  </div>
                ),
              },
            ]}
          />
        )}
      </section>

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title={`Forget ${pendingDelete?.name ?? "repository"}?`}
        description="This only removes it from this browser's history. Indexed vectors stay in Qdrant."
        confirmLabel="Forget"
        destructive
        onConfirm={() => {
          if (pendingDelete) {
            remove(pendingDelete.id);
            toast.success(`${pendingDelete.name} removed from history.`);
          }
          setPendingDelete(null);
        }}
      />
    </PageContainer>
  );
}
