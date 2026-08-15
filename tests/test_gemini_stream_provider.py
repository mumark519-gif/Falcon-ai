from unittest.mock import MagicMock, patch

from app.services.ai.gemini_provider import stream_gemini


@patch("app.services.ai.gemini_provider.client.models.generate_content_stream")
def test_stream_gemini(mock_stream):

    chunk1 = MagicMock()
    chunk1.text = "Hello "

    chunk2 = MagicMock()
    chunk2.text = "Falcon"

    mock_stream.return_value = [chunk1, chunk2]

    result = "".join(stream_gemini("Hi"))

    assert result == "Hello Falcon"