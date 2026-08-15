from __future__ import annotations

import json

from app.ai_service import ask_ai
from app.core.logger import logger


REASONING_PROMPT = """
You are Falcon AI's Reasoning Engine.

Analyze the execution plan before final synthesis.

Determine:

1. What the plan is trying to accomplish
2. Whether the selected agents/tools make sense
3. Dependencies between steps
4. Missing information
5. Potential contradictions
6. Potential failure points
7. What evidence should be trusted
8. What the final answer must contain

Do NOT answer the user's question.

Return ONLY valid JSON.

Format:

{
    "objective": "...",
    "valid": true,
    "dependencies": [],
    "missing_information": [],
    "risks": [],
    "verification_requirements": [],
    "recommended_synthesis": "...",
    "confidence": 0.0
}
"""


def reason_about_plan(
    question: str,
    plan: dict,
):
    prompt = (
        REASONING_PROMPT
        + "\n\nUser Question:\n"
        + question
        + "\n\nExecution Plan:\n"
        + json.dumps(
            plan,
            ensure_ascii=False,
            default=str,
        )
    )

    response = ask_ai(
        prompt
    )

    try:

        return json.loads(
            response
            .replace(
                "```json",
                "",
            )
            .replace(
                "```",
                "",
            )
            .strip()
        )

    except Exception:

        logger.warning(
            "Plan reasoning returned invalid JSON."
        )

        return {
            "objective": "",
            "valid": True,
            "dependencies": [],
            "missing_information": [],
            "risks": [],
            "verification_requirements": [],
            "recommended_synthesis": response,
            "confidence": 0.3,
        }


def reason(
    question: str,
    context: dict,
    plan: dict,
):
    """
    Legacy-compatible final reasoning function.
    """

    prompt = """
You are Falcon AI's Reasoning Engine.

Use the supplied plan and context to reason about the user's
question.

Do not invent facts.

Distinguish evidence from assumptions.

Produce a strong draft answer that can later be reviewed
by Falcon's Reflection Engine.

Return ONLY the draft answer.
"""

    prompt += (
        "\n\nUser Question:\n"
        + question
        + "\n\nPlan:\n"
        + json.dumps(
            plan,
            ensure_ascii=False,
            default=str,
        )
        + "\n\nContext:\n"
        + json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )
    )

    return ask_ai(
        prompt
    )