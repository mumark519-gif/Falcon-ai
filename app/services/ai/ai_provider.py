from __future__ import annotations

"""DEPRECATED: superseded by app.services.ai.ai_gateway / app.services.ai.providers,
which support OpenAI, Anthropic, Gemini, and Kimi behind one interface instead of
locking every caller to OpenAI. Nothing in the app imports this module anymore.
Kept only for backward compatibility with external code that may still import it.
"""

from app.core.config import settings
from app.core.logger import logger

from app.services.ai.openai_provider import (
    ask_openai,
)


class AIProviderError(Exception):
    """
    Raised when Falcon cannot reach its configured AI provider.
    """


def ask_ai(
    prompt: str,
) -> str:
    """
    Main AI gateway used by Falcon.

    All planners, agents, reasoning engines, reflection,
    synthesis, and other AI components should call this
    function rather than talking directly to a provider.
    """

    if prompt is None:
        raise ValueError(
            "Prompt cannot be None."
        )

    prompt = str(
        prompt
    ).strip()

    if not prompt:

        raise ValueError(
            "Prompt cannot be empty."
        )

    provider = (
        settings.AI_PROVIDER
        .strip()
        .lower()
    )

    logger.info(
        "Falcon AI provider selected: %s",
        provider,
    )

    if provider == "openai":

        try:

            return ask_openai(
                prompt
            )

        except Exception as exc:

            logger.exception(
                "OpenAI provider failed."
            )

            raise AIProviderError(
                "Falcon AI could not reach "
                "the OpenAI provider."
            ) from exc

    raise AIProviderError(
        f"Unsupported AI provider: {provider}"
    )