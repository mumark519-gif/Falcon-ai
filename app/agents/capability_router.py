from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.logger import logger


# ============================================================
# CAPABILITY DEFINITIONS
# ============================================================

CAPABILITIES = {
    "general_reasoning": {
        "description": "General reasoning, explanation, problem solving and decision support.",
        "priority": 100,
    },
    "research": {
        "description": "Research, information gathering and evidence synthesis.",
        "priority": 90,
    },
    "web": {
        "description": "Current, external or time-sensitive web information.",
        "priority": 90,
    },
    "documents": {
        "description": "User files, documents, PDFs, notes and uploaded material.",
        "priority": 90,
    },
    "coding": {
        "description": "Software engineering, debugging, programming and code generation.",
        "priority": 90,
    },
    "business": {
        "description": "Business strategy, operations, markets and commercial analysis.",
        "priority": 80,
    },
    "investment": {
        "description": "Investment, valuation, financial analysis and capital markets.",
        "priority": 85,
    },
    "data_analysis": {
        "description": "Numerical computation, datasets, statistics and structured analysis.",
        "priority": 85,
    },
    "browser": {
        "description": "Direct interaction with websites and browser interfaces.",
        "priority": 80,
    },
    "automation": {
        "description": "Executing multi-step tasks using tools and external systems.",
        "priority": 95,
    },
    "image": {
        "description": "Image understanding, image analysis and visual tasks.",
        "priority": 70,
    },
    "video": {
        "description": "Video understanding, analysis and generation-related workflows.",
        "priority": 70,
    },
    "voice": {
        "description": "Speech input, transcription, speech understanding and voice interaction.",
        "priority": 70,
    },
    "github": {
        "description": "Repositories, codebases, issues, pull requests and GitHub workflows.",
        "priority": 85,
    },
    "enterprise": {
        "description": "Enterprise workflows, organizational operations and business automation.",
        "priority": 90,
    },
}


# ============================================================
# SIGNALS
# ============================================================

CAPABILITY_SIGNALS = {
    "web": {
        "latest",
        "today",
        "current",
        "recent",
        "news",
        "price",
        "prices",
        "live",
        "this week",
        "this month",
        "this year",
        "search the web",
        "search online",
        "look up",
        "research online",
    },
    "documents": {
        "document",
        "documents",
        "pdf",
        "file",
        "files",
        "uploaded",
        "upload",
        "attachment",
        "attachments",
        "my report",
        "my reports",
        "my notes",
        "according to my",
        "according to the file",
        "according to the document",
        "in the file",
        "in the document",
        "in my file",
    },
    "coding": {
        "code",
        "coding",
        "program",
        "programming",
        "python",
        "javascript",
        "typescript",
        "java",
        "c++",
        "bug",
        "debug",
        "debugging",
        "function",
        "class",
        "api",
        "backend",
        "frontend",
        "repository",
        "software",
        "script",
    },
    "business": {
        "business",
        "company",
        "startup",
        "customer",
        "sales",
        "marketing",
        "strategy",
        "revenue",
        "profit",
        "operations",
        "market",
        "competitor",
        "competition",
    },
    "investment": {
        "investment",
        "invest",
        "stock",
        "stocks",
        "share",
        "shares",
        "valuation",
        "portfolio",
        "equity",
        "bond",
        "bonds",
        "dividend",
        "financial model",
        "dcf",
        "lbo",
        "merger",
        "acquisition",
    },
    "data_analysis": {
        "calculate",
        "calculation",
        "compute",
        "percentage",
        "percent",
        "statistics",
        "statistical",
        "dataset",
        "data analysis",
        "data processing",
        "csv",
        "excel",
        "spreadsheet",
        "forecast",
        "regression",
        "correlation",
    },
    "browser": {
        "open the website",
        "open this website",
        "open the url",
        "open this url",
        "go to the website",
        "go to this website",
        "browse this website",
        "browse this page",
        "read this page",
        "click",
        "login",
        "log in",
        "fill the form",
        "submit the form",
    },
    "github": {
        "github",
        "repository",
        "repo",
        "pull request",
        "pull requests",
        "issue",
        "issues",
        "commit",
        "branch",
        "github actions",
        "workflow",
        "codespace",
        "codespaces",
    },
    "automation": {
        "automate",
        "automation",
        "do this for me",
        "perform this task",
        "execute this",
        "carry this out",
        "complete this task",
        "take care of this",
        "handle this",
        "set this up",
    },
    "enterprise": {
        "enterprise",
        "organization",
        "organisation",
        "company-wide",
        "business process",
        "workflow automation",
        "enterprise agent",
        "internal operations",
        "employees",
        "department",
    },
    "image": {
        "image",
        "photo",
        "picture",
        "screenshot",
        "visual",
        "diagram",
        "logo",
        "design",
    },
    "video": {
        "video",
        "footage",
        "movie",
        "clip",
        "recording",
    },
    "voice": {
        "voice",
        "speech",
        "audio",
        "transcribe",
        "transcription",
        "spoken",
        "microphone",
    },
    "research": {
        "research",
        "analyze",
        "investigate",
        "study",
        "compare",
        "evidence",
        "sources",
        "literature",
        "deep research",
    },
}


# ============================================================
# ROUTE OBJECT
# ============================================================

@dataclass
class CapabilityRoute:
    """
    Structured representation of Falcon's capability decision.
    """

    capabilities: list[str] = field(
        default_factory=list
    )

    primary_capability: str = (
        "general_reasoning"
    )

    scores: dict[str, int] = field(
        default_factory=dict
    )

    requires_tools: bool = False

    requires_multiple_capabilities: bool = False

    confidence: float = 0.0

    reasons: dict[str, list[str]] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "capabilities": self.capabilities,
            "primary_capability": self.primary_capability,
            "scores": self.scores,
            "requires_tools": self.requires_tools,
            "requires_multiple_capabilities": (
                self.requires_multiple_capabilities
            ),
            "confidence": self.confidence,
            "reasons": self.reasons,
            "metadata": self.metadata,
        }


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_question(
    question: str,
) -> str:
    return " ".join(
        (question or "")
        .lower()
        .strip()
        .split()
    )


# ============================================================
# SCORING
# ============================================================

def _score_capability(
    question: str,
    capability: str,
) -> tuple[int, list[str]]:
    """
    Score a capability using deterministic signals.
    """

    signals = CAPABILITY_SIGNALS.get(
        capability,
        set(),
    )

    score = 0
    reasons = []

    for signal in signals:

        if signal in question:

            # Stronger weighting for phrases.
            weight = (
                2
                if " " in signal
                else 1
            )

            score += weight

            reasons.append(
                signal
            )

    return score, reasons


# ============================================================
# ROUTING
# ============================================================

def route_capabilities(
    question: str,
) -> CapabilityRoute:
    """
    Determine which Falcon capabilities should participate
    in solving a request.

    This layer does NOT execute anything.

    It only determines the capability graph that the rest of
    Falcon can use.
    """

    normalized = _normalize_question(
        question
    )

    if not normalized:

        return CapabilityRoute(
            capabilities=[
                "general_reasoning"
            ],
            primary_capability=(
                "general_reasoning"
            ),
            scores={
                "general_reasoning": 1
            },
            confidence=1.0,
        )

    scores = {}
    reasons = {}

    for capability in CAPABILITIES:

        score, matched = _score_capability(
            normalized,
            capability,
        )

        scores[capability] = score
        reasons[capability] = matched

    # --------------------------------------------------------
    # General reasoning is always available.
    # --------------------------------------------------------

    scores[
        "general_reasoning"
    ] = max(
        scores.get(
            "general_reasoning",
            0,
        ),
        1,
    )

    # --------------------------------------------------------
    # Rank capabilities.
    # --------------------------------------------------------

    ranked = sorted(
        scores.items(),
        key=lambda item: (
            item[1],
            CAPABILITIES.get(
                item[0],
                {},
            ).get(
                "priority",
                0,
            ),
        ),
        reverse=True,
    )

    selected = [
        capability
        for capability, score in ranked
        if score > 0
    ]

    # --------------------------------------------------------
    # Avoid activating every weak signal.
    # --------------------------------------------------------

    if not selected:

        selected = [
            "general_reasoning"
        ]

    else:

        highest_score = max(
            scores.get(
                capability,
                0,
            )
            for capability in selected
        )

        filtered = []

        for capability in selected:

            score = scores.get(
                capability,
                0,
            )

            if (
                score >= 2
                or capability
                == "general_reasoning"
                or score
                == highest_score
            ):
                filtered.append(
                    capability
                )

        selected = filtered

    # --------------------------------------------------------
    # Primary capability.
    # --------------------------------------------------------

    primary = selected[0]

    # General reasoning should not dominate a clearly
    # specialized request.
    if (
        primary
        == "general_reasoning"
        and len(selected) > 1
    ):

        specialized = [
            capability
            for capability in selected
            if capability
            != "general_reasoning"
        ]

        if specialized:

            primary = specialized[0]

    # --------------------------------------------------------
    # Tool requirement.
    # --------------------------------------------------------

    tool_capabilities = {
        "web",
        "documents",
        "data_analysis",
        "browser",
        "automation",
        "github",
        "image",
        "video",
        "voice",
    }

    requires_tools = bool(
        set(selected)
        & tool_capabilities
    )

    # --------------------------------------------------------
    # Multi-capability detection.
    # --------------------------------------------------------

    requires_multiple = (
        len(selected) > 1
    )

    # --------------------------------------------------------
    # Confidence.
    # --------------------------------------------------------

    highest = scores.get(
        primary,
        1,
    )

    second_scores = [
        score
        for capability, score in ranked
        if capability != primary
        and score > 0
    ]

    second = (
        second_scores[0]
        if second_scores
        else 0
    )

    if highest <= 1:

        confidence = 0.45

    elif highest >= 4:

        confidence = 0.90

    elif highest >= 2:

        confidence = 0.70

    else:

        confidence = 0.50

    # Ambiguous routing slightly reduces confidence.
    if second >= highest:

        confidence -= 0.15

    confidence = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    route = CapabilityRoute(
        capabilities=selected,
        primary_capability=primary,
        scores=scores,
        requires_tools=requires_tools,
        requires_multiple_capabilities=(
            requires_multiple
        ),
        confidence=round(
            confidence,
            4,
        ),
        reasons=reasons,
        metadata={
            "normalized_question": normalized,
        },
    )

    logger.info(
        "Falcon capability route: primary=%s capabilities=%s confidence=%.2f",
        route.primary_capability,
        route.capabilities,
        route.confidence,
    )

    return route


# ============================================================
# PUBLIC HELPERS
# ============================================================

def primary_capability(
    question: str,
) -> str:
    """
    Return Falcon's primary capability for a request.
    """

    return route_capabilities(
        question
    ).primary_capability


def selected_capabilities(
    question: str,
) -> list[str]:
    """
    Return all selected capabilities.
    """

    return route_capabilities(
        question
    ).capabilities


def requires_tools(
    question: str,
) -> bool:
    """
    Determine whether the request likely requires tools.
    """

    return route_capabilities(
        question
    ).requires_tools


def requires_multi_capability(
    question: str,
) -> bool:
    """
    Determine whether multiple capabilities should cooperate.
    """

    return route_capabilities(
        question
    ).requires_multiple_capabilities