from app.agents.router import classify_agent
from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT
from app.agents.planner import create_plan
from app.ai_service import ask_ai
from app.core.logger import logger
from app.agents.execution_engine import execute_plan

from app.agents.research_engine import (
    build_research_context,
)
from app.services.memory_provider import (
    MemoryProvider,
)

from app.agents.reasoning_engine import (
    reason_about_plan,
)
from app.agents.tool_reasoner import (
    decide_tool_usage,
)
from app.agents.rule_engine import (
    should_use_web,
    should_use_documents,
)
memory_provider = MemoryProvider()


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

        use_web = should_use_web(question)

        use_documents = should_use_documents(question)

        reasoning = reason_about_plan(
            question,
            plan,
        )

        tool_reasoning = decide_tool_usage(
            question,
            plan,
        )

        memories = memory_provider.search(
            db,
            username,
            question,
        )

        execution_results = execute_plan(
            username=username,
            plan=plan,
            question=question,
            use_web=use_web,
            use_documents=use_documents,
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

Reasoning:

{reasoning}

Tool Reasoning:

{tool_reasoning}

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