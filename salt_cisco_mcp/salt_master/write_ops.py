"""Salt write operations: apply a state and push raw config."""

from __future__ import annotations

from typing import Any

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter


def apply_state(adapter: SaltCallAdapter, target: str, sls: str) -> dict[str, Any]:
    """Apply *sls* via ``salt-call state.sls`` and return a result summary."""
    raw = adapter.call("state.sls", sls)
    changes: dict[str, Any] = raw.get("local") or {}
    success = all(v.get("result", False) for v in changes.values() if isinstance(v, dict))
    return {
        "sls": sls,
        "target": target,
        "changes": changes,
        "success": success,
        "count": len(changes),
    }


def push_config(
    adapter: SaltCallAdapter,
    target: str,
    config_text: str,
    mode: str = "merge",
) -> dict[str, Any]:
    """Push *config_text* to *target* via NAPALM (merge or replace)."""
    func = "net.load_replace_candidate" if mode == "replace" else "net.load_config"
    raw = adapter.call(func, config_text)
    data: dict[str, Any] = raw.get("local") or {}
    return {"target": target, "mode": mode, "result": data}
