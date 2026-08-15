from app.core.contracts import ProviderResponse
from app.services.ai.providers import BaseProvider, ProviderError, ProviderRouter


class FailingProvider(BaseProvider):
    name = "failing"
    model = "bad"

    def available(self):
        return True

    def generate(self, prompt, **kwargs):
        raise ProviderError("quota exhausted", provider=self.name)


class WorkingProvider(BaseProvider):
    name = "working"
    model = "good"

    def available(self):
        return True

    def generate(self, prompt, **kwargs):
        return ProviderResponse(self.name, self.model, "ok", None)


def test_provider_router_fails_over():
    router = ProviderRouter()
    router.providers = {"failing": FailingProvider(), "working": WorkingProvider()}
    result = router.generate("hello", provider="failing")
    assert result.provider == "working"
    assert result.text == "ok"
