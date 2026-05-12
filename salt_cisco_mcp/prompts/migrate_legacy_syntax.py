"""MCP prompt: migrate_legacy_syntax — migrate pre-3000 Salt SLS to 3007 syntax."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def migrate_legacy_syntax_logic(sls_content: str) -> str:
    """Return a migration prompt for converting legacy SLS to Salt 3007 syntax."""
    return (
        "You are a Salt 3007 migration expert. Migrate the following Salt SLS from "
        "legacy syntax (pre-3000) to Salt 3007 compatible syntax.\n\n"
        "Legacy SLS to migrate:\n"
        f"```yaml\n{sls_content}\n```\n\n"
        "Migration guidelines for Salt 3007:\n"
        "1. Replace `cmd.run` with explicit module functions where possible.\n"
        "2. Replace deprecated `pkgrepo.managed` `humanname` with `name`.\n"
        "3. Replace `service.running`/`service.dead` with `service.running(enable=True)`.\n"
        "4. Remove `- require_in:` in favour of `- require:` on the dependent state.\n"
        "5. Replace `file.managed source: salt://` with explicit `source:` list syntax.\n"
        "6. For NAPALM/Cisco states: verify all proxy module functions against Salt 3007 docs.\n"
        "7. Replace `netacl` module calls with current `salt.states.netacl` API.\n\n"
        "After migrating:\n"
        "- Call `validate_state` on the migrated SLS.\n"
        "- Call `confirm_function_exists` for every function name used.\n"
        "- Call `search_docs` to verify any changed syntax against Salt 3007 docs.\n\n"
        "Output format:\n"
        "- Migrated SLS in a fenced ```yaml block\n"
        "- Summary of changes made (bulleted list)\n"
        "- Salt 3007 docs citations for changed syntax\n"
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
