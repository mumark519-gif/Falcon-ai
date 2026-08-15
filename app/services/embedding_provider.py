from __future__ import annotations

import hashlib
import math

from app.core.settings import settings

class EmbeddingProvider:
    """Embedding adapter with a real-provider path and deterministic fallback.

    The fallback keeps tests/offline development functional and is intentionally
    deterministic; production deployments should configure a real embedding API.
    """

    def __init__(self):
        self.model = "gemini-embedding-001"

    def _fallback(self, text: str, dimensions: int = 128) -> list[float]:
        raw = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for i in range(dimensions):
            b = raw[i % len(raw)]
            values.append((b / 127.5) - 1.0)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def embed(self, text: str) -> list[float]:
        if not text:
            return []
        if settings.google_api_key:
            try:
                from google import genai
                client = genai.Client(api_key=settings.google_api_key)
                response = client.models.embed_content(
                    model=self.model,
                    contents=text,
                )
                embeddings = getattr(response, "embeddings", None)
                if embeddings:
                    first = embeddings[0]
                    values = getattr(first, "values", None)
                    if values:
                        return list(values)
                values = getattr(response, "values", None)
                if values:
                    return list(values)
            except Exception:
                pass
        return self._fallback(text)
