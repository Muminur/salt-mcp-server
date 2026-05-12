"""Tests for state_show_sls and state_test tool logic functions."""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


# --- state_show_sls ---


def test_state_show_sls_logic_returns_dict() -> None:
    from salt_cisco_mcp.tools.state_show_sls import state_show_sls_logic

    result = state_show_sls_logic(_adapter(), "cisco.acl.edge")
    assert isinstance(result, dict)


def test_state_show_sls_logic_no_adapter_returns_error() -> None:
    from salt_cisco_mcp.tools.state_show_sls import state_show_sls_logic

    result = state_show_sls_logic(None, "cisco.acl.edge")
    assert "error" in result


def test_state_show_sls_logic_has_states() -> None:
    from salt_cisco_mcp.tools.state_show_sls import state_show_sls_logic

    result = state_show_sls_logic(_adapter(), "cisco.acl.edge")
    assert "states" in result


def test_state_show_sls_logic_has_count() -> None:
    from salt_cisco_mcp.tools.state_show_sls import state_show_sls_logic

    result = state_show_sls_logic(_adapter(), "cisco.acl.edge")
    assert "count" in result


def test_state_show_sls_logic_preserves_sls_name() -> None:
    from salt_cisco_mcp.tools.state_show_sls import state_show_sls_logic

    result = state_show_sls_logic(_adapter(), "cisco.acl.edge")
    assert result.get("sls") == "cisco.acl.edge"


# --- state_test ---


def test_state_test_logic_returns_dict() -> None:
    from salt_cisco_mcp.tools.state_test import state_test_logic

    result = state_test_logic(_adapter(), "cisco.acl.edge")
    assert isinstance(result, dict)


def test_state_test_logic_no_adapter_returns_error() -> None:
    from salt_cisco_mcp.tools.state_test import state_test_logic

    result = state_test_logic(None, "cisco.acl.edge")
    assert "error" in result


def test_state_test_logic_has_success() -> None:
    from salt_cisco_mcp.tools.state_test import state_test_logic

    result = state_test_logic(_adapter(), "cisco.acl.edge")
    assert "success" in result
    assert isinstance(result["success"], bool)


def test_state_test_logic_has_changes() -> None:
    from salt_cisco_mcp.tools.state_test import state_test_logic

    result = state_test_logic(_adapter(), "cisco.acl.edge")
    assert "changes" in result


def test_state_test_logic_preserves_sls_name() -> None:
    from salt_cisco_mcp.tools.state_test import state_test_logic

    result = state_test_logic(_adapter(), "cisco.acl.edge")
    assert result.get("sls") == "cisco.acl.edge"


def test_state_test_logic_success_true_for_good_run() -> None:
    from salt_cisco_mcp.tools.state_test import state_test_logic

    result = state_test_logic(_adapter(), "cisco.acl.edge")
    assert result["success"] is True
