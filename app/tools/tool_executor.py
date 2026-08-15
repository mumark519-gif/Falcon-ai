from __future__ import annotations

from app.tools.tool_manager import (
    execute_tool,
)


def execute_tool_step(
    username: str,
    step: dict,
):

    tool = step.get(
        "tool",
        "",
    )

    tool_input = step.get(
        "input",
        "",
    )

    approved = step.get(
        "approved",
        False,
    )

    return execute_tool(
        username=username,
        tool=tool,
        tool_input=tool_input,
        approved=approved,
    )