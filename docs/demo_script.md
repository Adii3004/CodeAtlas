# Demo Script

A 2–3 minute walkthrough. Timings assume a repository that has already been
scanned once, so embeddings come from cache and nothing stalls on camera.

**Before recording**

- `docker compose up -d` — confirm both containers are healthy
- Backend and frontend running; `/status` shows everything reachable
- Index the demo repository once beforehand so the cache is warm
- Dark theme, browser at 1440×900, zoom 100%, bookmarks bar hidden
- Clear repository history if you want to show the first-run empty state

---

## 0:00 — Opening (15s)

> "This is CodeAtlas. Point it at a repository and it maps the codebase,
> then answers questions about the code using only what it actually read."

Land on **Repository Overview**. Let the counters animate.

Point out: Gemini, Qdrant and PostgreSQL health, the embedding cache size,
and the collections that already exist.

---

## 0:15 — Scanning (30s)

Go to **Repositories**. Paste an absolute path. Click **Scan repository**.

> "Scanning walks the tree, parses every Python file with Tree-sitter, and
> builds a dependency graph. No AI involved — this part is deterministic."

When the result card appears:

> "313 files, 336 top-level symbols, 730 imports, and no circular
> dependencies."

Call out the language badges and the graph statistics line.

---

## 0:45 — Indexing (25s)

Click **Index for questions**.

> "Indexing chunks the code — one chunk per class, per function, per file
> summary — embeds each chunk with Gemini, and stores it in Qdrant. Chunk
> IDs are content-hashed, so re-indexing only pays for what changed."

Show the completion bar and the cached-vs-embedded split.

> "Most of these came from cache, which is why it finished in seconds."

---

## 1:10 — Dependency map (35s)

Go to **Dependency Map**.

> "Every file is a node, every import an edge. Colour is the file category,
> size is how many files depend on it."

Press `/` and type a module name — nodes filter live.

Clear with Escape, then click a hub file such as `scanner/models.py`.

> "Selecting a file highlights its neighbours and dims everything else. The
> inspector lists what it depends on and what depends on it — and those are
> clickable, so you can walk the graph."

---

## 1:45 — Insights (25s)

Go to **Insights**.

> "The same analysis as a report: language and category distributions,
> which modules everything leans on, which modules pull in the most."

Switch to the **Most dependent** tab, scroll to potential issues.

> "Cycles, over-coupled modules, and unresolved imports — the unresolved
> ones here are third-party packages, which is expected."

Click **Download** to show the Markdown export.

---

## 2:10 — Ask CodeAtlas (40s)

Go to **Ask CodeAtlas**. Pick a suggested question, or ask something
specific:

> "How does the repository scanner decide which files to ignore?"

While it generates:

> "It embeds the question, pulls the most similar chunks out of Qdrant,
> assembles them under a token budget, and asks Gemini to answer using only
> that context."

When the answer lands, point at the metadata row:

> "Confidence 84 out of 100 — that's a heuristic score from retrieval
> strength, context size, how much of the answer is grounded, and a check
> for file paths that don't exist in the context. It cited these five files,
> and I can open any of them to verify."

Optionally ask something the repository can't answer:

> "Ask it about something that isn't in the code and it says so, rather
> than inventing an answer."

---

## 2:50 — Close (10s)

> "Python and FastAPI on the backend, Tree-sitter for parsing, Qdrant for
> vectors, React and React Flow on the front. 409 tests, and the whole
> pipeline runs against a local repository."

---

## Recording notes

- Record at 1440×900 or 1920×1080; crop to the browser viewport
- Keep the cursor still while narrating; move deliberately
- Don't record the first index of a large repository — the free-tier rate
  limit makes it slow
- If a take runs long, cut the Insights section first; scan → index → ask is
  the core story
