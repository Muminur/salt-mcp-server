"""search_docs MCP tool — hybrid BM25 retrieval with citation tuples."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from mcp.server.fastmcp import Context

from salt_cisco_mcp.docs.retriever import bm25_search, trim_to_budget
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.observability.log import log_tool_call

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def _module_name_from_url(url: str) -> str:
    """Extract module name from URL, e.g. 'salt.modules.ntp' from '...ntp.html'."""
    path = urlparse(url).path
    name = path.split("/")[-1]
    if name.endswith(".html"):
        name = name[:-5]
    return name


def search_docs_logic(
    store: DocStore,
    query: str,
    top_k: int = 10,
    token_budget: int | None = None,
    low_confidence_threshold: float = 1.0,
    *,
    brief: bool = False,
    live_fallback_enabled: bool = False,
    upstream_base: str = "",
) -> dict[str, Any]:
    """Core retrieval logic — no MCP dependencies, fully unit-testable."""
    if not query or not query.strip():
        return {"results": [], "low_confidence": False, "total": 0}

    results = bm25_search(store, query, limit=top_k)

    if token_budget is not None:
        results = trim_to_budget(results, token_budget)

    low_confidence = len(results) > 0 and results[0].score < low_confidence_threshold

    items = []
    for r in results:
        url = r.url
        anchor_url = url + r.anchor if url else r.anchor
        module = _module_name_from_url(url) if url else ""
        item: dict[str, Any] = {
            "anchor_url": anchor_url,
            "kind": r.kind,
            "doc_hash": r.doc_hash,
            "module": module,
            "function": r.heading,
        }
        if not brief:
            item["text"] = r.text
        items.append(item)

    out: dict[str, Any] = {"results": items, "low_confidence": low_confidence, "total": len(items)}
    if len(items) == 0 and live_fallback_enabled and upstream_base:
        out["live_fallback_hint"] = upstream_base
    return out


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the search_docs tool on the FastMCP instance."""

    @mcp.tool()
    async def search_docs(
        query: str,
        top_k: int = 5,
        token_budget: int | None = None,
        brief: bool = False,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Search Salt 3007 documentation and return cited chunks.

        Returns chunks with citation tuples {module, anchor_url, doc_hash}.
        Always call this before writing any Salt code.

        Args:
            brief: When True, return citation fields only (no text). Use for
                   scanning multiple topics before calling get_doc for full text.
                   Reduces tokens by ~80% per result.
        """
        t0 = time.perf_counter()
        app_state = ctx.request_context.lifespan_context
        budget = token_budget if token_budget is not None else settings.retrieval.default_response_tokens
        result = search_docs_logic(
            app_state.store,
            query,
            top_k=top_k,
            token_budget=budget,
            brief=brief,
            low_confidence_threshold=settings.retrieval.low_confidence_bm25,
            live_fallback_enabled=settings.network.live_fallback,
            upstream_base=settings.network.upstream_base,
        )
        duration_ms = (time.perf_counter() - t0) * 1000
        tokens_returned = sum(
            len(r.get("text", "").split()) for r in result.get("results", [])
        )
        log_tool_call(
            tool="search_docs",
            duration_ms=duration_ms,
            tokens_returned=tokens_returned,
            tokens_budget=budget,
            source="index",
            low_confidence=result.get("low_confidence"),
            client_id=ctx.client_id or "",
        )
        app_state.metrics.inc("salt_mcp_tool_calls_total", {"tool": "search_docs"})
        app_state.metrics.observe("salt_mcp_tool_latency_ms", duration_ms)
        if result.get("low_confidence"):
            app_state.metrics.inc("salt_mcp_validation_failures_total", {"tool": "search_docs"})
        app_state.metrics.write_textfile(
            str(Path(settings.telemetry.metrics_dir) / "metrics.prom")
        )
        return result
