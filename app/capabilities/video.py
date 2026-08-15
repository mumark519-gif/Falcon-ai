from __future__ import annotations
class VideoCapability:
    def inspect(self,path:str)->dict:return {"path":path,"status":"adapter-ready","frames":None}
    def generate(self,prompt:str,**kwargs)->dict:return {"status":"provider-required","prompt":prompt}
