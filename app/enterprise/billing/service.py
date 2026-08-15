from __future__ import annotations
PLANS={"free":{"monthly":0},"pro":{"monthly":20},"business":{"monthly":99},"enterprise":{"monthly":0}}
def get_plan(name): return PLANS.get(name,PLANS["free"])
def feature_allowed(plan,feature): return plan!="free" or feature in {"chat","read"}
