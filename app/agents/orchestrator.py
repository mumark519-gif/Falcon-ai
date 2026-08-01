from app.agents.router import classify_agent
from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT
from app.agents.planner import create_plan
from app.ai_service import ask_ai
from app.core.logger import logger
from app.agents.execution_engine import execute_plan

from app.services.research_context_builder import (
    build_research_context,
)
from app.services.memory_search import (
    search_memories,
)


def run_business_agent(question: str):

    prompt = (
        BUSINESS_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


def run_coding_agent(question: str):

    prompt = (
        CODING_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


def run_investment_agent(question: str):

    prompt = (
        INVESTMENT_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


def run_research_agent(question: str):

    prompt = (
        RESEARCH_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)

def orchestrate(
    db,
    username: str,
    question: str,
):

    try:

        # Create execution plan
        plan = create_plan(question)

        memories = search_memories(
            db,
            username,
            question,
        )

        execution_results = execute_plan(
            username=username,
            plan=plan,
            question=question,
        )

        tool_results = execution_results["tools"]
        results = execution_results["agents"]
        shared_context = execution_results["context"]

        research_context = build_research_context(
            tool_results.get(
                "web",
                [],
            )
        )

        synthesis_prompt = f"""
You are Falcon AI.

Execution Plan:

{plan}

Research Context:

{research_context}

Tool Results:

{tool_results}

Agent Results:

{results}

Shared Context:

{shared_context}

Combine the agent results into one clear,
accurate, non-repetitive answer.

If only one agent was used,
simply improve its answer.

If multiple agents were used,
merge them naturally.
"""

        return ask_ai(synthesis_prompt)

    except Exception as e:

        logger.exception(
            "Orchestrator failed."
        )

        return (
            "I'm sorry, but I encountered an internal "
            "error while processing your request. "
            "Please try again."
        )