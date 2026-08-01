TOOLS = {}


def register_tool(
    name: str,
    func,
):

    TOOLS[name] = func


def get_tool(
    name: str,
):

    return TOOLS.get(name)


def list_tools():

    return list(
        TOOLS.keys()
    )

from app.tools.document_tool import (
    document_search_tool,
)

register_tool(
    "document_search",
    document_search_tool,
)

from app.tools.web_search_tool import (
    web_search_tool,
)

register_tool(
    "web_search",
    web_search_tool,
)

from app.tools.python_tool import (
    python_tool,
)

register_tool(
    "python",
    python_tool,
)

from app.tools.browser_tool import (
    browser_tool,
)

register_tool(
    "browser",
    browser_tool,
)