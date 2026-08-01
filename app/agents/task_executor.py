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

        if agent == "BUSINESS":

            try:
                results["business"] = run_business_agent(
                    task,
                    agent_context,
                )

            except Exception:

                logger.exception(
                    "Business agent failed."
                )

                results["business"] = (
                    "Business agent could not complete the task."
                )


        elif agent == "CODING":

            try:
                results["coding"] = (
                    run_coding_agent(
                        task,
                        agent_context,
                    )
                )

            except Exception:

                logger.exception(
                    "Coding agent failed."
               )

                results["coding"] = (
                    "Coding agent could not complete the task."
                )

        elif agent == "INVESTMENT":

            try:
                results["investment"] = (
                    run_investment_agent(
                        task,
                        agent_context,
                    )
                )

            except Exception:

                logger.exception(
                    "Investment agent failed."
                )

                results["investment"] = (
                   "Investment agent could not complete the task."
                )

        elif agent == "RESEARCH":

            try:
                results["research"] = (
                    run_research_agent(
                        task,
                        agent_context,
                    )
                )

            except Exception:

                logger.exception(
                    "Research agent failed."
                )

                results["research"] = (
                    "Research agent could not complete the task."
                )

    return results
