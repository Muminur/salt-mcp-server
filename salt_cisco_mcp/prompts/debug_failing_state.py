"""MCP prompt: debug_failing_state — diagnostic walkthrough for failing Salt states."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def debug_failing_state_logic(error: str, sls: str) -> str:
    """Return a diagnostic prompt for debugging a failing Salt state."""
    return (
        f"You are a Salt 3007 expert. Help diagnose why the following Salt state is failing.\n\n"
        f"SLS: {sls}\n"
        f"Error: {error}\n\n"
        "Diagnostic steps:\n"
        "1. Call `get_pillar` to inspect the minion's pillar data — check for missing or "
        "   mismatched proxy credentials.\n"
        "2. Call `search_docs` with the error message to find relevant troubleshooting docs.\n"
        "3. Call `confirm_function_exists` for every function referenced in the failing state.\n"
        "4. Call `validate_state` on the SLS content to catch structural issues.\n"
        "5. Call `state_test` (dry-run) to see predicted changes without applying.\n"
        "6. Check grains with `get_grains` to verify the minion is the expected OS/version.\n\n"
        "Common causes for Cisco proxy state failures:\n"
        "- Missing or malformed `proxy:` pillar key (KeyError: 'proxytype')\n"
        "- Wrong NAPALM driver for the device OS\n"
        "- Network connectivity issue to the device\n"
        "- Salt function name hallucination (use `confirm_function_exists` to verify)\n"
        "- Syntax differences between Salt 2019 and Salt 3007\n\n"
        "Output format:\n"
        "- Root cause hypothesis (1-2 sentences)\n"
        "- Steps taken (tool calls and findings)\n"
        "- Recommended fix with corrected SLS or pillar snippet\n"
        "- Salt docs citation for the fix\n"
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
