# Project Structure

Generated snapshot of the repository layout (caches, virtual
environments, and `node_modules` omitted).

```text
CodeAtlas/
├── backend/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── models.py
│   │   ├── prompts.py
│   │   └── provider.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ask_routes.py
│   │   ├── ask_schemas.py
│   │   ├── dependencies.py
│   │   ├── envelope.py
│   │   ├── repository_routes.py
│   │   ├── repository_schemas.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── system_routes.py
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   └── models.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── context/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   └── models.py
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   ├── indexer.py
│   │   ├── models.py
│   │   ├── provider.py
│   │   └── store.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluator.py
│   │   └── models.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── builder.py
│   │   ├── models.py
│   │   ├── resolver.py
│   │   └── visualization.py
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   └── models.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── imports.py
│   │   ├── manager.py
│   │   ├── models.py
│   │   ├── python_parser.py
│   │   └── symbols.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── models.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── retriever.py
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── classifier.py
│   │   ├── inventory.py
│   │   ├── language.py
│   │   ├── models.py
│   │   └── repository_scanner.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── repository_service.py
│   │   └── self_check.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logging.py
│   ├── main.py
│   └── requirements.txt
├── docs/
│   ├── api_overview.md
│   ├── architecture.md
│   ├── demo_script.md
│   ├── development.md
│   ├── project_structure.md
│   ├── release.md
│   ├── resume.md
│   ├── sample_report.md
│   └── screenshots.md
├── examples/
│   ├── repository_inventory.py
│   └── scan_repository.py
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── chat-input.tsx
│   │   │   │   ├── confidence-badge.tsx
│   │   │   │   ├── message-bubble.tsx
│   │   │   │   ├── referenced-files-panel.tsx
│   │   │   │   └── suggested-questions.tsx
│   │   │   ├── common/
│   │   │   │   ├── animated-number.tsx
│   │   │   │   ├── confirm-dialog.tsx
│   │   │   │   ├── connection-status.tsx
│   │   │   │   ├── data-table.tsx
│   │   │   │   ├── empty-state.tsx
│   │   │   │   ├── error-boundary.tsx
│   │   │   │   ├── error-state.tsx
│   │   │   │   ├── loading.tsx
│   │   │   │   ├── page-header.tsx
│   │   │   │   ├── page-transition.tsx
│   │   │   │   ├── repository-path-field.tsx
│   │   │   │   ├── repository-selector.tsx
│   │   │   │   ├── stat-card.tsx
│   │   │   │   └── theme-toggle.tsx
│   │   │   ├── graph/
│   │   │   │   ├── category-colors.ts
│   │   │   │   ├── file-node.tsx
│   │   │   │   ├── graph-canvas.tsx
│   │   │   │   └── node-details-panel.tsx
│   │   │   ├── layout/
│   │   │   │   ├── app-shell.tsx
│   │   │   │   ├── header.tsx
│   │   │   │   ├── nav-items.ts
│   │   │   │   └── sidebar.tsx
│   │   │   ├── markdown/
│   │   │   │   ├── code-block.tsx
│   │   │   │   └── markdown-renderer.tsx
│   │   │   ├── report/
│   │   │   │   ├── distribution-chart.tsx
│   │   │   │   └── ranked-file-table.tsx
│   │   │   └── ui/
│   │   │       ├── alert.tsx
│   │   │       ├── badge.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── dialog.tsx
│   │   │       ├── dropdown-menu.tsx
│   │   │       ├── input.tsx
│   │   │       ├── label.tsx
│   │   │       ├── progress.tsx
│   │   │       ├── scroll-area.tsx
│   │   │       ├── select.tsx
│   │   │       ├── separator.tsx
│   │   │       ├── sheet.tsx
│   │   │       ├── skeleton.tsx
│   │   │       ├── sonner.tsx
│   │   │       ├── switch.tsx
│   │   │       ├── table.tsx
│   │   │       ├── tabs.tsx
│   │   │       ├── textarea.tsx
│   │   │       └── tooltip.tsx
│   │   ├── hooks/
│   │   │   ├── use-active-repository.ts
│   │   │   ├── use-api.ts
│   │   │   ├── use-copy-to-clipboard.ts
│   │   │   ├── use-keyboard-shortcut.ts
│   │   │   ├── use-local-storage.ts
│   │   │   ├── use-media-query.ts
│   │   │   ├── use-preferences.ts
│   │   │   └── use-repositories.ts
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── client.ts
│   │   │   │   ├── endpoints.ts
│   │   │   │   └── query-keys.ts
│   │   │   ├── env.ts
│   │   │   ├── format.ts
│   │   │   ├── report-markdown.ts
│   │   │   └── utils.ts
│   │   ├── pages/
│   │   │   ├── chat.tsx
│   │   │   ├── dashboard.tsx
│   │   │   ├── graph.tsx
│   │   │   ├── not-found.tsx
│   │   │   ├── report.tsx
│   │   │   ├── repositories.tsx
│   │   │   └── settings.tsx
│   │   ├── providers/
│   │   │   ├── app-providers.tsx
│   │   │   ├── motion-provider.tsx
│   │   │   ├── query-provider.tsx
│   │   │   └── theme-provider.tsx
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   └── chat.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── router.tsx
│   ├── .env.example
│   ├── .env.local
│   ├── .gitignore
│   ├── .oxlintrc.json
│   ├── components.json
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── tests/
│   ├── conftest.py
│   ├── test_ai.py
│   ├── test_api.py
│   ├── test_ask_api.py
│   ├── test_chunking.py
│   ├── test_classifier.py
│   ├── test_context.py
│   ├── test_embeddings.py
│   ├── test_evaluation.py
│   ├── test_graph.py
│   ├── test_graph_analysis.py
│   ├── test_imports.py
│   ├── test_inventory.py
│   ├── test_knowledge.py
│   ├── test_language.py
│   ├── test_parsers.py
│   ├── test_python_parser.py
│   ├── test_reports.py
│   ├── test_retrieval.py
│   ├── test_scanner.py
│   ├── test_symbols.py
│   ├── test_system_api.py
│   └── test_visualization.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── LICENSE
├── README.md
└── ruff.toml
```
