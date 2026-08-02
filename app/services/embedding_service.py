from app.services.embedding_provider import (
    EmbeddingProvider,
)

provider = EmbeddingProvider()


def create_embedding(
    text: str,
):

    if not text:
        return []

    try:

        return provider.embed(text)

    except Exception:

        # During testing or API failure
        return []