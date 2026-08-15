from app.tools.web_search import web_search
from app.tools.document_tool import document_search_tool


def run_research_pipeline(
    username: str,
    question: str,
    use_web: bool = False,
    use_documents: bool = False,
):
    """
    Falcon Research Pipeline

    Collects knowledge from all available sources
    before the Research Agent starts reasoning.
    """

    context = {}

    if use_web:

        context["web"] = web_search(
            question,
        )

    if use_documents:

        context["documents"] = document_search_tool(
            username,
            question,
        )

    return context