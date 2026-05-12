"""MCP tool: audit_cisco_config — audit Cisco IOS/NX-OS config text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.validate.cisco_audit import audit_config

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def audit_cisco_config_logic(config: str, vendor: str) -> dict[str, Any]:
    """Audit Cisco config text and return structured findings."""
    result = audit_config(config, vendor)
    return result.to_dict()


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the audit_cisco_config tool on *mcp*."""

    @mcp.tool()
    async def audit_cisco_config(
        config: str,
        vendor: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Audit Cisco device config for security and compliance findings."""
        return audit_cisco_config_logic(config, vendor)
