from __future__ import annotations
from dataclasses import dataclass
@dataclass
class Action:
    kind:str
    target:str|None=None
    value:str|None=None
    requires_confirmation:bool=True
class ComputerUsePolicy:
    SAFE={"screenshot","move_mouse","click","type_text","scroll","navigate"}
    SENSITIVE={"download","upload","purchase","send_message","delete","submit_form"}
    def authorize(self,action:Action,approved:bool=False)->bool:
        if action.kind in self.SENSITIVE: return approved
        return action.kind in self.SAFE
