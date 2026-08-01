from app.tools.registry import get_tool


def execute_tool_step(
    username: str,
    step: dict,
):

    tool_name = step.get(
        "tool",
        "",
    )

    tool = get_tool(tool_name)

    if tool is None:

        return None

    if tool_name == "web_search":

        return tool(
            step.get(
                "input",
                "",
            )
        )

    if tool_name == "document_search":

        return tool(
            username,
            step.get(
                "input",
                "",
            ),
        )

    if tool_name == "python":

        return tool(
            step.get(
                "input",
                "",
            )
        )

    return None