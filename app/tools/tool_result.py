from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    tool: str
    status: str

    output: Any = None
    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "attempts": self.attempts,
        }

    @classmethod
    def success(
        cls,
        tool: str,
        output: Any,
        attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> "ToolResult":

        return cls(
            tool=tool,
            status="success",
            output=output,
            attempts=attempts,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        tool: str,
        error: str,
        attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> "ToolResult":

        return cls(
            tool=tool,
            status="error",
            error=error,
            attempts=attempts,
            metadata=metadata or {},
        )

    @classmethod
    def permission_required(
        cls,
        tool: str,
    ) -> "ToolResult":

        return cls(
            tool=tool,
            status="permission_required",
            error=(
                "User permission is required "
                "before this tool can execute."
            ),
        )

    @classmethod
    def blocked(
        cls,
        tool: str,
        reason: str,
    ) -> "ToolResult":

        return cls(
            tool=tool,
            status="blocked",
            error=reason,
        )