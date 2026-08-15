from __future__ import annotations


READ_ONLY_TOOLS = {
    "web_search",
    "document_search",
}


APPROVAL_REQUIRED_TOOLS = {
    "python",
    "browser",
}


def requires_permission(
    tool: str,
) -> bool:

    return (
        tool.strip().lower()
        in APPROVAL_REQUIRED_TOOLS
    )


def is_read_only(
    tool: str,
) -> bool:

    return (
        tool.strip().lower()
        in READ_ONLY_TOOLS
    )


def validate_permission(
    tool: str,
    approved: bool = False,
) -> dict:

    tool = tool.strip().lower()

    if not tool:

        return {
            "allowed": False,
            "requires_permission": False,
            "reason": "Tool name is missing.",
        }

    if is_read_only(tool):

        return {
            "allowed": True,
            "requires_permission": False,
            "reason": "Read-only tool.",
        }

    if requires_permission(tool):

        if not approved:

            return {
                "allowed": False,
                "requires_permission": True,
                "reason": (
                    "User approval is required."
                ),
            }

        return {
            "allowed": True,
            "requires_permission": True,
            "reason": (
                "User approval received."
            ),
        }

    return {
        "allowed": True,
        "requires_permission": False,
        "reason": "Tool is allowed.",
    }