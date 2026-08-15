"""Compatibility registry backed by the canonical ToolRegistry.

Legacy callers use ``get_tool``/``list_tools`` while the execution layer uses
``app.tools.tool_registry.registry``. Keeping one source of truth prevents
duplicate tool definitions.
"""
from __future__ import annotations

from typing import Any, Callable

from app.tools.tool_registry import registry

def register_tool(name: str, func: Callable[..., Any]) -> None:
    registry.register(
        name=name,
        description=getattr(func, "__doc__", None) or f"Falcon {name} tool",
        executor=func,
        requires_permission=name in {"python", "browser"},
        retryable=name != "python",
    )

def get_tool(name: str):
    definition = registry.get(name)
    return definition.executor if definition else None

def list_tools() -> list[str]:
    _ensure_defaults()
    return registry.names()

def _ensure_defaults():
    if registry.names():
        return
    try:
        from app.tools.tool_manager import register_default_tools
        register_default_tools()
    except Exception:
        # Keep registration lazy and non-fatal during import/collection.
        pass
