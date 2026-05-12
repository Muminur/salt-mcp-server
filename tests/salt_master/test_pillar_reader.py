"""Tests for pillar_reader — load + redact pillar."""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.pillar_reader import read_pillar
from salt_cisco_mcp.salt_master.redactor import REDACTED

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, timeout=10)


def test_read_pillar_returns_dict() -> None:
    result = read_pillar(_adapter())
    assert isinstance(result, dict)


def test_read_pillar_redacts_password() -> None:
    result = read_pillar(_adapter())
    assert result["proxy"]["password"] == REDACTED


def test_read_pillar_redacts_enable_password() -> None:
    result = read_pillar(_adapter())
    assert result["proxy"]["enable_password"] == REDACTED


def test_read_pillar_redacts_community() -> None:
    result = read_pillar(_adapter())
    assert result["snmp"]["community"] == REDACTED


def test_read_pillar_redacts_token() -> None:
    result = read_pillar(_adapter())
    assert result["snmp"]["token"] == REDACTED


def test_read_pillar_preserves_safe_fields() -> None:
    result = read_pillar(_adapter())
    assert result["proxy"]["host"] == "192.168.1.1"
    assert result["proxy"]["username"] == "admin"
    assert result["proxy"]["driver"] == "ios"
    assert result["description"] == "edge router"


def test_read_pillar_with_extra_redact_keys() -> None:
    result = read_pillar(_adapter(), extra_redact_keys={"description"})
    assert result["description"] == REDACTED


def test_read_pillar_no_plain_secrets_in_result() -> None:
    result = read_pillar(_adapter())
    result_str = str(result)
    assert "TOP_SECRET_PASSWORD" not in result_str
    assert "ENABLE_SECRET" not in result_str
    assert "public_community_string" not in result_str
    assert "auth_token_12345" not in result_str
