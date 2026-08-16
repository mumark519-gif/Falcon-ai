from __future__ import annotations

import time
from typing import Any, Callable

from app.core.logger import logger

from app.tools.tool_registry import registry
from app.tools.tool_result import ToolResult
from app.tools.tool_policy import validate_permission


MAX_RETRIES = 2


# ============================================================
# TOOL ADAPTERS
# ============================================================

def _web_search(
    username: str,
    query: str,
):
    from app.tools.web_search_tool import web_search_tool

    return web_search_tool(query)


def _document_search(
    username: str,
    query: str,
):
    from app.tools.document_tool import document_search_tool

    return document_search_tool(
        username=username,
        query=query,
    )


def _python(
    username: str,
    query: str,
):
    from app.tools.python_tool import python_tool

    return python_tool(query)


def _browser(
    username: str,
    query: str,
):
    from app.tools.browser_tool import browser_tool

    return browser_tool(query)


# ============================================================
# DEFAULT TOOL REGISTRATION
# ============================================================

def register_default_tools() -> None:
    """
    Register Falcon's built-in tools.

    Safe to call repeatedly.
    """

    # Do not return early here based only on one tool.
    #
    # This makes registration robust if the registry was
    # partially initialized.
    #
    # Each registration is protected independently.

    if not registry.exists("web_search"):

        registry.register(
            name="web_search",
            description=(
                "Search the public web for current, "
                "external, or time-sensitive information."
            ),
            executor=_web_search,
            requires_permission=False,
            retryable=True,
        )

    if not registry.exists("document_search"):

        registry.register(
            name="document_search",
            description=(
                "Search documents and knowledge uploaded "
                "by the user."
            ),
            executor=_document_search,
            requires_permission=False,
            retryable=True,
        )

    if not registry.exists("python"):

        registry.register(
            name="python",
            description=(
                "Execute Python for calculations, "
                "data processing, analysis, and computation."
            ),
            executor=_python,
            requires_permission=False,
            retryable=False,
        )

    if not registry.exists("browser"):

        registry.register(
            name="browser",
            description=(
                "Interact with or retrieve information "
                "from supported web pages."
            ),
            executor=_browser,
            requires_permission=True,
            retryable=True,
        )


# ============================================================
# RESULT NORMALIZATION
# ============================================================

def _normalize_result(
    tool: str,
    result: Any,
    attempts: int,
    duration_ms: float,
) -> dict:
    """
    Convert any tool output into Falcon's standard
    structured result format.

    IMPORTANT:

    A nested tool result containing status='error',
    status='failed', or another failure state must remain
    a failure.

    It must never be incorrectly converted into a successful
    ToolResult merely because the outer Python object is a dict.
    """

    # --------------------------------------------------------
    # Canonical ToolResult
    # --------------------------------------------------------

    if isinstance(
        result,
        ToolResult,
    ):

        result.attempts = attempts

        normalized = result.to_dict()

    # --------------------------------------------------------
    # Dictionary result
    # --------------------------------------------------------

    elif isinstance(
        result,
        dict,
    ):

        result_status = str(
            result.get(
                "status",
                "",
            )
        ).strip().lower()

        # ----------------------------------------------------
        # Explicit failure / blocked / permission state
        # ----------------------------------------------------

        if result_status in {
            "error",
            "failed",
            "failure",
            "blocked",
            "permission_required",
        }:

            normalized = dict(
                result
            )

            normalized.setdefault(
                "tool",
                tool,
            )

            normalized["status"] = (
                result_status
            )

            normalized["attempts"] = (
                attempts
            )

        # ----------------------------------------------------
        # Explicit success
        # ----------------------------------------------------

        elif result_status in {
            "success",
            "complete",
            "completed",
        }:

            normalized = dict(
                result
            )

            normalized.setdefault(
                "tool",
                tool,
            )

            normalized["status"] = (
                result_status
            )

            normalized["attempts"] = (
                attempts
            )

        # ----------------------------------------------------
        # Legacy success/failure format
        # ----------------------------------------------------

        elif "success" in result:

            if result.get(
                "success",
                False,
            ):

                normalized = (
                    ToolResult.success(
                        tool=tool,
                        output=result.get(
                            "output"
                        ),
                        attempts=attempts,
                    ).to_dict()
                )

            else:

                normalized = (
                    ToolResult.failure(
                        tool=tool,
                        error=result.get(
                            "error",
                            "Tool execution failed.",
                        ),
                        attempts=attempts,
                    ).to_dict()
                )

        # ----------------------------------------------------
        # Unknown dictionary
        # ----------------------------------------------------

        else:

            normalized = (
                ToolResult.success(
                    tool=tool,
                    output=result,
                    attempts=attempts,
                ).to_dict()
            )

    # --------------------------------------------------------
    # Raw result
    # --------------------------------------------------------

    else:

        normalized = (
            ToolResult.success(
                tool=tool,
                output=result,
                attempts=attempts,
            ).to_dict()
        )

    # --------------------------------------------------------
    # Execution timing
    # --------------------------------------------------------

    normalized["duration_ms"] = round(
        duration_ms,
        2,
    )

    return normalized


# ============================================================
# TOOL DEFINITION VALIDATION
# ============================================================

def _validate_tool_definition(
    tool_name: str,
) -> tuple[bool, str]:
    """
    Verify that a registered tool has a usable
    executor definition.
    """

    definition = registry.get(
        tool_name
    )

    if definition is None:

        return (
            False,
            f"Unknown tool: {tool_name}",
        )

    executor = getattr(
        definition,
        "executor",
        None,
    )

    if not callable(
        executor
    ):

        return (
            False,
            f"Tool '{tool_name}' has no valid executor.",
        )

    return True, ""


# ============================================================
# SINGLE TOOL EXECUTION
# ============================================================

def execute_tool(
    username: str,
    tool: str,
    tool_input: str,
    approved: bool = False,
) -> dict:
    """
    Execute one Falcon tool safely.

    Flow:

    1. Register tools
    2. Validate tool name
    3. Validate tool definition
    4. Validate input
    5. Check permissions
    6. Execute with retry policy
    7. Normalize result
    8. Return structured execution result
    """

    register_default_tools()

    tool_name = (
        str(tool).strip().lower()
        if tool
        else ""
    )

    # --------------------------------------------------------
    # Tool name validation
    # --------------------------------------------------------

    if not tool_name:

        logger.warning(
            "Tool execution rejected: missing tool name."
        )

        return ToolResult.failure(
            tool="unknown",
            error="Tool name is missing.",
        ).to_dict()

    # --------------------------------------------------------
    # Tool definition validation
    # --------------------------------------------------------

    (
        valid_definition,
        definition_error,
    ) = _validate_tool_definition(
        tool_name
    )

    if not valid_definition:

        logger.warning(
            "Tool execution rejected: %s",
            definition_error,
        )

        return ToolResult.failure(
            tool=tool_name,
            error=definition_error,
        ).to_dict()

    definition = registry.get(
        tool_name
    )

    # --------------------------------------------------------
    # Defensive registry validation
    # --------------------------------------------------------

    if definition is None:

        logger.error(
            "Tool '%s' disappeared from the registry "
            "after validation.",
            tool_name,
        )

        return ToolResult.failure(
            tool=tool_name,
            error=(
                f"Tool '{tool_name}' is not registered."
            ),
        ).to_dict()

    executor = getattr(
        definition,
        "executor",
        None,
    )

    if not callable(
        executor
    ):

        logger.error(
            "Tool '%s' has no callable executor.",
            tool_name,
        )

        return ToolResult.failure(
            tool=tool_name,
            error=(
                f"Tool '{tool_name}' has no valid executor."
            ),
        ).to_dict()

    # --------------------------------------------------------
    # Input validation
    # --------------------------------------------------------

    if (
        tool_input is None
        or not str(tool_input).strip()
    ):

        return ToolResult.failure(
            tool=tool_name,
            error="Tool input is empty.",
        ).to_dict()

    tool_input = str(
        tool_input
    ).strip()

    # --------------------------------------------------------
    # Permission validation
    # --------------------------------------------------------

    try:

        permission = validate_permission(
            tool_name,
            approved=approved,
            tool_input=tool_input,
        )

    except TypeError:

        # Backward compatibility with older permission
        # functions that do not accept tool_input.
        try:

            permission = validate_permission(
                tool_name,
                approved=approved,
            )

        except Exception as exc:

            logger.exception(
                "Permission validation failed for tool '%s'.",
                tool_name,
            )

            return ToolResult.failure(
                tool=tool_name,
                error=(
                    "Tool permission validation failed: "
                    + str(exc)
                ),
            ).to_dict()

    except Exception as exc:

        logger.exception(
            "Permission validation failed for tool '%s'.",
            tool_name,
        )

        return ToolResult.failure(
            tool=tool_name,
            error=(
                "Tool permission validation failed: "
                + str(exc)
            ),
        ).to_dict()

    if not permission.get(
        "allowed",
        False,
    ):

        if permission.get(
            "requires_permission",
            False,
        ):

            logger.info(
                "Tool '%s' requires user permission.",
                tool_name,
            )

            return ToolResult.permission_required(
                tool_name
            ).to_dict()

        return ToolResult.blocked(
            tool=tool_name,
            reason=permission.get(
                "reason",
                "Tool execution was blocked.",
            ),
        ).to_dict()

    # --------------------------------------------------------
    # Retry policy
    # --------------------------------------------------------

    retryable = bool(
        getattr(
            definition,
            "retryable",
            False,
        )
    )

    if retryable:

        max_attempts = (
            MAX_RETRIES + 1
        )

    else:

        max_attempts = 1

    last_error: str | None = None

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        started_at = time.perf_counter()

        try:

            logger.info(
                "Executing Falcon tool '%s' "
                "attempt %s/%s.",
                tool_name,
                attempt,
                max_attempts,
            )

            result = executor(
                username=username,
                query=tool_input,
            )

            duration_ms = (
                time.perf_counter()
                - started_at
            ) * 1000

            normalized = _normalize_result(
                tool=tool_name,
                result=result,
                attempts=attempt,
                duration_ms=duration_ms,
            )

            logger.info(
                "Tool '%s' completed with status '%s' "
                "in %.2f ms.",
                tool_name,
                normalized.get(
                    "status",
                    "unknown",
                ),
                duration_ms,
            )

            return normalized

        except Exception as exc:

            duration_ms = (
                time.perf_counter()
                - started_at
            ) * 1000

            last_error = str(
                exc
            )

            logger.exception(
                "Tool '%s' failed on attempt %s/%s "
                "after %.2f ms.",
                tool_name,
                attempt,
                max_attempts,
                duration_ms,
            )

            if attempt < max_attempts:

                logger.warning(
                    "Retrying tool '%s'.",
                    tool_name,
                )

                continue

            return ToolResult.failure(
                tool=tool_name,
                error=(
                    last_error
                    or "Tool execution failed."
                ),
                attempts=attempt,
            ).to_dict()

    # --------------------------------------------------------
    # Defensive fallback
    # --------------------------------------------------------

    return ToolResult.failure(
        tool=tool_name,
        error=(
            last_error
            or "Tool execution failed unexpectedly."
        ),
        attempts=max_attempts,
    ).to_dict()


# ============================================================
# MULTI-TOOL EXECUTION
# ============================================================

def execute_tools(
    username: str,
    question: str,
    tools: list[str] | None = None,
    approved: bool = False,
) -> dict:
    """
    Execute multiple tools against the same question.

    Each tool is isolated so one failure does not
    automatically destroy the remaining tool executions.
    """

    register_default_tools()

    if not tools:

        from app.tools.tool_selector import select_tools

        tools = select_tools(
            question
        )

        if not tools:

            return {
                "status": "empty",
                "tools": {},
                "completed": 0,
                "failed": 0,
                "total": 0,
            }

    results: dict[str, dict] = {}

    completed = 0
    failed = 0

    for tool in tools:

        tool_name = (
            str(tool).strip().lower()
            if tool
            else ""
        )

        if not tool_name:
            continue

        try:

            result = execute_tool(
                username=username,
                tool=tool_name,
                tool_input=question,
                approved=approved,
            )

        except Exception as exc:

            logger.exception(
                "Unexpected multi-tool failure "
                "for '%s'.",
                tool_name,
            )

            result = ToolResult.failure(
                tool=tool_name,
                error=str(exc),
            ).to_dict()

        results[
            tool_name
        ] = result

        status = str(
            result.get(
                "status",
                "",
            )
        ).lower()

        if status in {
            "success",
            "complete",
            "completed",
        }:

            completed += 1

        else:

            failed += 1

    total = len(
        results
    )

    if total == 0:

        overall_status = "empty"

    elif failed == 0:

        overall_status = "complete"

    elif completed > 0:

        overall_status = "partial"

    else:

        overall_status = "failed"

    # Historical API compatibility.
    if "web_search" in results:

        results.setdefault(
            "web",
            results["web_search"],
        )

    response = {
        "status": overall_status,
        "tools": results,
        "completed": completed,
        "failed": failed,
        "total": total,
    }

    if "web_search" in results:

        response["web"] = (
            results["web_search"]
        )

    elif "web" in results:

        response["web"] = (
            results["web"]
        )

    return response


# ============================================================
# TOOL DISCOVERY
# ============================================================

def get_available_tools() -> list[dict]:
    """
    Return the tools currently registered with Falcon.

    This gives the planner/reasoning layer a clean way to
    discover available capabilities.
    """

    register_default_tools()

    tools = []

    for name in (
        "web_search",
        "document_search",
        "python",
        "browser",
    ):

        definition = registry.get(
            name
        )

        if definition is None:
            continue

        tools.append(
            {
                "name": name,
                "description": getattr(
                    definition,
                    "description",
                    "",
                ),
                "requires_permission": bool(
                    getattr(
                        definition,
                        "requires_permission",
                        False,
                    )
                ),
                "retryable": bool(
                    getattr(
                        definition,
                        "retryable",
                        False,
                    )
                ),
            }
        )

    return tools