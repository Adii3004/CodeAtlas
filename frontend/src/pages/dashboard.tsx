import {
  ArrowRight,
  Boxes,
  Clock,
  Database,
  FolderGit2,
  MessagesSquare,
  Network,
  Sparkles,
  Timer,
} from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { StatCardSkeleton } from "@/components/common/loading";
import {
  PageContainer,
  PageHeader,
  SectionHeading,
} from "@/components/common/page-header";
import { StaggerGroup, StaggerItem } from "@/components/common/page-transition";
import { StatCard } from "@/components/common/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useStatus } from "@/hooks/use-api";
import { useRepositories } from "@/hooks/use-repositories";
import { formatDuration, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { StatusResponse } from "@/types/api";

function ServiceRow({
  label,
  detail,
  ok,
}: {
  label: string;
  detail: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3.5">
      <div className="flex min-w-0 items-center gap-3">
        <span
          className={cn(
            "size-2 shrink-0 rounded-full",
            ok ? "bg-success" : "bg-destructive",
          )}
          aria-hidden
        />
        <div className="min-w-0">
          <p className="text-sm font-medium">{label}</p>
          <p className="text-muted-foreground truncate text-xs">{detail}</p>
        </div>
      </div>
      <Badge variant={ok ? "success" : "destructive"}>
        {ok ? "Ready" : "Unavailable"}
      </Badge>
    </div>
  );
}

function SystemHealth({ status }: { status: StatusResponse }) {
  return (
    <Card className="hover-lift h-full p-6">
      <SectionHeading
        title="System health"
        description="Services the pipeline depends on."
      />
      <div className="divide-border/70 mt-2 divide-y">
        <ServiceRow
          label="Gemini"
          detail={
            status.ai.gemini_configured
              ? `${status.ai.llm_model} · ${status.ai.embedding_model}`
              : "No API key configured"
          }
          ok={status.ai.gemini_configured}
        />
        <ServiceRow
          label="Qdrant"
          detail={`${status.statistics.available_collections.length} collection${
            status.statistics.available_collections.length === 1 ? "" : "s"
          } available`}
          ok={status.infrastructure.qdrant_reachable}
        />
        <ServiceRow
          label="PostgreSQL"
          detail="Relational storage"
          ok={status.infrastructure.postgres_reachable}
        />
      </div>
    </Card>
  );
}

function CollectionsCard({ status }: { status: StatusResponse }) {
  const collections = status.statistics.available_collections;

  return (
    <Card className="hover-lift h-full p-6">
      <SectionHeading
        title="Vector collections"
        description="Indexed repositories available for questions."
      />
      <div className="mt-4">
        {collections.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Nothing indexed yet — index a repository to start asking questions.
          </p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {collections.map((collection) => (
              <li key={collection}>
                <Badge variant="muted" className="font-mono">
                  <Database className="size-3" />
                  {collection}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const { data, isPending, isError, error, refetch, isFetching } = useStatus({
    refetchInterval: 60_000,
  });
  const { repositories } = useRepositories();
  const indexed = repositories.filter((repository) => repository.collectionName);

  return (
    <PageContainer className="space-y-8">
      <PageHeader
        eyebrow="Repository Intelligence"
        title="Repository Overview"
        description="Everything CodeAtlas knows right now — service health, indexed collections, and the repositories you have mapped."
        actions={
          <Button asChild>
            <Link to="/repositories">
              Scan a repository
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        }
      />

      {isError ? (
        <ErrorState
          error={error}
          onRetry={() => void refetch()}
          title="Cannot reach the backend"
        />
      ) : isPending ? (
        <StatCardSkeleton />
      ) : (
        <StaggerGroup className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StaggerItem>
            <StatCard
              label="Collections"
              value={data.statistics.available_collections.length}
              hint="Indexed and searchable"
              icon={Database}
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Cached embeddings"
              value={data.statistics.embedding_cache_entries}
              hint="Chunks that never need re-embedding"
              icon={Boxes}
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Repositories"
              value={repositories.length}
              hint={`${indexed.length} ready for questions`}
              icon={FolderGit2}
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Uptime"
              value={formatDuration(data.application.uptime_seconds)}
              hint={`API ${data.application.api_version} · v${data.application.version}`}
              icon={Timer}
            />
          </StaggerItem>
        </StaggerGroup>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {isPending ? (
          <>
            <Skeleton className="h-64 rounded-xl" />
            <Skeleton className="h-64 rounded-xl" />
          </>
        ) : isError ? null : (
          <>
            <SystemHealth status={data} />
            <CollectionsCard status={data} />
          </>
        )}
      </div>

      <section className="space-y-4">
        <SectionHeading
          title="Your repositories"
          description="Mapped from this browser. Scanning is local to the backend machine."
          actions={
            repositories.length > 0 ? (
              <Button asChild variant="ghost" size="sm">
                <Link to="/repositories">
                  View all
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            ) : null
          }
        />

        {repositories.length === 0 ? (
          <EmptyState
            icon={FolderGit2}
            title="Every great repository starts with a scan."
            description="Point CodeAtlas at a folder on the backend machine and it will map the structure, dependencies, and architecture in seconds."
            action={
              <Button asChild>
                <Link to="/repositories">
                  Scan your first repository
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            }
          />
        ) : (
          <StaggerGroup className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {repositories.slice(0, 6).map((repository) => (
              <StaggerItem key={repository.id}>
                <Card className="hover-lift h-full">
                  <CardContent className="space-y-4 p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 space-y-1">
                        <p className="truncate font-medium">{repository.name}</p>
                        <p className="text-muted-foreground truncate font-mono text-xs">
                          {repository.path}
                        </p>
                      </div>
                      {repository.collectionName ? (
                        <Badge variant="success">Ready</Badge>
                      ) : (
                        <Badge variant="outline">Scanned</Badge>
                      )}
                    </div>

                    <div className="text-muted-foreground flex items-center gap-4 text-xs">
                      {repository.totalFiles !== null ? (
                        <span className="tabular-nums">
                          {formatNumber(repository.totalFiles)} files
                        </span>
                      ) : null}
                      {repository.totalChunks !== null ? (
                        <span className="tabular-nums">
                          {formatNumber(repository.totalChunks)} chunks
                        </span>
                      ) : null}
                      {repository.lastScannedAt ? (
                        <span className="flex items-center gap-1">
                          <Clock className="size-3" aria-hidden />
                          {new Date(
                            repository.lastScannedAt,
                          ).toLocaleDateString()}
                        </span>
                      ) : null}
                    </div>

                    <div className="flex gap-2">
                      <Button asChild variant="outline" size="sm">
                        <Link to="/chat">
                          <MessagesSquare className="size-3.5" />
                          Ask
                        </Link>
                      </Button>
                      <Button asChild variant="ghost" size="sm">
                        <Link to="/graph">
                          <Network className="size-3.5" />
                          Map
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </StaggerItem>
            ))}
          </StaggerGroup>
        )}
      </section>

      {!isPending && !isError ? (
        <p className="text-muted-foreground flex items-center gap-1.5 text-xs">
          <Sparkles className="size-3" aria-hidden />
          {isFetching ? "Refreshing status…" : "Status refreshes every minute."}
        </p>
      ) : null}
    </PageContainer>
  );
}
