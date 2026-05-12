"""MCP tool: state_show_sls — show compiled state without executing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.dry_run import show_sls

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def state_show_sls_logic(adapter: SaltCallAdapter | None, sls: str) -> dict[str, Any]:
    """Return compiled state for *sls*, or error dict if adapter unavailable."""
    if adapter is None:
        return {"error": "salt-call not available", "sls": sls}
    return show_sls(adapter, sls)


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the state_show_sls tool on *mcp*."""

    @mcp.tool()
    async def state_show_sls(
        sls: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Show the compiled Salt state for an SLS file without executing it."""
        app_state = ctx.request_context.lifespan_context
        return state_show_sls_logic(app_state.adapter, sls)
