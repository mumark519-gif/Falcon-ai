from app.tools.registry import get_tool
from app.tools.tool_selector import select_tools


def execute_tools(
    username: str,
    question: str,
):

    results = {}

    selected_tools = select_tools(question)

    for tool_name in selected_tools:

        tool = get_tool(tool_name)

        if tool is None:
            continue

        if tool_name == "document_search":

            results["documents"] = tool(
                username,
                question,
            )

        elif tool_name == "web_search":

            results["web"] = tool(
                question,
            )

    return results