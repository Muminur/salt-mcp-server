"""MCP tool: state_test — run SLS in test mode and return predicted changes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.dry_run import run_test_mode

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def state_test_logic(
    adapter: SaltCallAdapter | None,
    sls: str,
    target: str | None = None,
) -> dict[str, Any]:
    """Run *sls* in test mode, or return error dict if adapter unavailable."""
    if adapter is None:
        return {"error": "salt-call not available", "sls": sls}
    result = run_test_mode(adapter, sls)
    if target:
        result["target"] = target
    return result


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the state_test tool on *mcp*."""

    @mcp.tool()
    async def state_test(
        sls: str,
        target: str | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Run a Salt state in test mode and return predicted changes without applying them."""
        app_state = ctx.request_context.lifespan_context
        return state_test_logic(app_state.adapter, sls, target)
