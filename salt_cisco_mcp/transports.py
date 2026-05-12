"""Transport selection for salt-cisco-mcp: stdio or streamable-http."""

from __future__ import annotations

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.server import create_server


def run_server(settings: Settings) -> None:
    """Select and start the appropriate MCP transport.

    Blocks until the server shuts down.
    """
    mcp = create_server(settings)
    if settings.server.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")
