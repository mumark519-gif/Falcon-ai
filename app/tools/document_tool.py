from app.services.vector_service import search_documents


def document_search_tool(
    username: str,
    query: str,
):

    return search_documents(
        username,
        query,
    )