"""MCP prompt: debug_failing_state — diagnostic walkthrough for failing Salt states."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def debug_failing_state_logic(error: str, sls: str) -> str:
    """Return a diagnostic prompt for debugging a failing Salt state."""
    return (
        f"Diagnose failing Salt state.\nSLS: {sls}\nError: {error}\n\n"
        "Steps: get_pillar → search_docs(error) → confirm_function_exists → validate_state → state_test → get_grains\n\n"
        "Common causes: missing proxy: pillar, wrong NAPALM driver, connectivity, function hallucination, old syntax.\n\n"
        "Output: root cause + fix (SLS/pillar snippet) + citation {{module, function, anchor_url}}\n"
    )


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the debug_failing_state prompt on *mcp*."""

    @mcp.prompt(
        name="debug_failing_state",
        description="Diagnostic walkthrough for a failing Salt state on a Cisco device",
    )
    def debug_failing_state(error: str, sls: str) -> str:
        """Debug a failing Salt state with structured diagnostic steps."""
        return debug_failing_state_logic(error=error, sls=sls)
