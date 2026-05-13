"""MCP prompt: migrate_legacy_syntax — migrate pre-3000 Salt SLS to 3007 syntax."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def migrate_legacy_syntax_logic(sls_content: str) -> str:
    """Return a migration prompt for converting legacy SLS to Salt 3007 syntax."""
    return (
        f"Migrate to Salt 3007 syntax:\n```yaml\n{sls_content}\n```\n\n"
        "Key changes: cmd.run→module functions, pkgrepo humanname→name, "
        "service.running(enable=True), require_in→require, file.managed source: list, "
        "netacl→salt.states.netacl API.\n\n"
        "After: validate_state → confirm_function_exists → search_docs\n\n"
        "Output: migrated ```yaml + change summary + citations\n"
    )


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the migrate_legacy_syntax prompt on *mcp*."""

    @mcp.prompt(
        name="migrate_legacy_syntax",
        description="Migrate pre-Salt-3000 SLS syntax to Salt 3007 compatible format",
    )
    def migrate_legacy_syntax(sls_content: str) -> str:
        """Migrate a legacy Salt SLS file to Salt 3007 syntax."""
        return migrate_legacy_syntax_logic(sls_content=sls_content)
