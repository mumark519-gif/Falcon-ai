from __future__ import annotations

import json
from typing import Any

from app.ai_service import ask_ai
from app.core.logger import logger


AGENT_INTELLIGENCE_PROMPT = """
You are part of Falcon AI's Agent Intelligence Layer.

You are a specialist agent working inside a larger AI system.

Your job is to analyze the assigned task carefully and return
structured findings that another Falcon component can use.

Do not blindly agree with assumptions.

Separate:
- facts
- reasoning
- assumptions
- uncertainties
- recommendations

Look for contradictions and missing information.

Return ONLY valid JSON.

Required format:

{
    "agent": "AGENT_NAME",
    "status": "complete",
    "answer": "Your useful specialist answer.",
    "key_findings": [
        "finding 1",
        "finding 2"
    ],
    "evidence": [
        "evidence or supporting information"
    ],
    "assumptions": [
        "assumption 1"
    ],
    "uncertainties": [
        "uncertainty 1"
    ],
    "risks": [
        "risk 1"
    ],
    "recommendations": [
        "recommendation 1"
    ],
    "confidence": 0.0
}

Confidence must be a number between 0 and 1.
"""


def _clean_json_response(
    response: str,
) -> str:
    """
    Remove common markdown JSON wrappers produced by models.
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


def _normalize_result(
    agent: str,
    result: Any,
) -> dict:
    """
    Convert model output into Falcon's standard agent result contract.
    """

    agent_name = agent.upper()

    if isinstance(result, dict):

        normalized = dict(result)

    else:

        normalized = {
            "answer": str(result),
        }

    normalized.setdefault(
        "agent",
        agent_name,
    )

    normalized.setdefault(
        "status",
        "complete",
    )

    normalized.setdefault(
        "answer",
        "",
    )

    normalized.setdefault(
        "key_findings",
        [],
    )

    normalized.setdefault(
        "evidence",
        [],
    )

    normalized.setdefault(
        "assumptions",
        [],
    )

    normalized.setdefault(
        "uncertainties",
        [],
    )

    normalized.setdefault(
        "risks",
        [],
    )

    normalized.setdefault(
        "recommendations",
        [],
    )

    confidence = normalized.get(
        "confidence",
        0.5,
    )

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.5

    normalized["confidence"] = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    return normalized


def analyze_agent_task(
    agent: str,
    task: str,
    context: dict | None = None,
    memories: list | None = None,
):
    """
    Run one specialist analysis and normalize its output.
    """

    if context is None:
        context = {}

    if memories is None:
        memories = []

    prompt = (
        AGENT_INTELLIGENCE_PROMPT
        + "\n\nAgent:\n"
        + agent.upper()
        + "\n\nTask:\n"
        + task
        + "\n\nRelevant Memories:\n"
        + str(memories)
        + "\n\nShared Context:\n"
        + str(context)
    )

    response = ask_ai(prompt)

    cleaned = _clean_json_response(
        response
    )

    try:

        parsed = json.loads(
            cleaned
        )

        return _normalize_result(
            agent,
            parsed,
        )

    except Exception:

        logger.warning(
            "Agent %s returned non-JSON output.",
            agent,
        )

        return _normalize_result(
            agent,
            {
                "answer": response,
                "uncertainties": [
                    "Agent output was not returned "
                    "in structured JSON format."
                ],
            },
        )


def combine_agent_findings(
    agent_results: dict[str, Any],
):
    """
    Convert specialist results into a normalized collaboration package.
    """

    findings = []

    for agent, result in agent_results.items():

        normalized = _normalize_result(
            agent,
            result,
        )

        findings.append(
            normalized
        )

    return findings


def detect_agent_conflicts(
    agent_results: dict[str, Any],
):
    """
    Ask Falcon to identify contradictions between specialists.
    """

    findings = combine_agent_findings(
        agent_results
    )

    if len(findings) < 2:
        return {
            "conflicts": [],
            "status": "no_multi_agent_conflict_check_needed",
        }

    prompt = """
You are Falcon AI's cross-agent verification engine.

Several specialist agents analyzed the same user request.

Identify:
1. Direct contradictions
2. Different assumptions
3. Conflicting recommendations
4. Missing evidence
5. Which finding appears stronger and why

Return ONLY valid JSON.

Format:

{
    "conflicts": [
        {
            "agents": ["AGENT_A", "AGENT_B"],
            "issue": "...",
            "resolution": "...",
            "confidence": 0.0
        }
    ],
    "overall_assessment": "...",
    "confidence": 0.0
}
"""

    prompt += (
        "\n\nAgent Findings:\n"
        + json.dumps(
            findings,
            ensure_ascii=False,
            default=str,
        )
    )

    response = ask_ai(prompt)

    cleaned = _clean_json_response(
        response
    )

    try:

        result = json.loads(
            cleaned
        )

        result.setdefault(
            "conflicts",
            [],
        )

        result.setdefault(
            "overall_assessment",
            "",
        )

        result.setdefault(
            "confidence",
            0.5,
        )

        return result

    except Exception:

        logger.warning(
            "Cross-agent conflict analysis returned invalid JSON."
        )

        return {
            "conflicts": [],
            "overall_assessment": response,
            "confidence": 0.3,
        }