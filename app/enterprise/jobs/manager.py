from __future__ import annotations
import uuid, threading
from concurrent.futures import ThreadPoolExecutor
class JobManager:
    def __init__(self,max_workers=4):
        self.executor=ThreadPoolExecutor(max_workers=max_workers); self.jobs={}
    def submit(self,fn,*args,**kwargs):
        jid=str(uuid.uuid4()); f=self.executor.submit(fn,*args,**kwargs); self.jobs[jid]=f; return jid
    def status(self,jid):
        f=self.jobs.get(jid)
        if not f:return {"status":"not_found"}
        if not f.done():return {"status":"running"}
        try:return {"status":"completed","result":f.result()}
        except Exception as e:return {"status":"failed","error":str(e)}
manager=JobManager()
