"""Legacy Gemini compatibility facade.

The canonical provider lives in ``app.services.ai.providers``.  This module
keeps the historical ``ask_gemini``/``stream_gemini`` API without requiring
the Gemini SDK at import time.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings

MODEL_NAME = settings.GEMINI_MODEL

class _UnavailableModels:
    def generate_content(self, **kwargs):
        raise RuntimeError("Gemini SDK is not installed or GOOGLE_API_KEY is unavailable.")
    def generate_content_stream(self, **kwargs):
        raise RuntimeError("Gemini SDK is not installed or GOOGLE_API_KEY is unavailable.")

class _UnavailableClient:
    models = _UnavailableModels()

def _build_client():
    try:
        from google import genai
        return genai.Client(api_key=settings.GOOGLE_API_KEY)
    except Exception:
        return _UnavailableClient()

client = _build_client()

def ask_gemini(prompt: str):
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return getattr(response, "text", "") or ""
    except Exception as exc:
        return (
            "Falcon AI could not contact the Gemini model at the moment. "
            f"Provider error: {exc}"
        )

def stream_gemini(prompt: str):
    try:
        response = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=prompt,
        )
        for chunk in response:
            text = getattr(chunk, "text", None)
            if text:
                yield text
    except Exception as exc:
        yield (
            "Falcon AI could not contact the Gemini model at the moment. "
            f"Provider error: {exc}"
        )
