"""MCP tool: state_apply — apply a Salt state (write path, gated by confirm_token)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.audit import append_audit, hash_str, verify_token
from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.write_ops import apply_state

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings

_TOKEN_NOT_SET = "write mode not configured — set SALT_MCP_SERVER__CONFIRM_TOKEN"
_TOKEN_MISMATCH = "confirm_token mismatch — apply rejected"


def state_apply_logic(
    adapter: SaltCallAdapter | None,
    sls: str,
    target: str,
    confirm_token: str,
    expected_token: str,
    audit_log_path: str,
    client_id: str = "",
) -> dict[str, Any]:
    """Apply *sls* to *target*, verifying *confirm_token* before executing."""
    if adapter is None:
        return {"error": "salt-call not available", "sls": sls}
    if not expected_token:
        return {"error": _TOKEN_NOT_SET, "sls": sls}
    if not verify_token(confirm_token, expected_token):
        return {"error": _TOKEN_MISMATCH, "sls": sls}
    result = apply_state(adapter, target=target, sls=sls)
    append_audit(
        audit_log_path,
        tool="state_apply",
        target=target,
        token_hash=hash_str(confirm_token),
        sls_hash=hash_str(sls),
        result=result.get("success"),
        client_id=client_id,
    )
    return result


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the state_apply tool on *mcp*."""

    @mcp.tool()
    async def state_apply(
        sls: str,
        target: str,
        confirm_token: str,
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Apply a Salt state SLS to target. Requires allow_write=true and a valid confirm_token."""
        app_state = ctx.request_context.lifespan_context
        return state_apply_logic(
            app_state.adapter,
            sls=sls,
            target=target,
            confirm_token=confirm_token,
            expected_token=settings.server.confirm_token,
            audit_log_path=settings.paths.audit_log,
            client_id=ctx.client_id or "",
        )
