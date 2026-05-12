"""MCP tool: get_pillar — retrieve redacted Salt pillar."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.pillar_reader import read_pillar

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def get_pillar_logic(
    adapter: SaltCallAdapter,
    minion_id: str | None = None,
) -> dict[str, Any]:
    """Return always-redacted pillar from salt-call --local pillar.items."""
    pillar = read_pillar(adapter)
    result: dict[str, Any] = {
        "pillar": pillar,
        "redacted": True,
    }
    if minion_id is not None:
        result["minion_id"] = minion_id
    return result


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the get_pillar tool on *mcp*."""

    @mcp.tool()
    async def get_pillar(
        minion_id: str | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Return redacted pillar data. Sensitive fields are always masked."""
        app_state = ctx.request_context.lifespan_context
        if app_state.adapter is None:
            return {"error": "salt-call not available", "pillar": {}, "redacted": True}
        return get_pillar_logic(app_state.adapter, minion_id=minion_id)
