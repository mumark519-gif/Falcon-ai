from app.tools.tool_manager import execute_tools


def test_execute_web_tool():

    results = execute_tools(
        "pytestuser",
        "Latest AI news today"
    )

    assert "web" in results