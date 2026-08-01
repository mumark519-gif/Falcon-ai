from app.tools.registry import (
    get_tool,
)

from app.tools.tool_selector import (
    select_tools,
)


def test_web_tool_registered():

    assert (
        get_tool("web_search")
        is not None
    )


def test_web_tool_selected():

    tools = select_tools(
        "What is the latest AI news today?"
    )

    assert (
        "web_search"
        in tools
    )