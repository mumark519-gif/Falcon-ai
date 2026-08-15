from fastapi import APIRouter
from app.observability.metrics import metrics
router=APIRouter(prefix="/evaluation",tags=["evaluation"])
@router.get("/metrics")
def evaluation_metrics(): return metrics.snapshot()
