import asyncio

from app.agents.task_executor import (
    run_business_agent,
    run_coding_agent,
    run_investment_agent,
    run_research_agent,
)
async def run_async(
    func,
    question,
):
    return await asyncio.to_thread(
        func,
        question,
    )
async def execute_parallel(tasks):

    coroutines = []

    for task in tasks:

        agent = task["agent"]
        question = task["task"]

        if agent == "BUSINESS":
            coroutines.append(
                run_async(
                    run_business_agent,
                    question,
                )
            )

        elif agent == "CODING":
            coroutines.append(
                run_async(
                    run_coding_agent,
                    question,
                )
            )

        elif agent == "INVESTMENT":
            coroutines.append(
                run_async(
                    run_investment_agent,
                    question,
                )
            )

        elif agent == "RESEARCH":
            coroutines.append(
                run_async(
                    run_research_agent,
                    question,
                )
            )

    return await asyncio.gather(*coroutines)