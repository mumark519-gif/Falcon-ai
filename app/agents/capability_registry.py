from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


# ============================================================
# FALCON UNIVERSAL CAPABILITY REGISTRY
# ============================================================
#
# This registry is the central description of what Falcon can
# do.
#
# It does NOT execute capabilities itself.
#
# It tells the planner / worker:
#
#     - what capabilities exist
#     - what category they belong to
#     - whether they are read-only
#     - whether they modify the outside world
#     - whether permission is required
#     - what input they expect
#
# Actual execution remains inside the appropriate executor.
#
# This lets Falcon grow without rewriting the orchestrator
# every time a new capability is added.
# ============================================================


# ============================================================
# CAPABILITY CATEGORIES
# ============================================================

CATEGORY_REASONING = "reasoning"
CATEGORY_RESEARCH = "research"
CATEGORY_CODE = "coding"
CATEGORY_WEB = "web"
CATEGORY_BROWSER = "browser"
CATEGORY_FILES = "files"
CATEGORY_DOCUMENTS = "documents"
CATEGORY_MEDIA = "media"
CATEGORY_COMMUNICATION = "communication"
CATEGORY_AUTOMATION = "automation"
CATEGORY_DEVELOPER = "developer"
CATEGORY_BUSINESS = "business"
CATEGORY_ENTERPRISE = "enterprise"
CATEGORY_SYSTEM = "system"


# ============================================================
# CAPABILITY DATA MODEL
# ============================================================

@dataclass(frozen=True)
class Capability:
    """
    Description of one Falcon capability.

    A capability is metadata describing an available action.

    Execution is intentionally separated from this registry.
    """

    name: str
    description: str
    category: str

    input_type: str = "text"

    read_only: bool = True

    requires_permission: bool = False

    external_side_effect: bool = False

    requires_authentication: bool = False

    enabled: bool = True

    tags: tuple[str, ...] = field(
        default_factory=tuple
    )


# ============================================================
# CAPABILITY REGISTRY
# ============================================================

class CapabilityRegistry:
    """
    Central registry for Falcon's capabilities.
    """

    def __init__(self) -> None:

        self._capabilities: dict[
            str,
            Capability,
        ] = {}

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    def register(
        self,
        capability: Capability,
    ) -> Capability:

        if not isinstance(
            capability,
            Capability,
        ):
            raise TypeError(
                "Capability must be a Capability instance."
            )

        name = (
            capability.name
            .strip()
            .lower()
        )

        if not name:
            raise ValueError(
                "Capability name cannot be empty."
            )

        if name in self._capabilities:
            raise ValueError(
                f"Capability already registered: {name}"
            )

        self._capabilities[name] = capability

        return capability

    # --------------------------------------------------------
    # Replace / update
    # --------------------------------------------------------

    def upsert(
        self,
        capability: Capability,
    ) -> Capability:

        if not isinstance(
            capability,
            Capability,
        ):
            raise TypeError(
                "Capability must be a Capability instance."
            )

        name = (
            capability.name
            .strip()
            .lower()
        )

        if not name:
            raise ValueError(
                "Capability name cannot be empty."
            )

        self._capabilities[name] = capability

        return capability

    # --------------------------------------------------------
    # Lookup
    # --------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> Capability | None:

        if not name:
            return None

        return self._capabilities.get(
            str(name).strip().lower()
        )

    # --------------------------------------------------------
    # Existence
    # --------------------------------------------------------

    def exists(
        self,
        name: str,
    ) -> bool:

        return self.get(name) is not None

    # --------------------------------------------------------
    # Remove
    # --------------------------------------------------------

    def remove(
        self,
        name: str,
    ) -> bool:

        normalized = (
            str(name)
            .strip()
            .lower()
        )

        if normalized not in self._capabilities:
            return False

        del self._capabilities[
            normalized
        ]

        return True

    # --------------------------------------------------------
    # List
    # --------------------------------------------------------

    def all(
        self,
        enabled_only: bool = True,
    ) -> list[Capability]:

        capabilities = list(
            self._capabilities.values()
        )

        if enabled_only:

            capabilities = [
                capability
                for capability in capabilities
                if capability.enabled
            ]

        return capabilities

    # --------------------------------------------------------
    # Category lookup
    # --------------------------------------------------------

    def by_category(
        self,
        category: str,
        enabled_only: bool = True,
    ) -> list[Capability]:

        normalized = (
            str(category)
            .strip()
            .lower()
        )

        return [
            capability
            for capability in self.all(
                enabled_only=enabled_only
            )
            if capability.category.lower()
            == normalized
        ]

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    def search(
        self,
        query: str,
        enabled_only: bool = True,
    ) -> list[Capability]:

        query = (
            str(query or "")
            .strip()
            .lower()
        )

        if not query:
            return []

        tokens = query.split()

        scored: list[
            tuple[int, Capability]
        ] = []

        for capability in self.all(
            enabled_only=enabled_only
        ):

            searchable = " ".join(
                [
                    capability.name,
                    capability.description,
                    capability.category,
                    capability.input_type,
                    *capability.tags,
                ]
            ).lower()

            score = 0

            for token in tokens:

                if token in searchable:
                    score += 1

            if score > 0:

                scored.append(
                    (
                        score,
                        capability,
                    )
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            capability
            for _, capability in scored
        ]

    # --------------------------------------------------------
    # Planner-facing representation
    # --------------------------------------------------------

    def describe(
        self,
        enabled_only: bool = True,
    ) -> list[dict[str, Any]]:

        return [
            {
                "name": capability.name,
                "description": capability.description,
                "category": capability.category,
                "input_type": capability.input_type,
                "read_only": capability.read_only,
                "requires_permission": (
                    capability.requires_permission
                ),
                "external_side_effect": (
                    capability.external_side_effect
                ),
                "requires_authentication": (
                    capability.requires_authentication
                ),
                "enabled": capability.enabled,
                "tags": list(
                    capability.tags
                ),
            }
            for capability in self.all(
                enabled_only=enabled_only
            )
        ]


# ============================================================
# GLOBAL REGISTRY
# ============================================================

capability_registry = CapabilityRegistry()


# ============================================================
# CORE FALCON CAPABILITIES
# ============================================================
#
# These describe Falcon's intended capability surface.
#
# Some are already partially implemented.
# Others will be connected to executors as we build them.
# ============================================================

_CORE_CAPABILITIES = [

    # --------------------------------------------------------
    # REASONING
    # --------------------------------------------------------

    Capability(
        name="reasoning",
        description=(
            "Analyze problems, compare alternatives, "
            "derive conclusions, and reason through tasks."
        ),
        category=CATEGORY_REASONING,
        tags=(
            "analysis",
            "reasoning",
            "problem solving",
            "logic",
        ),
    ),

    Capability(
        name="planning",
        description=(
            "Break complex user requests into executable "
            "steps and plans."
        ),
        category=CATEGORY_REASONING,
        tags=(
            "planner",
            "task planning",
            "workflow",
        ),
    ),

    Capability(
        name="multi_agent_reasoning",
        description=(
            "Use multiple specialist analyses and reconcile "
            "their findings."
        ),
        category=CATEGORY_REASONING,
        tags=(
            "agents",
            "collaboration",
            "specialists",
        ),
    ),

    # --------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------

    Capability(
        name="web_search",
        description=(
            "Search the web for current or external "
            "information."
        ),
        category=CATEGORY_RESEARCH,
        tags=(
            "internet",
            "search",
            "research",
            "current information",
        ),
    ),

    Capability(
        name="research",
        description=(
            "Conduct structured research using available "
            "information sources."
        ),
        category=CATEGORY_RESEARCH,
        tags=(
            "research",
            "investigation",
            "evidence",
        ),
    ),

    Capability(
        name="document_search",
        description=(
            "Search connected or uploaded documents for "
            "relevant information."
        ),
        category=CATEGORY_DOCUMENTS,
        tags=(
            "documents",
            "files",
            "knowledge",
            "retrieval",
        ),
    ),

    # --------------------------------------------------------
    # CODING
    # --------------------------------------------------------

    Capability(
        name="code_generation",
        description=(
            "Write code, scripts, modules, applications, "
            "and software components."
        ),
        category=CATEGORY_CODE,
        tags=(
            "coding",
            "programming",
            "software",
        ),
    ),

    Capability(
        name="code_analysis",
        description=(
            "Inspect, explain, debug, and improve source code."
        ),
        category=CATEGORY_CODE,
        tags=(
            "debugging",
            "code review",
            "software engineering",
        ),
    ),

    Capability(
        name="python_execution",
        description=(
            "Execute Python for calculations, analysis, "
            "data processing, and computational tasks."
        ),
        category=CATEGORY_CODE,
        input_type="code",
        read_only=True,
        tags=(
            "python",
            "computation",
            "data analysis",
        ),
    ),

    # --------------------------------------------------------
    # WEB / BROWSER
    # --------------------------------------------------------

    Capability(
        name="browser_navigation",
        description=(
            "Navigate websites and interact with web pages."
        ),
        category=CATEGORY_BROWSER,
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "browser",
            "web",
            "navigation",
        ),
    ),

    Capability(
        name="web_interaction",
        description=(
            "Interact with web applications and online "
            "services when authorized."
        ),
        category=CATEGORY_BROWSER,
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "browser",
            "web app",
            "automation",
        ),
    ),

    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    Capability(
        name="file_read",
        description=(
            "Read files supplied to Falcon or available "
            "through authorized connections."
        ),
        category=CATEGORY_FILES,
        tags=(
            "files",
            "documents",
            "read",
        ),
    ),

    Capability(
        name="file_write",
        description=(
            "Create or modify files when explicitly "
            "authorized."
        ),
        category=CATEGORY_FILES,
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "files",
            "write",
            "create",
            "modify",
        ),
    ),

    # --------------------------------------------------------
    # MEDIA
    # --------------------------------------------------------

    Capability(
        name="image_understanding",
        description=(
            "Analyze images and extract useful visual "
            "information."
        ),
        category=CATEGORY_MEDIA,
        input_type="image",
        tags=(
            "vision",
            "image",
            "visual",
        ),
    ),

    Capability(
        name="image_generation",
        description=(
            "Generate images from natural-language "
            "instructions."
        ),
        category=CATEGORY_MEDIA,
        input_type="text",
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "image",
            "generation",
            "design",
        ),
    ),

    Capability(
        name="video_understanding",
        description=(
            "Analyze video content and extract useful "
            "information."
        ),
        category=CATEGORY_MEDIA,
        input_type="video",
        tags=(
            "video",
            "vision",
        ),
    ),

    Capability(
        name="video_generation",
        description=(
            "Generate or transform video when supported "
            "by connected media systems."
        ),
        category=CATEGORY_MEDIA,
        input_type="text",
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "video",
            "generation",
            "media",
        ),
    ),

    # --------------------------------------------------------
    # COMMUNICATION
    # --------------------------------------------------------

    Capability(
        name="voice_input",
        description=(
            "Understand spoken user instructions."
        ),
        category=CATEGORY_COMMUNICATION,
        input_type="audio",
        tags=(
            "voice",
            "speech",
            "audio",
        ),
    ),

    Capability(
        name="voice_output",
        description=(
            "Produce spoken responses."
        ),
        category=CATEGORY_COMMUNICATION,
        input_type="text",
        tags=(
            "voice",
            "speech",
            "audio",
        ),
    ),

    # --------------------------------------------------------
    # AUTOMATION
    # --------------------------------------------------------

    Capability(
        name="task_automation",
        description=(
            "Execute authorized multi-step tasks across "
            "connected tools and services."
        ),
        category=CATEGORY_AUTOMATION,
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "automation",
            "worker",
            "tasks",
            "agent",
        ),
    ),

    Capability(
        name="autonomous_worker",
        description=(
            "Continue an authorized task through multiple "
            "execution steps while monitoring progress."
        ),
        category=CATEGORY_AUTOMATION,
        read_only=False,
        requires_permission=True,
        external_side_effect=True,
        tags=(
            "worker",
            "autonomous",
            "agent",
        ),
    ),

    # --------------------------------------------------------
    # DEVELOPER / GITHUB
    # --------------------------------------------------------

    Capability(
        name="github",
        description=(
            "Work with authorized GitHub repositories, "
            "issues, branches, pull requests, and code."
        ),
        category=CATEGORY_DEVELOPER,
        read_only=False,
        requires_permission=True,
        requires_authentication=True,
        external_side_effect=True,
        tags=(
            "github",
            "git",
            "repository",
            "developer",
        ),
    ),

    # --------------------------------------------------------
    # BUSINESS
    # --------------------------------------------------------

    Capability(
        name="business_analysis",
        description=(
            "Analyze businesses, markets, strategies, "
            "operations, and commercial decisions."
        ),
        category=CATEGORY_BUSINESS,
        tags=(
            "business",
            "strategy",
            "analysis",
        ),
    ),

    Capability(
        name="investment_analysis",
        description=(
            "Analyze investments, financial information, "
            "valuation, and investment decisions."
        ),
        category=CATEGORY_BUSINESS,
        tags=(
            "investment",
            "finance",
            "valuation",
        ),
    ),

    # --------------------------------------------------------
    # ENTERPRISE
    # --------------------------------------------------------

    Capability(
        name="enterprise_agent",
        description=(
            "Perform authorized enterprise workflows using "
            "business data, tools, documents, and automation."
        ),
        category=CATEGORY_ENTERPRISE,
        read_only=False,
        requires_permission=True,
        requires_authentication=True,
        external_side_effect=True,
        tags=(
            "enterprise",
            "business",
            "agent",
            "automation",
        ),
    ),
]


# ============================================================
# REGISTER CORE CAPABILITIES
# ============================================================

for _capability in _CORE_CAPABILITIES:

    capability_registry.upsert(
        _capability
    )


# ============================================================
# PUBLIC HELPERS
# ============================================================

def get_capability(
    name: str,
) -> Capability | None:

    return capability_registry.get(
        name
    )


def list_capabilities(
    enabled_only: bool = True,
) -> list[Capability]:

    return capability_registry.all(
        enabled_only=enabled_only
    )


def search_capabilities(
    query: str,
) -> list[Capability]:

    return capability_registry.search(
        query
    )


def describe_capabilities() -> list[dict[str, Any]]:

    return capability_registry.describe()


def capabilities_for_category(
    category: str,
) -> list[Capability]:

    return capability_registry.by_category(
        category
    )


# ============================================================
# CAPABILITY EXECUTION ADAPTER
# ============================================================

def execute_capability(
    name: str,
    executor: Callable[..., Any],
    **kwargs: Any,
) -> Any:
    """
    Execute a registered capability through an external
    executor.

    The registry deliberately does not know how individual
    capabilities are implemented.

    This prevents the registry from becoming a giant
    conditional execution file.
    """

    capability = get_capability(
        name
    )

    if capability is None:

        raise ValueError(
            f"Unknown Falcon capability: {name}"
        )

    if not capability.enabled:

        raise RuntimeError(
            f"Capability is disabled: {name}"
        )

    if not callable(executor):

        raise TypeError(
            "Capability executor must be callable."
        )

    return executor(
        capability=capability,
        **kwargs,
    )


# ============================================================
# INITIALIZATION CHECK
# ============================================================

def capability_health() -> dict[str, Any]:

    capabilities = list_capabilities()

    categories = {}

    for capability in capabilities:

        category = capability.category

        categories.setdefault(
            category,
            0,
        )

        categories[
            category
        ] += 1

    return {
        "status": "ok",
        "total_capabilities": len(
            capabilities
        ),
        "categories": categories,
        "capabilities": [
            capability.name
            for capability in capabilities
        ],
    }