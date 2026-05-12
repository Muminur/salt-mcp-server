"""Unit tests for live_fetch tool logic."""

from __future__ import annotations

import pytest

from salt_cisco_mcp.tools.live_fetch import live_fetch_logic

_ALLOWED_URL = "https://docs.saltproject.io/en/3007/topics/ntp.html"
_BLOCKED_URL = "https://example.com/page.html"


@pytest.mark.anyio
async def test_live_fetch_returns_error_when_disabled() -> None:
    result = await live_fetch_logic(_ALLOWED_URL, network_enabled=False)
    assert isinstance(result, dict)
    assert result.get("error") is not None


@pytest.mark.anyio
async def test_live_fetch_blocks_disallowed_domain() -> None:
    result = await live_fetch_logic(_BLOCKED_URL, network_enabled=True)
    assert isinstance(result, dict)
    assert result.get("error") is not None


@pytest.mark.anyio
async def test_live_fetch_returns_content_for_allowed_url(httpx_mock: None = None) -> None:
    """With a mock client, live_fetch returns content for allowed domain."""
    import httpx

    class _Mock(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"<html><body>NTP docs</body></html>",
                headers={"content-type": "text/html"},
            )

    client = httpx.AsyncClient(transport=_Mock())
    result = await live_fetch_logic(_ALLOWED_URL, network_enabled=True, client=client)
    await client.aclose()
    assert isinstance(result, dict)
    assert result.get("error") is None
    assert "content" in result or "html" in result or "text" in result


@pytest.mark.anyio
async def test_live_fetch_source_field_indicates_live() -> None:
    """Result carries source='live' when fetched successfully."""
    import httpx

    class _Mock(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"<html><body>ok</body></html>", headers={})

    client = httpx.AsyncClient(transport=_Mock())
    result = await live_fetch_logic(_ALLOWED_URL, network_enabled=True, client=client)
    await client.aclose()
    assert result.get("source") == "live"
