from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.falcon_orchestrator import orchestrator
from app.intelligence.engine import FalconIntelligence
from app.core.logger import logger


router = APIRouter(
    prefix="/intelligence",
    tags=["intelligence"],
)


class RunRequest(BaseModel):
    goal: str = Field(
        ...,
        min_length=1,
        description="The user's objective or task.",
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional contextual information.",
    )

    mode: str = Field(
        default="orchestrated",
        description=(
            "Execution mode. "
            "'orchestrated' uses Falcon's top-level control plane. "
            "'engine' directly invokes FalconIntelligence."
        ),
    )


@router.post("/run")
def run(request: RunRequest) -> dict[str, Any]:
    """
    Run Falcon Intelligence.

    Default flow:

        API
          ↓
        FalconOrchestrator
          ↓
        reasoning
          ↓
        planning
          ↓
        execution
          ↓
        verification
          ↓
        reflection
          ↓
        model response

    The underlying FalconIntelligence engine remains available through
    mode='engine' so existing functionality is not discarded.
    """

    goal = request.goal.strip()

    if not goal:
        return {
            "status": "error",
            "error": "empty_goal",
            "response": (
                "Please provide a question or task."
            ),
        }

    mode = request.mode.strip().lower()

    logger.info(
        "Intelligence request received: mode=%s",
        mode,
    )

    # ============================================================
    # DIRECT INTELLIGENCE ENGINE
    # ============================================================

    if mode == "engine":
        try:
            result = FalconIntelligence().run(
                goal,
                request.context,
            )

            return {
                "status": "complete",
                "mode": "engine",
                "goal": goal,
                "result": result,
            }

        except Exception:
            logger.exception(
                "FalconIntelligence engine failed."
            )

            return {
                "status": "error",
                "mode": "engine",
                "goal": goal,
                "response": (
                    "Falcon's intelligence engine encountered "
                    "an internal error."
                ),
                "error": "intelligence_engine_error",
            }

    # ============================================================
    # TOP-LEVEL FALCON ORCHESTRATOR
    # ============================================================

    if mode in {
        "orchestrated",
        "orchestrator",
        "falcon",
        "default",
    }:
        try:
            result = orchestrator.answer(
                goal=goal,
                context=request.context,
            )

            return {
                "status": result.get(
                    "status",
                    "complete",
                ),
                "mode": "orchestrated",
                "goal": goal,
                "result": result,
            }

        except Exception:
            logger.exception(
                "Falcon top-level orchestrator failed."
            )

            return {
                "status": "error",
                "mode": "orchestrated",
                "goal": goal,
                "response": (
                    "Falcon encountered an internal error "
                    "while processing your request."
                ),
                "error": "orchestration_error",
            }

    # ============================================================
    # INVALID MODE
    # ============================================================

    return {
        "status": "error",
        "error": "invalid_mode",
        "message": (
            "Invalid intelligence mode. "
            "Use 'orchestrated' or 'engine'."
        ),
    }