from __future__ import annotations
PLANS={"free":{"requests":100,"agents":1},"pro":{"requests":10000,"agents":10},"enterprise":{"requests":1000000,"agents":1000}}
def limit(plan:str,key:str)->int:return PLANS.get(plan,PLANS["free"]).get(key,0)
