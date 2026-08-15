from __future__ import annotations

"""Standalone streaming helper.

app.services.chat_service.chat_stream() is what actually powers the live
/chat-stream endpoint now -- it needs the routing decision *before*
streaming starts (to send the provider/model header to the client), so it
calls model_router.choose() + model_router.stream() directly rather than
through this module.

This function is kept as a simple, self-contained entry point for any other
code that just wants "stream me an answer to this prompt" without the full
chat pipeline (memory, plan, document retrieval, persistence).
"""

from app.intelligence.model_router import model_router


def stream_chat(
    prompt: str,
    task: str | None = None,
):
    """Stream a response to `prompt`, using `task` (defaults to `prompt`)
    for capability-based provider routing."""
    yield from model_router.stream(task or prompt, prompt)
