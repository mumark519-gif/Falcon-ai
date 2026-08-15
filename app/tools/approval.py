from __future__ import annotations
class ApprovalManager:
    def __init__(self):self.pending={}
    def request(self,action:str,payload:dict)->str:
        import uuid; i=str(uuid.uuid4());self.pending[i]={"action":action,"payload":payload,"approved":False};return i
    def approve(self,id:str):
        if id not in self.pending: raise KeyError(id)
        self.pending[id]["approved"]=True;return self.pending[id]
    def is_approved(self,id:str)->bool:return bool(self.pending.get(id,{}).get("approved"))
approvals=ApprovalManager()
