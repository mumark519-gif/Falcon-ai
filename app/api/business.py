from fastapi import APIRouter
from app.ai_service import analyze_business_problem
from pydantic import BaseModel

router = APIRouter()


class BusinessRequest(BaseModel):
    problem: str


@router.post("/analyze")
def analyze(request: BusinessRequest):
    analysis = analyze_business_problem(request.problem)

    return {
        "problem": request.problem,
        "analysis": analysis
    }