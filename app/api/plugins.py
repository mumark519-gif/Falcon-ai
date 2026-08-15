from fastapi import APIRouter
from app.plugins.registry import registry
router=APIRouter(prefix="/plugins",tags=["plugins"])
@router.get("")
def plugins(): return {"plugins":registry.initialize()}
