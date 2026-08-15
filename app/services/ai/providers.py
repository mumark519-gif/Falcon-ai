from __future__ import annotations

from typing import Any, Iterator

from app.core.contracts import ProviderResponse
from app.core.settings import settings


class ProviderError(RuntimeError):
    """Normalized error raised when a model provider cannot serve a request."""

    def __init__(self, message: str, *, provider: str | None = None, retryable: bool = True) -> None:
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable


class BaseProvider:
    name = "base"

    def available(self) -> bool:
        return False

    def generate(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        raise NotImplementedError

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        yield self.generate(prompt, **kwargs).text

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        text = str(exc).lower()
        return any(token in text for token in ("insufficient_quota", "credit_balance_exhausted", "quota"))


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self) -> None:
        self.key = settings.openai_api_key
        self.model = settings.openai_model

    def available(self) -> bool:
        return bool(self.key)

    def generate(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        if not self.key:
            raise ProviderError("OPENAI_API_KEY is not configured", provider=self.name, retryable=False)
        try:
            from openai import OpenAI

            model = kwargs.get("model", self.model)
            client = OpenAI(api_key=self.key, timeout=settings.ai_timeout, max_retries=0)
            response = client.responses.create(model=model, input=prompt)
            return ProviderResponse(self.name, model, getattr(response, "output_text", "") or "", response)
        except Exception as exc:
            raise ProviderError(
                f"OpenAI request failed: {exc}",
                provider=self.name,
                retryable=not self._is_quota_error(exc),
            ) from exc

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        if not self.key:
            raise ProviderError("OPENAI_API_KEY is not configured", provider=self.name, retryable=False)
        try:
            from openai import OpenAI

            model = kwargs.get("model", self.model)
            client = OpenAI(api_key=self.key, timeout=settings.ai_timeout, max_retries=0)
            with client.responses.stream(model=model, input=prompt) as stream:
                for event in stream:
                    if getattr(event, "type", "") == "response.output_text.delta":
                        delta = getattr(event, "delta", "")
                        if delta:
                            yield delta
        except Exception as exc:
            raise ProviderError(
                f"OpenAI streaming request failed: {exc}",
                provider=self.name,
                retryable=not self._is_quota_error(exc),
            ) from exc


class OpenAICompatibleProvider(BaseProvider):
    name = "openai-compatible"

    def __init__(self) -> None:
        self.key = settings.openai_compatible_api_key
        self.base = settings.openai_compatible_base_url
        self.model = settings.openai_compatible_model

    def available(self) -> bool:
        return bool(self.key and self.base and self.model)

    def generate(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        if not self.available():
            raise ProviderError("OpenAI-compatible provider is not configured", provider=self.name, retryable=False)
        try:
            from openai import OpenAI

            model = kwargs.get("model", self.model)
            client = OpenAI(api_key=self.key, base_url=self.base, timeout=settings.ai_timeout, max_retries=0)
            response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
            text = response.choices[0].message.content or ""
            return ProviderResponse(self.name, model, text, response)
        except Exception as exc:
            raise ProviderError(f"OpenAI-compatible request failed: {exc}", provider=self.name) from exc

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        if not self.available():
            raise ProviderError("OpenAI-compatible provider is not configured", provider=self.name, retryable=False)
        try:
            from openai import OpenAI

            model = kwargs.get("model", self.model)
            client = OpenAI(api_key=self.key, base_url=self.base, timeout=settings.ai_timeout, max_retries=0)
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as exc:
            raise ProviderError(f"OpenAI-compatible streaming request failed: {exc}", provider=self.name) from exc


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.key = settings.google_api_key
        self.model = settings.gemini_model

    def available(self) -> bool:
        return bool(self.key)

    def generate(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        if not self.available():
            raise ProviderError("GOOGLE_API_KEY is not configured", provider=self.name, retryable=False)
        try:
            from google import genai

            model = kwargs.get("model", self.model)
            client = genai.Client(api_key=self.key)
            response = client.models.generate_content(model=model, contents=prompt)
            return ProviderResponse(self.name, model, getattr(response, "text", "") or "", response)
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}", provider=self.name) from exc

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        if not self.available():
            raise ProviderError("GOOGLE_API_KEY is not configured", provider=self.name, retryable=False)
        try:
            from google import genai

            model = kwargs.get("model", self.model)
            client = genai.Client(api_key=self.key)
            for chunk in client.models.generate_content_stream(model=model, contents=prompt):
                text = getattr(chunk, "text", None)
                if text:
                    yield text
        except Exception as exc:
            raise ProviderError(f"Gemini streaming request failed: {exc}", provider=self.name) from exc


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self) -> None:
        self.key = settings.anthropic_api_key
        self.model = settings.anthropic_model

    def available(self) -> bool:
        return bool(self.key)

    def generate(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        if not self.key:
            raise ProviderError("ANTHROPIC_API_KEY is not configured", provider=self.name, retryable=False)
        try:
            import anthropic

            model = kwargs.get("model", self.model)
            client = anthropic.Anthropic(api_key=self.key, timeout=settings.ai_timeout, max_retries=0)
            response = client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 4096),
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(getattr(item, "text", "") for item in getattr(response, "content", []))
            return ProviderResponse(self.name, model, text, response)
        except Exception as exc:
            raise ProviderError(f"Anthropic request failed: {exc}", provider=self.name) from exc

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        if not self.key:
            raise ProviderError("ANTHROPIC_API_KEY is not configured", provider=self.name, retryable=False)
        try:
            import anthropic

            model = kwargs.get("model", self.model)
            client = anthropic.Anthropic(api_key=self.key, timeout=settings.ai_timeout, max_retries=0)
            with client.messages.stream(
                model=model,
                max_tokens=kwargs.get("max_tokens", 4096),
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                yield from stream.text_stream
        except Exception as exc:
            raise ProviderError(f"Anthropic streaming request failed: {exc}", provider=self.name) from exc


class KimiProvider(OpenAICompatibleProvider):
    name = "kimi"

    def __init__(self) -> None:
        self.key = settings.kimi_api_key
        self.base = "https://api.moonshot.ai/v1"
        self.model = settings.kimi_model

    def available(self) -> bool:
        return bool(self.key)


class ProviderRouter:
    """Single provider registry with deterministic selection and failover."""

    def __init__(self) -> None:
        self.providers: dict[str, BaseProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "kimi": KimiProvider(),
            "openai-compatible": OpenAICompatibleProvider(),
        }

    def available(self) -> list[str]:
        return [name for name, provider in self.providers.items() if provider.available()]

    def get(self, name: str | None = None) -> BaseProvider:
        wanted = name or settings.default_provider
        provider = self.providers.get(wanted)
        if provider and provider.available():
            return provider
        for candidate in self.providers.values():
            if candidate.available():
                return candidate
        raise ProviderError("No configured AI provider is available", retryable=False)

    def _candidate_names(self, preferred: str | None = None) -> list[str]:
        configured = self.available()
        if preferred and preferred in configured:
            return [preferred] + [name for name in configured if name != preferred]
        default = settings.default_provider
        if default in configured:
            return [default] + [name for name in configured if name != default]
        return configured

    def generate(self, prompt: str, provider: str | None = None, **kwargs: Any) -> ProviderResponse:
        errors: list[str] = []
        for name in self._candidate_names(provider):
            try:
                return self.providers[name].generate(prompt, **kwargs)
            except ProviderError as exc:
                errors.append(f"{name}: {exc}")
                if not exc.retryable:
                    continue
        raise ProviderError("All configured AI providers failed. " + " | ".join(errors), retryable=False)

    def stream(self, prompt: str, provider: str | None = None, **kwargs: Any) -> Iterator[str]:
        names = self._candidate_names(provider)
        if not names:
            raise ProviderError("No configured AI provider is available", retryable=False)
        last_error: ProviderError | None = None
        for index, name in enumerate(names):
            try:
                yield from self.providers[name].stream(prompt, **kwargs)
                return
            except ProviderError as exc:
                last_error = exc
                if index == len(names) - 1:
                    break
        raise last_error or ProviderError("All configured AI providers failed", retryable=False)


router = ProviderRouter()
