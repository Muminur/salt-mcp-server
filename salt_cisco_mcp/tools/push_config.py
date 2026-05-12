"""MCP tool: push_config — push raw config via NAPALM (write path, gated by confirm_token)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from salt_cisco_mcp.audit import append_audit, hash_str, verify_token
from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.write_ops import push_config as _push_config_op

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from salt_cisco_mcp.config import Settings

_TOKEN_NOT_SET = "write mode not configured — set SALT_MCP_SERVER__CONFIRM_TOKEN"
_TOKEN_MISMATCH = "confirm_token mismatch — push rejected"
_VALID_MODES = frozenset({"merge", "replace"})


def push_config_logic(
    adapter: SaltCallAdapter | None,
    config_text: str,
    target: str,
    mode: str,
    confirm_token: str,
    expected_token: str,
    audit_log_path: str,
    client_id: str = "",
) -> dict[str, Any]:
    """Push *config_text* to *target*, verifying *confirm_token* before executing."""
    if adapter is None:
        return {"error": "salt-call not available", "target": target}
    if not expected_token:
        return {"error": _TOKEN_NOT_SET, "target": target}
    if not verify_token(confirm_token, expected_token):
        return {"error": _TOKEN_MISMATCH, "target": target}
    if mode not in _VALID_MODES:
        return {"error": f"invalid mode {mode!r} — must be 'merge' or 'replace'", "target": target}
    result = _push_config_op(adapter, target=target, config_text=config_text, mode=mode)
    inner: Any = result.get("result") or {}
    append_audit(
        audit_log_path,
        tool="push_config",
        target=target,
        token_hash=hash_str(confirm_token),
        sls_hash=hash_str(config_text),
        result=inner.get("result") if isinstance(inner, dict) else None,
        client_id=client_id,
    )
    return result


def register(mcp: FastMCP[Any], settings: Settings) -> None:
    """Register the push_config tool on *mcp*."""

    @mcp.tool()
    async def push_config(
        config_text: str,
        target: str,
        mode: str = "merge",
        confirm_token: str = "",
        ctx: Context = ...,  # type: ignore[assignment,type-arg]
    ) -> dict[str, Any]:
        """Push raw config to a device via NAPALM (merge or replace).

        Requires allow_write=true and a valid confirm_token.
        """
        app_state = ctx.request_context.lifespan_context
        return push_config_logic(
            app_state.adapter,
            config_text=config_text,
            target=target,
            mode=mode,
            confirm_token=confirm_token,
            expected_token=settings.server.confirm_token,
            audit_log_path=settings.paths.audit_log,
            client_id=ctx.client_id or "",
        )
