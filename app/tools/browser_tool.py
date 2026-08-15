from __future__ import annotations

from app.tools.providers.simple_browser import (
    SimpleBrowserProvider,
)


_provider = SimpleBrowserProvider()


def browser_tool(
    url: str,
):

    if not url or not url.strip():

        return {
            "success": False,
            "error": "URL is empty.",
        }

    return _provider.read_page(
        url.strip()
    )