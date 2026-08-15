from __future__ import annotations

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
                headers={
                    "User-Agent": (
                        "FalconAI/1.0"
                    )
                },
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            for element in soup(
                [
                    "script",
                    "style",
                    "noscript",
                ]
            ):
                element.decompose()

            text = soup.get_text(
                separator="\n",
                strip=True,
            )

            return {
                "success": True,
                "url": url,
                "content": text,
            }

        except Exception as exc:

            return {
                "success": False,
                "url": url,
                "error": str(exc),
            }