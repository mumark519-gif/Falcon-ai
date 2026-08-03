from app.services.ai.gemini_provider import ask_gemini


def test_gemini_provider():

    response = ask_gemini(
        "Reply with exactly: Falcon migration successful"
    )

    assert "Falcon migration successful" in response