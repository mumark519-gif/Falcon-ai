from __future__ import annotations
from dataclasses import dataclass
import time, json
@dataclass
class AuditEvent:
    event:str
    actor:str
    details:dict
    timestamp:float
class AuditLog:
    def __init__(self):self.events=[]
    def record(self,event:str,actor:str,**details):self.events.append(AuditEvent(event,actor,details,time.time()))
    def export(self):return json.dumps([e.__dict__ for e in self.events],default=str)
audit_log=AuditLog()
