# Falcon AI

Falcon is a general-purpose agentic AI platform with a unified intelligence control plane, multi-provider model routing, research, coding, multimodal capability facades, tools, memory, documents/RAG, enterprise controls, commercial usage management, security, observability, evaluation and a React frontend.

## Included

- FastAPI backend with modular API/service/agent layers
- OpenAI, Anthropic, Gemini, Kimi and OpenAI-compatible providers
- Provider failover and normalized provider errors
- Chat, streaming, memory and document workflows
- Research, browser/web-search, coding, business and investment agents
- Tool registry, permissions, retries and structured tool results
- Persistent organizations, memberships, plans, subscriptions, usage records, audit records and hashed API keys
- JWT authentication
- Alembic production migrations
- PostgreSQL-ready Docker deployment
- React/Vite frontend
- Automated tests

## Local setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, configure the provider(s) you want to use, then:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm run dev
```

## Verification

```bash
python -m compileall -q app tests migrations
python -m pytest -q
```

The test suite uses mocked provider calls where appropriate, so it does not require paid API credits.

## Production

See [`infra/DEPLOYMENT.md`](infra/DEPLOYMENT.md). The included Docker stack provisions PostgreSQL, runs Alembic migrations, starts Falcon as a non-root user and exposes health/readiness endpoints.

Before production:

- set a strong `SECRET_KEY`
- set explicit `CORS_ORIGINS`
- configure provider credentials through a secret manager
- use persistent storage for uploaded documents
- configure TLS and backups
- monitor database/provider/queue health

## Scope boundary

This repository is the commercial Falcon platform and orchestration layer. It does **not** contain a trained proprietary Falcon foundation model. Building a frontier model requires separate model architecture, datasets, training infrastructure, evaluation and model-serving work.
