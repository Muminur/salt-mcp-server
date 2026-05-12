"""MCP prompt: draft_state_for_cisco — guided SLS authoring for Cisco devices."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def draft_state_for_cisco_logic(task: str, vendor: str) -> str:
    """Return a guidance prompt for drafting a Cisco SLS state."""
    vendor_note = {
        "ios": "IOS/IOS-XR (use `napalm` proxy driver)",
        "iosxr": "IOS-XR (use `napalm` proxy driver with driver=iosxr)",
        "nxos": "NX-OS (use `nxos` or `napalm` proxy driver with driver=nxos)",
    }.get(vendor.lower(), f"{vendor} (verify proxy driver before applying)")

    return (
        f"You are a Salt 3007 expert. Draft a Salt SLS state to accomplish the following task "
        f"on a Cisco {vendor_note} device:\n\n"
        f"Task: {task}\n\n"
        "Guidelines:\n"
        "1. Always call `search_docs` first to find the correct Salt module and function.\n"
        "2. Call `confirm_function_exists` to verify the function name before using it.\n"
        "3. Use `validate_state` to lint the SLS before presenting it.\n"
        "4. Use `state_test` to dry-run the state and confirm expected changes.\n"
        "5. Every state ID should be descriptive and unique.\n"
        "6. Include the Salt docs citation: module, function, anchor_url, doc_hash.\n"
        f"7. Target vendor: {vendor_note}.\n\n"
        "Output format:\n"
        "- SLS content in a fenced ```yaml block\n"
        "- Citation block: {module, function, anchor_url}\n"
        "- Brief explanation of what each state block does\n"
    )


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the draft_state_for_cisco prompt on *mcp*."""

    @mcp.prompt(
        name="draft_state_for_cisco",
        description="Guided SLS authoring for Cisco IOS/IOS-XR/NX-OS devices",
    )
    def draft_state_for_cisco(task: str, vendor: str = "ios") -> str:
        """Draft a Salt SLS state for a Cisco network device task."""
        return draft_state_for_cisco_logic(task=task, vendor=vendor)
