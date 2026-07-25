> Sample output of `GET /report`, generated from this repository.
> Regenerate any time with the endpoint or `reports.generate_report`.

# Repository Report: CodeAtlas

Generated: 2026-07-25 21:15:04
Root: `C:\Adii\Projects\CodeAtlas`

## General

| Metric | Value |
| --- | --- |
| Total files | 236 |
| Parsed files | 92 |
| Total symbols | 336 |
| Total imports | 730 |

## Languages

| Name | Files |
| --- | --- |
| unknown | 116 |
| python | 92 |
| json | 8 |
| markdown | 8 |
| text | 5 |
| typescript | 3 |
| css | 2 |
| html | 1 |
| yaml | 1 |

## Categories

| Name | Files |
| --- | --- |
| source_code | 75 |
| configuration | 12 |
| documentation | 8 |
| data | 5 |
| test | 23 |
| image | 5 |
| unknown | 108 |

## Dependency Graph

| Metric | Value |
| --- | --- |
| Nodes | 236 |
| Edges | 282 |
| Density | 0.0051 |
| Connected components | 146 |
| Largest component | 91 |
| Cycles | 0 |

## Architecture Highlights

### Most imported files

- `backend/scanner/__init__.py` (18)
- `backend/scanner/language.py` (16)
- `backend/config/settings.py` (11)
- `backend/embeddings/provider.py` (11)
- `backend/chunking/models.py` (10)
- `backend/knowledge/models.py` (10)
- `backend/scanner/classifier.py` (9)
- `backend/scanner/models.py` (9)
- `backend/context/models.py` (8)
- `backend/embeddings/cache.py` (8)

### Most dependent files

- `backend/services/repository_service.py` (16)
- `backend/services/ai_service.py` (12)
- `backend/services/self_check.py` (8)
- `backend/knowledge/models.py` (7)
- `backend/main.py` (7)
- `backend/api/dependencies.py` (6)
- `backend/api/repository_routes.py` (6)
- `backend/api/system_routes.py` (6)
- `backend/chunking/builder.py` (6)
- `backend/parsers/__init__.py` (6)

### Root modules

- `backend/api/__init__.py`
- `backend/config/__init__.py`
- `backend/services/__init__.py`
- `backend/utils/__init__.py`
- `examples/repository_inventory.py`
- `examples/scan_repository.py`
- `tests/test_ai.py`
- `tests/test_api.py`
- `tests/test_ask_api.py`
- `tests/test_chunking.py`
- `tests/test_classifier.py`
- `tests/test_context.py`
- `tests/test_embeddings.py`
- `tests/test_evaluation.py`
- `tests/test_graph.py`
- `tests/test_graph_analysis.py`
- `tests/test_imports.py`
- `tests/test_inventory.py`
- `tests/test_knowledge.py`
- `tests/test_language.py`
- `tests/test_parsers.py`
- `tests/test_python_parser.py`
- `tests/test_reports.py`
- `tests/test_retrieval.py`
- `tests/test_scanner.py`
- `tests/test_symbols.py`
- `tests/test_system_api.py`
- `tests/test_visualization.py`

### Leaf modules

- `backend/ai/models.py`
- `backend/api/ask_schemas.py`
- `backend/api/envelope.py`
- `backend/api/schemas.py`
- `backend/config/settings.py`
- `backend/embeddings/models.py`
- `backend/evaluation/models.py`
- `backend/parsers/imports.py`
- `backend/parsers/symbols.py`
- `backend/scanner/classifier.py`
- `backend/scanner/language.py`
- `backend/utils/logging.py`

### Isolated files

- `.claude/settings.local.json`
- `.env`
- `.env.example`
- `.gitignore`
- `.pytest_cache/.gitignore`
- `.pytest_cache/CACHEDIR.TAG`
- `.pytest_cache/README.md`
- `.pytest_cache/v/cache/lastfailed`
- `.pytest_cache/v/cache/nodeids`
- `.ruff_cache/.gitignore`
- `.ruff_cache/0.16.0/10661396720324249444`
- `.ruff_cache/0.16.0/10661556077344536661`
- `.ruff_cache/0.16.0/10694947100976132584`
- `.ruff_cache/0.16.0/11415296070684423765`
- `.ruff_cache/0.16.0/11422577091465048833`
- `.ruff_cache/0.16.0/1151813784609381385`
- `.ruff_cache/0.16.0/11629249724890765122`
- `.ruff_cache/0.16.0/1166716726694294850`
- `.ruff_cache/0.16.0/11714076617394631748`
- `.ruff_cache/0.16.0/11732562393432564315`
- `.ruff_cache/0.16.0/12136383730954089446`
- `.ruff_cache/0.16.0/12337360672599649068`
- `.ruff_cache/0.16.0/1245493031137992112`
- `.ruff_cache/0.16.0/12639272846722334623`
- `.ruff_cache/0.16.0/12853146702090136825`
- `.ruff_cache/0.16.0/12861064015084898173`
- `.ruff_cache/0.16.0/13020382950880987269`
- `.ruff_cache/0.16.0/13189783447432021856`
- `.ruff_cache/0.16.0/1328609602715431260`
- `.ruff_cache/0.16.0/13293875483315615826`
- `.ruff_cache/0.16.0/13452036073325137619`
- `.ruff_cache/0.16.0/1356675919756693120`
- `.ruff_cache/0.16.0/1359887780516950479`
- `.ruff_cache/0.16.0/13934123202038116901`
- `.ruff_cache/0.16.0/14131394161407809687`
- `.ruff_cache/0.16.0/14388872538863269352`
- `.ruff_cache/0.16.0/14448424885519406808`
- `.ruff_cache/0.16.0/14568028972621175836`
- `.ruff_cache/0.16.0/14772934417429050596`
- `.ruff_cache/0.16.0/14879773064239901925`
- `.ruff_cache/0.16.0/15297355123303869571`
- `.ruff_cache/0.16.0/15317562698044883699`
- `.ruff_cache/0.16.0/15396597100798381866`
- `.ruff_cache/0.16.0/15594178873398801595`
- `.ruff_cache/0.16.0/15699974255033230590`
- `.ruff_cache/0.16.0/15844746334502108143`
- `.ruff_cache/0.16.0/15973227288655085510`
- `.ruff_cache/0.16.0/16117450606457652724`
- `.ruff_cache/0.16.0/16237266180466844812`
- `.ruff_cache/0.16.0/16710202968645733409`
- `.ruff_cache/0.16.0/16754099735545052837`
- `.ruff_cache/0.16.0/16774472234722383935`
- `.ruff_cache/0.16.0/16894691702988790305`
- `.ruff_cache/0.16.0/16895246080771433257`
- `.ruff_cache/0.16.0/1694264672783988985`
- `.ruff_cache/0.16.0/17085332860804415255`
- `.ruff_cache/0.16.0/17196264700616419219`
- `.ruff_cache/0.16.0/17711942287846853116`
- `.ruff_cache/0.16.0/17736884755165974994`
- `.ruff_cache/0.16.0/17746180142233476783`
- `.ruff_cache/0.16.0/18277160892589043749`
- `.ruff_cache/0.16.0/203059832082918210`
- `.ruff_cache/0.16.0/2122079977205961712`
- `.ruff_cache/0.16.0/2130259591094060161`
- `.ruff_cache/0.16.0/2229598788303290239`
- `.ruff_cache/0.16.0/2277574255376511070`
- `.ruff_cache/0.16.0/2439279672032796720`
- `.ruff_cache/0.16.0/2785720155950519917`
- `.ruff_cache/0.16.0/2864539922009868137`
- `.ruff_cache/0.16.0/3665193995587308436`
- `.ruff_cache/0.16.0/3872235502109450450`
- `.ruff_cache/0.16.0/4020787009654166580`
- `.ruff_cache/0.16.0/4161812117931230928`
- `.ruff_cache/0.16.0/4173489079076228486`
- `.ruff_cache/0.16.0/423127559023700990`
- `.ruff_cache/0.16.0/4264772078958101840`
- `.ruff_cache/0.16.0/4374527932512450593`
- `.ruff_cache/0.16.0/4424421712678870739`
- `.ruff_cache/0.16.0/4683300152509483605`
- `.ruff_cache/0.16.0/4778114490656748100`
- `.ruff_cache/0.16.0/4845276355363630100`
- `.ruff_cache/0.16.0/4911062665904234434`
- `.ruff_cache/0.16.0/4922937864413790162`
- `.ruff_cache/0.16.0/5040472158842099385`
- `.ruff_cache/0.16.0/5571018662539272986`
- `.ruff_cache/0.16.0/5741271736258069986`
- `.ruff_cache/0.16.0/6152629171533973719`
- `.ruff_cache/0.16.0/6277709019612524275`
- `.ruff_cache/0.16.0/6329163170956892313`
- `.ruff_cache/0.16.0/660349113223022972`
- `.ruff_cache/0.16.0/6740843880791315450`
- `.ruff_cache/0.16.0/6846651466452424468`
- `.ruff_cache/0.16.0/7404787142938530482`
- `.ruff_cache/0.16.0/7413621832337064759`
- `.ruff_cache/0.16.0/7542801937259923101`
- `.ruff_cache/0.16.0/7586913492540824453`
- `.ruff_cache/0.16.0/7591979703523355765`
- `.ruff_cache/0.16.0/7635793256364000410`
- `.ruff_cache/0.16.0/7738121642518925707`
- `.ruff_cache/0.16.0/776224433652649542`
- `.ruff_cache/0.16.0/7787293205836981479`
- `.ruff_cache/0.16.0/8017462213224746068`
- `.ruff_cache/0.16.0/8145589541390137278`
- `.ruff_cache/0.16.0/8255582976568000897`
- `.ruff_cache/0.16.0/8366902877531833319`
- `.ruff_cache/0.16.0/8470811254902290243`
- `.ruff_cache/0.16.0/8531792673102923768`
- `.ruff_cache/0.16.0/8958331145610311646`
- `.ruff_cache/0.16.0/9066810390324180924`
- `.ruff_cache/0.16.0/9675863548677582961`
- `.ruff_cache/0.16.0/9751969763498680792`
- `.ruff_cache/0.16.0/9763255394440164777`
- `.ruff_cache/0.16.0/9940547632139091740`
- `.ruff_cache/0.16.0/9954785562516893090`
- `.ruff_cache/CACHEDIR.TAG`
- `README.md`
- `backend/.cache/embeddings.json`
- `backend/requirements.txt`
- `docker-compose.yml`
- `docs/api_overview.md`
- `docs/architecture.md`
- `docs/codeatlas_report.md`
- `docs/development.md`
- `docs/project_structure.md`
- `frontend/.gitignore`
- `frontend/.oxlintrc.json`
- `frontend/README.md`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/public/favicon.svg`
- `frontend/public/icons.svg`
- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/assets/hero.png`
- `frontend/src/assets/react.svg`
- `frontend/src/assets/vite.svg`
- `frontend/src/index.css`
- `frontend/src/main.tsx`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`
- `ruff.toml`
- `tests/conftest.py`

## Potential Issues

### High fan-in modules

- `backend/scanner/__init__.py` (18)
- `backend/scanner/language.py` (16)
- `backend/config/settings.py` (11)
- `backend/embeddings/provider.py` (11)
- `backend/chunking/models.py` (10)
- `backend/knowledge/models.py` (10)

### High fan-out modules

- `backend/services/repository_service.py` (16)
- `backend/services/ai_service.py` (12)

### Unresolved imports

- `backend/ai/models.py` line 3: `pydantic.BaseModel`
- `backend/ai/models.py` line 3: `pydantic.Field`
- `backend/ai/provider.py` line 44: `google.genai`
- `backend/ai/provider.py` line 56: `google.genai.types`
- `backend/api/ask_routes.py` line 5: `fastapi.APIRouter`
- `backend/api/ask_routes.py` line 5: `fastapi.Depends`
- `backend/api/ask_routes.py` line 5: `fastapi.HTTPException`
- `backend/api/ask_schemas.py` line 3: `pydantic.BaseModel`
- `backend/api/ask_schemas.py` line 3: `pydantic.Field`
- `backend/api/dependencies.py` line 9: `fastapi.Depends`
- `backend/api/dependencies.py` line 10: `qdrant_client.QdrantClient`
- `backend/api/envelope.py` line 9: `pydantic.BaseModel`
- `backend/api/repository_routes.py` line 5: `fastapi.APIRouter`
- `backend/api/repository_routes.py` line 5: `fastapi.Depends`
- `backend/api/repository_routes.py` line 5: `fastapi.HTTPException`
- `backend/api/repository_routes.py` line 5: `fastapi.Query`
- `backend/api/repository_schemas.py` line 3: `pydantic.BaseModel`
- `backend/api/repository_schemas.py` line 3: `pydantic.Field`
- `backend/api/routes.py` line 5: `fastapi.APIRouter`
- `backend/api/routes.py` line 5: `fastapi.Depends`
- `backend/api/schemas.py` line 3: `pydantic.BaseModel`
- `backend/api/system_routes.py` line 7: `fastapi.APIRouter`
- `backend/api/system_routes.py` line 7: `fastapi.Depends`
- `backend/api/system_routes.py` line 8: `pydantic.BaseModel`
- `backend/api/system_routes.py` line 9: `qdrant_client.QdrantClient`
- `backend/chunking/models.py` line 5: `pydantic.BaseModel`
- `backend/chunking/models.py` line 5: `pydantic.Field`
- `backend/config/settings.py` line 13: `pydantic.AliasChoices`
- `backend/config/settings.py` line 13: `pydantic.Field`
- `backend/config/settings.py` line 14: `pydantic_settings.BaseSettings`
- `backend/config/settings.py` line 14: `pydantic_settings.SettingsConfigDict`
- `backend/context/models.py` line 5: `pydantic.BaseModel`
- `backend/embeddings/models.py` line 3: `pydantic.BaseModel`
- `backend/embeddings/provider.py` line 47: `google.genai`
- `backend/embeddings/provider.py` line 59: `google.genai.types`
- `backend/embeddings/store.py` line 6: `qdrant_client.QdrantClient`
- `backend/embeddings/store.py` line 7: `qdrant_client.models.Distance`
- `backend/embeddings/store.py` line 7: `qdrant_client.models.PointStruct`
- `backend/embeddings/store.py` line 7: `qdrant_client.models.VectorParams`
- `backend/evaluation/models.py` line 3: `pydantic.BaseModel`
- `backend/evaluation/models.py` line 3: `pydantic.Field`
- `backend/graph/analysis.py` line 9: `networkx`
- `backend/graph/analysis.py` line 10: `pydantic.BaseModel`
- `backend/graph/builder.py` line 5: `networkx`
- `backend/graph/models.py` line 8: `networkx`
- `backend/graph/models.py` line 9: `pydantic.BaseModel`
- `backend/graph/visualization.py` line 11: `networkx`
- `backend/graph/visualization.py` line 12: `pydantic.BaseModel`
- `backend/graph/visualization.py` line 12: `pydantic.PrivateAttr`
- `backend/knowledge/models.py` line 9: `pydantic.BaseModel`
- `backend/knowledge/models.py` line 9: `pydantic.Field`
- `backend/main.py` line 10: `fastapi.FastAPI`
- `backend/main.py` line 10: `fastapi.Request`
- `backend/main.py` line 11: `fastapi.exceptions.RequestValidationError`
- `backend/main.py` line 12: `fastapi.middleware.cors.CORSMiddleware`
- `backend/main.py` line 13: `fastapi.responses.JSONResponse`
- `backend/main.py` line 14: `starlette.exceptions.HTTPException`
- `backend/parsers/imports.py` line 11: `pydantic.BaseModel`
- `backend/parsers/imports.py` line 12: `tree_sitter.Node`
- `backend/parsers/imports.py` line 12: `tree_sitter.Tree`
- `backend/parsers/models.py` line 5: `pydantic.BaseModel`
- `backend/parsers/models.py` line 5: `pydantic.Field`
- `backend/parsers/python_parser.py` line 14: `tree_sitter_python`
- `backend/parsers/python_parser.py` line 15: `tree_sitter.Language`
- `backend/parsers/python_parser.py` line 15: `tree_sitter.Node`
- `backend/parsers/python_parser.py` line 15: `tree_sitter.Parser`
- `backend/parsers/python_parser.py` line 15: `tree_sitter.Tree`
- `backend/parsers/symbols.py` line 11: `pydantic.BaseModel`
- `backend/parsers/symbols.py` line 12: `tree_sitter.Node`
- `backend/parsers/symbols.py` line 12: `tree_sitter.Tree`
- `backend/reports/generator.py` line 6: `pydantic.BaseModel`
- `backend/reports/models.py` line 5: `pydantic.BaseModel`
- `backend/retrieval/models.py` line 3: `pydantic.BaseModel`
- `backend/retrieval/models.py` line 3: `pydantic.Field`
- `backend/retrieval/retriever.py` line 6: `qdrant_client.QdrantClient`
- `backend/retrieval/retriever.py` line 7: `qdrant_client.models.FieldCondition`
- `backend/retrieval/retriever.py` line 7: `qdrant_client.models.Filter`
- `backend/retrieval/retriever.py` line 7: `qdrant_client.models.MatchValue`
- `backend/scanner/inventory.py` line 11: `pydantic.BaseModel`
- `backend/scanner/models.py` line 5: `pydantic.BaseModel`
- `backend/services/ai_service.py` line 12: `qdrant_client.QdrantClient`
- `backend/services/repository_service.py` line 11: `qdrant_client.QdrantClient`
- `backend/services/self_check.py` line 9: `qdrant_client.QdrantClient`
- `tests/test_ai.py` line 6: `pytest`
- `tests/test_api.py` line 12: `pytest`
- `tests/test_api.py` line 13: `fastapi.testclient.TestClient`
- `tests/test_api.py` line 14: `qdrant_client.QdrantClient`
- `tests/test_ask_api.py` line 8: `pytest`
- `tests/test_ask_api.py` line 9: `fastapi.testclient.TestClient`
- `tests/test_ask_api.py` line 10: `qdrant_client.QdrantClient`
- `tests/test_classifier.py` line 3: `pytest`
- `tests/test_context.py` line 5: `pytest`
- `tests/test_embeddings.py` line 11: `qdrant_client.QdrantClient`
- `tests/test_evaluation.py` line 5: `pytest`
- `tests/test_graph_analysis.py` line 5: `pytest`
- `tests/test_imports.py` line 3: `tree_sitter_python`
- `tests/test_imports.py` line 4: `tree_sitter.Language`
- `tests/test_imports.py` line 4: `tree_sitter.Parser`
- `tests/test_imports.py` line 4: `tree_sitter.Tree`
- `tests/test_inventory.py` line 5: `pytest`
- `tests/test_knowledge.py` line 5: `pytest`
- `tests/test_language.py` line 3: `pytest`
- `tests/test_parsers.py` line 6: `pytest`
- `tests/test_python_parser.py` line 6: `pytest`
- `tests/test_reports.py` line 6: `pytest`
- `tests/test_retrieval.py` line 10: `pytest`
- `tests/test_retrieval.py` line 11: `qdrant_client.QdrantClient`
- `tests/test_scanner.py` line 6: `pytest`
- `tests/test_symbols.py` line 3: `tree_sitter_python`
- `tests/test_symbols.py` line 4: `tree_sitter.Language`
- `tests/test_symbols.py` line 4: `tree_sitter.Parser`
- `tests/test_symbols.py` line 4: `tree_sitter.Tree`
- `tests/test_system_api.py` line 10: `pytest`
- `tests/test_system_api.py` line 11: `fastapi.testclient.TestClient`
- `tests/test_system_api.py` line 12: `qdrant_client.QdrantClient`
- `tests/test_system_api.py` line 179: `qdrant_client.models.Distance`
- `tests/test_system_api.py` line 179: `qdrant_client.models.VectorParams`
- `tests/test_visualization.py` line 5: `pytest`
