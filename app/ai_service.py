from __future__ import annotations

from app.agents.router import get_system_prompt
from app.services.ai.ai_gateway import generate


def _validate_prompt(prompt: str) -> str:
    if prompt is None:
        raise ValueError("Prompt cannot be None.")
    text = str(prompt).strip()
    if not text:
        raise ValueError("Prompt cannot be empty.")
    return text


def ask_ai(
    prompt: str,
    provider: str | None = None,
    **kwargs,
) -> str:
    """Main Falcon AI facade.

    All application-level AI calls should flow through the unified provider
    gateway so OpenAI, Anthropic/Claude, Kimi, and other compatible providers
    can be routed without changing callers.
    """
    text = _validate_prompt(prompt)
    system = get_system_prompt(text)
    full_prompt = f"{system}\n\nUser Request:\n{text}"
    return generate(full_prompt, provider=provider, **kwargs)


def analyze_business_problem(
    problem: str,
    provider: str | None = None,
    **kwargs,
) -> str:
    """Analyze a business problem through Falcon's unified AI gateway."""
    text = _validate_prompt(problem)
    prompt = (
        "Analyze the following business problem as a professional business "
        "advisor. Identify the situation, key causes, risks, opportunities, "
        "recommended actions, and measurable next steps. Be practical and "
        "specific.\n\nBusiness problem:\n"
        + text
    )
    return ask_ai(prompt, provider=provider, **kwargs)


def generate_chat_title(message: str) -> str:
    text = _validate_prompt(message)
    try:
        return generate(
            "Create a concise 4-8 word chat title. Return title only.\n"
            + text
        ).strip()[:120]
    except Exception:
        return text[:80] or "New Chat"


def extract_memory(message: str) -> dict[str, str]:
    """Extract durable user facts from a message.

    This compatibility facade keeps the memory subsystem independent from the
    concrete model provider. It asks the unified Falcon gateway for structured
    JSON and safely falls back to a small deterministic extractor when a model
    is unavailable or returns malformed data.
    """
    text = _validate_prompt(message)
    prompt = (
        "Extract only durable user-specific facts from the message below. "
        "Return a JSON object mapping concise snake_case keys to short values. "
        "Do not include temporary requests, questions, instructions, or facts "
        "about the assistant. If there are no durable facts, return {}.\n\n"
        f"Message:\n{text}"
    )
    try:
        import json
        import re
        raw = generate(prompt)
        candidate = raw.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", candidate, flags=re.I)
        data = json.loads(candidate)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if v is not None}
    except Exception:
        pass

    # Deterministic fallback for common memory statements.
    import re
    result: dict[str, str] = {}
    patterns = [
        (r"\\bmy favorite (?:color|colour) is ([A-Za-z][A-Za-z -]*)", "favorite_color"),
        (r"\\bmy name is ([A-Za-z][A-Za-z -]*)", "name"),
        (r"\\bi am from ([A-Za-z][A-Za-z ,'-]*)", "location"),
        (r"\\bi live in ([A-Za-z][A-Za-z ,'-]*)", "location"),
    ]
    for pattern, key in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            result[key] = match.group(1).strip().rstrip(".!?")
    return result


def ask_gemini(prompt: str, **kwargs) -> str:
    """Backward-compatible Gemini facade for legacy callers/tests."""
    return ask_ai(prompt, provider="gemini", **kwargs)
