from __future__ import annotations
from dataclasses import dataclass
@dataclass
class Tenant:
    id:str
    name:str
    plan:str="free"
    active:bool=True
class TenantManager:
    def __init__(self):self.tenants={}
    def create(self,id:str,name:str,plan:str="free"): self.tenants[id]=Tenant(id,name,plan); return self.tenants[id]
    def get(self,id:str):return self.tenants.get(id)
tenants=TenantManager()
