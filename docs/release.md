# GitHub Release Material

## Repository description

Under GitHub's 350-character limit; the first is the recommended one.

> Repository intelligence: scans a codebase with Tree-sitter, maps its
> dependency graph, and answers questions about the code with citations and
> confidence scoring. FastAPI + Qdrant + Gemini, React 19 frontend.

Shorter alternative:

> Map any codebase and ask it questions — Tree-sitter parsing, dependency
> graphs, and grounded answers with file citations.

## Topics

```
code-analysis  static-analysis  tree-sitter  dependency-graph
rag  vector-search  qdrant  gemini  llm
fastapi  python  react  typescript  react-flow  developer-tools
```

GitHub allows 20; these 15 cover the search terms that matter.

## License

**MIT.** Correct default for a portfolio project: permissive, universally
understood, and it lets reviewers read, run, and borrow from the code
without friction. Apache-2.0 would add an explicit patent grant, which this
project does not need. Copyleft (GPL) would discourage exactly the reuse a
portfolio piece wants to invite.

The `LICENSE` file is at the repository root.

---

## Release notes — v0.1.0

```markdown
# CodeAtlas v0.1.0

First public release. CodeAtlas maps a local repository and answers
questions about it, grounded in code it has actually parsed.

## What it does

**Analysis** — Recursive scanning with sensible ignore rules, file
classification and language detection, Tree-sitter parsing of Python
(top-level classes, functions, and all import forms), and a NetworkX
dependency graph with a resolver that separates first-party imports from
stdlib and third-party.

**Insights** — Cycle detection, fan-in/fan-out rankings, roots, leaves,
isolated files, connected components, and density, rendered as an
architecture report with Markdown export.

**Question answering** — Deterministic chunking with content-hashed IDs,
Gemini embeddings cached locally, Qdrant vector search with metadata
filters, token-budgeted context assembly, and answers from Gemini 2.5 Flash
constrained to the retrieved context.

**Verification** — Every answer carries a 0–100 confidence score derived
from retrieval strength, context size, grounding ratio, and a check for file
paths absent from the context, plus the list of files it cited.

**Interface** — React 19 frontend with an interactive dependency map,
analysis dashboards, and a chat view. Dark and light themes, keyboard
shortcuts, reduced-motion support.

## Requirements

- Python 3.12+, Node.js 20+, Docker
- A Gemini API key

## Getting started

```bash
cp .env.example .env      # set GEMINI_API_KEY
docker compose up -d
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

Full instructions in the README.

## Notes

- Python is the only language with a parser implemented. The framework
  dispatches by language, so additional Tree-sitter grammars slot in without
  architectural change.
- On the Gemini free tier, embedding requests are rate-limited. Large
  repositories may report partial indexing; re-running resumes from cache.
- PostgreSQL is provisioned in `docker-compose.yml` but not yet used by the
  application.

## Tests

409 pytest tests, all offline — the Gemini client is mocked and Qdrant runs
in memory, so no containers or API key are needed to run the suite.
```

---

## Pre-publication checklist

- [ ] `.env` is gitignored and contains no committed key
- [ ] Screenshots captured per `docs/screenshots.md`, no personal paths
      visible
- [ ] Social preview image uploaded (Settings → General → Social preview)
- [ ] Description and topics set
- [ ] `LICENSE` present at the root
- [ ] `npm run build` and `pytest tests -q` both pass from a clean clone
- [ ] Repository description matches the README opening
- [ ] Tag `v0.1.0` and publish the release notes above
