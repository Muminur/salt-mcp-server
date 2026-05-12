"""MCP resources for salt-docs:// URI scheme."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from mcp.server.fastmcp import Context

from salt_cisco_mcp.docs.store import DocStore

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def _module_name_from_url(url: str) -> str:
    path = urlparse(url).path
    name = path.split("/")[-1]
    if name.endswith(".html"):
        name = name[:-5]
    return name


def contents_logic(store: DocStore) -> list[dict[str, Any]]:
    """Return all distinct module URLs with kind and name."""
    rows = store.list_module_urls()
    return [
        {
            "url": row["url"],
            "kind": row["kind"],
            "name": _module_name_from_url(str(row["url"])),
        }
        for row in rows
    ]


def module_doc_logic(store: DocStore, kind: str, name: str) -> list[dict[str, Any]]:
    """Return all chunks for modules matching kind and name."""
    rows = store.list_module_urls(kind=kind)
    results = []
    for row in rows:
        url = str(row["url"])
        if _module_name_from_url(url) == name:
            chunks = store.get_chunks_by_url(url)
            results.extend(chunks)
    return results


def function_doc_logic(store: DocStore, qualified_name: str) -> dict[str, Any] | None:
    """Return the chunk whose heading matches the qualified function name."""
    return store.get_chunk_by_heading(qualified_name)


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register salt-docs:// MCP resources."""

    @mcp.resource(
        "salt-docs://contents",
        description="List all Salt 3007 modules indexed in the offline doc store.",
        mime_type="application/json",
    )
    async def salt_docs_contents(
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> str:
        """Enumerate all modules in the offline doc index."""
        app_state = ctx.request_context.lifespan_context
        modules = contents_logic(app_state.store)
        return json.dumps(modules)

    @mcp.resource(
        "salt-docs://module/{kind}/{name}",
        description="Retrieve all doc chunks for a specific Salt module.",
        mime_type="application/json",
    )
    async def salt_docs_module(
        kind: str,
        name: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> str:
        """Fetch all chunks for the given module kind and name."""
        app_state = ctx.request_context.lifespan_context
        chunks = module_doc_logic(app_state.store, kind, name)
        return json.dumps(chunks)

    @mcp.resource(
        "salt-docs://function/{qualified_name}",
        description="Retrieve the doc chunk for a Salt function by its qualified name.",
        mime_type="application/json",
    )
    async def salt_docs_function(
        qualified_name: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> str:
        """Fetch the doc chunk matching the given qualified function name."""
        app_state = ctx.request_context.lifespan_context
        chunk = function_doc_logic(app_state.store, qualified_name)
        return json.dumps(chunk)
