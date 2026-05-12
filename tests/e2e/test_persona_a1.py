"""E2E test: Persona A1 — Maya adds an ACL state for edge routers.

Flow (from PRD §4.1 use case A1):
  1. list_minions → get edge router IDs
  2. validate_state with a drafted ACL SLS → pass
  3. state_test dry-run → success=True, changes present
"""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.tools.list_minions import list_minions_logic
from salt_cisco_mcp.tools.state_test import state_test_logic
from salt_cisco_mcp.tools.validate_state import validate_state_logic

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]

_ACL_SLS = """\
deny-ssh-from-rfc1918:
  acl.managed:
    - name: deny-ssh-from-rfc1918
    - entries:
        - sequence: 10
          action: deny
          protocol: tcp
          source: 10.0.0.0/8
          destination: any
          destination_port: 22
"""


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


def test_a1_step1_list_minions() -> None:
    """Maya gets edge router minion IDs."""
    result = list_minions_logic(_adapter())
    assert isinstance(result["minions"], list)
    assert len(result["minions"]) >= 1


def test_a1_step2_validate_state_passes() -> None:
    """Drafted ACL SLS passes structural lint."""
    result = validate_state_logic(_ACL_SLS)
    assert result["valid"] is True
    assert isinstance(result["state_ids"], list)
    assert "deny-ssh-from-rfc1918" in result["state_ids"]


def test_a1_step3_dry_run_succeeds() -> None:
    """state.sls test=True predicts success."""
    result = state_test_logic(_adapter(), "cisco.acl.edge")
    assert result["success"] is True
    assert isinstance(result["changes"], dict)


def test_a1_full_flow_coherent() -> None:
    """All three steps produce consistent results."""
    adapter = _adapter()

    minions = list_minions_logic(adapter)
    assert len(minions["minions"]) >= 1

    lint = validate_state_logic(_ACL_SLS)
    assert lint["valid"] is True

    dry = state_test_logic(adapter, "cisco.acl.edge")
    assert dry["success"] is True
    assert dry["count"] >= 1
