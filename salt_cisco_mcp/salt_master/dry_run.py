"""Dry-run helpers: state.show_sls and state.sls test=True."""

from __future__ import annotations

from typing import Any

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter


def show_sls(adapter: SaltCallAdapter, sls: str) -> dict[str, Any]:
    """Return compiled state dict for *sls* without executing it."""
    result = adapter.call("state.show_sls", sls)
    states: dict[str, Any] = result.get("local") or {}
    return {"sls": sls, "states": states, "count": len(states)}


def run_test_mode(adapter: SaltCallAdapter, sls: str) -> dict[str, Any]:
    """Run *sls* in test mode and return predicted changes + success flag."""
    result = adapter.call("state.sls", sls, "test=True")
    changes: dict[str, Any] = result.get("local") or {}
    success = all(
        v.get("result", False)
        for v in changes.values()
        if isinstance(v, dict)
    )
    return {"sls": sls, "changes": changes, "success": success, "count": len(changes)}
