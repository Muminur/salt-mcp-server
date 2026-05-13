"""get_doc MCP tool — fetch a specific doc chunk by anchor URL."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
from mcp.server.fastmcp import Context

from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.live.fallback import fetch as _fallback_fetch

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings

_ALLOWED_DOMAINS: frozenset[str] = frozenset(["docs.saltproject.io"])


def get_doc_logic(store: DocStore, anchor_url: str) -> dict[str, Any] | None:
    """Core lookup logic — returns chunk dict or None if not found."""
    row = store.get_chunk_by_anchor_url(anchor_url)
    if row is None:
        return None
    url = str(row.get("url", ""))
    anchor = str(row.get("anchor", ""))
    return {
        "text": row["text"],
        "anchor_url": url + anchor,
        "heading": row["heading"],
        "kind": row["kind"],
        "doc_hash": row["doc_hash"],
    }


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the get_doc tool on the FastMCP instance."""

    @mcp.tool()
    async def get_doc(
        anchor_url: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any] | None:
        """Fetch the full normalized doc chunk for a given anchor URL.

        Returns None if the anchor is not in the offline index.
        Falls back to live fetch when network.live_fallback is enabled.
        """
        app_state = ctx.request_context.lifespan_context
        result = get_doc_logic(app_state.store, anchor_url)
        if result is not None:
            return result
        if not settings.network.live_fallback:
            return None
        async with httpx.AsyncClient(timeout=float(settings.network.request_timeout_s)) as client:
            return await _fallback_fetch(
                anchor_url,
                network_enabled=True,
                allowed_domains=_ALLOWED_DOMAINS,
                cache_dir=settings.paths.live_cache,
                ttl_s=settings.network.live_cache_ttl_s,
                client=client,
            )
