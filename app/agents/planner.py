from __future__ import annotations

import json
from typing import Any

from app.services.ai.ai_gateway import generate as ask_ai
from app.core.logger import logger


AVAILABLE_AGENTS = {
    "BUSINESS",
    "CODING",
    "INVESTMENT",
    "RESEARCH",
}

AVAILABLE_TOOLS = {
    "web_search",
    "document_search",
    "python",
    "browser",
}

VALID_STEP_TYPES = {
    "agent",
    "tool",
}


PLANNER_PROMPT = """
You are Falcon AI's Execution Planner.

Your job is NOT to answer the user's question.

Your job is to analyze the user's request and produce the
smallest reliable execution plan required to solve it.

Return ONLY valid JSON.

Never use markdown.
Never use code fences.
Never explain the plan outside the JSON.
Never answer the user's question directly.

Available specialist agents:

BUSINESS
CODING
INVESTMENT
RESEARCH

Available tools:

web_search
document_search
python
browser

Valid step formats:

Agent:

{
    "type": "agent",
    "agent": "RESEARCH",
    "task": "..."
}

Tool:

{
    "type": "tool",
    "tool": "web_search",
    "input": "..."
}

Rules:

1. Use an agent when specialist reasoning is required.

2. Use web_search when the request requires:
   - current information
   - latest information
   - news
   - external facts
   - current prices
   - current company information
   - recent events
   - external research

3. Use document_search when the user's uploaded documents,
   files, reports, notes, or stored knowledge are relevant.

4. Use python when actual computation, numerical analysis,
   data processing, or code execution is required.

5. Use browser when the task requires reading a specific
   webpage or URL.

6. Do not use tools unnecessarily.

7. If a tool provides information needed by a later agent,
   place the tool step before that agent.

8. If multiple specialist agents are needed, execute them
   in a logical dependency order.

9. Do not create duplicate steps.

10. Do not create steps for work that another step already performs.

11. For investment questions involving current or recent
    information, normally research first and investment
    analysis second.

12. For business questions requiring current market information,
    normally research/web first and business analysis afterward.

13. For coding questions, use the CODING agent unless actual
    Python execution is explicitly required.

14. For simple questions that do not require tools or specialist
    analysis, use the most appropriate single agent.

15. Do not invent tools or agents.

16. Every step must contain all required fields.

17. Return an empty plan only when the request genuinely requires
    no execution.

Required JSON format:

{
    "steps": [
        {
            "type": "agent",
            "agent": "RESEARCH",
            "task": "..."
        }
    ]
}

Example:

User:
Should I invest in Apple stock?

Output:

{
    "steps": [
        {
            "type": "tool",
            "tool": "web_search",
            "input": "Apple latest financial results valuation analyst outlook"
        },
        {
            "type": "agent",
            "agent": "RESEARCH",
            "task": "Analyze Apple's latest financial and market information."
        },
        {
            "type": "agent",
            "agent": "INVESTMENT",
            "task": "Evaluate Apple as an investment using the research findings."
        }
    ]
}

User:
Fix my FastAPI authentication error.

Output:

{
    "steps": [
        {
            "type": "agent",
            "agent": "CODING",
            "task": "Diagnose the FastAPI authentication error and provide the appropriate fix."
        }
    ]
}

User:
Calculate 25 factorial using Python.

Output:

{
    "steps": [
        {
            "type": "tool",
            "tool": "python",
            "input": "import math; print(math.factorial(25))"
        }
    ]
}

User:
Research NVIDIA's latest earnings and tell me whether it is a good investment.

Output:

{
    "steps": [
        {
            "type": "tool",
            "tool": "web_search",
            "input": "NVIDIA latest earnings revenue profit guidance valuation"
        },
        {
            "type": "agent",
            "agent": "RESEARCH",
            "task": "Analyze NVIDIA's latest earnings and relevant financial information."
        },
        {
            "type": "agent",
            "agent": "INVESTMENT",
            "task": "Evaluate NVIDIA as an investment using the research findings."
        }
    ]
}

User:
Read this webpage and summarize it.

Output:

{
    "steps": [
        {
            "type": "tool",
            "tool": "browser",
            "input": "Read the webpage supplied by the user."
        },
        {
            "type": "agent",
            "agent": "RESEARCH",
            "task": "Summarize and explain the webpage using the browser results."
        }
    ]
}

Always return valid JSON.
"""


def _clean_model_response(
    response: str,
) -> str:
    """
    Remove common markdown wrappers from model-generated JSON.
    """

    if not response:
        return ""

    text = response.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def _normalize_step(
    step: Any,
) -> dict[str, Any] | None:
    """
    Validate and normalize one planner step.
    """

    if not isinstance(step, dict):
        return None

    step_type = str(
        step.get("type", "")
    ).strip().lower()

    if step_type not in VALID_STEP_TYPES:
        return None

    if step_type == "agent":

        agent = str(
            step.get("agent", "")
        ).strip().upper()

        task = str(
            step.get("task", "")
        ).strip()

        if agent not in AVAILABLE_AGENTS:
            return None

        if not task:
            return None

        return {
            "type": "agent",
            "agent": agent,
            "task": task,
        }

    if step_type == "tool":

        tool = str(
            step.get("tool", "")
        ).strip().lower()

        tool_input = str(
            step.get("input", "")
        ).strip()

        if tool not in AVAILABLE_TOOLS:
            return None

        if not tool_input:
            return None

        return {
            "type": "tool",
            "tool": tool,
            "input": tool_input,
        }

    return None


def _validate_plan(
    plan: Any,
) -> dict[str, list[dict[str, Any]]]:
    """
    Validate the complete planner output.

    Invalid steps are discarded instead of allowing malformed
    model output to reach the execution engine.
    """

    if not isinstance(plan, dict):
        return {
            "steps": [],
        }

    raw_steps = plan.get(
        "steps",
        [],
    )

    if not isinstance(raw_steps, list):
        return {
            "steps": [],
        }

    normalized_steps = []

    for step in raw_steps:

        normalized = _normalize_step(
            step
        )

        if normalized is None:
            continue

        normalized_steps.append(
            normalized
        )

    return {
        "steps": normalized_steps,
    }


def _fallback_plan(
    question: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Safe deterministic fallback when the planner fails.

    The fallback intentionally does not invent tool usage.
    """

    question = (
        question or ""
    ).strip()

    if not question:
        return {
            "steps": [],
        }

    text = question.lower()

    coding_keywords = {
        "python",
        "fastapi",
        "javascript",
        "typescript",
        "react",
        "sql",
        "code",
        "coding",
        "bug",
        "error",
        "api",
        "program",
    }

    investment_keywords = {
        "stock",
        "stocks",
        "shares",
        "invest",
        "investment",
        "portfolio",
        "etf",
        "dividend",
        "bitcoin",
        "crypto",
        "valuation",
    }

    business_keywords = {
        "business",
        "company",
        "startup",
        "marketing",
        "sales",
        "customer",
        "revenue",
        "profit",
        "strategy",
    }

    if any(
        keyword in text
        for keyword in coding_keywords
    ):
        agent = "CODING"

    elif any(
        keyword in text
        for keyword in investment_keywords
    ):
        agent = "INVESTMENT"

    elif any(
        keyword in text
        for keyword in business_keywords
    ):
        agent = "BUSINESS"

    else:
        agent = "RESEARCH"

    return {
        "steps": [
            {
                "type": "agent",
                "agent": agent,
                "task": question,
            }
        ]
    }


def create_plan(
    question: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Create and validate a Falcon execution plan.

    The planner is responsible only for planning.
    It does not execute tools or agents.
    """

    question = (
        question or ""
    ).strip()

    if not question:
        return {
            "steps": [],
        }

    prompt = (
        PLANNER_PROMPT
        + "\n\nUser Request:\n"
        + question
    )

    try:

        response = ask_ai(
            prompt
        )

        cleaned = _clean_model_response(
            response
        )

        parsed = json.loads(
            cleaned
        )

        plan = _validate_plan(
            parsed
        )

        if plan["steps"]:
            return plan

        logger.warning(
            "Planner returned an empty or invalid plan. "
            "Using deterministic fallback."
        )

        return _fallback_plan(
            question
        )

    except json.JSONDecodeError:

        logger.warning(
            "Planner returned invalid JSON. "
            "Using deterministic fallback."
        )

        return _fallback_plan(
            question
        )

    except Exception:

        logger.exception(
            "Planner failed. "
            "Using deterministic fallback."
        )

        return _fallback_plan(
            question
        )