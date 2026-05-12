"""Tests for dry_run module."""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


def test_show_sls_returns_dict() -> None:
    from salt_cisco_mcp.salt_master.dry_run import show_sls

    result = show_sls(_adapter(), "cisco.acl.edge")
    assert isinstance(result, dict)


def test_show_sls_has_sls_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import show_sls

    result = show_sls(_adapter(), "cisco.acl.edge")
    assert result["sls"] == "cisco.acl.edge"


def test_show_sls_has_states_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import show_sls

    result = show_sls(_adapter(), "cisco.acl.edge")
    assert "states" in result
    assert isinstance(result["states"], dict)


def test_show_sls_has_count_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import show_sls

    result = show_sls(_adapter(), "cisco.acl.edge")
    assert result["count"] == len(result["states"])


def test_show_sls_states_not_empty() -> None:
    from salt_cisco_mcp.salt_master.dry_run import show_sls

    result = show_sls(_adapter(), "cisco.acl.edge")
    assert result["count"] >= 1


def test_run_test_mode_returns_dict() -> None:
    from salt_cisco_mcp.salt_master.dry_run import run_test_mode

    result = run_test_mode(_adapter(), "cisco.acl.edge")
    assert isinstance(result, dict)


def test_run_test_mode_has_sls_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import run_test_mode

    result = run_test_mode(_adapter(), "cisco.acl.edge")
    assert result["sls"] == "cisco.acl.edge"


def test_run_test_mode_has_success_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import run_test_mode

    result = run_test_mode(_adapter(), "cisco.acl.edge")
    assert "success" in result
    assert isinstance(result["success"], bool)


def test_run_test_mode_has_changes_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import run_test_mode

    result = run_test_mode(_adapter(), "cisco.acl.edge")
    assert "changes" in result
    assert isinstance(result["changes"], dict)


def test_run_test_mode_success_true_for_stub() -> None:
    from salt_cisco_mcp.salt_master.dry_run import run_test_mode

    result = run_test_mode(_adapter(), "cisco.acl.edge")
    assert result["success"] is True


def test_run_test_mode_has_count_key() -> None:
    from salt_cisco_mcp.salt_master.dry_run import run_test_mode

    result = run_test_mode(_adapter(), "cisco.acl.edge")
    assert result["count"] == len(result["changes"])
