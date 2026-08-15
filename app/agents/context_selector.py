from typing import Any


AGENT_CONTEXT_RULES = {
    "BUSINESS": {
        "always": [
            "memory",
            "business",
            "research",
        ],
        "optional": [
            "web",
            "documents",
            "coding",
            "investment",
        ],
    },
    "CODING": {
        "always": [
            "memory",
            "coding",
        ],
        "optional": [
            "documents",
            "web",
            "research",
        ],
    },
    "INVESTMENT": {
        "always": [
            "memory",
            "investment",
            "research",
        ],
        "optional": [
            "web",
            "documents",
            "business",
        ],
    },
    "RESEARCH": {
        "always": [
            "memory",
            "research",
            "web",
            "documents",
        ],
        "optional": [
            "business",
            "investment",
            "coding",
        ],
    },
}


def select_context(
    agent: str,
    context: dict[str, Any] | None,
):
    """
    Select the most relevant shared context for an agent.

    Unknown context keys are preserved only when they are explicitly
    listed as optional for that agent.
    """

    if not context:
        return {}

    agent_name = agent.upper()

    rules = AGENT_CONTEXT_RULES.get(
        agent_name,
        {
            "always": [],
            "optional": [],
        },
    )

    selected = {}

    allowed_keys = set(
        rules["always"]
        + rules["optional"]
    )

    for key, value in context.items():

        if key in allowed_keys:
            selected[key] = value

    return selected