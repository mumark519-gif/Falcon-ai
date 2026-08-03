from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT
from app.core.logger import logger

from app.ai_service import ask_ai

from app.agents.agent_runner import (
    run_agent,
)
from app.agents.context_selector import (
    select_context,
)


def run_business_agent(
    question: str,
    context: dict | None = None,
):

    return run_agent(
        BUSINESS_PROMPT,
        question,
        context,
    )


def run_coding_agent(
    question: str,
    context: dict | None = None,
):

    return run_agent(
        CODING_PROMPT,
        question,
        context,
    )


def run_investment_agent(
    question: str,
    context: dict | None = None,
):

    return run_agent(
        INVESTMENT_PROMPT,
        question,
        context,
    )


def run_research_agent(
    question: str,
    context: dict | None = None,
):

    return run_agent(
        RESEARCH_PROMPT,
        question,
        context,
    )

AGENT_RUNNERS = {
    "BUSINESS": (
        run_business_agent,
        "business",
        "Business agent failed.",
        "Business agent could not complete the task.",
    ),
    "CODING": (
        run_coding_agent,
        "coding",
        "Coding agent failed.",
        "Coding agent could not complete the task.",
    ),
    "INVESTMENT": (
        run_investment_agent,
        "investment",
        "Investment agent failed.",
        "Investment agent could not complete the task.",
    ),
    "RESEARCH": (
        run_research_agent,
        "research",
        "Research agent failed.",
        "Research agent could not complete the task.",
    ),
}

def execute_tasks(
    plan: dict,
    question: str,
    context: dict | None = None,
):
 
    if context is None:
        context = {}
    results = {}

    steps = plan.get("steps", [])

    for step in steps:

        step_type = step.get(
            "type",
            "agent",
        )

        agent = step.get(
            "agent",
            ""
        ).upper()

        agent_context = select_context(
            agent,
            context,
        )

        task = step.get(
            "task",
            question
        )

        runner = AGENT_RUNNERS.get(agent)

        if runner is None:
            continue

        agent_function, result_key, error_log, error_message = runner

        try:

            results[result_key] = agent_function(
                task,
                agent_context,
            )

        except Exception:

            logger.exception(
                error_log,
            )

            results[result_key] = error_message

    return results
