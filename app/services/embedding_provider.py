from app.core.config import settings
import google.generativeai as genai


class EmbeddingProvider:

    def __init__(self):

        genai.configure(
            api_key=settings.GOOGLE_API_KEY,
        )

    def embed(
        self,
        text: str,
    ):

        response = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
        )

        return response["embedding"]