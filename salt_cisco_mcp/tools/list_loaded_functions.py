"""MCP tool: list_loaded_functions — enumerate available Salt functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.module_introspect import FunctionCache

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


_DEFAULT_LIMIT = 200
_MAX_LIMIT = 500


def list_loaded_functions_logic(
    cache: FunctionCache,
    prefix: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Return known Salt functions, optionally filtered by module prefix."""
    fns = cache.list_functions(prefix=prefix)
    capped = limit if limit > 0 else _MAX_LIMIT
    capped = min(capped, _MAX_LIMIT)
    truncated = len(fns) > capped
    return {
        "functions": fns[:capped],
        "total": len(fns),
        "truncated": truncated,
    }


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the list_loaded_functions tool on *mcp*."""

    @mcp.tool()
    async def list_loaded_functions(
        prefix: str | None = None,
        limit: int = _DEFAULT_LIMIT,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """List Salt functions available on this master, filtered by optional module prefix.

        Args:
            prefix: Module prefix filter (e.g. 'napalm', 'state'). Recommended to avoid
                    large unfiltered responses.
            limit: Max functions to return (default 200, max 500).
        """
        app_state = ctx.request_context.lifespan_context
        if app_state.function_cache is None:
            return {"error": "salt-call not available", "functions": [], "total": 0}
        return list_loaded_functions_logic(app_state.function_cache, prefix=prefix, limit=limit)
