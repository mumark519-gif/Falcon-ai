from app.tools.tool_manager import execute_tools
from app.agents.task_executor import execute_tasks
from app.tools.tool_executor import execute_tool_step
from app.agents.shared_context import (
    SharedContext,
)


def execute_plan(
    username: str,
    plan: dict,
    question: str,
):

    tool_results = {}
    agent_results = {}

    context = SharedContext()

    steps = plan.get("steps", [])

    # Backward compatibility:
    # if no step types exist, use the old execution.
    if not any("type" in step for step in steps):

        tool_results = execute_tools(
            username=username,
            question=question,
        )

        agent_results = execute_tasks(
            plan=plan,
            question=question,
        )

        return {
            "tools": tool_results,
            "agents": agent_results,
        }

    for step in steps:

        step_type = step.get(
            "type",
            "agent",
        )

        if step_type == "tool":

            result = execute_tool_step(
               username=username,
               step=step,
            )

            tool_name = step.get(
                "tool",
                "",
            )

            if result is not None:

                if tool_name == "web_search":

                    tool_results["web"] = result
                    context.set(
                        "web",
                        result,
                    )

                elif tool_name == "document_search":

                    tool_results["documents"] = result
                    context.set(
                        "documents",
                        result,
                    )

                elif tool_name == "python":

                    tool_results["python"] = result
                    context.set(
                        "python",
                        result,
                    )

                elif tool_name == "browser":

                    tool_results["browser"] = result
                    context.set(
                        "browser",
                        result,
                    )

        elif step_type == "agent":

            agent_plan = {
                "steps": [
                    step
               ]
            }

            result = execute_tasks(
                plan=agent_plan,
                question=question,
                context=context.all(),
            )

            agent_results.update(result)

            for key, value in result.items():

                context.set(
                    key,
                    value,
            )

    return {
        "tools": tool_results,
        "agents": agent_results,
        "context": context.all(),
    }