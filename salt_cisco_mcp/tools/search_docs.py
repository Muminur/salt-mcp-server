"""search_docs MCP tool — hybrid BM25 retrieval with citation tuples."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from mcp.server.fastmcp import Context

from salt_cisco_mcp.docs.retriever import bm25_search, trim_to_budget
from salt_cisco_mcp.docs.store import DocStore

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
        chunk_row = store.get_chunk_by_id(r.chunk_id)
        url = chunk_row["url"] if chunk_row else ""
        anchor_url = url + r.anchor if url else r.anchor
        module = _module_name_from_url(url) if url else ""
        items.append(
            {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "anchor_url": anchor_url,
                "heading": r.heading,
                "kind": r.kind,
                "score": r.score,
                "doc_hash": r.doc_hash,
                "module": module,
            }
        )

    return {"results": items, "low_confidence": low_confidence, "total": len(items)}


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the search_docs tool on the FastMCP instance."""

    @mcp.tool()
    async def search_docs(
        query: str,
        top_k: int = 10,
        token_budget: int | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Search Salt 3007 documentation and return cited chunks.

        Returns chunks with citation tuples {module, anchor_url, doc_hash}.
        Always call this before writing any Salt code.
        """
        app_state = ctx.request_context.lifespan_context
        budget = token_budget if token_budget is not None else settings.retrieval.hard_cap_tokens
        return search_docs_logic(
            app_state.store,
            query,
            top_k=top_k,
            token_budget=budget,
            low_confidence_threshold=settings.retrieval.low_confidence_bm25,
        )
