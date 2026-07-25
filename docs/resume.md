# Resume & Interview Material

Reference notes for talking about CodeAtlas. Every number here is measured,
not estimated.

---

## Resume bullets

Pick 2–3 depending on the role.

**Full-stack / general**

> Built CodeAtlas, a repository intelligence tool that parses a codebase
> with Tree-sitter, builds a NetworkX dependency graph, and answers
> questions about the code using retrieval-augmented generation over Qdrant
> — with per-answer confidence scoring and file-level citations. Python
> (FastAPI) backend with 409 tests; React 19 / TypeScript frontend.

**Backend-leaning**

> Designed a 13-module Python analysis pipeline (scan → parse → knowledge
> model → dependency graph → chunk → embed → retrieve → answer → evaluate)
> behind a FastAPI service. Each stage is independently testable with typed
> Pydantic boundaries; 409 pytest tests run without network access or
> containers.

**AI/ML-leaning**

> Implemented a grounded question-answering pipeline over source code:
> deterministic content-hashed chunking, Gemini embeddings cached to avoid
> re-embedding unchanged code, vector retrieval with metadata filters,
> token-budgeted context assembly, and a heuristic evaluator that scores
> answer confidence and detects references to files absent from the
> retrieved context.

**Frontend-leaning**

> Built a React 19 + TypeScript interface with a 313-node interactive
> dependency graph (React Flow), live analysis dashboards, and a chat view
> surfacing answer confidence and citations. Route-level code splitting and
> vendor chunking keep the initial bundle at 280 kB.

---

## Interview talking points

### 30-second version

> CodeAtlas answers questions about an unfamiliar codebase. It scans a
> repository, parses it with Tree-sitter, builds a dependency graph, and
> indexes the code into a vector store. When you ask a question it retrieves
> the relevant chunks and asks Gemini to answer using only those — then
> scores how well-grounded the answer actually is. The point is that you can
> verify what it tells you.

### What makes it more than a wrapper

Three things:

1. **Structure before retrieval.** Chunks are real code units — a class, a
   function, a documentation section — extracted from a Tree-sitter parse
   tree, not fixed-size windows that split a function in half.
2. **Grounding is enforced and measured.** The prompt constrains the model
   to the supplied context, and a separate heuristic layer scores the result
   and flags file paths that don't exist in that context.
3. **Deterministic where it can be.** Scanning, parsing, graph analysis, and
   chunk IDs involve no model at all, so the same repository always produces
   the same structure.

---

## Technical challenges solved

### React Flow rendered zero edges

**Symptom:** 313 nodes rendered, 282 edges did not, and the viewport never
fit to content.

**Investigation:** Nodes carried `visibility: hidden`, which React Flow
applies until a node is measured. A minimal two-node reproduction showed the
same failure, ruling out my data. Observing an element directly proved
`ResizeObserver` callbacks were never delivered in that environment — and
React Flow measures nodes exclusively through it.

**Fix:** Declare node dimensions and handle positions on the node objects
themselves. React Flow accepts `width`, `height`, and `handles`, and
`toHandleBounds` uses them in place of measured bounds. Edges then render on
first paint, and the per-node measurement pass is skipped entirely — which
is also faster at 300+ nodes.

**Takeaway:** reading the library's own source (`getEdgePosition`,
`isNodeInitialized`) answered in minutes what guessing had not.

### Retired embedding model

`text-embedding-004` began returning 404. Listing available models showed
`gemini-embedding-001` as the successor. Because the provider is behind an
`EmbeddingProvider` interface, the change was two lines — model name and an
`output_dimensionality=768` config to keep existing vectors compatible.

### Tree-sitter ABI mismatch corrupting the heap

Chunking a whole repository crashed with an access violation and impossible
`TypeError`s. The cause was `tree-sitter` 0.26.0 bindings against a 0.25.0
grammar wheel. Pinning the bindings to 0.25.2 fixed it. It only surfaced
under chunking's heavier allocation pattern — earlier steps parsed fewer
files per process and never tripped it.

### Free-tier rate limits during indexing

Indexing hundreds of chunks exceeds Gemini's free-tier embedding quota. The
indexer already retried with exponential backoff and reported
`failed_chunks` rather than aborting; because the cache persists successful
embeddings, re-running resumes instead of restarting. The UI reports
"Indexed with gaps" with the completion percentage rather than a false
success.

### Answers citing files that weren't retrieved

The first reference extractor matched bare filenames, so an answer
mentioning `backend/graph/models.py` marked `backend/scanner/models.py` as
cited. Fixed with a boundary-aware match so a filename inside a different
path no longer counts — caught by a live run, then pinned with a regression
test.

---

## Engineering decisions

### Why Tree-sitter over Python's `ast`

The pipeline started on `ast` and moved to Tree-sitter deliberately:

- **Multi-language path.** `ast` is Python-only. Tree-sitter has grammars
  for most languages, so adding one is a new parser subclass, not a new
  architecture.
- **Error tolerance.** Tree-sitter produces a usable tree for files that
  don't fully parse; `ast` raises and yields nothing.
- **Uniform interface.** One traversal model across languages.

The cost was honest: Tree-sitter's error-tolerant grammar accepts some code
`ast` rejects (a `def` with no indented body), so a test changed behaviour
in the swap. I documented it rather than papering over it.

### Why Qdrant

- Runs locally in Docker with no managed service or account
- Payload filtering on the same query as vector search, so retrieval can be
  scoped by language, chunk type, or path
- Named vectors and explicit distance metrics
- Client version pinned to the server version after a compatibility warning

pgvector was the alternative — PostgreSQL is already in the stack. Qdrant
won on filtering ergonomics and on keeping the vector concern separate from
relational storage.

### Why Gemini

- Generous free tier, which matters for a portfolio project
- One SDK for both embeddings and generation
- Long context window suits large code contexts
- 2.5 Flash is fast enough that answers land in seconds

Both the embedding provider and the LLM provider sit behind abstract
interfaces (`EmbeddingProvider`, `AIProvider`), so swapping to OpenAI or a
local model is a class, not a refactor. That paid off when the embedding
model was retired.

### Why FastAPI

- Pydantic models serve as validation, serialisation, and OpenAPI schema at
  once
- Automatic interactive documentation
- Dependency injection made testing straightforward — swapping the embedding
  provider and Qdrant client is one override per test
- Native async available if streaming is added later

### Why React Query

Server state and client state have different problems. React Query handles
caching, deduplication, retries, and loading/error states; the small amount
of genuinely local state (theme, preferences, repository history) lives in
`useState` and `localStorage`. No Redux or Zustand — there was no global
client state worth the ceremony.

Retry logic is type-aware: a typed `ApiError` exposes `isRetryable`, so a
400 fails immediately while a network blip retries.

---

## Tradeoffs

| Decision | Gained | Gave up |
| --- | --- | --- |
| Top-level symbols only | Simple, fast, predictable extraction | Method- and nested-function-level retrieval |
| File-level dependency graph | Readable at 300+ nodes | Symbol-level call graphs |
| Heuristic evaluation | Free, deterministic, no extra latency | Semantic accuracy judgement |
| Client-side repository history | No auth, no database, works immediately | History doesn't follow the user across browsers |
| Single-shot generation | Simpler backend and error handling | No token streaming |
| Stateless backend | Trivial to reason about and test | Path re-sent on every request |

---

## Performance optimisations

**Backend**
- Embedding cache keyed by chunk ID + content hash — unchanged chunks are
  never re-embedded; a full re-index of an unchanged repository is
  cache-only and finishes in under a second
- Batched embedding requests with exponential-backoff retry
- Deterministic Qdrant point IDs so re-indexing upserts instead of
  duplicating
- Directories pruned before traversal, so `node_modules` is never entered
- The graph is built once per request and shared by analysis, visualisation,
  and report generation

**Frontend**
- Route-level lazy loading; Recharts additionally lazy-loaded inside the
  Insights page
- Vendor chunking (react / charts / flow / markdown) cut the initial bundle
  from 552 kB to 280 kB
- React Flow renders only viewport-visible elements above 200 nodes, and
  skips DOM measurement via declared node dimensions
- `useDeferredValue` on graph search so typing doesn't block re-layout
- Memoised chart and node components; `useMemo` on the node/edge transforms

---

## Testing strategy

**409 backend tests**, all offline: the Gemini client is mocked and Qdrant
runs in the client's in-memory mode, so the suite needs no containers and no
API key.

- **Unit** — each pipeline stage independently: scanner ignore rules,
  classifier categories, language detection, symbol extraction (including
  what must *not* be extracted — methods, nested functions), import forms,
  graph resolution, chunking, evaluation scoring
- **Integration** — full pipeline over temporary repositories built in the
  test itself
- **API** — FastAPI `TestClient` against every endpoint, including structured
  error shapes and a check that no response leaks a traceback
- **Regression** — each bug found during development got a test: the
  false-positive file citation, partial-failure indexing, tree storage on
  parse errors

Deliberate choice: **no mocking of internal modules**. Tests exercise real
scanning, real parsing, real graph construction against fixtures on disk.
Only the network boundary is mocked.

Frontend verification was behavioural rather than unit-based — driving the
real UI against the live backend and asserting on the DOM. That is how the
React Flow edge bug and the animated-counter bug were both found.
