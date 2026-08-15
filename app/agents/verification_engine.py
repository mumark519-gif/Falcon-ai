from __future__ import annotations

from typing import Any


def verify_execution(
    question: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Basic deterministic execution verification.

    This is intentionally conservative.
    """

    if not isinstance(result, dict):

        return {
            "verified": False,
            "reason": (
                "Execution result is not a dictionary."
            ),
        }

    status = str(
        result.get(
            "status",
            "",
        )
    ).lower()

    if status not in {
        "complete",
        "completed",
        "success",
        "partial",
    }:

        return {
            "verified": False,
            "reason": (
                f"Execution status was '{status}'."
            ),
        }

    total = int(
        result.get(
            "total_steps",
            0,
        )
        or 0
    )

    completed = int(
        result.get(
            "completed_steps",
            0,
        )
        or 0
    )

    failed = int(
        result.get(
            "failed_steps",
            0,
        )
        or 0
    )

    if total <= 0:

        return {
            "verified": False,
            "reason": (
                "No execution steps were completed."
            ),
        }

    if failed > 0:

        return {
            "verified": False,
            "reason": (
                f"{failed} execution step(s) failed."
            ),
        }

    if completed < total:

        return {
            "verified": False,
            "reason": (
                "Not all execution steps completed."
            ),
        }

    return {
        "verified": True,
        "reason": (
            "All execution steps completed successfully."
        ),
        "completed_steps": completed,
        "total_steps": total,
    }