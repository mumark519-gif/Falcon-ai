from app.tools.tool_selector import (
    select_tools,
)


def test_document_tool_selected():

    tools = select_tools(
        "Summarize my uploaded PDF"
    )

    assert (
        "document_search"
        in tools
    )


def test_no_tool_needed():

    tools = select_tools(
        "Explain recursion"
    )

    assert tools == []