"""Request/response models for the repository endpoints."""

from pydantic import BaseModel, Field

from graph.visualization import GraphEdge, GraphNode


class ScanRequest(BaseModel):
    repository_path: str = Field(min_length=1)
    build_graph: bool = True
    build_report: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "repository_path": "C:/projects/my-repo",
                    "build_graph": True,
                    "build_report": True,
                }
            ]
        }
    }


class GraphStatistics(BaseModel):
    nodes: int
    edges: int
    density: float
    connected_components: int
    largest_component_size: int
    cycles: int
    unresolved_imports: int


class ReportSummary(BaseModel):
    issues: int
    circular_dependencies: int
    high_fan_in_modules: int
    high_fan_out_modules: int
    unresolved_imports: int


class ScanResponse(BaseModel):
    repository_name: str
    root_path: str
    total_files: int
    parsed_files: int
    total_symbols: int
    total_imports: int
    languages: dict[str, int]
    graph: GraphStatistics | None = None
    report: ReportSummary | None = None


class IndexRequest(BaseModel):
    repository_path: str = Field(min_length=1)
    collection_name: str | None = None
    rebuild: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "repository_path": "C:/projects/my-repo",
                    "collection_name": "codeatlas_my_repo",
                    "rebuild": False,
                }
            ]
        }
    }


class IndexResponse(BaseModel):
    repository_name: str
    collection_name: str
    embedding_model: str
    vector_dimension: int
    total_chunks: int
    indexed_chunks: int
    cached_chunks: int
    failed_chunks: int
    elapsed_seconds: float


class GraphResponse(BaseModel):
    repository_name: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    statistics: GraphStatistics
