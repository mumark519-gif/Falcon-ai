from __future__ import annotations

from app.services.vector_service import (
    hybrid_search,
)


def document_search_tool(
    username: str,
    query: str,
):

    if not username:

        return []

    if not query or not query.strip():

        return []

    return hybrid_search(
        username,
        query,
    )