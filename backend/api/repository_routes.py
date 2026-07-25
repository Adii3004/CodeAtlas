"""Repository endpoints. Routes call RepositoryService; no orchestration here."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_repository_service
from api.envelope import ApiResponse, error_example
from api.repository_schemas import (
    GraphResponse,
    GraphStatistics,
    IndexRequest,
    IndexResponse,
    ReportSummary,
    ScanRequest,
    ScanResponse,
)
from reports.models import RepositoryReport
from scanner.repository_scanner import ScanError
from services.repository_service import RepositoryService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Repository"])

_BAD_PATH_RESPONSE = {
    400: {
        "description": "Repository path does not exist or is not a directory",
        "content": error_example(
            "invalid_repository_path", "Repository path does not exist: ..."
        ),
    }
}


def _invalid_path(exc: ScanError) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"error": "invalid_repository_path", "message": str(exc)},
    )


def _graph_statistics(repository_graph, analysis) -> GraphStatistics:
    return GraphStatistics(
        nodes=analysis.node_count,
        edges=analysis.edge_count,
        density=round(analysis.density, 6),
        connected_components=analysis.component_count,
        largest_component_size=analysis.largest_component_size,
        cycles=analysis.cycle_count,
        unresolved_imports=len(repository_graph.unresolved_imports),
    )


@router.post(
    "/scan",
    response_model=ApiResponse[ScanResponse],
    summary="Scan and analyze a repository",
    description=(
        "Scans a local repository, builds the knowledge model, and returns "
        "a summary: file counts, symbols, imports, language distribution, "
        "and optionally dependency-graph statistics and a report summary."
    ),
    responses=_BAD_PATH_RESPONSE,
)
def scan_repository(
    request: ScanRequest,
    service: RepositoryService = Depends(get_repository_service),
) -> ApiResponse[ScanResponse]:
    """Scan a repository and return its summary."""
    try:
        knowledge = service.build_knowledge(request.repository_path)
    except ScanError as exc:
        raise _invalid_path(exc) from exc

    graph_stats: GraphStatistics | None = None
    report_summary: ReportSummary | None = None
    if request.build_graph or request.build_report:
        repository_graph = service.build_graph(knowledge)
        analysis = service.analyze(repository_graph)
        if request.build_graph:
            graph_stats = _graph_statistics(repository_graph, analysis)
        if request.build_report:
            report = service.build_report(knowledge, repository_graph, analysis)
            report_summary = ReportSummary(
                issues=report.issues.issue_count,
                circular_dependencies=len(report.issues.circular_dependencies),
                high_fan_in_modules=len(report.issues.high_fan_in),
                high_fan_out_modules=len(report.issues.high_fan_out),
                unresolved_imports=len(report.issues.unresolved_imports),
            )

    data = ScanResponse(
        repository_name=knowledge.repository_name,
        root_path=knowledge.root_path,
        total_files=knowledge.total_files,
        parsed_files=len(knowledge.parsed_files),
        total_symbols=knowledge.total_symbols,
        total_imports=knowledge.total_imports,
        languages={
            language.value: count
            for language, count in knowledge.inventory.language_counts.items()
        },
        graph=graph_stats,
        report=report_summary,
    )
    return ApiResponse(data=data, message="Repository scanned successfully.")


@router.post(
    "/index",
    response_model=ApiResponse[IndexResponse],
    summary="Index a repository into Qdrant",
    description=(
        "Scans, chunks, embeds, and indexes a repository into a Qdrant "
        "collection. Unchanged chunks are served from the embedding cache. "
        "Set `rebuild` to drop and recreate the collection."
    ),
    responses={
        **_BAD_PATH_RESPONSE,
        502: {
            "description": "The embedding provider failed for every chunk",
            "content": error_example("embedding_failed", "All chunks failed to embed."),
        },
    },
)
def index_repository(
    request: IndexRequest,
    service: RepositoryService = Depends(get_repository_service),
) -> ApiResponse[IndexResponse]:
    """Scan, chunk, embed, and index a repository into Qdrant."""
    try:
        indexed = service.index(
            request.repository_path, request.collection_name, request.rebuild
        )
    except ScanError as exc:
        raise _invalid_path(exc) from exc

    stats = indexed.statistics
    if stats.failed_chunks and not (stats.embedded_chunks or stats.cached_chunks):
        raise HTTPException(
            status_code=502,
            detail={
                "error": "embedding_failed",
                "message": (
                    f"All {stats.failed_chunks} chunks failed to embed; "
                    "check the embedding provider configuration."
                ),
            },
        )

    data = IndexResponse(
        repository_name=indexed.repository_name,
        collection_name=indexed.collection_name,
        embedding_model=indexed.embedding_model,
        vector_dimension=indexed.vector_dimension,
        total_chunks=stats.total_chunks,
        indexed_chunks=stats.embedded_chunks,
        cached_chunks=stats.cached_chunks,
        failed_chunks=stats.failed_chunks,
        elapsed_seconds=stats.elapsed_seconds,
    )
    return ApiResponse(data=data, message="Repository indexed successfully.")


@router.get(
    "/graph",
    response_model=ApiResponse[GraphResponse],
    summary="Dependency graph visualization",
    description=(
        "Builds the repository dependency graph and returns draw-ready "
        "nodes (with deterministic positions), edges, and graph statistics."
    ),
    responses=_BAD_PATH_RESPONSE,
)
def get_graph(
    repository_path: str = Query(min_length=1, description="Local repository path"),
    service: RepositoryService = Depends(get_repository_service),
) -> ApiResponse[GraphResponse]:
    """Return the dependency graph in draw-ready form."""
    try:
        knowledge = service.build_knowledge(repository_path)
    except ScanError as exc:
        raise _invalid_path(exc) from exc

    repository_graph = service.build_graph(knowledge)
    analysis = service.analyze(repository_graph)
    visualization = service.build_visualization(repository_graph)

    data = GraphResponse(
        repository_name=knowledge.repository_name,
        nodes=visualization.nodes,
        edges=visualization.edges,
        statistics=_graph_statistics(repository_graph, analysis),
    )
    return ApiResponse(data=data, message="Dependency graph built successfully.")


@router.get(
    "/report",
    response_model=ApiResponse[RepositoryReport],
    summary="Complete repository report",
    description=(
        "Builds and returns the full engineering report: general metrics, "
        "language and category distributions, dependency-graph summary, "
        "architecture highlights, and potential issues."
    ),
    responses=_BAD_PATH_RESPONSE,
)
def get_report(
    repository_path: str = Query(min_length=1, description="Local repository path"),
    service: RepositoryService = Depends(get_repository_service),
) -> ApiResponse[RepositoryReport]:
    """Return the complete repository report."""
    try:
        knowledge = service.build_knowledge(repository_path)
    except ScanError as exc:
        raise _invalid_path(exc) from exc

    repository_graph = service.build_graph(knowledge)
    analysis = service.analyze(repository_graph)
    report = service.build_report(knowledge, repository_graph, analysis)
    return ApiResponse(data=report, message="Report generated successfully.")
