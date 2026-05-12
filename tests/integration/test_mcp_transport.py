"""MCP transport integration tests: in-memory harness and protocol round-trips."""

from __future__ import annotations

from pathlib import Path

import anyio
import pytest
from mcp import ClientSession
from mcp.types import Tool

from salt_cisco_mcp.config import HttpAuthConfig, SecurityConfig, Settings
from salt_cisco_mcp.server import create_server

# ---------------------------------------------------------------------------
# In-memory harness (direct FastMCP API — no transport layer)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_in_memory_list_tools_has_registered_tools() -> None:
    """create_server registers all four tools."""
    srv = create_server(Settings())
    tools = await srv.list_tools()
    tool_names = {t.name for t in tools}
    assert {"search_docs", "get_doc", "list_modules", "live_fetch"} <= tool_names


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
async def test_in_memory_list_prompts() -> None:
    srv = create_server(Settings())
    prompts = await srv.list_prompts()
    prompt_names = {p.name for p in prompts}
    assert {"draft_state_for_cisco", "debug_failing_state"} <= prompt_names


@pytest.mark.anyio
async def test_in_memory_list_resources_empty() -> None:
    srv = create_server(Settings())
    resources = await srv.list_resources()
    assert resources == []


# ---------------------------------------------------------------------------
# Stdio round-trip via memory streams (full JSON-RPC protocol)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_stdio_round_trip_list_tools(tmp_path: Path) -> None:
    """Full JSON-RPC round-trip via in-process memory streams."""
    settings = Settings()
    settings.paths.doc_db = str(tmp_path / "rt.db")
    srv = create_server(settings)
    init_opts = srv._mcp_server.create_initialization_options()

    s_in_send, s_in_recv = anyio.create_memory_object_stream(100)
    s_out_send, s_out_recv = anyio.create_memory_object_stream(100)

    tools_result: list[Tool] = []

    async def _run_server() -> None:
        try:
            await srv._mcp_server.run(s_in_recv, s_out_send, init_opts, raise_exceptions=True)
        except Exception:
            pass

    async def _run_client() -> None:
        async with ClientSession(s_out_recv, s_in_send) as session:
            await session.initialize()
            result = await session.list_tools()
            tools_result.extend(result.tools)

    async with anyio.create_task_group() as tg:
        tg.start_soon(_run_server)
        tg.start_soon(_run_client)

    tool_names = {t.name for t in tools_result}
    assert {"search_docs", "get_doc", "list_modules", "live_fetch"} <= tool_names


@pytest.mark.anyio
async def test_stdio_round_trip_list_prompts(tmp_path: Path) -> None:
    """Prompts are advertised over full JSON-RPC round-trip."""
    settings = Settings()
    settings.paths.doc_db = str(tmp_path / "rtp.db")
    srv = create_server(settings)
    init_opts = srv._mcp_server.create_initialization_options()

    s_in_send, s_in_recv = anyio.create_memory_object_stream(100)
    s_out_send, s_out_recv = anyio.create_memory_object_stream(100)

    prompts_result: list[object] = []

    async def _run_server() -> None:
        try:
            await srv._mcp_server.run(s_in_recv, s_out_send, init_opts, raise_exceptions=True)
        except Exception:
            pass

    async def _run_client() -> None:
        async with ClientSession(s_out_recv, s_in_send) as session:
            await session.initialize()
            result = await session.list_prompts()
            prompts_result.extend(result.prompts)

    async with anyio.create_task_group() as tg:
        tg.start_soon(_run_server)
        tg.start_soon(_run_client)

    prompt_names = {p.name for p in prompts_result}  # type: ignore[union-attr]
    assert {"draft_state_for_cisco", "debug_failing_state"} <= prompt_names


# ---------------------------------------------------------------------------
# HTTP bearer token auth challenge
# ---------------------------------------------------------------------------


def test_http_bearer_rejects_unauthenticated(tmp_path: Path) -> None:
    """HTTP transport returns 401 for requests without a valid bearer token."""
    from starlette.testclient import TestClient

    from salt_cisco_mcp.transports import BearerTokenMiddleware

    token_file = tmp_path / "bearer.token"
    token_file.write_text("s3cr3t-http-token")

    settings = Settings(
        security=SecurityConfig(
            http_auth=HttpAuthConfig(mode="bearer", bearer_token_file=str(token_file))
        )
    )
    srv = create_server(settings)

    from salt_cisco_mcp.transports import build_http_app

    app = build_http_app(srv, settings)
    assert isinstance(app, BearerTokenMiddleware)

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/mcp")
    assert r.status_code == 401


def test_http_bearer_accepts_valid_token(tmp_path: Path) -> None:
    """HTTP transport passes through requests with the correct bearer token."""
    from starlette.testclient import TestClient

    token_file = tmp_path / "bearer.token"
    token_file.write_text("valid-token")

    settings = Settings(
        security=SecurityConfig(
            http_auth=HttpAuthConfig(mode="bearer", bearer_token_file=str(token_file))
        )
    )
    srv = create_server(settings)

    from salt_cisco_mcp.transports import build_http_app

    app = build_http_app(srv, settings)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/mcp", headers={"Authorization": "Bearer valid-token"})
    assert r.status_code != 401
