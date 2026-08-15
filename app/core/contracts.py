from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class ToolRequest:
    name: str
    arguments: dict[str,Any] = field(default_factory=dict)
    requires_approval: bool = False

@dataclass
class ToolResult:
    name: str
    success: bool
    data: Any = None
    error: str|None = None
    metadata: dict[str,Any] = field(default_factory=dict)

@dataclass
class AgentTask:
    id: str
    goal: str
    user: str|None = None
    context: dict[str,Any] = field(default_factory=dict)
    steps: list[dict[str,Any]] = field(default_factory=list)
    status: str = "created"

@dataclass
class ProviderResponse:
    provider: str
    model: str
    text: str
    raw: Any = None
    usage: dict[str,Any] = field(default_factory=dict)
