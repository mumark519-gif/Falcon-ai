from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class SecurityPolicy:
    allowed_tools:set[str]=field(default_factory=set)
    require_approval_for:set[str]=field(default_factory=lambda:{"delete","purchase","send_message","publish","create_pull_request"})
    max_file_bytes:int=10_000_000
    def can_use(self,tool:str)->bool:return not self.allowed_tools or tool in self.allowed_tools
    def needs_approval(self,tool:str)->bool:return tool in self.require_approval_for
