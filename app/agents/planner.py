from __future__ import annotations

import json
import re
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

Your job is to determine whether the request requires
specialist reasoning, external tools, computation, or execution.

Return ONLY valid JSON.

Never use markdown.
Never use code fences.
Never explain outside the JSON.

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

Rules:

1. Simple conversation, greetings, acknowledgements,
   confirmations, casual questions, and requests that can
   be answered directly require NO execution plan.

2. For simple requests return:

{
    "steps": []
}

3. Use CODING for software development, debugging,
   programming, APIs, repositories, or code tasks.

4. Use INVESTMENT for investment analysis, stocks,
   portfolios, valuation, crypto, or financial decisions.

5. Use BUSINESS for business strategy, companies,
   startups, sales, marketing, customers, or revenue.

6. Use RESEARCH for genuine research, investigation,
   comparison, synthesis, or specialist knowledge work.

7. Use web_search for current, latest, recent, external,
   news, prices, market data, or current company information.

8. Use document_search when uploaded documents are relevant.

9. Use python when actual computation, mathematical calculation,
   numerical analysis, data processing, or executable Python
   is required.

10. Use browser only when actual webpage interaction or reading
    a supplied webpage is required.

11. Do not use tools unnecessarily.

12. Do not invent tools or agents.

13. Use the smallest reliable number of steps.

14. Never answer the user's question directly.

15. For mathematical/computational questions, prefer the Python
    tool when actual calculation is required.

Required format:

{
    "steps": [
        {
            "type": "agent",
            "agent": "RESEARCH",
            "task": "..."
        }
    ]
}

Python tool format:

{
    "steps": [
        {
            "type": "tool",
            "tool": "python",
            "input": "..."
        }
    ]
}

For a simple request:

{
    "steps": []
}
"""


def _clean_model_response(
    response: str,
) -> str:
    """
    Remove common markdown wrappers from model-generated JSON.
    """

    if not response:
        return ""

    text = str(
        response
    ).strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(
            lines
        ).strip()

    return text


def _normalize_step(
    step: Any,
) -> dict[str, Any] | None:
    """
    Validate and normalize one planner step.
    """

    if not isinstance(
        step,
        dict,
    ):
        return None

    step_type = str(
        step.get(
            "type",
            "",
        )
    ).strip().lower()

    if step_type not in VALID_STEP_TYPES:
        return None

    if step_type == "agent":

        agent = str(
            step.get(
                "agent",
                "",
            )
        ).strip().upper()

        task = str(
            step.get(
                "task",
                "",
            )
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
            step.get(
                "tool",
                "",
            )
        ).strip().lower()

        tool_input = str(
            step.get(
                "input",
                "",
            )
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

    if not isinstance(
        plan,
        dict,
    ):
        return {
            "steps": [],
        }

    raw_steps = plan.get(
        "steps",
        [],
    )

    if not isinstance(
        raw_steps,
        list,
    ):
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
    Safe deterministic fallback when the planner model
    is unavailable.

    This function is intentionally deterministic so Falcon
    can continue functioning even when every AI provider is
    unavailable.
    """

    question = str(
        question or ""
    ).strip()

    if not question:
        return {
            "steps": [],
        }

    text = question.lower()

    # ========================================================
    # SIMPLE CONVERSATION
    # ========================================================

    simple_patterns = [
        r"^(hi|hello|hey|hola|salam|assalamualaikum)[!. ]*$",
        r"^(thanks|thank you|ok|okay|alright|great|good)[!. ]*$",
        r"^say hello",
        r"^just say",
        r"^confirm",
        r"^can you confirm",
        r"^are you there",
        r"^how are you",
        r"^what('?s| is) your name",
        r"^who are you",
        r"^good morning",
        r"^good afternoon",
        r"^good evening",
        r"^good night",
    ]

    if any(
        re.search(
            pattern,
            text,
            re.I,
        )
        for pattern in simple_patterns
    ):
        return {
            "steps": [],
        }

    # ========================================================
    # COMPUTATION / PYTHON
    # ========================================================

    computation_patterns = [
        r"\bfactorial\b",
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\bsolve\b",
        r"\bevaluate\b",
        r"\bconvert\b.*\bto\b",
        r"\bpercentage\b",
        r"\bpercent\b",
        r"\baverage\b",
        r"\bmean\b",
        r"\bmedian\b",
        r"\bstandard deviation\b",
        r"\bsum of\b",
        r"\bproduct of\b",
        r"\bpower of\b",
        r"\bsquare root\b",
        r"\bcube root\b",
        r"\bhow many\b",
        r"\bhow much\b",
    ]

    if any(
        re.search(
            pattern,
            text,
            re.I,
        )
        for pattern in computation_patterns
    ):

        # ----------------------------------------------------
        # Factorial
        #
        # Supports both:
        #
        #   25 factorial
        #   factorial of 25
        #   what is 25 factorial?
        # ----------------------------------------------------

        factorial_match = re.search(
            r"\b(?:factorial\s+of\s+(\d+)|(\d+)\s+factorial)\b",
            text,
            re.I,
        )

        if factorial_match:

            number = (
                factorial_match.group(1)
                or factorial_match.group(2)
            )

            return {
                "steps": [
                    {
                        "type": "tool",
                        "tool": "python",
                        "input": (
                            f"import math; "
                            f"print(math.factorial({number}))"
                        ),
                    }
                ]
            }

        # ----------------------------------------------------
        # General calculation
        #
        # IMPORTANT:
        # Pass the actual user question to the Python tool.
        # Do not pass an instruction such as:
        #
        # "Calculate the requested mathematical operation..."
        #
        # because the Python tool executes the supplied input.
        # ----------------------------------------------------

        return {
            "steps": [
                {
                    "type": "tool",
                    "tool": "python",
                    "input": question,
                }
            ]
        }

    # ========================================================
    # SPECIALIST KEYWORDS
    # ========================================================

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
        "repository",
        "github",
        "function",
        "class",
        "debug",
        "compile",
        "refactor",
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
        "market cap",
        "earnings",
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
        "enterprise",
        "pricing",
        "market",
    }

    research_keywords = {
        "research",
        "investigate",
        "analyze",
        "analyse",
        "compare",
        "comparison",
        "study",
        "explain in detail",
        "deep dive",
        "find out",
    }

    current_keywords = {
        "latest",
        "current",
        "today",
        "recent",
        "news",
        "right now",
        "this week",
        "this month",
        "live price",
        "current price",
    }

    # ========================================================
    # CODING
    # ========================================================

    if any(
        keyword in text
        for keyword in coding_keywords
    ):
        return {
            "steps": [
                {
                    "type": "agent",
                    "agent": "CODING",
                    "task": question,
                }
            ]
        }

    # ========================================================
    # INVESTMENT
    # ========================================================

    if any(
        keyword in text
        for keyword in investment_keywords
    ):

        if any(
            keyword in text
            for keyword in current_keywords
        ):
            return {
                "steps": [
                    {
                        "type": "tool",
                        "tool": "web_search",
                        "input": question,
                    },
                    {
                        "type": "agent",
                        "agent": "INVESTMENT",
                        "task": question,
                    },
                ]
            }

        return {
            "steps": [
                {
                    "type": "agent",
                    "agent": "INVESTMENT",
                    "task": question,
                }
            ]
        }

    # ========================================================
    # BUSINESS
    # ========================================================

    if any(
        keyword in text
        for keyword in business_keywords
    ):

        if any(
            keyword in text
            for keyword in current_keywords
        ):
            return {
                "steps": [
                    {
                        "type": "tool",
                        "tool": "web_search",
                        "input": question,
                    },
                    {
                        "type": "agent",
                        "agent": "BUSINESS",
                        "task": question,
                    },
                ]
            }

        return {
            "steps": [
                {
                    "type": "agent",
                    "agent": "BUSINESS",
                    "task": question,
                }
            ]
        }

    # ========================================================
    # RESEARCH
    # ========================================================

    if any(
        keyword in text
        for keyword in research_keywords
    ):

        if any(
            keyword in text
            for keyword in current_keywords
        ):
            return {
                "steps": [
                    {
                        "type": "tool",
                        "tool": "web_search",
                        "input": question,
                    },
                    {
                        "type": "agent",
                        "agent": "RESEARCH",
                        "task": question,
                    },
                ]
            }

        return {
            "steps": [
                {
                    "type": "agent",
                    "agent": "RESEARCH",
                    "task": question,
                }
            ]
        }

    # ========================================================
    # UNKNOWN / DIRECT RESPONSE
    # ========================================================

    return {
        "steps": [],
    }


def create_plan(
    question: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Create and validate a Falcon execution plan.

    The planner never executes tools or agents itself.
    """

    question = str(
        question or ""
    ).strip()

    if not question:
        return {
            "steps": [],
        }

    # ========================================================
    # DETERMINISTIC FAST-PATHS
    # ========================================================

    deterministic_plan = _fallback_plan(
        question
    )

    if deterministic_plan["steps"]:

        logger.info(
            "Planner deterministic fast-path selected."
        )

        return deterministic_plan

    # ========================================================
    # AI PLANNER
    # ========================================================

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

        # Empty plans are VALID.
        if (
            isinstance(
                parsed,
                dict,
            )
            and "steps" in parsed
        ):
            return plan

        logger.warning(
            "Planner returned invalid structure. "
            "Using deterministic fallback."
        )

        return deterministic_plan

    except json.JSONDecodeError:

        logger.warning(
            "Planner returned invalid JSON. "
            "Using deterministic fallback."
        )

        return deterministic_plan

    except Exception:

        logger.warning(
            "Planner AI unavailable. "
            "Using deterministic fallback."
        )

        return deterministic_plan