# Falcon AI deployment

## Local

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
alembic upgrade head
uvicorn app.main:app --reload
```

## Docker

```bash
cd infra/docker
docker compose up --build
```

The API is exposed on port 8000. Configure provider keys in the compose environment or a secrets manager before production use.

## Production requirements

- PostgreSQL (the included compose file provides it for a single-host deployment).
- A strong `SECRET_KEY` stored in a secrets manager.
- Explicit `CORS_ORIGINS`; never use `*` for a credentialed production frontend.
- Provider API credentials stored outside source control.
- TLS termination through a reverse proxy/load balancer.
- Persistent object storage for uploaded documents in a multi-instance deployment.
- Redis or another shared queue/cache if horizontal workers are enabled.
- Backups and restore testing for PostgreSQL and uploaded documents.
- Monitoring for API latency, provider errors, queue depth, storage, and database health.
