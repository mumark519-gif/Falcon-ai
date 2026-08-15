from __future__ import annotations
from typing import Any
from app.capabilities.voice import VoiceCapability

class AudioCapability(VoiceCapability):
    """Unified audio capability; voice transcription and speech synthesis are provided by VoiceCapability."""
    def transcribe(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return super().transcribe(path, **kwargs)

    def synthesize(self, text: str, output_path: str, **kwargs: Any) -> str:
        return super().synthesize(text, output_path, **kwargs)
