"""MCP tool: list_loaded_functions — enumerate available Salt functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.module_introspect import FunctionCache

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def list_loaded_functions_logic(
    cache: FunctionCache,
    prefix: str | None = None,
) -> dict[str, Any]:
    """Return known Salt functions, optionally filtered by module prefix."""
    fns = cache.list_functions(prefix=prefix)
    return {"functions": fns, "total": len(fns)}


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the list_loaded_functions tool on *mcp*."""

    @mcp.tool()
    async def list_loaded_functions(
        prefix: str | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """List Salt functions available on this master, filtered by optional module prefix."""
        app_state = ctx.request_context.lifespan_context
        if app_state.function_cache is None:
            return {"error": "salt-call not available", "functions": [], "total": 0}
        return list_loaded_functions_logic(app_state.function_cache, prefix=prefix)
