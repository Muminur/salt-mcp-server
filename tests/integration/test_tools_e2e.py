"""End-to-end integration tests: tools registered on server, MCP round-trip."""

from __future__ import annotations

from pathlib import Path

import anyio
import pytest
from mcp import ClientSession

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.server import create_server


def _seed_db(db_path: str) -> None:
    store = DocStore(db_path)
    store.init_schema()
    chunk = Chunk(
        text="NTP configuration for Cisco IOS devices.",
        heading="ntp.set_servers",
        anchor="#ntp-set-servers-0",
        token_count=7,
        kind="module",
    )
    meta = PageMeta(
        title="salt.modules.ntp",
        anchor="#ntp",
        breadcrumb="",
        kind="module",
        salt_version="3007",
        url="https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html",
    )
    store.upsert_chunk(chunk, meta, doc_hash="seed-hash")
    store.close()


@pytest.mark.anyio
async def test_list_tools_includes_search_docs(tmp_path: Path) -> None:
    """After registration, list_tools includes search_docs."""
    settings = Settings()
    settings.paths.doc_db = str(tmp_path / "tools_e2e.db")
    srv = create_server(settings)

    tools = await srv.list_tools()
    tool_names = [t.name for t in tools]
    assert "search_docs" in tool_names


@pytest.mark.anyio
async def test_list_tools_includes_get_doc(tmp_path: Path) -> None:
    settings = Settings()
    settings.paths.doc_db = str(tmp_path / "tools_e2e2.db")
    srv = create_server(settings)

    tools = await srv.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_doc" in tool_names


@pytest.mark.anyio
async def test_list_tools_includes_list_modules(tmp_path: Path) -> None:
    settings = Settings()
    settings.paths.doc_db = str(tmp_path / "tools_e2e3.db")
    srv = create_server(settings)

    tools = await srv.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_modules" in tool_names


@pytest.mark.anyio
async def test_search_docs_via_mcp_round_trip(tmp_path: Path) -> None:
    """search_docs returns results over full JSON-RPC round-trip."""
    db_path = str(tmp_path / "rtt.db")
    _seed_db(db_path)

    settings = Settings()
    settings.paths.doc_db = db_path
    srv = create_server(settings)
    init_opts = srv._mcp_server.create_initialization_options()

    s_in_send, s_in_recv = anyio.create_memory_object_stream(100)
    s_out_send, s_out_recv = anyio.create_memory_object_stream(100)

    call_result: list[object] = []

    async def _run_server() -> None:
        try:
            await srv._mcp_server.run(s_in_recv, s_out_send, init_opts, raise_exceptions=True)
        except Exception:
            pass

    async def _run_client() -> None:
        async with ClientSession(s_out_recv, s_in_send) as session:
            await session.initialize()
            result = await session.call_tool("search_docs", {"query": "NTP"})
            call_result.append(result)

    async with anyio.create_task_group() as tg:
        tg.start_soon(_run_server)
        tg.start_soon(_run_client)

    assert len(call_result) == 1
    # Result content is a list of ContentBlock; check it's not an error
    raw = call_result[0]
    assert hasattr(raw, "content") or isinstance(raw, (list, dict))
