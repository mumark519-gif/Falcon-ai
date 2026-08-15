from __future__ import annotations
from typing import Any
class ImageGenerationCapability:
    def generate(self,prompt:str,**kwargs:Any)->dict[str,Any]:
        from app.intelligence.model_router import model_router
        return {"status":"provider_required","prompt":prompt,"provider":kwargs.get("provider") or model_router.choose(prompt).provider,"note":"Connect a configured image-generation provider to produce binary image output."}
