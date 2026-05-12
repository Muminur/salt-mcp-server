"""Tests for salt-master:// MCP resources."""

from __future__ import annotations

from unittest.mock import MagicMock

from salt_cisco_mcp.resources.salt_master import (
    grains_logic,
    minions_logic,
    pillar_logic,
)
from salt_cisco_mcp.salt_master.redactor import REDACTED


def _make_adapter(minions=None, grains=None, pillar=None):  # type: ignore[no-untyped-def]
    adapter = MagicMock()
    adapter.key_list.return_value = {
        "minions": minions or ["router1.ex.com", "router2.ex.com"],
        "minions_pre": [],
        "minions_rejected": [],
    }
    adapter.call.side_effect = lambda func, *args: (
        {"local": grains or {"id": "salt-master", "os": "Linux"}}
        if func == "grains.items"
        else {"local": pillar or {"proxy": {"host": "1.1.1.1", "password": "SECRET"}}}
    )
    return adapter


def test_minions_logic_returns_list() -> None:
    result = minions_logic(_make_adapter())
    assert isinstance(result, list)


def test_minions_logic_contains_minion_dicts() -> None:
    result = minions_logic(_make_adapter())
    assert all(isinstance(m, dict) for m in result)


def test_minions_logic_has_id_field() -> None:
    result = minions_logic(_make_adapter())
    assert all("id" in m for m in result)


def test_minions_logic_includes_all_minions() -> None:
    result = minions_logic(_make_adapter(["r1", "r2", "r3"]))
    ids = [m["id"] for m in result]
    assert "r1" in ids and "r3" in ids


def test_grains_logic_returns_dict() -> None:
    result = grains_logic(_make_adapter(), "salt-master")
    assert isinstance(result, dict)


def test_grains_logic_has_grains() -> None:
    result = grains_logic(_make_adapter(), "salt-master")
    assert "grains" in result


def test_pillar_logic_returns_dict() -> None:
    result = pillar_logic(_make_adapter(), "router1")
    assert isinstance(result, dict)


def test_pillar_logic_has_pillar_key() -> None:
    result = pillar_logic(_make_adapter(), "router1")
    assert "pillar" in result


def test_pillar_logic_always_redacted() -> None:
    result = pillar_logic(_make_adapter(), "router1")
    assert result["pillar"]["proxy"]["password"] == REDACTED


def test_pillar_logic_has_redacted_flag() -> None:
    result = pillar_logic(_make_adapter(), "router1")
    assert result.get("redacted") is True
