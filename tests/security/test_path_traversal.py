"""Security: path-traversal and domain-allowlist enforcement."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

_ALLOWED: frozenset[str] = frozenset(["docs.saltproject.io"])


def _no_network_client() -> httpx.AsyncClient:
    class _T(httpx.AsyncBaseTransport):
        async def handle_async_request(self, req: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected network call: {req.url}")

    return httpx.AsyncClient(transport=_T())


@pytest.mark.anyio
async def test_file_scheme_blocked(tmp_path: Path) -> None:
    """file:// URLs must be rejected — domain allowlist blocks non-http(s) schemes."""
    from salt_cisco_mcp.live.fallback import fetch

    result = await fetch(
        "file:///etc/passwd",
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=60,
        client=_no_network_client(),
    )
    assert "error" in result


@pytest.mark.anyio
async def test_localhost_blocked(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import fetch

    result = await fetch(
        "http://localhost/attack",
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=60,
        client=_no_network_client(),
    )
    assert "error" in result


@pytest.mark.anyio
async def test_private_ip_blocked(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import fetch

    result = await fetch(
        "http://192.168.1.1/secret",
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=60,
        client=_no_network_client(),
    )
    assert "error" in result


@pytest.mark.anyio
async def test_subdomain_squatting_blocked(tmp_path: Path) -> None:
    """docs.saltproject.io.evil.com must NOT pass the allowlist."""
    from salt_cisco_mcp.live.fallback import fetch

    result = await fetch(
        "https://docs.saltproject.io.evil.com/steal",
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=60,
        client=_no_network_client(),
    )
    assert "error" in result


def test_anchor_url_traversal_returns_none() -> None:
    """Anchor URL with path traversal chars doesn't access the filesystem."""
    from salt_cisco_mcp.docs.store import DocStore
    from salt_cisco_mcp.tools.get_doc import get_doc_logic

    store = DocStore(":memory:")
    store.init_schema()
    result = get_doc_logic(store, "https://docs.saltproject.io/../../../etc/passwd")
    assert result is None


def test_cache_key_no_path_traversal() -> None:
    """Cache filename is always a hex digest — no path traversal possible."""
    from salt_cisco_mcp.live.fallback import _cache_key

    key = _cache_key("https://docs.saltproject.io/../../../etc/passwd")
    assert "/" not in key
    assert "\\" not in key
    assert ".." not in key
    assert len(key) == 64  # SHA-256 hex


def test_store_sql_parameterized_no_injection() -> None:
    """SQL injection via anchor URL is neutralized by parameterized queries."""
    from salt_cisco_mcp.docs.store import DocStore

    store = DocStore(":memory:")
    store.init_schema()
    result = store.get_chunk_by_anchor_url("'; DROP TABLE chunks; --")
    assert result is None  # returns None safely, table still intact
    assert store.count_chunks() == 0  # chunks table still exists
