"""MCP tool: validate_state — lint SLS state structure."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.validate.state_lint import lint_sls_text

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def validate_state_logic(sls: str) -> dict[str, Any]:
    """Lint SLS text and return structured pass/fail."""
    result = lint_sls_text(sls)
    return result.to_dict()


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the validate_state tool on *mcp*."""

    @mcp.tool()
    async def validate_state(
        sls: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Validate Salt SLS state structure. Returns pass/fail with errors."""
        return validate_state_logic(sls)
