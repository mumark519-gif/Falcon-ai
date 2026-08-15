from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
@dataclass
class CodingTask:
    goal:str
    repository:str|None=None
    files:list[str]=field(default_factory=list)
    tests:list[str]=field(default_factory=list)
    status:str="planned"
class CodingController:
    def inspect_tree(self,root:str,limit:int=500)->list[str]:
        p=Path(root); return [str(x.relative_to(p)) for x in p.rglob("*") if x.is_file()][:limit]
    def create_task(self,goal:str,repository:str|None=None)->CodingTask: return CodingTask(goal,repository)
