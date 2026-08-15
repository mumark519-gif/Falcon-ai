from __future__ import annotations
from dataclasses import dataclass
from typing import Callable,Any
@dataclass
class AutonomyPolicy:
    max_steps:int=20
    max_retries:int=3
    require_confirmation_for_side_effects:bool=True
class AutonomousLoop:
    def __init__(self,policy=None):self.policy=policy or AutonomyPolicy()
    def run(self,step:Callable[[int],Any],verify:Callable[[Any],bool])->dict[str,Any]:
        history=[]
        for i in range(self.policy.max_steps):
            out=step(i); history.append(out)
            if verify(out): return {"success":True,"steps":i+1,"history":history}
        return {"success":False,"steps":self.policy.max_steps,"history":history,"error":"max_steps_reached"}
