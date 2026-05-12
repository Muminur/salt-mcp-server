"""MCP tool: generate_pillar — produce known-good proxy pillar templates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml
from mcp.server.fastmcp import Context

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings

_TEMPLATES: dict[str, dict[str, Any]] = {
    "napalm": {
        "proxy": {
            "proxytype": "napalm",
            "driver": "{driver}",
            "host": "{host}",
            "username": "{username}",
            "password": "<<password>>",
            "optional_args": {},
        }
    },
    "nxos": {
        "proxy": {
            "proxytype": "nxos",
            "host": "{host}",
            "username": "{username}",
            "password": "<<password>>",
        }
    },
    "nxos_api": {
        "proxy": {
            "proxytype": "nxos_api",
            "host": "{host}",
            "username": "{username}",
            "password": "<<password>>",
        }
    },
    "cisconso": {
        "proxy": {
            "proxytype": "cisconso",
            "host": "{host}",
            "username": "{username}",
            "password": "<<password>>",
        }
    },
}


def generate_pillar_logic(
    proxytype: str,
    driver: str | None,
    host: str,
    username: str,
) -> dict[str, Any]:
    """Generate a known-good pillar template with <<password>> placeholder."""
    template = _TEMPLATES.get(proxytype)
    if template is None:
        return {
            "error": f"Unknown proxytype '{proxytype}'",
            "pillar": "",
            "proxytype": proxytype,
        }

    import copy

    filled = copy.deepcopy(template)
    proxy = filled["proxy"]

    proxy["host"] = host
    proxy["username"] = username
    if "{driver}" in str(proxy.get("driver", "")) and driver:
        proxy["driver"] = driver
    elif "{driver}" in str(proxy.get("driver", "")):
        proxy["driver"] = "ios"

    return {
        "pillar": yaml.dump(filled, default_flow_style=False),
        "proxytype": proxytype,
    }


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the generate_pillar tool on *mcp*."""

    @mcp.tool()
    async def generate_pillar(
        proxytype: str,
        host: str,
        username: str,
        driver: str | None = None,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Generate a known-good Salt proxy pillar template with <<password>> placeholder."""
        return generate_pillar_logic(
            proxytype=proxytype, driver=driver, host=host, username=username
        )
