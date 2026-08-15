from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolDefinition:
    name: str
    description: str
    executor: Callable[..., Any]

    requires_permission: bool = False
    retryable: bool = True


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        executor: Callable[..., Any],
        requires_permission: bool = False,
        retryable: bool = True,
    ) -> None:

        name = name.strip().lower()

        if not name:
            raise ValueError(
                "Tool name cannot be empty."
            )

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            executor=executor,
            requires_permission=requires_permission,
            retryable=retryable,
        )

    def get(
        self,
        name: str,
    ) -> ToolDefinition | None:

        if not name:
            return None

        return self._tools.get(
            name.strip().lower()
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return self.get(name) is not None

    def names(self) -> list[str]:
        return list(
            self._tools.keys()
        )

    def all(self) -> dict[str, ToolDefinition]:
        return dict(
            self._tools
        )

    def clear(self) -> None:
        self._tools.clear()


registry = ToolRegistry()