from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid

@dataclass
class PlanStep:
    id: str
    action: str
    tool: str | None = None
    requires_approval: bool = False
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"

@dataclass
class ExecutionPlan:
    id: str
    goal: str
    steps: list[PlanStep]
    success_criteria: list[str]

class Planner:
    def create(self, goal: str) -> ExecutionPlan:
        g=goal.strip()
        sid=lambda: str(uuid.uuid4())
        return ExecutionPlan(str(uuid.uuid4()),g,[
            PlanStep(sid(),"understand request"),
            PlanStep(sid(),"select capabilities"),
            PlanStep(sid(),"execute approved operations"),
            PlanStep(sid(),"verify outputs"),
            PlanStep(sid(),"synthesize response"),
        ],["all required operations completed","no unverified action is claimed"])
planner=Planner()
