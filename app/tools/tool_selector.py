from app.tools.registry import (
    list_tools,
)


def select_tools(
    question: str,
):

    question = question.lower()

    selected = []

    web_keywords = [
        "today",
        "latest",
        "news",
        "current",
        "price",
        "weather",
        "search",
    ]

    if (
        "document" in question
        or "pdf" in question
        or "file" in question
        or "upload" in question
    ):
        selected.append(
            "document_search"
        )

    if any(
        word in question
        for word in web_keywords
    ):
        selected.append(
            "web_search"
        )

    return selected