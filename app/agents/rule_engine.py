from __future__ import annotations

from collections.abc import Iterable


WEB_INDICATORS = {
    "latest",
    "today",
    "current",
    "recent",
    "news",
    "price",
    "prices",
    "live",
    "this week",
    "this month",
    "this year",
    "what happened",
    "search the web",
    "search online",
    "look up",
    "research",
}

DOCUMENT_INDICATORS = {
    "document",
    "documents",
    "pdf",
    "file",
    "files",
    "uploaded",
    "upload",
    "attachment",
    "attachments",
    "my report",
    "my reports",
    "my document",
    "my documents",
    "my notes",
    "according to my",
    "according to the file",
    "according to the document",
    "in the file",
    "in the document",
    "in my file",
}

PYTHON_INDICATORS = {
    "calculate",
    "calculation",
    "compute",
    "equation",
    "percentage",
    "percent",
    "compound interest",
    "forecast",
    "data analysis",
    "data processing",
    "statistics",
    "statistical",
    "dataset",
    "csv",
    "excel",
    "spreadsheet",
    "python",
    "run this code",
    "execute this code",
}

BROWSER_INDICATORS = {
    "open the website",
    "open this website",
    "open the url",
    "open this url",
    "go to the website",
    "go to this website",
    "go to the url",
    "browse this website",
    "browse this page",
    "read this page",
    "read this webpage",
    "read this url",
    "click",
    "login",
    "log in",
    "fill the form",
    "fill out the form",
    "submit the form",
}


def _normalize_question(
    question: str,
) -> str:
    """
    Normalize user input before rule evaluation.
    """

    return " ".join(
        (question or "")
        .lower()
        .strip()
        .split()
    )


def _contains_any(
    question: str,
    indicators: Iterable[str],
) -> bool:
    """
    Return True when any indicator appears in the normalized question.
    """

    return any(
        indicator in question
        for indicator in indicators
    )


def _score_matches(
    question: str,
    indicators: Iterable[str],
) -> int:
    """
    Count matching indicators.

    Longer multi-word indicators receive slightly more weight
    because they are generally stronger signals.
    """

    score = 0

    for indicator in indicators:

        if indicator in question:

            if " " in indicator:
                score += 2
            else:
                score += 1

    return score


def should_use_web(
    question: str,
) -> bool:
    """
    Determine whether external/current web information is likely required.
    """

    q = _normalize_question(
        question
    )

    if not q:
        return False

    return _contains_any(
        q,
        WEB_INDICATORS,
    )


def should_use_documents(
    question: str,
) -> bool:
    """
    Determine whether uploaded/user documents are likely relevant.
    """

    q = _normalize_question(
        question
    )

    if not q:
        return False

    return _contains_any(
        q,
        DOCUMENT_INDICATORS,
    )


def should_use_python(
    question: str,
) -> bool:
    """
    Determine whether actual computation or Python execution is likely useful.

    This is intentionally conservative. A word such as "model" alone
    should not automatically cause Falcon to execute Python.
    """

    q = _normalize_question(
        question
    )

    if not q:
        return False

    strong_indicators = {
        "calculate",
        "calculation",
        "compute",
        "equation",
        "percentage",
        "percent",
        "compound interest",
        "data analysis",
        "data processing",
        "statistics",
        "statistical",
        "dataset",
        "csv",
        "excel",
        "spreadsheet",
        "python",
        "run this code",
        "execute this code",
    }

    return _contains_any(
        q,
        strong_indicators,
    )


def should_use_browser(
    question: str,
) -> bool:
    """
    Determine whether direct webpage/browser interaction is required.

    Merely mentioning a website does not necessarily mean Falcon
    should use browser interaction.
    """

    q = _normalize_question(
        question
    )

    if not q:
        return False

    return _contains_any(
        q,
        BROWSER_INDICATORS,
    )


def tool_score(
    tool: str,
    question: str,
) -> int:
    """
    Return a deterministic confidence score for a tool.

    This allows future orchestration logic to rank tools instead
    of relying only on True/False decisions.
    """

    tool_name = (
        (tool or "")
        .strip()
        .lower()
    )

    q = _normalize_question(
        question
    )

    if not q:
        return 0

    if tool_name == "web_search":
        return _score_matches(
            q,
            WEB_INDICATORS,
        )

    if tool_name == "document_search":
        return _score_matches(
            q,
            DOCUMENT_INDICATORS,
        )

    if tool_name == "python":
        return _score_matches(
            q,
            PYTHON_INDICATORS,
        )

    if tool_name == "browser":
        return _score_matches(
            q,
            BROWSER_INDICATORS,
        )

    return 0


def allowed_tool(
    tool: str,
    question: str,
) -> bool:
    """
    Determine whether a specific tool is appropriate for a request.
    """

    tool_name = (
        (tool or "")
        .strip()
        .lower()
    )

    if tool_name == "web_search":
        return should_use_web(
            question
        )

    if tool_name == "document_search":
        return should_use_documents(
            question
        )

    if tool_name == "python":
        return should_use_python(
            question
        )

    if tool_name == "browser":
        return should_use_browser(
            question
        )

    return False


def select_allowed_tools(
    question: str,
) -> list[str]:
    """
    Return all tools that have a positive deterministic signal.

    This does not execute anything.
    """

    tools = [
        "document_search",
        "web_search",
        "python",
        "browser",
    ]

    scored = [
        (
            tool_score(
                tool,
                question,
            ),
            tool,
        )
        for tool in tools
    ]

    scored = [
        item
        for item in scored
        if item[0] > 0
    ]

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        tool
        for _, tool in scored
    ]