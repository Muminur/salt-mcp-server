"""Tests for salt_cisco_mcp.server — FastMCP instance and lifespan."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.server import create_server


def test_create_server_returns_fastmcp() -> None:
    srv = create_server(Settings())
    assert isinstance(srv, FastMCP)


def test_server_name() -> None:
    srv = create_server(Settings())
    assert srv.name == "salt-cisco-mcp"


def test_server_has_instructions() -> None:
    srv = create_server(Settings())
    assert srv.instructions is not None
    assert len(srv.instructions) > 10


@pytest.mark.anyio
async def test_server_list_tools_empty_initially() -> None:
    srv = create_server(Settings())
    tools = await srv.list_tools()
    assert tools == []


@pytest.mark.anyio
async def test_server_list_tools_returns_list() -> None:
    srv = create_server(Settings())
    tools = await srv.list_tools()
    assert isinstance(tools, list)


@pytest.mark.anyio
async def test_lifespan_runs_without_error(tmp_path: pytest.TempPathFactory) -> None:
    """Lifespan enter/exit must not raise."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")  # type: ignore[operator]
    settings.paths.doc_db = db_path  # type: ignore[assignment]

    srv = create_server(settings)
    lifespan = _make_lifespan(settings)
    async with lifespan(srv):
        pass  # just verify no exception


@pytest.mark.anyio
async def test_lifespan_closes_store_on_exit(tmp_path: pytest.TempPathFactory) -> None:
    """DocStore must be closed after lifespan exits."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")  # type: ignore[operator]
    settings.paths.doc_db = db_path  # type: ignore[assignment]

    srv = create_server(settings)
    closed_stores: list[object] = []

    from unittest.mock import patch

    from salt_cisco_mcp.docs.store import DocStore

    original_close = DocStore.close

    def _spy_close(self: DocStore) -> None:
        closed_stores.append(self)
        original_close(self)

    with patch.object(DocStore, "close", _spy_close):
        lifespan = _make_lifespan(settings)
        async with lifespan(srv):
            pass

    assert len(closed_stores) == 1
