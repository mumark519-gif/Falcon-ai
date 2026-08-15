from __future__ import annotations
import os
from typing import Any
import requests
from app.tools.search_provider import SearchProvider

class TavilyProvider(SearchProvider):
    """Production Tavily REST client with normalized results."""
    name = "tavily"
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        query = str(query or "").strip()
        if not query:
            raise ValueError("Search query cannot be empty")
        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY is not configured")
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": kwargs.get("search_depth", "advanced"),
            "topic": kwargs.get("topic", "general"),
            "max_results": min(int(kwargs.get("max_results", 10)), 20),
            "include_answer": bool(kwargs.get("include_answer", True)),
            "include_raw_content": bool(kwargs.get("include_raw_content", False)),
            "include_images": bool(kwargs.get("include_images", False)),
        }
        response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        if response.status_code == 401:
            raise RuntimeError("Tavily authentication failed")
        if response.status_code == 429:
            raise RuntimeError("Tavily rate limit reached")
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score"),
                "raw_content": item.get("raw_content"),
            })
        return {"query": query, "answer": data.get("answer"), "results": results, "response_time": data.get("response_time")}
