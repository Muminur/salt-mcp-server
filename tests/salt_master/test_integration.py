"""Integration tests: adapter against real fake-master fixture."""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.module_introspect import FunctionCache
from salt_cisco_mcp.salt_master.pillar_reader import read_pillar
from salt_cisco_mcp.salt_master.redactor import REDACTED

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


def test_full_pillar_redaction_end_to_end() -> None:
    result = read_pillar(_adapter())
    assert result["proxy"]["password"] == REDACTED
    assert result["proxy"]["enable_password"] == REDACTED
    assert result["snmp"]["community"] == REDACTED
    assert result["snmp"]["token"] == REDACTED
    assert result["proxy"]["host"] == "192.168.1.1"


def test_full_function_resolution_end_to_end() -> None:
    cache = FunctionCache(_adapter())
    assert cache.confirm_function_exists("ntp.set_servers") is True
    assert cache.confirm_function_exists("fake.hallucinated") is False


def test_full_grains_retrieval_end_to_end() -> None:
    adapter = _adapter()
    result = adapter.call("grains.items")
    grains = result["local"]
    assert grains["saltversion"].startswith("3007")
    assert grains["os"] == "Ubuntu"


def test_full_key_list_end_to_end() -> None:
    adapter = _adapter()
    result = adapter.key_list()
    assert "router1.example.com" in result["minions"]
    assert isinstance(result["minions_pre"], list)


def test_full_sys_list_functions_end_to_end() -> None:
    cache = FunctionCache(_adapter())
    fns = cache.list_functions()
    assert "test.ping" in fns
    assert "sys.list_functions" in fns


def test_full_prefix_filter_end_to_end() -> None:
    cache = FunctionCache(_adapter())
    ntp_fns = cache.list_functions(prefix="ntp")
    assert len(ntp_fns) >= 1
    assert all(f.startswith("ntp.") for f in ntp_fns)
