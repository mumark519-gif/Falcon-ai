from app.tools.providers.tavily import (
    TavilyProvider,
)

_provider = TavilyProvider()


def web_search_tool(
    query: str,
):

    return _provider.search(query)