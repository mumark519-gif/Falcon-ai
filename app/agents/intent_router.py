import re


def detect_intent(question: str) -> str:
    """
    Returns one of:

    chat
    business
    coding
    investment
    research
    document
    complex
    """

    q = question.lower()

    # Document requests
    if any(word in q for word in [
        "document",
        "pdf",
        "file",
        "upload",
        "attachment",
    ]):
        return "document"

    # Coding
    if any(word in q for word in [
        "python",
        "fastapi",
        "sql",
        "javascript",
        "react",
        "bug",
        "error",
        "code",
        "api",
    ]):
        return "coding"

    # Investment
    if any(word in q for word in [
        "stock",
        "shares",
        "invest",
        "portfolio",
        "nvidia",
        "apple",
        "tesla",
        "bitcoin",
        "crypto",
    ]):
        return "investment"

    # Business
    if any(word in q for word in [
        "business",
        "company",
        "startup",
        "marketing",
        "sales",
        "customer",
        "profit",
    ]):
        return "business"

    # Research
    if any(word in q for word in [
        "research",
        "latest",
        "news",
        "compare",
        "analyze",
        "study",
        "report",
    ]):
        return "research"

    # Very long questions usually need orchestration
    if len(question.split()) > 80:
        return "complex"

    return "chat"