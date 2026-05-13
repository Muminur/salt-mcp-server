"""MCP prompt: generate_proxy_pillar — proxy pillar bootstrap guidance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def generate_proxy_pillar_logic(proxytype: str, host: str) -> str:
    """Return a guidance prompt for generating a Salt proxy pillar."""
    return (
        f"Generate proxy pillar for {proxytype} minion at {host}.\n\n"
        f"Steps: generate_pillar(proxytype='{proxytype}', host='{host}', username='<username>') "
        f"→ validate_pillar → place at pillar/<minion_id>/init.sls\n\n"
        f"{proxytype} notes: {_proxytype_notes(proxytype)}\n\n"
        "Security: never commit passwords — use gpg renderer or Vault. "
        "Verify: salt-proxy --proxyid=<id> -l debug\n"
    )


def _proxytype_notes(proxytype: str) -> str:
    notes = {
        "napalm": (
            "- Requires `driver` field: ios, iosxr, nxos, nxos_ssh, eos, junos\n"
            "- `optional_args` can carry `port`, `secret`, `transport`\n"
            "- Verify with: `salt <id> net.facts`"
        ),
        "nxos": (
            "- NX-OS XML API proxy; default port 22\n"
            "- Verify with: `salt <id> nxos.show_run`"
        ),
        "nxos_api": (
            "- NX-OS NX-API (REST) proxy; default port 80/443\n"
            "- Verify with: `salt <id> nxos.show_run`"
        ),
        "cisconso": (
            "- Cisco NSO proxy; REST transport\n"
            "- Verify with: `salt <id> cisconso.get_data`"
        ),
    }
    return notes.get(
        proxytype.lower(),
        f"- Refer to Salt docs for `{proxytype}` proxy configuration",
    )


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the generate_proxy_pillar prompt on *mcp*."""

    @mcp.prompt(
        name="generate_proxy_pillar",
        description="Bootstrap a Salt proxy pillar for Cisco/NAPALM proxy minions",
    )
    def generate_proxy_pillar(proxytype: str, host: str) -> str:
        """Generate a Salt proxy pillar template with security guidance."""
        return generate_proxy_pillar_logic(proxytype=proxytype, host=host)
