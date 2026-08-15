from __future__ import annotations

from typing import Any

from app.ai_service import ask_ai
from app.agents.agent_intelligence import (
    analyze_agent_task,
)


# ============================================================
# AGENT CONFIGURATION
# ============================================================

SUPPORTED_AGENTS = {
    "BUSINESS",
    "CODING",
    "INVESTMENT",
    "RESEARCH",
}


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def _normalize_context(
    context: dict | None,
) -> dict:
    """
    Normalize shared agent context.

    Agents should always receive a dictionary even when
    no shared context exists.
    """

    if not isinstance(context, dict):
        return {}

    return dict(context)


def _normalize_memories(
    memories: list | None,
) -> list:
    """
    Normalize memory input.

    Invalid memory containers are converted into an empty list
    rather than breaking agent execution.
    """

    if not isinstance(memories, list):
        return []

    return list(memories)


def _normalize_agent_name(
    agent: str,
) -> str:
    """
    Normalize the specialist agent name.
    """

    if not agent:
        return ""

    return str(
        agent
    ).strip().upper()


def _build_agent_task(
    system_prompt: str,
    question: str,
) -> str:
    """
    Build the specialist task passed into Falcon's
    structured intelligence layer.

    The intelligence layer is responsible for converting
    the specialist response into Falcon's standard result
    contract.
    """

    system_prompt = (
        str(system_prompt or "")
        .strip()
    )

    question = (
        str(question or "")
        .strip()
    )

    if not system_prompt:
        return question

    if not question:
        return system_prompt

    return (
        system_prompt
        + "\n\n"
        + "User Task:\n"
        + question
    )


# ============================================================
# LEGACY AGENT EXECUTION
# ============================================================

def run_agent(
    system_prompt: str,
    question: str,
    context: dict | None = None,
    memories=None,
):
    """
    Legacy-compatible agent runner.

    Returns the specialist answer as plain text.

    This function remains available so older Falcon components
    can continue using the original text-based agent interface.
    """

    context = _normalize_context(
        context
    )

    memories = _normalize_memories(
        memories
    )

    system_prompt = (
        str(system_prompt or "")
        .strip()
    )

    question = (
        str(question or "")
        .strip()
    )

    prompt = (
        system_prompt
        + "\n\nRelevant Memories:\n"
        + str(memories)
        + "\n\nShared Context:\n"
        + str(context)
        + "\n\nUser Question:\n"
        + question
    )

    return ask_ai(
        prompt
    )


# ============================================================
# STRUCTURED AGENT EXECUTION
# ============================================================

def run_intelligent_agent(
    agent: str,
    system_prompt: str,
    question: str,
    context: dict | None = None,
    memories=None,
):
    """
    Execute one specialist agent through Falcon's structured
    intelligence layer.

    The result follows Falcon's normalized agent contract:

        {
            "agent": "...",
            "status": "...",
            "answer": "...",
            "key_findings": [...],
            "evidence": [...],
            "assumptions": [...],
            "uncertainties": [...],
            "risks": [...],
            "recommendations": [...],
            "confidence": 0.0
        }

    This function is deliberately responsible only for one
    specialist execution. Multi-agent collaboration belongs
    to the collaboration layer.
    """

    agent_name = _normalize_agent_name(
        agent
    )

    context = _normalize_context(
        context
    )

    memories = _normalize_memories(
        memories
    )

    if not agent_name:
        return {
            "agent": "UNKNOWN",
            "status": "error",
            "answer": "",
            "key_findings": [],
            "evidence": [],
            "assumptions": [],
            "uncertainties": [
                "Agent name is missing."
            ],
            "risks": [],
            "recommendations": [],
            "confidence": 0.0,
        }

    if agent_name not in SUPPORTED_AGENTS:
        return {
            "agent": agent_name,
            "status": "error",
            "answer": "",
            "key_findings": [],
            "evidence": [],
            "assumptions": [],
            "uncertainties": [
                f"Unsupported agent: {agent_name}"
            ],
            "risks": [],
            "recommendations": [],
            "confidence": 0.0,
        }

    if not str(
        question or ""
    ).strip():

        return {
            "agent": agent_name,
            "status": "error",
            "answer": "",
            "key_findings": [],
            "evidence": [],
            "assumptions": [],
            "uncertainties": [
                "Agent task is empty."
            ],
            "risks": [],
            "recommendations": [],
            "confidence": 0.0,
        }

    task = _build_agent_task(
        system_prompt=system_prompt,
        question=question,
    )

    try:

        result = analyze_agent_task(
            agent=agent_name,
            task=task,
            context=context,
            memories=memories,
        )

        if not isinstance(
            result,
            dict,
        ):

            return {
                "agent": agent_name,
                "status": "error",
                "answer": str(result),
                "key_findings": [],
                "evidence": [],
                "assumptions": [],
                "uncertainties": [
                    "Agent returned an invalid result object."
                ],
                "risks": [],
                "recommendations": [],
                "confidence": 0.3,
            }

        result.setdefault(
            "agent",
            agent_name,
        )

        result.setdefault(
            "status",
            "complete",
        )

        result.setdefault(
            "answer",
            "",
        )

        result.setdefault(
            "key_findings",
            [],
        )

        result.setdefault(
            "evidence",
            [],
        )

        result.setdefault(
            "assumptions",
            [],
        )

        result.setdefault(
            "uncertainties",
            [],
        )

        result.setdefault(
            "risks",
            [],
        )

        result.setdefault(
            "recommendations",
            [],
        )

        confidence = result.get(
            "confidence",
            0.5,
        )

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.5

        result["confidence"] = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        return result

    except Exception as exc:

        return {
            "agent": agent_name,
            "status": "error",
            "answer": "",
            "key_findings": [],
            "evidence": [],
            "assumptions": [],
            "uncertainties": [
                "Agent execution failed."
            ],
            "risks": [
                str(exc)
            ],
            "recommendations": [],
            "confidence": 0.0,
        }


# ============================================================
# AGENT RESULT VALIDATION
# ============================================================

def is_agent_result_successful(
    result: Any,
) -> bool:
    """
    Determine whether an agent produced a usable result.
    """

    if not isinstance(
        result,
        dict,
    ):
        return False

    status = str(
        result.get(
            "status",
            "",
        )
    ).lower()

    if status in {
        "error",
        "failed",
        "blocked",
    }:
        return False

    answer = result.get(
        "answer",
        "",
    )

    return bool(
        str(
            answer or ""
        ).strip()
    )


def get_agent_answer(
    result: Any,
) -> str:
    """
    Safely extract an agent's answer from a structured result.
    """

    if not isinstance(
        result,
        dict,
    ):
        return str(
            result or ""
        )

    return str(
        result.get(
            "answer",
            "",
        )
        or ""
    ).strip()