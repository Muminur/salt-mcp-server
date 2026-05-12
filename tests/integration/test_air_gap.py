"""Integration tests: air-gap mode and opt-in live network tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Air-gap: retrieval tools return gracefully with live_fallback disabled
# ---------------------------------------------------------------------------


def test_search_docs_air_gap_no_crash() -> None:
    from salt_cisco_mcp.docs.store import DocStore
    from salt_cisco_mcp.tools.search_docs import search_docs_logic

    store = DocStore(":memory:")
    store.init_schema()
    result = search_docs_logic(store, "ntp set servers", live_fallback_enabled=False)
    assert "results" in result
    assert isinstance(result["results"], list)


def test_search_docs_air_gap_hint_absent() -> None:
    from salt_cisco_mcp.docs.store import DocStore
    from salt_cisco_mcp.tools.search_docs import search_docs_logic

    store = DocStore(":memory:")
    store.init_schema()
    result = search_docs_logic(store, "ntp", live_fallback_enabled=False)
    assert "live_fallback_hint" not in result


def test_search_docs_hint_present_when_fallback_enabled() -> None:
    """live_fallback_hint appears when enabled and 0 results returned."""
    from salt_cisco_mcp.docs.store import DocStore
    from salt_cisco_mcp.tools.search_docs import search_docs_logic

    store = DocStore(":memory:")
    store.init_schema()
    result = search_docs_logic(
        store,
        "ntp",
        live_fallback_enabled=True,
        upstream_base="https://docs.saltproject.io/en/3007",
    )
    assert "live_fallback_hint" in result
    assert result["live_fallback_hint"] == "https://docs.saltproject.io/en/3007"


def test_get_doc_air_gap_returns_none() -> None:
    from salt_cisco_mcp.docs.store import DocStore
    from salt_cisco_mcp.tools.get_doc import get_doc_logic

    store = DocStore(":memory:")
    store.init_schema()
    result = get_doc_logic(store, "https://docs.saltproject.io/en/3007/no-such-page.html")
    assert result is None


@pytest.mark.anyio
async def test_live_fetch_air_gap_returns_error() -> None:
    from salt_cisco_mcp.tools.live_fetch import live_fetch_logic

    result = await live_fetch_logic(
        "https://docs.saltproject.io/en/3007/topics/ntp.html",
        network_enabled=False,
    )
    assert "error" in result


# ---------------------------------------------------------------------------
# Opt-in live network tests (SALT_MCP_LIVE_TESTS=1)
# ---------------------------------------------------------------------------

_LIVE = pytest.mark.skipif(
    os.environ.get("SALT_MCP_LIVE_TESTS") != "1",
    reason="set SALT_MCP_LIVE_TESTS=1 to run live network tests",
)


@_LIVE
@pytest.mark.anyio
async def test_live_fetch_real_request(tmp_path: Path) -> None:
    import httpx

    from salt_cisco_mcp.live.fallback import fetch

    async with httpx.AsyncClient(timeout=15.0) as client:
        result = await fetch(
            "https://docs.saltproject.io/en/3007/contents.html",
            network_enabled=True,
            allowed_domains=frozenset(["docs.saltproject.io"]),
            cache_dir=str(tmp_path),
            ttl_s=300,
            client=client,
        )
    assert "error" not in result
    assert result.get("source") in ("live", "live-cache")
