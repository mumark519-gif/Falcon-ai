from __future__ import annotations

def web_search_tool(query: str):
    """Search the web when Tavily is configured; otherwise return a safe status."""
    if not query or not query.strip():
        return []
    try:
        from app.tools.providers.tavily import TavilyProvider
        provider = TavilyProvider()
        return provider.search(query)
    except Exception as exc:
        return {
            "success": False,
            "error": (
                "Web search is unavailable. Configure TAVILY_API_KEY "
                f"to enable live search. ({exc})"
            ),
            "output": [],
        }
