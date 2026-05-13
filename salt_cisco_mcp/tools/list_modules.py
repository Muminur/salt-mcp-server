"""list_modules MCP tool — enumerate Salt modules from the doc index."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from mcp.server.fastmcp import Context

from salt_cisco_mcp.docs.store import DocStore

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def _module_name_from_url(url: str) -> str:
    """Extract module name from URL path, e.g. 'salt.modules.ntp' from '...ntp.html'."""
    path = urlparse(url).path
    name = path.split("/")[-1]
    if name.endswith(".html"):
        name = name[:-5]
    return name


_DEFAULT_LIMIT = 200
_MAX_LIMIT = 1000


def list_modules_logic(
    store: DocStore,
    kind: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Return distinct modules from the doc index, optionally filtered by kind."""
    rows = store.list_module_urls(kind=kind)
    capped = min(limit if limit > 0 else _MAX_LIMIT, _MAX_LIMIT)
    return [
        {
            "url": row["url"],
            "kind": row["kind"],
            "name": _module_name_from_url(str(row["url"])),
        }
        for row in rows[:capped]
    ]


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the list_modules tool on the FastMCP instance."""

    @mcp.tool()
    async def list_modules(
        kind: str | None = None,
        limit: int = _DEFAULT_LIMIT,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> list[dict[str, Any]]:
        """Enumerate Salt 3007 modules indexed in the offline doc store.

        Args:
            kind: Filter by 'module', 'state', 'proxy', 'runner', or None for all.
            limit: Max modules to return (default 200, max 1000).
        """
        app_state = ctx.request_context.lifespan_context
        return list_modules_logic(app_state.store, kind=kind, limit=limit)
