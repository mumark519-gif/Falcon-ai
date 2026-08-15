"""Compatibility bridge for agent-level tool execution.

The canonical tool execution implementation lives under ``app.tools``.
This module preserves the agent execution API so older/newer orchestration
code can call the same function without duplicating tool registries.
"""
from __future__ import annotations

from typing import Any

from app.tools.tool_executor import execute_tool


def execute_tool_step(
    username: str,
    step: dict[str, Any],
) -> dict[str, Any]:
    """Execute one orchestration tool step through the canonical tool layer."""
    if not isinstance(step, dict):
        return {
            "status": "error",
            "tool": "",
            "error": "Execution step must be a dictionary.",
        }

    tool = str(step.get("tool", "") or "").strip().lower()
    tool_input = step.get("input", "")
    approved = bool(step.get("approved", False))

    return execute_tool(
        username=username,
        tool=tool,
        tool_input=str(tool_input or ""),
        approved=approved,
    )


def execute_tools(
    requests: list[dict[str, Any]],
    username: str = "",
) -> list[dict[str, Any]]:
    """Execute multiple orchestration tool steps independently."""
    if not isinstance(requests, list):
        return [{
            "status": "error",
            "tool": "",
            "error": "Tool requests must be a list.",
        }]

    return [
        execute_tool_step(username=username, step=request)
        for request in requests
    ]
