from fastapi import APIRouter
from app.security.policy import SecurityPolicy
router=APIRouter(prefix="/security",tags=["security"])
@router.get("/policy")
def policy():
    p=SecurityPolicy(); return {"approval_required_for":sorted(p.require_approval_for),"max_file_bytes":p.max_file_bytes}
