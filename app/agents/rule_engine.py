LIVE_KEYWORDS = {
    "today",
    "latest",
    "news",
    "current",
    "recent",
    "this week",
    "this month",
    "stock price",
    "weather",
    "earnings",
}


DOCUMENT_KEYWORDS = {
    "document",
    "pdf",
    "file",
    "upload",
    "uploaded",
    "my notes",
    "my document",
}


def should_use_web(
    question: str,
) -> bool:

    question = question.lower()

    return any(
        keyword in question
        for keyword in LIVE_KEYWORDS
    )


def should_use_documents(
    question: str,
) -> bool:

    question = question.lower()

    return any(
        keyword in question
        for keyword in DOCUMENT_KEYWORDS
    )