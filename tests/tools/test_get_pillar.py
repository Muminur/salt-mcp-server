"""Tests for get_pillar tool logic — always redacted."""

from __future__ import annotations

from unittest.mock import MagicMock

from salt_cisco_mcp.salt_master.redactor import REDACTED
from salt_cisco_mcp.tools.get_pillar import get_pillar_logic

_PILLAR = {
    "proxy": {"host": "1.2.3.4", "password": "SECRET", "username": "admin"},
    "snmp": {"community": "public"},
}


def _make_adapter(pillar: dict | None = None) -> MagicMock:
    adapter = MagicMock()
    adapter.call.return_value = {"local": pillar or _PILLAR}
    return adapter


def test_get_pillar_returns_dict() -> None:
    result = get_pillar_logic(_make_adapter())
    assert isinstance(result, dict)


def test_get_pillar_has_pillar_key() -> None:
    result = get_pillar_logic(_make_adapter())
    assert "pillar" in result


def test_get_pillar_redacts_password() -> None:
    result = get_pillar_logic(_make_adapter())
    assert result["pillar"]["proxy"]["password"] == REDACTED


def test_get_pillar_redacts_community() -> None:
    result = get_pillar_logic(_make_adapter())
    assert result["pillar"]["snmp"]["community"] == REDACTED


def test_get_pillar_preserves_safe_fields() -> None:
    result = get_pillar_logic(_make_adapter())
    assert result["pillar"]["proxy"]["host"] == "1.2.3.4"
    assert result["pillar"]["proxy"]["username"] == "admin"


def test_get_pillar_always_redacted_cannot_be_disabled() -> None:
    """Even with no extra_redact_keys, secrets must still be redacted."""
    result = get_pillar_logic(_make_adapter())
    assert "SECRET" not in str(result)
    assert "public" not in str(result)


def test_get_pillar_has_redacted_flag() -> None:
    result = get_pillar_logic(_make_adapter())
    assert result.get("redacted") is True


def test_get_pillar_has_minion_id_in_result() -> None:
    result = get_pillar_logic(_make_adapter(), minion_id="router1")
    assert result.get("minion_id") == "router1"


def test_get_pillar_calls_pillar_items() -> None:
    adapter = _make_adapter()
    get_pillar_logic(adapter)
    adapter.call.assert_called_once_with("pillar.items")
