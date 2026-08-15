from __future__ import annotations

from typing import Any

from app.agents.rule_engine import (
    allowed_tool,
    select_allowed_tools,
    tool_score,
)

from app.agents.tool_reasoner import (
    decide_tool_usage,
    validate_tool_request,
)

from app.agents.tool_executor import (
    execute_tool_step,
)

from app.core.logger import logger


class ToolManager:
    """
    Falcon's central tool-management interface.

    Responsibilities:

    1. Determine which tools may be relevant.
    2. Ask the tool reasoner for a higher-level decision.
    3. Validate tool requests.
    4. Execute approved tool steps.
    5. Keep tool execution centralized.

    Individual tools remain implemented in their own
    execution layer.
    """

    def available_tools(
        self,
        question: str,
    ) -> list[str]:
        """
        Return tools with a positive deterministic signal.
        """

        return select_allowed_tools(
            question
        )

    def score(
        self,
        tool: str,
        question: str,
    ) -> int:
        """
        Return deterministic relevance score.
        """

        return tool_score(
            tool,
            question,
        )

    def allowed(
        self,
        tool: str,
        question: str,
    ) -> bool:
        """
        Determine whether a tool is appropriate.
        """

        return allowed_tool(
            tool,
            question,
        )

    def reason(
        self,
        question: str,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Ask Falcon's tool-reasoning layer which tools
        should actually be used.
        """

        return decide_tool_usage(
            question=question,
            plan=plan,
        )

    def validate(
        self,
        tool: str,
        tool_input: str,
    ) -> dict[str, Any]:
        """
        Validate a proposed tool request.
        """

        return validate_tool_request(
            tool=tool,
            tool_input=tool_input,
        )

    def execute(
        self,
        username: str,
        step: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute one tool request through Falcon's
        existing tool executor.
        """

        try:
            return execute_tool_step(
                username=username,
                step=step,
            )

        except Exception as exc:
            logger.exception(
                "ToolManager execution failed."
            )

            return {
                "status": "error",
                "tool": step.get(
                    "tool",
                    "",
                ),
                "error": str(exc),
            }


def create_tool_manager() -> ToolManager:
    """
    Create a ToolManager instance.
    """

    return ToolManager()