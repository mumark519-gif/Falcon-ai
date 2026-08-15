from __future__ import annotations
from app.services.ai.providers import router
def generate(prompt:str, provider:str|None=None, **kwargs)->str:
    return router.generate(prompt,provider,**kwargs).text
def stream(prompt:str, provider:str|None=None, **kwargs):
    """Yield text chunks as they arrive from the selected provider."""
    yield from router.stream(prompt,provider,**kwargs)
def available_providers()->list[str]:
    return [n for n,p in router.providers.items() if p.available()]
