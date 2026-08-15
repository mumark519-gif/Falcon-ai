from fastapi import APIRouter
from app.observability.health import health
from app.agents.falcon_orchestrator import orchestrator
router=APIRouter(prefix="/capabilities",tags=["capabilities"])
@router.get("/health")
def capabilities_health(): return health()
@router.get("/providers")
def providers(): return {"providers":orchestrator.prepare("list configured providers")["model"].__dict__}
