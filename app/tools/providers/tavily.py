from tavily import TavilyClient

from app.core.config import settings
from app.tools.providers.base import SearchProvider


class TavilyProvider(SearchProvider):

    def __init__(self):

        self.client = TavilyClient(
            api_key=settings.TAVILY_API_KEY
        )

    def search(
        self,
        query: str,
    ):

        try:

            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=5,
            )

            results = []

            for item in response.get("results", []):

                title = item.get("title", "")
                content = item.get("content", "")
                url = item.get("url", "")

                results.append(
                    {
                        "title": title,
                        "content": content,
                        "url": url,
                    }
                )
            if not results:

                return []

            return results
            

        except Exception:

            return []