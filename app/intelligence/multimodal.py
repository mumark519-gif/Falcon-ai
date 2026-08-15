from __future__ import annotations
from typing import Any
class MultimodalController:
    """Capability facade. Actual inference is delegated to configured providers."""
    def requirements(self,media_type:str)->dict[str,Any]:
        return {"media_type":media_type,"supported":media_type.lower() in {"image","audio","video","pdf","document"},"provider_backends":["openai","gemini","anthropic"]}
