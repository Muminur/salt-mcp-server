"""MCP tool: confirm_function_exists — canonical anti-hallucination gate."""

from __future__ import annotations

from difflib import get_close_matches
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.module_introspect import FunctionCache

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def confirm_function_exists_logic(
    cache: FunctionCache,
    name: str,
) -> dict[str, Any]:
    """Check if *name* exists; return suggestions from the same module on miss."""
    exists = cache.confirm_function_exists(name)
    if exists:
        return {"name": name, "exists": True, "suggestions": []}

    module = name.split(".")[0] if "." in name else ""
    all_fns = cache.list_functions(prefix=module) if module else cache.list_functions()
    suggestions = get_close_matches(name, all_fns, n=5, cutoff=0.4)
    return {"name": name, "exists": False, "suggestions": suggestions}


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the confirm_function_exists tool on *mcp*."""

    @mcp.tool()
    async def confirm_function_exists(
        name: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Verify a Salt function name exists. Returns close matches if not found."""
        app_state = ctx.request_context.lifespan_context
        if app_state.function_cache is None:
            return {
                "name": name,
                "exists": False,
                "suggestions": [],
                "error": "salt-call not available",
            }
        return confirm_function_exists_logic(app_state.function_cache, name)
