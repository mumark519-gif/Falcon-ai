from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any
@dataclass
class ContextWindow:
    system:str=''
    messages:list[dict[str,Any]]=field(default_factory=list)
    memories:list[str]=field(default_factory=list)
    documents:list[str]=field(default_factory=list)
    max_items:int=50
    def add(self,role:str,content:str,**meta):
        self.messages.append({"role":role,"content":content,**meta}); self.messages=self.messages[-self.max_items:]
    def as_prompt(self)->str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in self.messages)
