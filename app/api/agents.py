from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.falcon_orchestrator import orchestrator
router=APIRouter(prefix="/agents",tags=["agents"])
class AgentRequest(BaseModel): goal:str; context:dict|None=None
@router.post("/run")
def run(req:AgentRequest):
    return orchestrator.answer(req.goal,req.context)
@router.post("/prepare")
def prepare(req:AgentRequest): return orchestrator.prepare(req.goal,req.context)
