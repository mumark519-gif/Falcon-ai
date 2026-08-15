from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import time, uuid
@dataclass
class Memory:
    id: str
    user_id: str
    text: str
    kind: str
    importance: float
    created_at: float
class MemoryController:
    def __init__(self): self._items: list[Memory]=[]
    def add(self,user_id:str,text:str,kind:str="semantic",importance:float=.5)->Memory:
        m=Memory(str(uuid.uuid4()),user_id,text,kind,max(0,min(1,importance)),time.time()); self._items.append(m); return m
    def search(self,user_id:str,query:str,limit:int=10)->list[Memory]:
        q=set(query.lower().split())
        items=[m for m in self._items if m.user_id==user_id]
        scored=sorted(items,key=lambda m:(len(q & set(m.text.lower().split()))+m.importance),reverse=True)
        return scored[:limit]
memory_controller=MemoryController()
