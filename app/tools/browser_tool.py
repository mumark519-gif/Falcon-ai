from app.tools.providers.simple_browser import (
    SimpleBrowserProvider,
)

_provider = SimpleBrowserProvider()


def browser_tool(
    url: str,
):

    return _provider.read_page(url)