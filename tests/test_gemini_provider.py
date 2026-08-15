from unittest.mock import patch

from app.services.ai.gemini_provider import ask_gemini


@patch("app.services.ai.gemini_provider.client.models.generate_content")
def test_gemini_provider(mock_generate):

    mock_generate.return_value.text = "Falcon migration successful"

    response = ask_gemini("Hello")

    assert response == "Falcon migration successful"

def test_provider_router_exposes_available_method():
    from app.services.ai.providers import router
    assert isinstance(router.available(), list)
