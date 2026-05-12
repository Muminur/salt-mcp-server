"""MCP tool: list_minions — enumerate Salt minions from salt-key."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def list_minions_logic(
    adapter: SaltCallAdapter,
    filter: str | None = None,
) -> dict[str, Any]:
    """Return minion IDs from salt-key, optionally filtered."""
    raw = adapter.key_list()
    all_minions: list[str] = list(raw.get("minions") or [])
    if filter:
        all_minions = [m for m in all_minions if filter in m]
    return {
        "minions": all_minions,
        "total": len(all_minions),
        "pending": list(raw.get("minions_pre") or []),
        "rejected": list(raw.get("minions_rejected") or []),
    }


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the list_minions tool on *mcp*."""

    @mcp.tool()
    async def list_minions(
        filter: str | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """List Salt minion IDs from salt-key, with optional substring filter."""
        app_state = ctx.request_context.lifespan_context
        if app_state.adapter is None:
            return {
                "error": "salt-call not available",
                "minions": [],
                "total": 0,
                "pending": [],
                "rejected": [],
            }
        return list_minions_logic(app_state.adapter, filter=filter)
