"""Tests for salt_cisco_mcp.live.fallback ETag-aware disk cache."""

from __future__ import annotations

import time
from pathlib import Path

import httpx
import pytest

_URL = "https://docs.saltproject.io/en/3007/topics/ntp.html"
_BLOCKED = "https://evil.example.com/steal.html"
_ALLOWED: frozenset[str] = frozenset(["docs.saltproject.io"])


# ---------------------------------------------------------------------------
# transport helpers
# ---------------------------------------------------------------------------


def _client_200(content: str = "<html>ok</html>", etag: str | None = None) -> httpx.AsyncClient:
    class _T(httpx.AsyncBaseTransport):
        async def handle_async_request(self, req: httpx.Request) -> httpx.Response:
            headers = {"etag": etag} if etag else {}
            return httpx.Response(200, text=content, headers=headers)

    return httpx.AsyncClient(transport=_T())


def _client_304() -> httpx.AsyncClient:
    class _T(httpx.AsyncBaseTransport):
        async def handle_async_request(self, req: httpx.Request) -> httpx.Response:
            return httpx.Response(304)

    return httpx.AsyncClient(transport=_T())


def _client_no_network() -> httpx.AsyncClient:
    """Raises if any network call is made (verifies offline path)."""

    class _T(httpx.AsyncBaseTransport):
        async def handle_async_request(self, req: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected network call to {req.url}")

    return httpx.AsyncClient(transport=_T())


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_fetch_network_disabled_no_cache(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import fetch

    result = await fetch(
        _URL,
        network_enabled=False,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=_client_no_network(),
    )
    assert "error" in result


@pytest.mark.anyio
async def test_fetch_network_disabled_with_cache(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import _cache_path, _save_cache, fetch

    path = _cache_path(str(tmp_path), _URL)
    _save_cache(
        path,
        {
            "url": _URL,
            "content": "<html>cached</html>",
            "status_code": 200,
            "cached_at": time.time(),
        },
    )

    result = await fetch(
        _URL,
        network_enabled=False,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=_client_no_network(),
    )
    assert result.get("source") == "cache"
    assert "content" in result


@pytest.mark.anyio
async def test_fetch_domain_not_allowed(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import fetch

    result = await fetch(
        _BLOCKED,
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=_client_200(),
    )
    assert "error" in result


@pytest.mark.anyio
async def test_fetch_creates_cache_file(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import _cache_path, fetch

    result = await fetch(
        _URL,
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=_client_200("<html>fresh</html>"),
    )
    assert result.get("source") == "live"
    assert _cache_path(str(tmp_path), _URL).exists()


@pytest.mark.anyio
async def test_fetch_within_ttl_serves_from_disk(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import _cache_path, _save_cache, fetch

    path = _cache_path(str(tmp_path), _URL)
    _save_cache(
        path,
        {
            "url": _URL,
            "content": "<html>cached</html>",
            "status_code": 200,
            "cached_at": time.time(),
        },
    )

    result = await fetch(
        _URL,
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=_client_no_network(),
    )
    assert result.get("source") == "live-cache"


@pytest.mark.anyio
async def test_fetch_sends_etag_header_on_re_fetch(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import _cache_path, _save_cache, fetch

    path = _cache_path(str(tmp_path), _URL)
    _save_cache(
        path,
        {
            "url": _URL,
            "content": "<html>cached</html>",
            "status_code": 200,
            "cached_at": 0.0,
            "etag": '"my-etag"',
        },
    )

    received: list[dict[str, str]] = []

    class _T(httpx.AsyncBaseTransport):
        async def handle_async_request(self, req: httpx.Request) -> httpx.Response:
            received.append(dict(req.headers))
            return httpx.Response(304)

    client = httpx.AsyncClient(transport=_T())
    await fetch(
        _URL,
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=client,
    )
    assert any("if-none-match" in h for h in received)


@pytest.mark.anyio
async def test_fetch_304_returns_live_cache_source(tmp_path: Path) -> None:
    from salt_cisco_mcp.live.fallback import _cache_path, _save_cache, fetch

    path = _cache_path(str(tmp_path), _URL)
    _save_cache(
        path,
        {
            "url": _URL,
            "content": "<html>cached</html>",
            "status_code": 200,
            "cached_at": 0.0,
            "etag": '"abc"',
        },
    )

    result = await fetch(
        _URL,
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=3600,
        client=_client_304(),
    )
    assert result.get("source") == "live-cache"


@pytest.mark.anyio
async def test_ttl_zero_revalidates_via_etag(tmp_path: Path) -> None:
    """ttl_s=0 forces network revalidation even when cache is fresh."""
    from salt_cisco_mcp.live.fallback import _cache_path, _save_cache, fetch

    path = _cache_path(str(tmp_path), _URL)
    _save_cache(
        path,
        {
            "url": _URL,
            "content": "<html>old</html>",
            "status_code": 200,
            "cached_at": time.time(),
        },
    )

    result = await fetch(
        _URL,
        network_enabled=True,
        allowed_domains=_ALLOWED,
        cache_dir=str(tmp_path),
        ttl_s=0,
        client=_client_200("<html>new</html>"),
    )
    assert result.get("source") == "live"
