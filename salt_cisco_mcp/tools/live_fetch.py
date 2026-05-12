"""live_fetch MCP tool — live fallback to docs.saltproject.io with ETag cache."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING, Any

import httpx
from mcp.server.fastmcp import Context

from salt_cisco_mcp.live.fallback import fetch as _fallback_fetch

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings

_ALLOWED_DOMAINS: frozenset[str] = frozenset(["docs.saltproject.io"])


async def live_fetch_logic(
    url: str,
    *,
    network_enabled: bool = True,
    cache_dir: str | None = None,
    ttl_s: int = 3600,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Fetch a live URL from the allowed domain list with ETag disk cache.

    Returns a dict with 'content', 'source', or 'error'.
    cache_dir=None uses a per-call temp directory (no cross-call caching).
    """
    effective_cache_dir = cache_dir if cache_dir is not None else tempfile.mkdtemp()
    close_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
    try:
        return await _fallback_fetch(
            url,
            network_enabled=network_enabled,
            allowed_domains=_ALLOWED_DOMAINS,
            cache_dir=effective_cache_dir,
            ttl_s=ttl_s,
            client=client,
        )
    finally:
        if close_client:
            await client.aclose()


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the live_fetch tool on the FastMCP instance (network-gated)."""

    @mcp.tool()
    async def live_fetch(
        url: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Live fallback: fetch a page from docs.saltproject.io.

        Only available when network.live_fallback is enabled in config.
        Domain is restricted to docs.saltproject.io.
        """
        return await live_fetch_logic(
            url,
            network_enabled=settings.network.live_fallback,
            cache_dir=settings.paths.live_cache,
            ttl_s=settings.network.live_cache_ttl_s,
        )
