from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.api.auth import router as auth_router
from app.api.business import router as business_router
from app.api.chat import router as chat_router
from app.api.documents import router as document_router
from app.api.memory import router as memory_router
from app.core.exceptions import (
    FalconException,
    falcon_exception_handler,
)
from app.core.middleware import log_requests
from app.api.system import router as system_router
from app.api.intelligence import router as intelligence_router
from app.api.agents import router as agents_router
from app.api.research import router as research_router
from app.api.capabilities import router as capabilities_router
from app.api.security import router as security_router
from app.api.evaluation import router as evaluation_router
from app.api.plugins import router as plugins_router
from app.api.multimodal import router as multimodal_router
from app.api.commercial import router as commercial_router
from app.database import engine, ensure_schema
from app.models import Base


if settings.env == "production":
    if settings.secret_key in {"", "change-me", "replace-with-a-long-random-secret"}:
        raise RuntimeError("A strong SECRET_KEY is required in production.")
    if settings.cors_origins.strip() == "*":
        raise RuntimeError("CORS_ORIGINS must be explicit in production.")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)


_cors_origins = (
    ["*"]
    if settings.cors_origins.strip() == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(
    FalconException,
    falcon_exception_handler,
)


app.middleware("http")(log_requests)


app.include_router(auth_router)
app.include_router(business_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(memory_router)
app.include_router(system_router)
app.include_router(intelligence_router)
app.include_router(agents_router)
app.include_router(research_router)
app.include_router(capabilities_router)
app.include_router(security_router)
app.include_router(evaluation_router)
app.include_router(plugins_router)
app.include_router(multimodal_router)
app.include_router(commercial_router)


if settings.env in {"development", "testing"}:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "Welcome to Falcon AI!"
    }