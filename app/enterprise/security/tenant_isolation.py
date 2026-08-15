from __future__ import annotations
def assert_tenant(resource_tenant:str,request_tenant:str)->None:
    if resource_tenant != request_tenant: raise PermissionError("Tenant isolation violation")
