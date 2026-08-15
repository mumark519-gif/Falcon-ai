from __future__ import annotations


WEB_KEYWORDS = {
    "today",
    "latest",
    "current",
    "recent",
    "news",
    "price",
    "weather",
    "stock",
    "market",
    "search",
    "who is",
    "what happened",
    "this week",
    "this month",
}


DOCUMENT_KEYWORDS = {
    "document",
    "documents",
    "pdf",
    "file",
    "files",
    "upload",
    "uploaded",
    "my report",
    "my reports",
    "my notes",
}


PYTHON_KEYWORDS = {
    "calculate",
    "calculation",
    "compute",
    "python",
    "program",
    "code",
    "data analysis",
    "dataset",
}


BROWSER_KEYWORDS = {
    "open this url",
    "open this website",
    "read this page",
    "read this url",
    "website",
    "webpage",
}


def _contains_keyword(
    question: str,
    keywords: set[str],
) -> bool:

    return any(
        keyword in question
        for keyword in keywords
    )


def select_tools(
    question: str,
) -> list[str]:

    question = (
        question or ""
    ).lower().strip()

    selected: list[str] = []

    if _contains_keyword(
        question,
        DOCUMENT_KEYWORDS,
    ):
        selected.append(
            "document_search"
        )

    if _contains_keyword(
        question,
        WEB_KEYWORDS,
    ):
        selected.append(
            "web_search"
        )

    if _contains_keyword(
        question,
        PYTHON_KEYWORDS,
    ):
        selected.append(
            "python"
        )

    if _contains_keyword(
        question,
        BROWSER_KEYWORDS,
    ):
        selected.append(
            "browser"
        )

    return list(
        dict.fromkeys(selected)
    )