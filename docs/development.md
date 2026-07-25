# Development Guide

## Prerequisites

- Python 3.12+
- Node.js 20+ (frontend only)
- Docker Desktop (PostgreSQL and Qdrant containers)
- A Google Gemini API key

## Install

```powershell
git clone <repository-url> CodeAtlas
cd CodeAtlas

# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# Frontend (optional at this stage)
cd frontend
npm install
cd ..
```

## Configure

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set at minimum:

- `GEMINI_API_KEY` — required for indexing and question answering.

Every other variable has a working default for local development; see the
comments in [.env.example](../.env.example).

## Run

```powershell
# 1. Infrastructure (PostgreSQL + Qdrant)
docker compose up -d

# 2. Backend API
cd backend
.\venv\Scripts\uvicorn.exe main:app --reload
```

The API runs at `http://127.0.0.1:8000` (Swagger UI at `/docs`).
Check everything is wired up:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/status
```

## Index a repository

```powershell
$body = '{"repository_path": "C:/path/to/repo"}'
Invoke-RestMethod -Method Post http://127.0.0.1:8000/index `
    -ContentType 'application/json' -Body $body
```

The response reports indexed/cached/failed chunks and the collection name
(default `codeatlas_<repo>`). Re-running only embeds changed chunks — the
rest come from the embedding cache. Note: the Gemini free tier limits
embedding requests per minute; large first-time indexing runs may need to be
repeated until `failed_chunks` reaches 0 (the cache accumulates progress).

## Ask questions

```powershell
$body = @'
{
  "collection_name": "codeatlas_repo",
  "repository_path": "C:/path/to/repo",
  "question": "How does the scanner decide which files to ignore?"
}
'@
Invoke-RestMethod -Method Post http://127.0.0.1:8000/ask `
    -ContentType 'application/json' -Body $body
```

The answer includes a confidence score, the files it references, and
warnings (empty retrieval, possible hallucinations, …).

## Tests and linting

```powershell
# From the project root
backend\venv\Scripts\python.exe -m pytest tests -q
backend\venv\Scripts\python.exe -m ruff check backend examples tests
backend\venv\Scripts\python.exe -m ruff format --check backend examples tests
```

Unit tests never call the real Gemini API and run Qdrant in-memory — no
running containers are required for the test suite.

## Examples

```powershell
backend\venv\Scripts\python.exe examples\scan_repository.py [path]
backend\venv\Scripts\python.exe examples\repository_inventory.py [path]
```
