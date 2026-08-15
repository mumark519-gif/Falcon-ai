from __future__ import annotations

import json
from typing import Any

from app.ai_service import ask_ai
from app.core.logger import logger


AVAILABLE_TOOLS = {
    "web_search": {
        "description": "Search the web for current or external information.",
        "requires_permission": False,
        "retryable": True,
    },
    "document_search": {
        "description": "Search documents uploaded by the user.",
        "requires_permission": False,
        "retryable": True,
    },
    "python": {
        "description": "Execute Python for calculations and data processing.",
        "requires_permission": True,
        "retryable": True,
    },
    "browser": {
        "description": "Interact with supported web pages or browser tasks.",
        "requires_permission": True,
        "retryable": True,
    },
}


TOOL_REASONER_PROMPT = """
You are Falcon AI's Tool Reasoning Engine.

Your job is to determine whether external tools are required
to solve the user's request and, if so, which tools should be used.

Available tools:

web_search
document_search
python
browser

Rules:

- Do not use tools unnecessarily.
- Use web_search for current, external, or time-sensitive information.
- Use document_search when the user's uploaded documents are relevant.
- Use python for calculations, structured data processing, or computation.
- Use browser only when actual browser interaction is required.
- Never claim a tool was used unless it actually executes.
- Prefer the smallest number of tools necessary.
- Tool inputs must be concrete and useful.

Return ONLY valid JSON.

Format:

{
    "use_tools": true,
    "steps": [
        {
            "tool": "web_search",
            "input": "specific search query",
            "reason": "why this tool is needed"
        }
    ],
    "confidence": 0.0
}
"""


def _parse_json(
    response: str,
) -> dict[str, Any]:
    text = (response or "").strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except Exception:
        pass

    return {
        "use_tools": False,
        "steps": [],
        "confidence": 0.0,
    }


def decide_tool_usage(
    question: str,
    plan: dict,
):
    prompt = (
        TOOL_REASONER_PROMPT
        + "\n\nUser Request:\n"
        + question
        + "\n\nExisting Plan:\n"
        + json.dumps(
            plan,
            ensure_ascii=False,
            default=str,
        )
    )

    try:
        response = ask_ai(prompt)

        result = _parse_json(response)

        result.setdefault(
            "use_tools",
            False,
        )

        result.setdefault(
            "steps",
            [],
        )

        result.setdefault(
            "confidence",
            0.5,
        )

        return result

    except Exception:
        logger.exception(
            "Tool reasoning failed."
        )

        return {
            "use_tools": False,
            "steps": [],
            "confidence": 0.0,
        }


def validate_tool_request(
    tool: str,
    tool_input: str,
):
    """
    Validate a tool request before execution.
    """

    tool_name = (tool or "").strip().lower()

    if tool_name not in AVAILABLE_TOOLS:
        return {
            "allowed": False,
            "reason": "Unknown tool.",
        }

    if not tool_input or not str(tool_input).strip():
        return {
            "allowed": False,
            "reason": "Tool input is empty.",
        }

    return {
        "allowed": True,
        "reason": "Tool request is valid.",
        "tool": tool_name,
        "requires_permission": AVAILABLE_TOOLS[
            tool_name
        ]["requires_permission"],
    }