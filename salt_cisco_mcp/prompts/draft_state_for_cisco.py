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
        f"Draft a Salt 3007 SLS state for: {task}\n"
        f"Target: Cisco {vendor_note}\n\n"
        "Steps: search_docs → confirm_function_exists → validate_state → state_test\n\n"
        "Output: fenced ```yaml SLS + citation {{module, function, anchor_url, doc_hash}}\n"
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
