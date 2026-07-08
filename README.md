# Falcon AI

AI-powered Business Operating System built around a FastAPI backend.

## Current Project Analysis

The existing project is a compact Python API with these active pieces:

- `app/main.py`: FastAPI entrypoint with registration, login, profile, and business analysis routes.
- `app/auth.py`: password hashing and JWT helpers.
- `app/database.py`: SQLAlchemy engine/session setup from `DATABASE_URL`.
- `app/models.py`: SQLAlchemy user model.
- `app/schemas.py`: Pydantic request/response schemas.
- `app/ai_service.py`: rule-based business problem analysis.
- `falcon.db`: local database file currently present in the project root.

## Complete Folder Structure

```text
Falcon-ai/
  app/
    api/
      dependencies/       # Shared FastAPI dependencies
      routes/             # Route modules grouped by feature
    agents/               # AI agent definitions and orchestration
    core/                 # Settings, security, app-wide constants
    prompts/              # Prompt templates and prompt versions
    repositories/         # Database access layer
    services/             # Business logic and provider integrations
    tools/                # Internal AI tools/functions
    utils/                # Small shared helpers
    ai_service.py         # Existing business analysis service
    auth.py               # Existing auth helpers
    database.py           # Existing database setup
    main.py               # Existing FastAPI app entrypoint
    models.py             # Existing SQLAlchemy models
    schemas.py            # Existing Pydantic schemas
  frontend/
    public/               # Static assets
    src/
      app/                # Frontend routes/pages
      components/         # Reusable UI components
      features/           # Feature-specific UI modules
      hooks/              # Reusable frontend hooks
      lib/                # Browser/client helpers
      styles/             # Global styles and design tokens
  data/
    raw/                  # Original imported data
    processed/            # Cleaned/transformed data
    embeddings/           # Vector data and embedding outputs
    exports/              # Generated reports and downloads
  docs/
    architecture/         # System design notes
    product/              # Product requirements and roadmap
    runbooks/             # Operational guides
  infra/
    docker/               # Docker assets
    k8s/                  # Kubernetes manifests
    terraform/            # Cloud provisioning
  scripts/                # Developer and maintenance scripts
  tests/
    unit/                 # Fast isolated tests
    integration/          # API/database integration tests
    e2e/                  # End-to-end workflow tests
    fixtures/             # Shared test data
  tools/                  # Local project tooling
  .github/
    workflows/            # CI workflows
```

## Recommended Next Refactor

Keep the app running as-is for now. When the code grows, move routes from `app/main.py` into `app/api/routes/`, move settings and secrets into `app/core/`, and move database reads/writes into `app/repositories/`.
