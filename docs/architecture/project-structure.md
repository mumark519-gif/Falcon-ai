# Falcon AI Structure

This structure keeps the current FastAPI backend intact while preparing the project for a fuller AI business operating system.

## Backend Boundaries

- `app/api/routes`: HTTP endpoints only.
- `app/services`: business logic such as analysis, recommendations, and provider calls.
- `app/repositories`: database persistence and queries.
- `app/agents`: autonomous or multi-step AI workflows.
- `app/prompts`: versioned prompt text and templates.
- `app/core`: settings, auth configuration, startup configuration, and shared constants.

## Product Areas

- `frontend`: future customer-facing dashboard.
- `data`: datasets, exports, embeddings, and generated artifacts.
- `docs/product`: product plans, user workflows, and requirements.
- `docs/architecture`: technical design decisions.
- `docs/runbooks`: operational notes for deployment and maintenance.
