import { motion } from "framer-motion";
import {
  AlertTriangle,
  Download,
  FileBarChart,
  FileCode2,
  GitBranch,
  Import,
  Layers,
} from "lucide-react";
import { lazy, Suspense, useMemo } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { DataTable } from "@/components/common/data-table";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { ChartSkeleton, StatCardSkeleton } from "@/components/common/loading";
import {
  PageContainer,
  PageHeader,
  SectionHeading,
} from "@/components/common/page-header";
import { StaggerGroup, StaggerItem } from "@/components/common/page-transition";
import { RepositorySelector } from "@/components/common/repository-selector";
import { StatCard } from "@/components/common/stat-card";
import { MarkdownRenderer } from "@/components/markdown/markdown-renderer";
import { RankedFileTable } from "@/components/report/ranked-file-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useReport } from "@/hooks/use-api";
import { useActiveRepository } from "@/hooks/use-active-repository";
import { formatNumber } from "@/lib/format";
import { downloadTextFile, reportToMarkdown } from "@/lib/report-markdown";
import type { RepositoryReport, UnresolvedImport } from "@/types/api";

// Recharts is heavy; keep it out of the page's initial chunk.
const DistributionChart = lazy(
  () => import("@/components/report/distribution-chart"),
);

function toChartData(record: Record<string, number>) {
  return Object.entries(record)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));
}

function IssuesSection({ report }: { report: RepositoryReport }) {
  const { issues } = report;
  const total =
    issues.circular_dependencies.length +
    issues.high_fan_in.length +
    issues.high_fan_out.length +
    issues.unresolved_imports.length;

  if (total === 0) {
    return (
      <Card className="border-success/30 bg-success/5 p-6">
        <div className="space-y-1">
          <p className="font-editorial text-xl">Nothing needs your attention.</p>
          <p className="text-muted-foreground text-sm">
            No circular dependencies, no over-coupled modules, no unresolved
            imports.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="space-y-6 p-6">
        {issues.circular_dependencies.length > 0 ? (
          <div className="space-y-2">
            <SectionHeading
              title="Circular dependencies"
              description="Import cycles worth untangling."
            />
            <ul className="space-y-1.5">
              {issues.circular_dependencies.map((cycle) => (
                <li
                  key={cycle.join()}
                  className="text-destructive flex items-start gap-2 font-mono text-xs"
                >
                  <AlertTriangle className="mt-0.5 size-3 shrink-0" aria-hidden />
                  <span className="break-all">
                    {cycle.join(" → ")} → {cycle[0]}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {issues.high_fan_in.length > 0 ? (
          <div className="space-y-2">
            <SectionHeading
              title="Widely depended upon"
              description="Changes here ripple furthest."
            />
            <RankedFileTable rows={issues.high_fan_in} countHeader="Fan-in" />
          </div>
        ) : null}

        {issues.high_fan_out.length > 0 ? (
          <div className="space-y-2">
            <SectionHeading
              title="Depends on many"
              description="Modules that pull in a lot of the codebase."
            />
            <RankedFileTable rows={issues.high_fan_out} countHeader="Fan-out" />
          </div>
        ) : null}

        {issues.unresolved_imports.length > 0 ? (
          <div className="space-y-2">
            <SectionHeading
              title="Unresolved imports"
              description="Usually third-party packages, which is expected."
            />
            <DataTable<UnresolvedImport>
              rows={issues.unresolved_imports.slice(0, 25)}
              rowKey={(row, index) => `${row.file_path}-${index}`}
              columns={[
                {
                  id: "file",
                  header: "File",
                  cell: (row) => (
                    <span className="font-mono text-xs break-all">
                      {row.file_path}
                    </span>
                  ),
                },
                {
                  id: "target",
                  header: "Import",
                  cell: (row) => (
                    <span className="font-mono text-xs">
                      {[row.statement.module, row.statement.name]
                        .filter(Boolean)
                        .join(".")}
                    </span>
                  ),
                },
                {
                  id: "line",
                  header: "Line",
                  align: "right",
                  className: "w-16",
                  cell: (row) => row.statement.line,
                },
              ]}
            />
            {issues.unresolved_imports.length > 25 ? (
              <p className="text-muted-foreground text-xs">
                Showing 25 of {formatNumber(issues.unresolved_imports.length)}.
                Download the report for the full list.
              </p>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default function ReportPage() {
  const { active, repositories } = useActiveRepository();
  const { data, isPending, isError, error, refetch } = useReport(active?.path);

  const markdown = useMemo(
    () => (data ? reportToMarkdown(data) : ""),
    [data],
  );

  const handleDownload = () => {
    if (!data) return;
    const slug = data.general.repository_name
      .replace(/[^a-zA-Z0-9]+/g, "-")
      .toLowerCase();
    downloadTextFile(`${slug}-report.md`, markdown);
    toast.success("Report downloaded", {
      description: `${slug}-report.md saved to your downloads.`,
    });
  };

  if (repositories.length === 0) {
    return (
      <PageContainer className="space-y-8">
        <PageHeader
          eyebrow="Know your architecture"
          title="Repository Insights"
          description="Metrics, distributions, rankings, and the issues worth knowing about."
        />
        <EmptyState
          icon={FileBarChart}
          title="Insights arrive with your first scan."
          description="Scan a repository and CodeAtlas measures its shape — languages, coupling, cycles, and the files that matter most."
          action={
            <Button asChild>
              <Link to="/repositories">Scan a repository</Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer className="space-y-8">
      <PageHeader
        eyebrow="Know your architecture"
        title="Repository Insights"
        description="Metrics, distributions, rankings, and the issues worth knowing about."
        actions={
          <>
            <RepositorySelector />
            <Button onClick={handleDownload} disabled={!data} variant="outline">
              <Download className="size-4" />
              Download
            </Button>
          </>
        }
      />

      {isError ? (
        <ErrorState
          error={error}
          onRetry={() => void refetch()}
          title="Could not build the report"
        />
      ) : isPending ? (
        <div className="space-y-6">
          <StatCardSkeleton />
          <div className="grid gap-4 lg:grid-cols-2">
            <ChartSkeleton className="rounded-xl" />
            <ChartSkeleton className="rounded-xl" />
          </div>
          <Skeleton className="h-64 rounded-xl" />
        </div>
      ) : (
        <>
          <StaggerGroup className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StaggerItem>
              <StatCard
                label="Files"
                value={data.general.total_files}
                hint={`${formatNumber(data.general.parsed_files)} parsed`}
                icon={FileCode2}
              />
            </StaggerItem>
            <StaggerItem>
              <StatCard
                label="Symbols"
                value={data.general.total_symbols}
                hint="Classes and functions"
                icon={Layers}
              />
            </StaggerItem>
            <StaggerItem>
              <StatCard
                label="Imports"
                value={data.general.total_imports}
                hint={`${formatNumber(data.graph_summary.edges)} resolved internally`}
                icon={Import}
              />
            </StaggerItem>
            <StaggerItem>
              <StatCard
                label="Cycles"
                value={data.graph_summary.cycle_count}
                hint={
                  data.graph_summary.cycle_count === 0
                    ? "Clean dependency flow"
                    : "Circular dependencies"
                }
                icon={GitBranch}
              />
            </StaggerItem>
          </StaggerGroup>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="grid gap-4 lg:grid-cols-2"
          >
            <Card className="hover-lift">
              <CardContent className="space-y-4 p-6">
                <SectionHeading
                  title="Languages"
                  description="Files per detected language."
                />
                <Suspense fallback={<ChartSkeleton />}>
                  <DistributionChart data={toChartData(data.languages)} />
                </Suspense>
              </CardContent>
            </Card>

            <Card className="hover-lift">
              <CardContent className="space-y-4 p-6">
                <SectionHeading
                  title="Categories"
                  description="How files are classified."
                />
                <Suspense fallback={<ChartSkeleton />}>
                  <DistributionChart data={toChartData(data.categories)} />
                </Suspense>
              </CardContent>
            </Card>
          </motion.div>

          <Card>
            <CardContent className="space-y-4 p-6">
              <SectionHeading
                title="Coupling"
                description="The modules everything leans on, and the ones that lean hardest."
              />
              <Tabs defaultValue="imported">
                <TabsList>
                  <TabsTrigger value="imported">Most imported</TabsTrigger>
                  <TabsTrigger value="dependent">Most dependent</TabsTrigger>
                  <TabsTrigger value="structure">Structure</TabsTrigger>
                </TabsList>

                <TabsContent value="imported" className="mt-4">
                  <RankedFileTable
                    rows={data.architecture.most_imported}
                    countHeader="Fan-in"
                    emptyTitle="No imports resolved between files yet."
                  />
                </TabsContent>

                <TabsContent value="dependent" className="mt-4">
                  <RankedFileTable
                    rows={data.architecture.most_dependent}
                    countHeader="Fan-out"
                    emptyTitle="No internal dependencies found."
                  />
                </TabsContent>

                <TabsContent value="structure" className="mt-4">
                  <div className="grid gap-6 sm:grid-cols-3">
                    {[
                      {
                        label: "Entry points",
                        hint: "Imported by nothing",
                        files: data.architecture.root_modules,
                      },
                      {
                        label: "Leaf modules",
                        hint: "Import nothing internally",
                        files: data.architecture.leaf_modules,
                      },
                      {
                        label: "Isolated files",
                        hint: "No connections at all",
                        files: data.architecture.isolated_files,
                      },
                    ].map((group) => (
                      <div key={group.label} className="space-y-2">
                        <div>
                          <p className="text-sm font-medium">{group.label}</p>
                          <p className="text-muted-foreground text-xs">
                            {group.hint} · {formatNumber(group.files.length)}
                          </p>
                        </div>
                        <ul className="space-y-1">
                          {group.files.slice(0, 8).map((file) => (
                            <li
                              key={file}
                              className="text-muted-foreground truncate font-mono text-xs"
                              title={file}
                            >
                              {file}
                            </li>
                          ))}
                          {group.files.length > 8 ? (
                            <li className="text-muted-foreground text-xs">
                              +{group.files.length - 8} more
                            </li>
                          ) : null}
                        </ul>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <section className="space-y-4">
            <SectionHeading
              title="Potential issues"
              description="Flagged with configurable thresholds on the backend."
              actions={
                <Badge variant="muted">
                  Density {data.graph_summary.density.toFixed(4)}
                </Badge>
              }
            />
            <IssuesSection report={data} />
          </section>

          <section className="space-y-4">
            <SectionHeading
              title="Full report"
              description="The same document you can download as Markdown."
              actions={
                <Button variant="ghost" size="sm" onClick={handleDownload}>
                  <Download className="size-4" />
                  Download .md
                </Button>
              }
            />
            <Card>
              <CardContent className="p-6">
                <div className="scrollbar-thin max-h-[32rem] overflow-y-auto pr-2">
                  <MarkdownRenderer content={markdown} />
                </div>
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </PageContainer>
  );
}
