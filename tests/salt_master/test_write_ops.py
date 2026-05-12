"""Tests for write_ops module: apply_state and push_config."""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


# --- apply_state ---


def test_apply_state_returns_dict() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert isinstance(result, dict)


def test_apply_state_has_sls_key() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert result["sls"] == "cisco.acl.edge"


def test_apply_state_has_target_key() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert result["target"] == "router1"


def test_apply_state_has_success_key() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert "success" in result
    assert isinstance(result["success"], bool)


def test_apply_state_success_true_for_stub() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert result["success"] is True


def test_apply_state_has_changes_key() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert "changes" in result
    assert isinstance(result["changes"], dict)


def test_apply_state_count_matches_changes() -> None:
    from salt_cisco_mcp.salt_master.write_ops import apply_state

    result = apply_state(_adapter(), target="router1", sls="cisco.acl.edge")
    assert result["count"] == len(result["changes"])


# --- push_config ---


def test_push_config_merge_returns_dict() -> None:
    from salt_cisco_mcp.salt_master.write_ops import push_config

    result = push_config(
        _adapter(), target="router1", config_text="hostname router1\n", mode="merge"
    )
    assert isinstance(result, dict)


def test_push_config_replace_returns_dict() -> None:
    from salt_cisco_mcp.salt_master.write_ops import push_config

    result = push_config(
        _adapter(), target="router1", config_text="hostname router1\n", mode="replace"
    )
    assert isinstance(result, dict)


def test_push_config_has_target_key() -> None:
    from salt_cisco_mcp.salt_master.write_ops import push_config

    result = push_config(_adapter(), target="router1", config_text="hostname router1\n")
    assert result["target"] == "router1"


def test_push_config_has_mode_key() -> None:
    from salt_cisco_mcp.salt_master.write_ops import push_config

    result = push_config(
        _adapter(), target="router1", config_text="hostname router1\n", mode="replace"
    )
    assert result["mode"] == "replace"


def test_push_config_default_mode_is_merge() -> None:
    from salt_cisco_mcp.salt_master.write_ops import push_config

    result = push_config(_adapter(), target="router1", config_text="hostname router1\n")
    assert result["mode"] == "merge"


def test_push_config_result_success_true_for_stub() -> None:
    from salt_cisco_mcp.salt_master.write_ops import push_config

    result = push_config(
        _adapter(), target="router1", config_text="hostname router1\n", mode="merge"
    )
    assert result["result"]["result"] is True
