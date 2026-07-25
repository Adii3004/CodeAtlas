/**
 * Backend API contract.
 *
 * Mirrors the CodeAtlas FastAPI models. Every endpoint returns the shared
 * `ApiResponse` envelope: { success, data, error, message }.
 */

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  message: string;
}

/** Machine-readable error codes returned by the backend. */
export type ApiErrorCode =
  | "invalid_repository_path"
  | "validation_error"
  | "embedding_failed"
  | "answer_generation_failed"
  | "internal_error"
  | "http_error"
  | "network_error"
  | "timeout"
  | "unknown_error";

/* -------------------------------------------------------------------------- */
/* System                                                                      */
/* -------------------------------------------------------------------------- */

export interface RootResponse {
  message: string;
  app_name: string;
  version: string;
  docs_url: string;
  health_url: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
}

export interface ApplicationStatus {
  version: string;
  api_version: string;
  uptime_seconds: number;
}

export interface InfrastructureStatus {
  postgres_reachable: boolean;
  qdrant_reachable: boolean;
}

export interface AIStatus {
  gemini_configured: boolean;
  embedding_model: string;
  llm_model: string;
}

export interface StatisticsStatus {
  embedding_cache_entries: number;
  available_collections: string[];
}

export interface StatusResponse {
  application: ApplicationStatus;
  infrastructure: InfrastructureStatus;
  ai: AIStatus;
  statistics: StatisticsStatus;
}

/* -------------------------------------------------------------------------- */
/* Repository — scan                                                           */
/* -------------------------------------------------------------------------- */

export interface ScanRequest {
  repository_path: string;
  build_graph?: boolean;
  build_report?: boolean;
}

export interface GraphStatistics {
  nodes: number;
  edges: number;
  density: number;
  connected_components: number;
  largest_component_size: number;
  cycles: number;
  unresolved_imports: number;
}

export interface ReportSummary {
  issues: number;
  circular_dependencies: number;
  high_fan_in_modules: number;
  high_fan_out_modules: number;
  unresolved_imports: number;
}

export interface ScanResponse {
  repository_name: string;
  root_path: string;
  total_files: number;
  parsed_files: number;
  total_symbols: number;
  total_imports: number;
  languages: Record<string, number>;
  graph: GraphStatistics | null;
  report: ReportSummary | null;
}

/* -------------------------------------------------------------------------- */
/* Repository — index                                                          */
/* -------------------------------------------------------------------------- */

export interface IndexRequest {
  repository_path: string;
  collection_name?: string | null;
  rebuild?: boolean;
}

export interface IndexResponse {
  repository_name: string;
  collection_name: string;
  embedding_model: string;
  vector_dimension: number;
  total_chunks: number;
  indexed_chunks: number;
  cached_chunks: number;
  failed_chunks: number;
  elapsed_seconds: number;
}

/* -------------------------------------------------------------------------- */
/* Repository — graph                                                          */
/* -------------------------------------------------------------------------- */

export type FileCategory =
  | "source_code"
  | "configuration"
  | "documentation"
  | "data"
  | "test"
  | "script"
  | "image"
  | "archive"
  | "binary"
  | "unknown";

export type ProgrammingLanguage =
  | "python"
  | "javascript"
  | "typescript"
  | "java"
  | "cpp"
  | "c"
  | "csharp"
  | "go"
  | "rust"
  | "php"
  | "ruby"
  | "swift"
  | "kotlin"
  | "html"
  | "css"
  | "json"
  | "yaml"
  | "xml"
  | "markdown"
  | "shell"
  | "docker"
  | "text"
  | "unknown";

export interface GraphNode {
  id: string;
  label: string;
  relative_path: string;
  category: FileCategory;
  language: ProgrammingLanguage;
  symbol_count: number;
  import_count: number;
  fan_in: number;
  fan_out: number;
  group: string;
  x: number;
  y: number;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphResponse {
  repository_name: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  statistics: GraphStatistics;
}

/* -------------------------------------------------------------------------- */
/* Repository — report                                                         */
/* -------------------------------------------------------------------------- */

export interface RankedFile {
  path: string;
  count: number;
}

export interface GeneralSection {
  repository_name: string;
  root_path: string;
  generated_at: string;
  total_files: number;
  parsed_files: number;
  total_symbols: number;
  total_imports: number;
}

export interface GraphSummarySection {
  nodes: number;
  edges: number;
  density: number;
  connected_components: number;
  largest_component_size: number;
  cycle_count: number;
}

export interface ArchitectureSection {
  most_imported: RankedFile[];
  most_dependent: RankedFile[];
  root_modules: string[];
  leaf_modules: string[];
  isolated_files: string[];
}

export interface ImportStatement {
  module: string | null;
  name: string | null;
  alias: string | null;
  relative_level: number;
  line: number;
  file_path: string;
}

export interface UnresolvedImport {
  file_path: string;
  statement: ImportStatement;
}

export interface IssuesSection {
  circular_dependencies: string[][];
  high_fan_in: RankedFile[];
  high_fan_out: RankedFile[];
  unresolved_imports: UnresolvedImport[];
}

export interface RepositoryReport {
  general: GeneralSection;
  languages: Record<string, number>;
  categories: Record<string, number>;
  graph_summary: GraphSummarySection;
  architecture: ArchitectureSection;
  issues: IssuesSection;
}

/* -------------------------------------------------------------------------- */
/* AI — ask                                                                    */
/* -------------------------------------------------------------------------- */

export interface AskRequest {
  collection_name: string;
  repository_path: string;
  question: string;
  top_k?: number;
  max_context_tokens?: number;
  temperature?: number;
}

export interface AskResponse {
  answer: string;
  confidence: number;
  referenced_files: string[];
  retrieved_chunks: number;
  context_tokens: number;
  warnings: string[];
  generation_time: number;
}
