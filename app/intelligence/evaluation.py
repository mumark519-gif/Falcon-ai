from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
@dataclass
class EvaluationCase:
    name:str
    prompt:str
    expected:Any
    evaluator:Callable[[Any,Any],bool]
class EvaluationSuite:
    def run_case(self,case:EvaluationCase,actual:Any)->dict[str,Any]:
        ok=bool(case.evaluator(case.expected,actual)); return {"name":case.name,"passed":ok,"expected":case.expected,"actual":actual}
    def score(self,results:list[dict[str,Any]])->float:
        return sum(1 for r in results if r["passed"])/len(results) if results else 0.0
