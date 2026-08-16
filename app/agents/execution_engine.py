from __future__ import annotations

from typing import Any

from app.agents.shared_context import SharedContext
from app.agents.agent_runner import run_intelligent_agent
from app.agents.context_selector import select_context

from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT

from app.agents.tool_executor import execute_tool_step
from app.core.logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

AGENT_CONFIG = {
    "BUSINESS": BUSINESS_PROMPT,
    "CODING": CODING_PROMPT,
    "INVESTMENT": INVESTMENT_PROMPT,
    "RESEARCH": RESEARCH_PROMPT,
}

VALID_STEP_TYPES = {
    "agent",
    "tool",
}

MAX_AGENT_RETRIES = 1
MAX_STEP_RETRIES = 1


# ============================================================
# CONTEXT STORAGE
# ============================================================

def _store_tool_result(
    context: SharedContext,
    tool_name: str,
    result: Any,
) -> str:
    """
    Store a tool result inside Falcon's shared context.
    """

    mapping = {
        "web_search": "web",
        "document_search": "documents",
        "python": "python",
        "browser": "browser",
    }

    key = mapping.get(
        tool_name,
        tool_name or "tool",
    )

    context.set(
        key,
        result,
        source="tool",
        priority=10,
    )

    return key


def _store_agent_result(
    context: SharedContext,
    agent_name: str,
    result: Any,
) -> str:
    """
    Store an agent result inside Falcon's shared context.
    """

    key = agent_name.lower()

    context.set(
        key,
        result,
        source="agent",
        agent=agent_name.upper(),
        priority=20,
    )

    return key


# ============================================================
# STEP VALIDATION
# ============================================================

def _validate_step(
    step: Any,
) -> tuple[bool, str]:
    """
    Validate one execution step before execution.
    """

    if not isinstance(step, dict):
        return (
            False,
            "Execution step must be a dictionary.",
        )

    step_type = str(
        step.get(
            "type",
            "",
        )
    ).strip().lower()

    if step_type not in VALID_STEP_TYPES:
        return (
            False,
            f"Unsupported execution step type: {step_type}",
        )

    if step_type == "agent":

        agent = str(
            step.get(
                "agent",
                "",
            )
        ).strip().upper()

        if not agent:
            return (
                False,
                "Agent name is missing.",
            )

        if agent not in AGENT_CONFIG:
            return (
                False,
                f"Unknown agent: {agent}",
            )

        task = str(
            step.get(
                "task",
                "",
            )
        ).strip()

        if not task:
            return (
                False,
                "Agent task is empty.",
            )

    if step_type == "tool":

        tool = str(
            step.get(
                "tool",
                "",
            )
        ).strip().lower()

        if not tool:
            return (
                False,
                "Tool name is missing.",
            )

        tool_input = str(
            step.get(
                "input",
                "",
            )
        ).strip()

        if not tool_input:
            return (
                False,
                "Tool input is empty.",
            )

    return True, ""


# ============================================================
# AGENT EXECUTION
# ============================================================

def _execute_agent_step(
    username: str,
    step: dict,
    context: SharedContext,
    memories: list | None,
) -> dict:
    """
    Execute one specialist agent using the relevant shared
    context and memory.
    """

    agent = str(
        step.get(
            "agent",
            "",
        )
    ).strip().upper()

    system_prompt = AGENT_CONFIG.get(
        agent
    )

    if not system_prompt:

        return {
            "agent": agent,
            "status": "error",
            "error": f"Unknown agent: {agent}",
        }

    task = str(
        step.get(
            "task",
            "",
        )
    ).strip()

    agent_context = select_context(
        agent,
        context.all(),
    )

    memories = memories or []

    last_result: Any = None
    last_error: str | None = None

    for attempt in range(
        1,
        MAX_AGENT_RETRIES + 2,
    ):

        try:

            logger.info(
                "Executing agent '%s' attempt %s",
                agent,
                attempt,
            )

            result = run_intelligent_agent(
                agent=agent,
                system_prompt=system_prompt,
                question=task,
                context=agent_context,
                memories=memories,
            )

            last_result = result

            if isinstance(result, dict):

                result.setdefault(
                    "agent",
                    agent,
                )

                result.setdefault(
                    "status",
                    "complete",
                )

                result.setdefault(
                    "attempts",
                    attempt,
                )

                return result

            return {
                "agent": agent,
                "status": "complete",
                "answer": str(result),
                "attempts": attempt,
            }

        except Exception as exc:

            last_error = str(exc)

            logger.exception(
                "Agent '%s' failed on attempt %s.",
                agent,
                attempt,
            )

    return {
        "agent": agent,
        "status": "error",
        "error": (
            last_error
            or "Agent execution failed."
        ),
        "attempts": (
            MAX_AGENT_RETRIES + 1
        ),
        "result": last_result,
    }


# ============================================================
# TOOL EXECUTION
# ============================================================

def _execute_tool_step(
    username: str,
    step: dict,
    context: SharedContext,
) -> dict:
    """
    Execute one tool step.

    Tool permission and validation remain handled by the
    tool-executor layer.
    """

    tool_name = str(
        step.get(
            "tool",
            "",
        )
    ).strip().lower()

    try:

        logger.info(
            "Executing tool '%s'.",
            tool_name,
        )

        result = execute_tool_step(
            username=username,
            step=step,
        )

        _store_tool_result(
            context,
            tool_name,
            result,
        )

        if isinstance(result, dict):

            status = result.get(
                "status",
                "success",
            )

        else:

            status = "success"

        return {
            "type": "tool",
            "tool": tool_name,
            "status": status,
            "result": result,
        }

    except Exception as exc:

        logger.exception(
            "Tool '%s' execution failed.",
            tool_name,
        )

        error_result = {
            "tool": tool_name,
            "status": "error",
            "error": str(exc),
        }

        _store_tool_result(
            context,
            tool_name,
            error_result,
        )

        return {
            "type": "tool",
            "tool": tool_name,
            "status": "error",
            "result": error_result,
            "error": str(exc),
        }


# ============================================================
# GENERIC STEP EXECUTION
# ============================================================

def _execute_step(
    username: str,
    step: dict,
    context: SharedContext,
    memories: list | None,
) -> dict:
    """
    Execute one validated Falcon execution step.
    """

    valid, error = _validate_step(
        step
    )

    if not valid:

        return {
            "type": str(
                step.get(
                    "type",
                    "unknown",
                )
            ).lower()
            if isinstance(step, dict)
            else "unknown",
            "status": "error",
            "error": error,
        }

    step_type = str(
        step.get(
            "type",
            "",
        )
    ).strip().lower()

    if step_type == "tool":

        return _execute_tool_step(
            username=username,
            step=step,
            context=context,
        )

    if step_type == "agent":

        agent_name = str(
            step.get(
                "agent",
                "",
            )
        ).strip().upper()

        result = _execute_agent_step(
            username=username,
            step=step,
            context=context,
            memories=memories,
        )

        _store_agent_result(
            context,
            agent_name,
            result,
        )

        return {
            "type": "agent",
            "agent": agent_name,
            "status": result.get(
                "status",
                "complete",
            )
            if isinstance(result, dict)
            else "complete",
            "result": result,
        }

    return {
        "type": step_type,
        "status": "error",
        "error": (
            f"Unsupported execution step: "
            f"{step_type}"
        ),
    }


# ============================================================
# EXECUTION STATUS
# ============================================================

def _is_successful_execution(
    execution: dict,
) -> bool:
    """
    Determine whether a step completed successfully.
    """

    if not isinstance(
        execution,
        dict,
    ):
        return False

    status = str(
        execution.get(
            "status",
            "",
        )
    ).lower()

    return status in {
        "success",
        "complete",
        "completed",
    }


# ============================================================
# MAIN PLAN EXECUTION
# ============================================================

def execute_plan(
    username: str,
    plan: dict,
    question: str,
    use_web: bool = False,
    use_documents: bool = False,
    memories=None,
):
    """
    Execute a complete Falcon plan.

    Responsibilities:

    1. Validate the plan.
    2. Create shared context.
    3. Execute tools and specialist agents.
    4. Propagate results through shared context.
    5. Preserve execution order.
    6. Isolate individual failures.
    7. Retry failed steps where appropriate.
    8. Return structured execution state.

    Actual planning is handled by planner.py.
    Workflow preparation is handled by workflow_engine.py.
    Tool permissions are handled by tool_executor.py.
    Agent intelligence is handled by agent_runner.py.
    """

    context = SharedContext()

    results = {
        "status": "running",
        "question": question,
        "tools": {},
        "agents": {},
        "steps": [],
        "completed_steps": 0,
        "failed_steps": 0,
        "total_steps": 0,
    }

    if not isinstance(
        plan,
        dict,
    ):

        logger.error(
            "Execution plan is not a dictionary."
        )

        results["status"] = "error"

        results["error"] = (
            "Execution plan must be a dictionary."
        )

        return results

    steps = plan.get(
        "steps",
        [],
    )

    if not isinstance(
        steps,
        list,
    ):

        logger.error(
            "Execution plan steps are invalid."
        )

        results["status"] = "error"

        results["error"] = (
            "Execution plan steps must be a list."
        )

        return results

    results["total_steps"] = len(
        steps
    )

    if not steps:

        logger.warning(
            "Execution plan contains no steps."
        )

        results["status"] = "empty"

        return results

    memories = memories or []

    # --------------------------------------------------------
    # Sequential execution
    # --------------------------------------------------------

    for index, step in enumerate(
        steps,
        start=1,
    ):

        logger.info(
            "Executing Falcon plan step %s/%s.",
            index,
            len(steps),
        )

        execution = None

        # ----------------------------------------------------
        # Step retry loop
        # ----------------------------------------------------

        for attempt in range(
            1,
            MAX_STEP_RETRIES + 2,
        ):

            try:

                execution = _execute_step(
                    username=username,
                    step=step,
                    context=context,
                    memories=memories,
                )

                if _is_successful_execution(
                    execution
                ):

                    break

                result_data = execution.get(
                    "result",
                    {},
                )

                if isinstance(
                    result_data,
                    dict,
                ):

                    result_status = str(
                        result_data.get(
                            "status",
                            "",
                        )
                    ).lower()

                    if result_status in {
                        "permission_required",
                        "blocked",
                    }:

                        break

            except Exception as exc:

                logger.exception(
                    "Unexpected failure in plan step %s "
                    "attempt %s.",
                    index,
                    attempt,
                )

                execution = {
                    "type": (
                        step.get(
                            "type",
                            "unknown",
                        )
                        if isinstance(
                            step,
                            dict,
                        )
                        else "unknown"
                    ),
                    "status": "error",
                    "error": str(exc),
                }

            if attempt <= MAX_STEP_RETRIES:

                logger.warning(
                    "Retrying Falcon plan step %s "
                    "(attempt %s/%s).",
                    index,
                    attempt + 1,
                    MAX_STEP_RETRIES + 1,
                )

        # ----------------------------------------------------
        # Safety fallback
        # ----------------------------------------------------

        if execution is None:

            execution = {
                "type": (
                    step.get(
                        "type",
                        "unknown",
                    )
                    if isinstance(
                        step,
                        dict,
                    )
                    else "unknown"
                ),
                "status": "error",
                "error": (
                    "Step produced no execution result."
                ),
            }

        # ----------------------------------------------------
        # Add execution metadata
        # ----------------------------------------------------

        execution["step_index"] = index
        execution["attempts"] = execution.get(
            "attempts",
            1,
        )

        results["steps"].append(
            execution
        )

        # ----------------------------------------------------
        # Store top-level result
        # ----------------------------------------------------

        execution_type = execution.get(
            "type",
            "",
        )

        if execution_type == "tool":

            tool_name = execution.get(
                "tool",
                "tool",
            )

            results["tools"][
                tool_name
            ] = execution.get(
                "result"
            )

        elif execution_type == "agent":

            agent_name = execution.get(
                "agent",
                "agent",
            )

            results["agents"][
                str(
                    agent_name
                ).lower()
            ] = execution.get(
                "result"
            )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        if _is_successful_execution(
            execution
        ):

            results[
                "completed_steps"
            ] += 1

        else:

            results[
                "failed_steps"
            ] += 1

    # ========================================================
    # FINAL EXECUTION STATUS
    # ========================================================

    if results["failed_steps"] == 0:

        results["status"] = "complete"

    elif results["completed_steps"] > 0:

        results["status"] = (
            "partial"
        )

    else:

        results["status"] = "failed"

    # ========================================================
    # FINAL SHARED CONTEXT
    # ========================================================

    results["context_snapshot"] = (
        context.all()
    )

    results["context_entries"] = (
        context.entries()
    )

    logger.info(
        "Falcon plan execution finished: "
        "status=%s completed=%s failed=%s total=%s",
        results["status"],
        results["completed_steps"],
        results["failed_steps"],
        results["total_steps"],
    )

    return results