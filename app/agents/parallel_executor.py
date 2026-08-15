from __future__ import annotations

import asyncio

from app.agents.orchestrator import (
    run_business_agent,
    run_coding_agent,
    run_investment_agent,
    run_research_agent,
)

AGENT_FUNCTIONS = {
    "BUSINESS": run_business_agent,
    "CODING": run_coding_agent,
    "INVESTMENT": run_investment_agent,
    "RESEARCH": run_research_agent,
}


async def run_async(func, question):
    return await asyncio.to_thread(func, question)


async def execute_parallel(tasks):
    coroutines = []
    for task in tasks:
        agent = str(task.get("agent", "")).upper()
        question = task.get("task", "")
        agent_function = AGENT_FUNCTIONS.get(agent)
        if agent_function:
            coroutines.append(run_async(agent_function, question))
    return await asyncio.gather(*coroutines)
