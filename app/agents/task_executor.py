from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT

from app.core.logger import logger

from app.agents.agent_runner import (
    run_intelligent_agent,
)

from app.agents.context_selector import (
    select_context,
)


AGENT_RUNNERS = {
    "BUSINESS": (
        BUSINESS_PROMPT,
        "business",
        "Business agent failed.",
        "Business agent could not complete the task.",
    ),

    "CODING": (
        CODING_PROMPT,
        "coding",
        "Coding agent failed.",
        "Coding agent could not complete the task.",
    ),

    "INVESTMENT": (
        INVESTMENT_PROMPT,
        "investment",
        "Investment agent failed.",
        "Investment agent could not complete the task.",
    ),

    "RESEARCH": (
        RESEARCH_PROMPT,
        "research",
        "Research agent failed.",
        "Research agent could not complete the task.",
    ),
}


def execute_tasks(
    plan: dict,
    question: str,
    context: dict | None = None,
    memories=None,
):
    """
    Execute specialist agents from a plan.

    Every specialist produces a structured result.
    """

    if context is None:
        context = {}

    if memories is None:
        memories = []

    results = {}

    steps = plan.get(
        "steps",
        [],
    )

    for step in steps:

        step_type = step.get(
            "type",
            "agent",
        )

        if step_type != "agent":
            continue

        agent = step.get(
            "agent",
            "",
        ).upper()

        configuration = AGENT_RUNNERS.get(
            agent
        )

        if configuration is None:
            logger.warning(
                "Unknown agent requested: %s",
                agent,
            )
            continue

        (
            system_prompt,
            result_key,
            error_log,
            error_message,
        ) = configuration

        agent_context = select_context(
            agent,
            context,
        )

        task = step.get(
            "task",
            question,
        )

        try:

            result = run_intelligent_agent(
                agent=agent,
                system_prompt=system_prompt,
                question=task,
                context=agent_context,
                memories=memories,
            )

            results[result_key] = result

        except Exception:

            logger.exception(
                error_log
            )

            results[result_key] = {
                "agent": agent,
                "status": "failed",
                "answer": error_message,
                "key_findings": [],
                "evidence": [],
                "assumptions": [],
                "uncertainties": [
                    error_message
                ],
                "risks": [],
                "recommendations": [],
                "confidence": 0.0,
            }

    return results