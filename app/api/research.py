from fastapi import APIRouter
from pydantic import BaseModel
from app.intelligence.research import ResearchController, Source
router=APIRouter(prefix="/research",tags=["research"])
class ResearchRequest(BaseModel): query:str
@router.post("/plan")
def plan(req:ResearchRequest): return {"query":req.query,"strategy":["decompose","search in parallel","rank sources","cross-check claims","cite sources","synthesize report"]}
