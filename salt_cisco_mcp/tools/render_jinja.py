"""MCP tool: render_jinja — sandboxed Jinja2 template rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.validate.jinja_preview import render_jinja_safe

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings


def render_jinja_logic(template: str, context: dict[str, Any]) -> dict[str, Any]:
    """Render a Jinja2 template in a sandboxed environment."""
    result = render_jinja_safe(template, context)
    return result.to_dict()


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the render_jinja tool on *mcp*."""

    @mcp.tool()
    async def render_jinja(
        template: str,
        context: dict[str, Any],
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Render a Jinja2 template safely. Returns output, warnings for unsafe constructs."""
        return render_jinja_logic(template, context)
