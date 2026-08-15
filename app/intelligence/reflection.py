from __future__ import annotations
from typing import Any
class ReflectionController:
    def inspect(self, result: dict[str, Any]) -> dict[str, Any]:
        errors=[]
        if result.get("error"): errors.append(result["error"])
        if result.get("executed") is False and result.get("status")=="complete": errors.append("execution not confirmed")
        return {"passed": not errors, "issues": errors, "retry_recommended": bool(errors)}
