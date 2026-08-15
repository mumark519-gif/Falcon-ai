# Falcon AI — Consolidated Commercial Build

## Verified in the build environment

- `python -m compileall -q app tests migrations` — passed
- Every importable module under `app/` — passed
- `python -m pytest -q` — **35 passed**
- Alembic migration smoke test (`upgrade head`) — passed
- Provider router failover test — passed
- Commercial workspace/usage/API-key lifecycle tests — passed

## Architecture consolidation

- `app/services/ai/providers.py` is the canonical provider abstraction and router.
- OpenAI, Anthropic, Gemini, Kimi and OpenAI-compatible providers are behind one interface.
- Provider failures are normalized and the router can fail over to another configured provider.
- Legacy AI/provider modules remain only as compatibility facades and no longer force SDK imports at application import time.
- `app/tools/tavily_provider.py` is the canonical Tavily implementation; the older provider path is a compatibility wrapper.
- `app/tools/web_search.py` exposes the canonical `web_search` alias used by the research pipeline.
- Specialist agent execution is centralized through the orchestrator; the parallel executor imports those canonical runners.
- SQLite is configured safely for local/test threading and production deployments are prepared for PostgreSQL.
- Production database migrations are provided through Alembic.
- Commercial foundations are connected to persistent organizations, memberships, plans, subscriptions, usage records, audit records and hashed API keys.
- Readiness checks now verify database connectivity and provider configuration.
- Production startup rejects unsafe default secrets and wildcard credentialed CORS.
- Docker deployment includes PostgreSQL, migrations, non-root API execution and health checks.

## Important deployment limitation

The automated suite deliberately does not spend real provider credits. Real provider verification must be performed after production credentials/credits are configured. The suite therefore proves Falcon's software contracts, routing/failover behavior and internal integration without requiring paid API calls.

Falcon's own foundation model/intelligence weights are intentionally outside this build. The platform is designed to host and route external models until Falcon's proprietary intelligence is built separately.
