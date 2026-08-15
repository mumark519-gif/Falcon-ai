from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class Plugin:
    name:str
    version:str
    description:str
    tools:dict[str,Callable[...,Any]]

class PluginManager:
    def __init__(self): self.plugins={}
    def register(self,plugin:Plugin): self.plugins[plugin.name]=plugin
    def unregister(self,name): self.plugins.pop(name,None)
    def list(self): return [{"name":p.name,"version":p.version,"description":p.description,"tools":list(p.tools)} for p in self.plugins.values()]
    def invoke(self,tool:str,**kwargs):
        for p in self.plugins.values():
            if tool in p.tools: return p.tools[tool](**kwargs)
        raise KeyError(f"Plugin tool not found: {tool}")
manager=PluginManager()
