from __future__ import annotations
class PermissionEngine:
    def authorize(self,tool:str,permissions:set[str],approved:bool=False,write:bool=False)->dict:
        if tool not in permissions:return {"allowed":False,"reason":"permission_not_granted"}
        if write and not approved:return {"allowed":False,"reason":"approval_required"}
        return {"allowed":True}
