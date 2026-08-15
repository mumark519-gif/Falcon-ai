from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


# ============================================================
# TOOL DEFINITION
# ============================================================


@dataclass
class ToolDefinition:
    """
    Canonical definition of a Falcon capability/tool.

    Every executable capability should eventually be registered
    through this structure.

    Examples:

        web_search
        browser
        python
        files
        github
        image_generation
        voice
        plugins
        etc.
    """

    name: str

    description: str

    handler: Callable[..., Any]

    category: str = "general"

    requires_permission: bool = False

    requires_confirmation: bool = False

    enabled: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# TOOL REGISTRY
# ============================================================


class ToolRegistry:
    """
    Central registry for Falcon executable capabilities.

    The registry is deliberately independent from the LLM.

    The AI decides what it wants to accomplish.

    The registry determines which actual executable capability
    corresponds to that request.
    """

    def __init__(self) -> None:

        self._tools: dict[
            str,
            ToolDefinition,
        ] = {}


    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    def register(
        self,
        tool: ToolDefinition,
    ) -> None:

        if not isinstance(
            tool,
            ToolDefinition,
        ):
            raise TypeError(
                "tool must be a ToolDefinition."
            )

        name = (
            str(tool.name or "")
            .strip()
            .lower()
        )

        if not name:
            raise ValueError(
                "Tool name cannot be empty."
            )

        if name in self._tools:
            raise ValueError(
                f"Tool '{name}' is already registered."
            )

        tool.name = name

        self._tools[name] = tool


    # --------------------------------------------------------
    # REMOVE
    # --------------------------------------------------------

    def unregister(
        self,
        name: str,
    ) -> bool:

        name = (
            str(name or "")
            .strip()
            .lower()
        )

        if name not in self._tools:
            return False

        del self._tools[name]

        return True


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> ToolDefinition | None:

        name = (
            str(name or "")
            .strip()
            .lower()
        )

        return self._tools.get(
            name
        )


    # --------------------------------------------------------
    # EXISTS
    # --------------------------------------------------------

    def exists(
        self,
        name: str,
    ) -> bool:

        return (
            self.get(name)
            is not None
        )


    # --------------------------------------------------------
    # ENABLE / DISABLE
    # --------------------------------------------------------

    def enable(
        self,
        name: str,
    ) -> bool:

        tool = self.get(name)

        if tool is None:
            return False

        tool.enabled = True

        return True


    def disable(
        self,
        name: str,
    ) -> bool:

        tool = self.get(name)

        if tool is None:
            return False

        tool.enabled = False

        return True


    # --------------------------------------------------------
    # LIST
    # --------------------------------------------------------

    def list_tools(
        self,
        *,
        enabled_only: bool = True,
        category: str | None = None,
    ) -> list[ToolDefinition]:

        tools = list(
            self._tools.values()
        )

        if enabled_only:

            tools = [
                tool
                for tool in tools
                if tool.enabled
            ]

        if category:

            category = (
                str(category)
                .strip()
                .lower()
            )

            tools = [
                tool
                for tool in tools
                if tool.category.lower()
                == category
            ]

        return tools


    # --------------------------------------------------------
    # DESCRIPTIONS
    # --------------------------------------------------------

    def describe_tools(
        self,
    ) -> list[dict[str, Any]]:

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "requires_permission": (
                    tool.requires_permission
                ),
                "requires_confirmation": (
                    tool.requires_confirmation
                ),
                "enabled": tool.enabled,
                "metadata": tool.metadata,
            }
            for tool in self.list_tools()
        ]


    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    def execute(
        self,
        name: str,
        **kwargs: Any,
    ) -> Any:

        tool = self.get(name)

        if tool is None:

            raise KeyError(
                f"Tool '{name}' is not registered."
            )

        if not tool.enabled:

            raise RuntimeError(
                f"Tool '{name}' is disabled."
            )

        return tool.handler(
            **kwargs
        )


# ============================================================
# GLOBAL REGISTRY
# ============================================================


tool_registry = ToolRegistry()