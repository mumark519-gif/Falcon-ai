import requests
from bs4 import BeautifulSoup

from app.tools.providers.browser_base import (
    BrowserProvider,
)


class SimpleBrowserProvider(
    BrowserProvider
):

    def read_page(
        self,
        url: str,
    ):

        try:

            response = requests.get(
                url,
                timeout=10,
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            return soup.get_text(
                separator="\n",
                strip=True,
            )

        except Exception as e:

            return (
                f"Browser error: {e}"
            )