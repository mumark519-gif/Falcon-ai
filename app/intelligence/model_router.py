from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from app.core.settings import settings
from app.services.ai.providers import router

@dataclass
class ModelDecision:
    provider: str
    model: str
    reason: str
    confidence: float

class FalconModelRouter:
    """Policy router for heterogeneous model backends. It never pretends a provider is available."""
    def available(self) -> list[str]:
        return [name for name, provider in router.providers.items() if provider.available()]

    def choose(self, task: str, *, preferred: str | None = None, require: set[str] | None = None) -> ModelDecision:
        require = require or set()
        if preferred and preferred in self.available():
            p = router.get(preferred); return ModelDecision(preferred, p.model, "explicit preference", .99)
        text = task.lower()
        candidates = self.available()
        if "code" in text or "repository" in text:
            order = ["anthropic", "openai", "kimi", "gemini"]
        elif "research" in text or "sources" in text or "citations" in text:
            order = ["openai", "anthropic", "gemini", "kimi"]
        elif require & {"vision", "image"}:
            order = ["openai", "gemini", "anthropic"]
        else:
            order = [settings.default_provider, "openai", "anthropic", "gemini", "kimi"]
        for name in order:
            if name in candidates:
                p=router.get(name); return ModelDecision(name,p.model,"capability policy",.8)
        raise RuntimeError("No configured AI provider is available")

    def generate(self, task: str, prompt: str, **kwargs: Any) -> str:
        decision=self.choose(task, preferred=kwargs.pop("provider",None), require=set(kwargs.pop("require",set())))
        return router.generate(prompt, decision.provider, model=kwargs.pop("model", decision.model), **kwargs).text

    def generate_with_meta(self, task: str, prompt: str, **kwargs: Any) -> tuple[str, "ModelDecision"]:
        """Like generate(), but also returns the routing decision so callers
        (e.g. the chat API) can tell the user which provider/model answered."""
        decision=self.choose(task, preferred=kwargs.pop("provider",None), require=set(kwargs.pop("require",set())))
        response = router.generate(
            prompt,
            decision.provider,
            model=kwargs.pop("model", decision.model),
            **kwargs,
        )
        if response.provider != decision.provider:
            decision = ModelDecision(
                response.provider,
                response.model,
                f"provider failover from {decision.provider}",
                0.7,
            )
        return response.text, decision

    def stream(self, task: str, prompt: str, **kwargs: Any):
        """Pick a provider using the same capability policy as generate(),
        then yield its response as text chunks."""
        decision=self.choose(task, preferred=kwargs.pop("provider",None), require=set(kwargs.pop("require",set())))
        yield from router.stream(prompt, decision.provider, model=kwargs.pop("model", decision.model), **kwargs)

model_router=FalconModelRouter()
