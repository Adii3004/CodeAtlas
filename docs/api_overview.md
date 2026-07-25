# API Overview

Base URL (development): `http://127.0.0.1:8000` — interactive docs at
`/docs`, OpenAPI at `/openapi.json`.

Every endpoint returns the shared envelope:

```json
{ "success": true, "data": { }, "error": null, "message": "..." }
```

Errors use the same shape with `success: false`, a machine-readable `error`
code, and a human-readable `message`. Stack traces are never returned.

## System

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Application info and useful links |
| GET | `/health` | Health check for monitoring |
| GET | `/status` | Version, uptime, PostgreSQL/Qdrant reachability, AI configuration, cache size, collections |

## Repository

### `POST /scan`

Scan a repository and return its summary.

```json
{ "repository_path": "C:/projects/my-repo", "build_graph": true, "build_report": true }
```

Returns file/symbol/import counts, language distribution, graph statistics,
and a report issue summary. `400 invalid_repository_path` for bad paths.

### `POST /index`

Scan → chunk → embed → index into Qdrant.

```json
{ "repository_path": "C:/projects/my-repo", "collection_name": "codeatlas_my_repo", "rebuild": false }
```

Returns indexed/cached/failed chunk counts and elapsed time. Unchanged
chunks are served from the embedding cache. `rebuild: true` drops and
recreates the collection. `502 embedding_failed` when every chunk fails.

### `GET /graph?repository_path=...`

Dependency graph in draw-ready form: nodes (with deterministic positions,
category, language, fan-in/out, group) plus edges and graph statistics.

### `GET /report?repository_path=...`

The complete `RepositoryReport`: general metrics, language/category
distributions, graph summary, architecture highlights, and potential issues.

## AI

### `POST /ask`

Full RAG flow over an indexed collection.

```json
{
  "collection_name": "codeatlas_my_repo",
  "repository_path": "C:/projects/my-repo",
  "question": "How does authentication work?",
  "top_k": 10,
  "max_context_tokens": 4000,
  "temperature": 0.2
}
```

Returns the grounded answer plus quality signals:

```json
{
  "answer": "...",
  "confidence": 84,
  "referenced_files": ["backend/auth/service.py"],
  "retrieved_chunks": 10,
  "context_tokens": 3828,
  "warnings": [],
  "generation_time": 11.2
}
```

`400 invalid_repository_path`, `502 answer_generation_failed`, and
`422 validation_error` for malformed requests.

## Error codes

| Code | Status | Meaning |
| --- | --- | --- |
| `invalid_repository_path` | 400 | Path missing or not a directory |
| `validation_error` | 422 | Request body/params failed validation |
| `embedding_failed` | 502 | Embedding provider failed for every chunk |
| `answer_generation_failed` | 502 | Gemini failed permanently after retries |
| `internal_error` | 500 | Unexpected server error (details in logs) |
