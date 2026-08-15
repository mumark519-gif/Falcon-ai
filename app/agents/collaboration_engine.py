from __future__ import annotations

import json
from typing import Any

from app.ai_service import ask_ai
from app.core.logger import logger

from app.agents.agent_intelligence import (
    combine_agent_findings,
    detect_agent_conflicts,
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_SYNTHESIS_FINDINGS = 30
MAX_SYNTHESIS_CONFLICTS = 20
MAX_SYNTHESIS_TEXT = 12000


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_agent_results(
    agent_results: Any,
) -> dict[str, Any]:
    """
    Normalize the collection of specialist results.

    Falcon's collaboration layer expects:

        {
            "AGENT_NAME": result,
            ...
        }
    """

    if not isinstance(
        agent_results,
        dict,
    ):
        return {}

    normalized = {}

    for agent, result in agent_results.items():

        agent_name = str(
            agent or ""
        ).strip().upper()

        if not agent_name:
            continue

        normalized[
            agent_name
        ] = result

    return normalized


def _normalize_confidence(
    value: Any,
    default: float = 0.5,
) -> float:
    """
    Normalize confidence into the range 0.0 - 1.0.
    """

    try:

        confidence = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        confidence = default

    return max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )


def _normalize_list(
    value: Any,
) -> list:
    """
    Normalize list-like agent fields.
    """

    if value is None:
        return []

    if isinstance(
        value,
        list,
    ):
        return value

    return [
        value
    ]


# ============================================================
# AGENT QUALITY
# ============================================================

def _agent_quality(
    result: Any,
) -> float:
    """
    Estimate the basic quality of a specialist result.

    This is not a truth score. It is only a structural quality
    indicator used to help prioritize better-formed findings.
    """

    if not isinstance(
        result,
        dict,
    ):
        return 0.0

    score = 0.0

    status = str(
        result.get(
            "status",
            "",
        )
    ).lower()

    if status in {
        "complete",
        "completed",
        "success",
    }:
        score += 0.30

    answer = str(
        result.get(
            "answer",
            "",
        )
        or ""
    ).strip()

    if answer:
        score += 0.20

    findings = _normalize_list(
        result.get(
            "key_findings",
            [],
        )
    )

    evidence = _normalize_list(
        result.get(
            "evidence",
            [],
        )
    )

    recommendations = _normalize_list(
        result.get(
            "recommendations",
            [],
        )
    )

    if findings:
        score += 0.15

    if evidence:
        score += 0.20

    if recommendations:
        score += 0.05

    score += (
        _normalize_confidence(
            result.get(
                "confidence",
                0.5,
            )
        )
        * 0.10
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def _rank_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Rank specialist findings by confidence and structural quality.
    """

    ranked = []

    for finding in findings:

        if not isinstance(
            finding,
            dict,
        ):
            continue

        confidence = _normalize_confidence(
            finding.get(
                "confidence",
                0.5,
            )
        )

        quality = _agent_quality(
            finding
        )

        item = dict(
            finding
        )

        item[
            "_collaboration_score"
        ] = round(
            (
                confidence
                * 0.7
            )
            + (
                quality
                * 0.3
            ),
            4,
        )

        ranked.append(
            item
        )

    ranked.sort(
        key=lambda item: item.get(
            "_collaboration_score",
            0.0,
        ),
        reverse=True,
    )

    return ranked


# ============================================================
# COLLABORATION
# ============================================================

def collaborate(
    agent_results: dict,
):
    """
    Run cross-agent collaboration.

    Produces a normalized package containing:

    - specialist findings
    - ranked specialists
    - conflicts
    - cross-agent assessment
    - aggregate confidence
    """

    logger.info(
        "Running Falcon Multi-Agent Collaboration..."
    )

    normalized_results = _normalize_agent_results(
        agent_results
    )

    if not normalized_results:

        return {
            "agents": [],
            "ranked_agents": [],
            "conflicts": [],
            "assessment": "",
            "confidence": 0.0,
            "status": "no_agent_results",
        }

    findings = combine_agent_findings(
        normalized_results
    )

    if not findings:

        return {
            "agents": [],
            "ranked_agents": [],
            "conflicts": [],
            "assessment": "",
            "confidence": 0.0,
            "status": "no_valid_findings",
        }

    ranked_findings = _rank_findings(
        findings
    )

    # Remove internal ranking metadata from the public
    # collaboration package.

    ranked_public = []

    for finding in ranked_findings:

        public_finding = dict(
            finding
        )

        public_finding.pop(
            "_collaboration_score",
            None,
        )

        ranked_public.append(
            public_finding
        )

    # Conflict detection is unnecessary when only one
    # specialist was used.

    if len(normalized_results) < 2:

        conflicts = {
            "conflicts": [],
            "overall_assessment": "",
            "confidence": _normalize_confidence(
                findings[0].get(
                    "confidence",
                    0.5,
                )
            ),
        }

    else:

        try:

            conflicts = detect_agent_conflicts(
                normalized_results
            )

        except Exception as exc:

            logger.exception(
                "Cross-agent conflict detection failed."
            )

            conflicts = {
                "conflicts": [],
                "overall_assessment": "",
                "confidence": 0.3,
                "error": str(exc),
            }

    conflict_list = _normalize_list(
        conflicts.get(
            "conflicts",
            [],
        )
    )

    conflict_list = conflict_list[
        :MAX_SYNTHESIS_CONFLICTS
    ]

    assessment = str(
        conflicts.get(
            "overall_assessment",
            "",
        )
        or ""
    ).strip()

    # Calculate aggregate confidence.

    individual_confidences = [
        _normalize_confidence(
            finding.get(
                "confidence",
                0.5,
            )
        )
        for finding in findings
        if isinstance(
            finding,
            dict,
        )
    ]

    if individual_confidences:

        average_confidence = (
            sum(
                individual_confidences
            )
            / len(
                individual_confidences
            )
        )

    else:

        average_confidence = 0.0

    conflict_confidence = _normalize_confidence(
        conflicts.get(
            "confidence",
            0.5,
        )
    )

    # When conflicts exist, reduce aggregate confidence rather
    # than pretending that all specialists agree.

    conflict_penalty = min(
        0.30,
        len(
            conflict_list
        )
        * 0.05,
    )

    aggregate_confidence = (
        (
            average_confidence
            * 0.70
        )
        + (
            conflict_confidence
            * 0.30
        )
        - conflict_penalty
    )

    aggregate_confidence = max(
        0.0,
        min(
            1.0,
            aggregate_confidence,
        ),
    )

    return {
        "agents": findings,
        "ranked_agents": ranked_public,
        "conflicts": conflict_list,
        "assessment": assessment,
        "confidence": round(
            aggregate_confidence,
            4,
        ),
        "status": "complete",
    }


# ============================================================
# SYNTHESIS CONTEXT
# ============================================================

def _prepare_synthesis_package(
    collaboration: dict,
) -> dict:
    """
    Reduce and normalize collaboration data before sending it
    to the synthesis model.
    """

    if not isinstance(
        collaboration,
        dict,
    ):
        return {
            "agents": [],
            "conflicts": [],
            "assessment": "",
            "confidence": 0.0,
        }

    agents = collaboration.get(
        "ranked_agents",
        collaboration.get(
            "agents",
            [],
        ),
    )

    conflicts = collaboration.get(
        "conflicts",
        [],
    )

    agents = (
        agents
        if isinstance(
            agents,
            list,
        )
        else []
    )

    conflicts = (
        conflicts
        if isinstance(
            conflicts,
            list,
        )
        else []
    )

    agents = agents[
        :MAX_SYNTHESIS_FINDINGS
    ]

    conflicts = conflicts[
        :MAX_SYNTHESIS_CONFLICTS
    ]

    package = {
        "agents": agents,
        "conflicts": conflicts,
        "assessment": str(
            collaboration.get(
                "assessment",
                "",
            )
            or ""
        ),
        "confidence": _normalize_confidence(
            collaboration.get(
                "confidence",
                0.5,
            )
        ),
    }

    serialized = json.dumps(
        package,
        ensure_ascii=False,
        default=str,
    )

    if len(serialized) > MAX_SYNTHESIS_TEXT:

        serialized = serialized[
            :MAX_SYNTHESIS_TEXT
        ]

        package = {
            "truncated_context": serialized
        }

    return package


# ============================================================
# SYNTHESIS
# ============================================================

def synthesize_collaboration(
    question: str,
    collaboration: dict,
):
    """
    Turn collaborative specialist findings into a coherent
    intermediate answer.

    Final reflection still happens afterward.

    The synthesis layer does not independently invent research.
    It works from the supplied specialist package.
    """

    question = str(
        question or ""
    ).strip()

    if not question:

        return ""

    if not isinstance(
        collaboration,
        dict,
    ):

        return (
            "No valid collaboration results were available."
        )

    package = _prepare_synthesis_package(
        collaboration
    )

    if not package.get(
        "agents"
    ):

        return (
            "No specialist findings were available "
            "for synthesis."
        )

    prompt = """
You are Falcon AI's Multi-Agent Synthesis Engine.

Your job is to combine specialist analyses into one accurate
intermediate answer.

The specialist results may disagree.

Rules:

1. Do not blindly merge contradictory claims.

2. Prefer findings supported by stronger evidence.

3. Explicitly resolve meaningful disagreements when the
   supplied evidence allows resolution.

4. If the evidence does not allow resolution, preserve
   the uncertainty instead of inventing an answer.

5. Do not invent facts that are absent from the supplied
   specialist findings.

6. Do not duplicate the same information.

7. Preserve important assumptions and uncertainties.

8. Distinguish evidence from recommendations.

9. Do not claim that a tool, source, document, or website
   was used unless the supplied context proves it.

10. Answer the user's actual question directly.

11. Do not mention internal Falcon architecture,
    specialist agents, planners, workflows, or collaboration
    unless that information is specifically relevant to the
    user's question.

12. Produce a clear, useful intermediate answer that can
    safely pass through Falcon's final reflection layer.

Return ONLY the synthesized answer.
"""

    prompt += (
        "\n\nUser Question:\n"
        + question
        + "\n\nCollaboration Package:\n"
        + json.dumps(
            package,
            ensure_ascii=False,
            default=str,
        )
    )

    try:

        response = ask_ai(
            prompt
        )

        return str(
            response or ""
        ).strip()

    except Exception as exc:

        logger.exception(
            "Multi-agent synthesis failed."
        )

        # Safe fallback: return the strongest specialist
        # answer instead of losing all useful work.

        ranked_agents = collaboration.get(
            "ranked_agents",
            collaboration.get(
                "agents",
                [],
            ),
        )

        if isinstance(
            ranked_agents,
            list,
        ):

            for agent in ranked_agents:

                if not isinstance(
                    agent,
                    dict,
                ):
                    continue

                answer = str(
                    agent.get(
                        "answer",
                        "",
                    )
                    or ""
                ).strip()

                if answer:

                    return answer

        return (
            "Falcon was unable to synthesize the specialist "
            f"results: {exc}"
        )