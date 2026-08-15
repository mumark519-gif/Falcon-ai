from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any,Callable
@dataclass
class ToolSpec:
    name:str
    description:str
    handler:Callable[...,Any]
    read_only:bool=True
    requires_approval:bool=False
    input_schema:dict[str,Any]=field(default_factory=dict)
