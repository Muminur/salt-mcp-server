"""get_doc MCP tool — fetch a specific doc chunk by anchor URL."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.docs.store import DocStore

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def get_doc_logic(store: DocStore, anchor_url: str) -> dict[str, Any] | None:
    """Core lookup logic — returns chunk dict or None if not found."""
    row = store.get_chunk_by_anchor_url(anchor_url)
    if row is None:
        return None
    url = str(row.get("url", ""))
    anchor = str(row.get("anchor", ""))
    return {
        "chunk_id": row["id"],
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
        """
        app_state = ctx.request_context.lifespan_context
        return get_doc_logic(app_state.store, anchor_url)
