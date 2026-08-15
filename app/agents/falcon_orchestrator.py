from __future__ import annotations
from typing import Any
from app.intelligence.reasoning import ReasoningController
from app.intelligence.planning import planner
from app.intelligence.model_router import model_router
from app.intelligence.reflection import ReflectionController
from app.intelligence.execution import ExecutionController
class FalconOrchestrator:
    """Top-level cognitive control plane. It coordinates, but does not fabricate completed actions."""
    def __init__(self): self.reasoning=ReasoningController(); self.reflection=ReflectionController(); self.execution=ExecutionController()
    def prepare(self,goal:str,context:dict[str,Any]|None=None)->dict[str,Any]:
        trace=self.reasoning.build(goal); plan=planner.create(goal); decision=model_router.choose(goal)
        return {"goal":goal,"context":context or {},"trace":trace,"plan":plan,"model":decision}
    def answer(self,goal:str,context:dict[str,Any]|None=None,**kwargs)->dict[str,Any]:
        state=self.prepare(goal,context); prompt=kwargs.pop("prompt",goal)
        text=model_router.generate(goal,prompt,**kwargs)
        state["response"]=text; state["verification"]={"response_generated":True}; return state
orchestrator=FalconOrchestrator()
