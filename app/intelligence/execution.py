from __future__ import annotations
from typing import Any, Callable
from dataclasses import dataclass
@dataclass
class ExecutionResult:
    success:bool
    output:Any=None
    error:str|None=None
    attempts:int=1
class ExecutionController:
    def run(self,fn:Callable[[],Any],retries:int=2)->ExecutionResult:
        last=None
        for attempt in range(1,retries+2):
            try:return ExecutionResult(True,fn(),None,attempt)
            except Exception as e:last=str(e)
        return ExecutionResult(False,None,last,retries+1)
