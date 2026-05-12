"""MCP tool: get_grains — retrieve Salt grains."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def get_grains_logic(
    adapter: SaltCallAdapter,
    minion_id: str | None = None,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    """Return grains dict from salt-call, optionally filtered by key names."""
    raw = adapter.call("grains.items")
    grains: dict[str, Any] = dict(raw.get("local") or {})
    if keys:
        grains = {k: v for k, v in grains.items() if k in keys}
    result: dict[str, Any] = {"grains": grains}
    if minion_id is not None:
        result["minion_id"] = minion_id
    else:
        result["minion_id"] = grains.get("id", "local")
    return result


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the get_grains tool on *mcp*."""

    @mcp.tool()
    async def get_grains(
        minion_id: str | None = None,
        keys: list[str] | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Retrieve Salt grains for a minion (defaults to master's own grains)."""
        app_state = ctx.request_context.lifespan_context
        if app_state.adapter is None:
            return {"error": "salt-call not available", "grains": {}}
        return get_grains_logic(app_state.adapter, minion_id=minion_id, keys=keys)
