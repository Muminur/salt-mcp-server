"""live_fetch MCP tool — live fallback to docs.saltproject.io with ETag cache."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import Context

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings

_ALLOWED_DOMAINS = frozenset(["docs.saltproject.io"])


def _domain_is_allowed(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host in _ALLOWED_DOMAINS


async def live_fetch_logic(
    url: str,
    *,
    network_enabled: bool = True,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Fetch a live URL from the allowed domain list.

    Returns a dict with 'content', 'source', or 'error'.
    """
    if not network_enabled:
        return {
            "error": "live network access is disabled (network.live_fallback=false)",
            "url": url,
        }

    if not _domain_is_allowed(url):
        return {
            "error": f"domain not in allowlist: {urlparse(url).hostname}",
            "url": url,
        }

    close_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)

    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return {
            "url": url,
            "status_code": response.status_code,
            "content": response.text,
            "source": "live",
        }
    except httpx.HTTPError as exc:
        return {"error": str(exc), "url": url}
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
        return await live_fetch_logic(url, network_enabled=settings.network.live_fallback)
