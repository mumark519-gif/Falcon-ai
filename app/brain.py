from __future__ import annotations

from typing import Any

from app.agents.orchestrator import orchestrate
from app.core.logger import logger


class FalconBrain:
    """
    Central public interface for Falcon's intelligence.

    The brain does not implement individual capabilities.
    It delegates cognitive work to Falcon's orchestration layer.

    Future capabilities such as:
    - voice
    - vision
    - coding
    - research
    - web
    - documents
    - automation
    - enterprise agents
    - GitHub
    - browser
    - image/video understanding
    - memory
    - payments
    - autonomous task execution

    can connect to this interface without changing the
    external API of Falcon's brain.
    """

    def __init__(self, db=None):
        self.db = db

    def ask(
        self,
        username: str,
        question: str,
    ) -> dict[str, Any]:
        """
        Send a user request through Falcon's complete
        orchestration pipeline.
        """

        question = str(
            question or ""
        ).strip()

        if not question:
            return {
                "error": True,
                "message": (
                    "Please provide a question or task."
                ),
            }

        try:
            return orchestrate(
                db=self.db,
                username=username,
                question=question,
            )

        except Exception as exc:
            logger.exception(
                "Falcon Brain execution failed."
            )

            return {
                "error": True,
                "message": (
                    "Falcon Brain encountered an internal "
                    "processing error."
                ),
                "details": str(exc),
            }


def create_brain(
    db=None,
) -> FalconBrain:
    """
    Create a Falcon Brain instance.
    """

    return FalconBrain(
        db=db
    )


def ask(
    db,
    username: str,
    question: str,
) -> dict[str, Any]:
    """
    Compatibility helper for simple callers.
    """

    brain = FalconBrain(
        db=db
    )

    return brain.ask(
        username=username,
        question=question,
    )


def run(
    db,
    username: str,
    question: str,
) -> dict[str, Any]:
    """
    Compatibility alias for Falcon's main brain entry point.
    """

    return ask(
        db=db,
        username=username,
        question=question,
    )