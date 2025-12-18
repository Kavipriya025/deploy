import pytest


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {tool.name for tool in tools}

    # Positive: all expected tools are registered
    assert {
        "create_whistle",
        "list_whistles",
        "search_businesses",
        "toggle_visibility",
        "get_user_profile",
    }.issubset(tool_names)


@pytest.mark.asyncio
async def test_list_tools_does_not_expose_unknown_tool(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {tool.name for tool in tools}

    # Negative: an obviously fake tool should not be present
    assert "non_existent_tool_xyz" not in tool_names

