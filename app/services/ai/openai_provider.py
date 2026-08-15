from __future__ import annotations

import time
from typing import Any

from app.core.config import settings
from app.core.logger import logger


MODEL_NAME = settings.OPENAI_MODEL

MAX_RETRIES = settings.AI_MAX_RETRIES
RETRY_DELAY = settings.AI_RETRY_DELAY

def _client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAIProviderError("The openai package is not installed.") from exc
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.AI_TIMEOUT,
        max_retries=0,
    )


class OpenAIProviderError(Exception):
    """
    Raised when the OpenAI provider cannot complete a request.
    """


def _validate_prompt(
    prompt: str,
) -> str:
    """
    Validate and normalize an incoming prompt.
    """

    if prompt is None:
        raise ValueError(
            "Prompt cannot be None."
        )

    prompt = str(prompt).strip()

    if not prompt:
        raise ValueError(
            "Prompt cannot be empty."
        )

    return prompt


def _extract_text(
    response: Any,
) -> str:
    """
    Extract text safely from an OpenAI Responses API result.
    """

    text = getattr(
        response,
        "output_text",
        None,
    )

    if text:
        return str(text).strip()

    output = getattr(
        response,
        "output",
        None,
    )

    if not output:
        return ""

    parts: list[str] = []

    for item in output:

        content = getattr(
            item,
            "content",
            None,
        )

        if not content:
            continue

        for content_item in content:

            item_text = getattr(
                content_item,
                "text",
                None,
            )

            if item_text:
                parts.append(
                    str(item_text)
                )

    return "\n".join(
        parts
    ).strip()


def ask_openai(
    prompt: str,
) -> str:
    """
    Send a prompt to OpenAI and return plain text.

    Retries transient provider failures.
    """

    prompt = _validate_prompt(
        prompt
    )

    last_error: Exception | None = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            logger.info(
                "OpenAI request attempt %s/%s using %s.",
                attempt,
                MAX_RETRIES,
                MODEL_NAME,
            )

            response = _client().responses.create(
                model=MODEL_NAME,
                input=prompt,
            )

            text = _extract_text(
                response
            )

            if not text:

                raise OpenAIProviderError(
                    "OpenAI returned an empty response."
                )

            return text

        except Exception as exc:

            last_error = exc

            logger.warning(
                "OpenAI request failed on attempt %s/%s: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )

            if attempt >= MAX_RETRIES:
                break

            time.sleep(
                RETRY_DELAY * attempt
            )

    raise OpenAIProviderError(
        "OpenAI provider failed after "
        f"{MAX_RETRIES} attempts: "
        f"{last_error}"
    )


def test_openai() -> str:
    """
    Basic provider connectivity test.
    """

    answer = ask_openai(
        "Say only: OpenAI is working."
    )

    print(answer)

    return answer