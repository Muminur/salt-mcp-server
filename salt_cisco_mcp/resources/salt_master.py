"""MCP resources for salt-master:// URI scheme."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.pillar_reader import read_pillar

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def minions_logic(adapter: SaltCallAdapter) -> list[dict[str, Any]]:
    """Return list of minion dicts from salt-key."""
    raw = adapter.key_list()
    return [{"id": m} for m in (raw.get("minions") or [])]


def grains_logic(adapter: SaltCallAdapter, minion_id: str) -> dict[str, Any]:
    """Return grains for *minion_id* (currently master-local grains)."""
    raw = adapter.call("grains.items")
    grains: dict[str, Any] = dict(raw.get("local") or {})
    return {"minion_id": minion_id, "grains": grains}


def pillar_logic(adapter: SaltCallAdapter, minion_id: str) -> dict[str, Any]:
    """Return always-redacted pillar for *minion_id*."""
    pillar = read_pillar(adapter)
    return {"minion_id": minion_id, "pillar": pillar, "redacted": True}


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register salt-master:// resources on *mcp*."""

    @mcp.resource("salt-master://minions")
    async def resource_minions(
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> str:
        import json

        app_state = ctx.request_context.lifespan_context
        if app_state.adapter is None:
            return json.dumps([])
        return json.dumps(minions_logic(app_state.adapter))

    @mcp.resource("salt-master://grains/{minion_id}")
    async def resource_grains(
        minion_id: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> str:
        import json

        app_state = ctx.request_context.lifespan_context
        if app_state.adapter is None:
            return json.dumps({"minion_id": minion_id, "grains": {}})
        return json.dumps(grains_logic(app_state.adapter, minion_id))

    @mcp.resource("salt-master://pillar/{minion_id}")
    async def resource_pillar(
        minion_id: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> str:
        import json

        app_state = ctx.request_context.lifespan_context
        if app_state.adapter is None:
            return json.dumps({"minion_id": minion_id, "pillar": {}, "redacted": True})
        return json.dumps(pillar_logic(app_state.adapter, minion_id))
