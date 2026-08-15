from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class SearchProvider(ABC):
    """Contract for external web-search providers."""
    name = "search"

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> Any:
        """Return normalized search results for a query."""
        raise NotImplementedError
