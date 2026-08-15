from __future__ import annotations
from collections import Counter
import time
class Metrics:
    def __init__(self):self.counters=Counter(); self.latencies=[]
    def inc(self,name:str,n:int=1):self.counters[name]+=n
    def observe(self,seconds:float):self.latencies.append(seconds)
    def snapshot(self):return {"counters":dict(self.counters),"avg_latency":sum(self.latencies)/len(self.latencies) if self.latencies else 0}
metrics=Metrics()
