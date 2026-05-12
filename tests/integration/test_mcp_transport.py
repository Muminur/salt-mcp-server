"""In-memory MCP server harness: boot server, list tools, assert empty surface."""

from __future__ import annotations

import pytest

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.server import create_server


@pytest.mark.anyio
async def test_in_memory_list_tools_empty() -> None:
    """Fresh server has no tools registered."""
    srv = create_server(Settings())
    tools = await srv.list_tools()
    assert tools == []


@pytest.mark.anyio
async def test_in_memory_list_tools_returns_list_type() -> None:
    srv = create_server(Settings())
    result = await srv.list_tools()
    assert isinstance(result, list)


@pytest.mark.anyio
async def test_in_memory_call_unknown_tool_raises() -> None:
    """Calling a non-existent tool must raise an error."""
    from mcp.server.fastmcp.exceptions import ToolError

    srv = create_server(Settings())
    with pytest.raises((ToolError, KeyError, Exception)):
        await srv.call_tool("nonexistent_tool", {})


@pytest.mark.anyio
async def test_in_memory_list_prompts_empty() -> None:
    srv = create_server(Settings())
    prompts = await srv.list_prompts()
    assert prompts == []


@pytest.mark.anyio
async def test_in_memory_list_resources_empty() -> None:
    srv = create_server(Settings())
    resources = await srv.list_resources()
    assert resources == []
