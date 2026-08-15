from __future__ import annotations
from dataclasses import dataclass
from queue import Queue
import uuid
@dataclass
class Job:
    id:str
    kind:str
    payload:dict
    status:str="queued"
class JobQueue:
    def __init__(self):self.queue=Queue();self.jobs={}
    def submit(self,kind:str,payload:dict)->Job:
        j=Job(str(uuid.uuid4()),kind,payload);self.jobs[j.id]=j;self.queue.put(j);return j
    def get(self):return self.queue.get()
queue=JobQueue()
