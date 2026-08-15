from __future__ import annotations
from app.intelligence.computer_use import Action,ComputerUsePolicy
class ComputerCapability:
    def __init__(self):self.policy=ComputerUsePolicy()
    def authorize(self,kind:str,target:str|None=None,value:str|None=None,approved:bool=False):return self.policy.authorize(Action(kind,target,value),approved)
