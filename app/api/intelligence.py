from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.intelligence.engine import FalconIntelligence

router = APIRouter(
    prefix="/intelligence",
    tags=["intelligence"],
)


class RunRequest(BaseModel):
    goal: str
    context: dict = Field(default_factory=dict)


@router.post("/run")
def run(request: RunRequest):
    return FalconIntelligence().run(
        request.goal,
        request.context,
    )