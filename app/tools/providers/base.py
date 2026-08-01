from abc import ABC, abstractmethod


class SearchProvider(ABC):

    @abstractmethod
    def search(
        self,
        query: str,
    ) -> str:
        """Return search results for a query."""
        raise NotImplementedError