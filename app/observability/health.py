from __future__ import annotations
from app.services.ai.providers import router
def health()->dict:
    return {"status":"ok","providers":{n:p.available() for n,p in router.providers.items()}}
