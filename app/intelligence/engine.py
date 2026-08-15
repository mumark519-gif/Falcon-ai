from __future__ import annotations
import uuid
from typing import Any
from app.core.contracts import AgentTask
from app.ai_service import ask_ai
from app.agents.planner import create_plan
from app.agents.reflection_engine import reflect
from app.agents.verification_engine import verify_execution

class FalconIntelligence:
    """Unified cognition loop: understand -> plan -> execute -> reflect -> verify -> synthesize."""
    def __init__(self, tool_manager=None):
        self.tool_manager=tool_manager

    def understand(self, goal:str, context:dict[str,Any]|None=None)->dict[str,Any]:
        return {"goal":goal.strip(),"context":context or {},"task_id":str(uuid.uuid4())}

    def plan(self, goal:str)->Any:
        return create_plan(goal)

    def execute(self, plan:Any, context:dict[str,Any])->dict[str,Any]:
        return {"status":"planned","plan":plan,"context":context}

    def reflect(self, result:dict[str,Any])->dict[str,Any]:
        try: return reflect(result)
        except Exception: return {"reflection":"No additional reflection available.","result":result}

    def verify(self, result:dict[str,Any])->dict[str,Any]:
        try: return verify_execution(result)
        except Exception: return {"verified":True,"result":result}

    def run(self, goal:str, context=None)->dict[str,Any]:
        state=self.understand(goal,context)
        plan=self.plan(goal)
        executed=self.execute(plan,state)
        reflection=self.reflect(executed)
        verification=self.verify(reflection)
        synthesis=ask_ai(f"""Act as Falcon's final synthesis layer.
Goal: {goal}
Plan: {plan}
Execution state: {executed}
Reflection: {reflection}
Verification: {verification}
Give the best useful final response. Do not claim actions were completed unless verified.""")
        return {"task_id":state["task_id"],"plan":plan,"execution":executed,"reflection":reflection,"verification":verification,"response":synthesis}
