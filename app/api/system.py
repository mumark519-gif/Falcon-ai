from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.settings import settings
from app.database import engine
from app.services.ai.ai_gateway import available_providers

router = APIRouter(prefix="/system", tags=["system"])


def _database_ok() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get("/health")
def health():
    """Liveness endpoint: process is running."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.env}


@router.get("/ready")
def readiness():
    """Readiness endpoint for load balancers and container orchestration."""
    db_ok = _database_ok()
    providers = available_providers()
    ready = db_ok
    return {
        "status": "ready" if ready else "not_ready",
        "database": "ok" if db_ok else "error",
        "providers": providers,
        "provider_configured": bool(providers),
    }


@router.get("/providers")
def providers():
    return {"providers": available_providers(), "default": settings.default_provider}
