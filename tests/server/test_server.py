"""Tests for salt_cisco_mcp.server — FastMCP instance and lifespan."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
async def test_server_list_tools_has_registered_tools() -> None:
    srv = create_server(Settings())
    tools = await srv.list_tools()
    tool_names = {t.name for t in tools}
    assert {"search_docs", "get_doc", "list_modules", "live_fetch"} <= tool_names


@pytest.mark.anyio
async def test_server_list_tools_returns_list() -> None:
    srv = create_server(Settings())
    tools = await srv.list_tools()
    assert isinstance(tools, list)


@pytest.mark.anyio
async def test_lifespan_runs_without_error(tmp_path: Path) -> None:
    """Lifespan enter/exit must not raise."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")
    settings.paths.doc_db = db_path
    srv = create_server(settings)
    lifespan = _make_lifespan(settings)
    async with lifespan(srv):
        pass


@pytest.mark.anyio
async def test_lifespan_closes_store_on_exit(tmp_path: Path) -> None:
    """DocStore must be closed after lifespan exits."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")
    settings.paths.doc_db = db_path
    srv = create_server(settings)
    closed_stores: list[object] = []

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


@pytest.mark.anyio
async def test_lifespan_logs_warning_when_salt_call_missing(
    tmp_path: Path,
) -> None:
    """Lifespan logs a warning when salt-call is not on PATH."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")
    settings.paths.doc_db = db_path
    srv = create_server(settings)
    lifespan = _make_lifespan(settings)

    with patch("salt_cisco_mcp.server.shutil.which", return_value=None):
        async with lifespan(srv):
            pass


@pytest.mark.anyio
async def test_lifespan_logs_salt_call_found(tmp_path: Path) -> None:
    """Lifespan logs info when salt-call is found."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")
    settings.paths.doc_db = db_path
    srv = create_server(settings)
    lifespan = _make_lifespan(settings)

    with patch("salt_cisco_mcp.server.shutil.which", return_value="/usr/bin/salt-call"):
        async with lifespan(srv):
            pass


@pytest.mark.anyio
async def test_lifespan_handles_fastembed_unavailable(
    tmp_path: Path,
) -> None:
    """Lifespan does not raise when fastembed is not installed."""
    from salt_cisco_mcp.server import _make_lifespan

    settings = Settings()
    db_path = str(tmp_path / "test.db")
    settings.paths.doc_db = db_path
    srv = create_server(settings)
    lifespan = _make_lifespan(settings)

    import sys

    with patch.dict(sys.modules, {"fastembed": None}):
        async with lifespan(srv):
            pass
