from __future__ import annotations


# ============================================================
# TOOL POLICY
# ============================================================

READ_ONLY_TOOLS = {
    "web_search",
    "document_search",
}


# Tools that normally perform actions requiring approval.
APPROVAL_REQUIRED_TOOLS = {
    "browser",
}


# Deterministic/safe tools that Falcon may execute automatically.
# Python is allowed here because Falcon's Python tool is used for
# controlled computation and analysis.
AUTO_ALLOWED_TOOLS = {
    "python",
}


# ============================================================
# POLICY HELPERS
# ============================================================

def requires_permission(
    tool: str,
    tool_input: str = "",
) -> bool:
    """
    Determine whether a tool requires user approval.

    Python is automatically allowed for deterministic computation.
    Browser remains approval-gated because it can interact with
    external systems/pages.
    """

    tool_name = (
        str(tool or "")
        .strip()
        .lower()
    )

    if tool_name in AUTO_ALLOWED_TOOLS:
        return False

    return tool_name in APPROVAL_REQUIRED_TOOLS


def is_read_only(
    tool: str,
) -> bool:
    """
    Determine whether a tool is read-only.
    """

    return (
        str(tool or "")
        .strip()
        .lower()
        in READ_ONLY_TOOLS
    )


def is_auto_allowed(
    tool: str,
    tool_input: str = "",
) -> bool:
    """
    Determine whether Falcon can execute the tool automatically.
    """

    tool_name = (
        str(tool or "")
        .strip()
        .lower()
    )

    return tool_name in AUTO_ALLOWED_TOOLS


# ============================================================
# PERMISSION VALIDATION
# ============================================================

def validate_permission(
    tool: str,
    approved: bool = False,
    tool_input: str = "",
) -> dict:
    """
    Validate whether Falcon may execute a tool.

    Policy:

    - web_search       -> automatically allowed
    - document_search  -> automatically allowed
    - python           -> automatically allowed
    - browser          -> requires explicit approval
    - unknown tools    -> allowed by default only when they are
                           not registered as approval-gated

    The important distinction is that deterministic Python
    computation does NOT require user approval.
    """

    tool_name = (
        str(tool or "")
        .strip()
        .lower()
    )

    if not tool_name:
        return {
            "allowed": False,
            "requires_permission": False,
            "reason": "Tool name is missing.",
        }

    # --------------------------------------------------------
    # Read-only tools
    # --------------------------------------------------------

    if is_read_only(tool_name):

        return {
            "allowed": True,
            "requires_permission": False,
            "reason": "Read-only tool.",
        }

    # --------------------------------------------------------
    # Safe deterministic tools
    # --------------------------------------------------------

    if is_auto_allowed(
        tool_name,
        tool_input,
    ):

        return {
            "allowed": True,
            "requires_permission": False,
            "reason": "Safe deterministic computation.",
        }

    # --------------------------------------------------------
    # Approval-required tools
    # --------------------------------------------------------

    if requires_permission(
        tool_name,
        tool_input,
    ):

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

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    return {
        "allowed": True,
        "requires_permission": False,
        "reason": "Tool is allowed.",
    }