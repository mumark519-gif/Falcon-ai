from __future__ import annotations
from pathlib import Path
class Sandbox:
    def __init__(self,root:str="./data/sandbox"): self.root=Path(root).resolve(); self.root.mkdir(parents=True,exist_ok=True)
    def safe_path(self,relative:str)->Path:
        p=(self.root/relative).resolve()
        if self.root not in p.parents and p != self.root: raise PermissionError("Path escapes Falcon sandbox")
        return p
