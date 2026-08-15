from __future__ import annotations


def web_search_tool(query: str):
    """Search the public web through the configured search provider."""
    if not query or not query.strip():
        return []
    try:
        from app.tools.tavily_provider import TavilyProvider
        provider = TavilyProvider()
        return provider.search(query)
    except Exception as exc:
        return {
            "success": False,
            "error": f"Web search is unavailable: {exc}",
            "output": [],
        }


# Canonical compatibility alias used by the research pipeline.
web_search = web_search_tool
