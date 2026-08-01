from abc import ABC, abstractmethod


class BrowserProvider(ABC):

    @abstractmethod
    def read_page(
        self,
        url: str,
    ):
        pass