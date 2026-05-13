"""live_fetch MCP tool — live fallback to docs.saltproject.io with ETag cache."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from mcp.server.fastmcp import Context

from salt_cisco_mcp.live.fallback import fetch as _fallback_fetch
from salt_cisco_mcp.observability.log import log_tool_call

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

    _MAX_CONTENT_CHARS = 16_000  # ~4K tokens; prevents 50KB+ raw HTML responses

    @mcp.tool()
    async def live_fetch(
        url: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Live fallback: fetch a page from docs.saltproject.io.

        Only available when network.live_fallback is enabled in config.
        Domain is restricted to docs.saltproject.io.
        Content is capped at ~4K tokens to avoid oversized responses.
        """
        t0 = time.perf_counter()
        app_state = ctx.request_context.lifespan_context
        result = await live_fetch_logic(
            url,
            network_enabled=settings.network.live_fallback,
            cache_dir=settings.paths.live_cache,
            ttl_s=settings.network.live_cache_ttl_s,
        )
        content = result.get("content", "")
        if len(content) > _MAX_CONTENT_CHARS:
            result = {**result, "content": content[:_MAX_CONTENT_CHARS], "truncated": True}
        duration_ms = (time.perf_counter() - t0) * 1000
        content_len = len(result.get("content", ""))
        log_tool_call(
            tool="live_fetch",
            duration_ms=duration_ms,
            tokens_returned=content_len // 4,
            tokens_budget=None,
            source=result.get("source"),
            low_confidence=None,
            client_id=ctx.client_id or "",
        )
        app_state.metrics.inc("salt_mcp_tool_calls_total", {"tool": "live_fetch"})
        app_state.metrics.observe("salt_mcp_tool_latency_ms", duration_ms)
        app_state.metrics.inc("salt_mcp_live_fallback_calls_total")
        app_state.metrics.write_textfile(
            str(Path(settings.telemetry.metrics_dir) / "metrics.prom")
        )
        return result
