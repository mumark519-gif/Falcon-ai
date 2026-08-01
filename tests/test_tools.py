from app.tools.registry import (
    get_tool,
    list_tools,
)


def test_document_tool_registered():

    assert (
        get_tool("document_search")
        is not None
    )

    assert (
        "document_search"
        in list_tools()
    )