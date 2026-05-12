"""MCP tool: validate_pillar — validate proxy pillar YAML against schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml
from mcp.server.fastmcp import Context

from salt_cisco_mcp.validate.pillar_schema import validate_pillar_dict

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def validate_pillar_logic(pillar_yaml: str) -> dict[str, Any]:
    """Validate proxy pillar YAML and return structured pass/fail with doc URLs."""
    try:
        pillar = yaml.safe_load(pillar_yaml)
    except yaml.YAMLError as exc:
        return {
            "valid": False,
            "errors": [{"message": f"YAML parse error: {exc}", "anchor_url": ""}],
        }

    if not isinstance(pillar, dict):
        return {
            "valid": False,
            "errors": [{"message": "Pillar must be a YAML mapping", "anchor_url": ""}],
        }

    result = validate_pillar_dict(pillar)
    return {"valid": result.valid, "errors": result.errors}


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the validate_pillar tool on *mcp*."""

    @mcp.tool()
    async def validate_pillar(
        yaml: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Validate Salt proxy pillar YAML. Returns pass/fail with anchored doc URLs."""
        return validate_pillar_logic(yaml)
