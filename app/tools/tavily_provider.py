from app.tools.search_provider import SearchProvider


class TavilyProvider(SearchProvider):

    def search(
        self,
        query: str,
    ) -> str:

        return (
            f"Tavily search placeholder: {query}"
        )