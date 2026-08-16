from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.settings import settings
from app.services.ai.providers import router, ProviderError


@dataclass
class ModelDecision:
    provider: str
    model: str
    reason: str
    confidence: float


class FalconModelRouter:
    """
    Capability-aware model router for Falcon AI.

    Selects an available provider based on the task and supports:
    - explicit provider selection
    - capability-based routing
    - normal generation
    - generation with routing metadata
    - streaming
    - provider failover
    """

    @staticmethod
    def _provider_model(provider: Any) -> str:
        """
        Safely obtain the configured model from a provider.

        BaseProvider does not guarantee a statically typed `model`
        attribute, so we access it dynamically and provide a fallback.
        """
        model = getattr(provider, "model", None)

        if model is None:
            model = getattr(provider, "model_name", None)

        if model is None:
            model = "default"

        return str(model)

    def available(self) -> list[str]:
        """
        Return providers that are currently configured and available.
        """
        available_providers: list[str] = []

        for name, provider in router.providers.items():
            try:
                if provider.available():
                    available_providers.append(name)
            except Exception:
                continue

        return available_providers

    def choose(
        self,
        task: str,
        *,
        preferred: str | None = None,
        require: set[str] | None = None,
    ) -> ModelDecision:
        """
        Select the best available provider for the task.
        """

        required_capabilities = require or set()
        available_providers = self.available()

        if not available_providers:
            raise ProviderError(
                "No configured AI provider is currently available."
            )

        # Explicit provider preference.
        if preferred and preferred in available_providers:
            provider = router.get(preferred)

            return ModelDecision(
                provider=preferred,
                model=self._provider_model(provider),
                reason="explicit preference",
                confidence=0.99,
            )

        text = (task or "").lower()

        # Coding / repository work.
        if (
            "code" in text
            or "coding" in text
            or "repository" in text
            or "github" in text
            or "programming" in text
        ):
            order = [
                "anthropic",
                "openai",
                "kimi",
                "gemini",
            ]
            reason = "coding capability policy"

        # Research work.
        elif (
            "research" in text
            or "sources" in text
            or "citations" in text
            or "researching" in text
        ):
            order = [
                "openai",
                "anthropic",
                "gemini",
                "kimi",
            ]
            reason = "research capability policy"

        # Vision/image work.
        elif required_capabilities & {"vision", "image"}:
            order = [
                "openai",
                "gemini",
                "anthropic",
            ]
            reason = "vision/image capability policy"

        # General Falcon requests.
        else:
            order = [
                settings.default_provider,
                "openai",
                "anthropic",
                "gemini",
                "kimi",
            ]
            reason = "default capability policy"

        # Remove duplicate providers while preserving priority.
        unique_order: list[str] = []

        for name in order:
            if name not in unique_order:
                unique_order.append(name)

        for name in unique_order:
            if name not in available_providers:
                continue

            try:
                provider = router.get(name)
            except Exception:
                continue

            return ModelDecision(
                provider=name,
                model=self._provider_model(provider),
                reason=reason,
                confidence=0.80,
            )

        raise ProviderError(
            "No available AI provider satisfies the current routing policy."
        )

    def generate(
        self,
        task: str,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response using the selected provider.
        """

        preferred = kwargs.pop("provider", None)

        required_capabilities = set(
            kwargs.pop("require", set())
        )

        decision = self.choose(
            task,
            preferred=preferred,
            require=required_capabilities,
        )

        requested_model = kwargs.pop(
            "model",
            decision.model,
        )

        try:
            response = router.generate(
                prompt,
                decision.provider,
                model=requested_model,
                **kwargs,
            )

            return response.text

        except ProviderError:
            raise

        except Exception as exc:
            raise ProviderError(
                f"Provider '{decision.provider}' failed: {exc}"
            ) from exc

    def generate_with_meta(
        self,
        task: str,
        prompt: str,
        **kwargs: Any,
    ) -> tuple[str, ModelDecision]:
        """
        Generate a response and return the actual routing decision.
        """

        preferred = kwargs.pop("provider", None)

        required_capabilities = set(
            kwargs.pop("require", set())
        )

        decision = self.choose(
            task,
            preferred=preferred,
            require=required_capabilities,
        )

        requested_model = kwargs.pop(
            "model",
            decision.model,
        )

        try:
            response = router.generate(
                prompt,
                decision.provider,
                model=requested_model,
                **kwargs,
            )

        except ProviderError:
            raise

        except Exception as exc:
            raise ProviderError(
                f"Provider '{decision.provider}' failed: {exc}"
            ) from exc

        actual_provider = getattr(
            response,
            "provider",
            decision.provider,
        )

        actual_model = getattr(
            response,
            "model",
            requested_model,
        )

        if actual_provider != decision.provider:
            decision = ModelDecision(
                provider=str(actual_provider),
                model=str(actual_model),
                reason=(
                    f"provider failover from "
                    f"{decision.provider}"
                ),
                confidence=0.70,
            )

        else:
            decision = ModelDecision(
                provider=str(actual_provider),
                model=str(actual_model),
                reason=decision.reason,
                confidence=decision.confidence,
            )

        return response.text, decision

    def stream(
        self,
        task: str,
        prompt: str,
        **kwargs: Any,
    ):
        """
        Stream a response using the selected provider.
        """

        preferred = kwargs.pop("provider", None)

        required_capabilities = set(
            kwargs.pop("require", set())
        )

        decision = self.choose(
            task,
            preferred=preferred,
            require=required_capabilities,
        )

        requested_model = kwargs.pop(
            "model",
            decision.model,
        )

        try:
            yield from router.stream(
                prompt,
                decision.provider,
                model=requested_model,
                **kwargs,
            )

        except ProviderError:
            raise

        except Exception as exc:
            raise ProviderError(
                f"Provider '{decision.provider}' failed during streaming: {exc}"
            ) from exc


model_router = FalconModelRouter()