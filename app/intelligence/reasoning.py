from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ReasoningStep:
    name: str
    purpose: str
    status: str = "pending"
    output: Any = None

@dataclass
class ReasoningTrace:
    goal: str
    steps: list[ReasoningStep] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

class ReasoningController:
    """Deterministic control plane around model reasoning; hidden chain-of-thought is never persisted."""
    def build(self, goal: str) -> ReasoningTrace:
        return ReasoningTrace(goal=goal, steps=[
            ReasoningStep("understand", "identify objective, constraints and missing inputs"),
            ReasoningStep("decompose", "split the objective into verifiable sub-tasks"),
            ReasoningStep("plan", "choose tools, dependencies and execution order"),
            ReasoningStep("execute", "perform approved tool operations"),
            ReasoningStep("verify", "check outputs against explicit success criteria"),
            ReasoningStep("synthesize", "produce the user-facing result"),
        ])

    def next_step(self, trace: ReasoningTrace) -> ReasoningStep | None:
        for step in trace.steps:
            if step.status == "pending": return step
        return None

    def mark(self, trace: ReasoningTrace, name: str, output: Any=None, status: str="complete") -> None:
        for step in trace.steps:
            if step.name == name:
                step.status=status; step.output=output; return
