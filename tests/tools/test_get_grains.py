"""Tests for get_grains tool logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from salt_cisco_mcp.tools.get_grains import get_grains_logic

_GRAINS = {
    "id": "salt-master",
    "os": "Ubuntu",
    "saltversion": "3007.0",
    "kernel": "Linux",
}


def _make_adapter(grains: dict | None = None) -> MagicMock:
    adapter = MagicMock()
    adapter.call.return_value = {"local": grains or _GRAINS}
    return adapter


def test_get_grains_returns_dict() -> None:
    result = get_grains_logic(_make_adapter())
    assert isinstance(result, dict)


def test_get_grains_has_grains_key() -> None:
    result = get_grains_logic(_make_adapter())
    assert "grains" in result


def test_get_grains_returns_all_grains_by_default() -> None:
    result = get_grains_logic(_make_adapter())
    assert result["grains"] == _GRAINS


def test_get_grains_filter_by_keys() -> None:
    result = get_grains_logic(_make_adapter(), keys=["os", "saltversion"])
    assert set(result["grains"].keys()) <= {"os", "saltversion"}


def test_get_grains_filter_missing_key_is_absent() -> None:
    result = get_grains_logic(_make_adapter(), keys=["nonexistent_grain"])
    assert "nonexistent_grain" not in result["grains"]


def test_get_grains_has_minion_id_in_result() -> None:
    result = get_grains_logic(_make_adapter(), minion_id="router1")
    assert result.get("minion_id") == "router1"


def test_get_grains_no_minion_id_defaults_to_local() -> None:
    result = get_grains_logic(_make_adapter())
    assert result.get("minion_id") in (None, "local", "salt-master")


def test_get_grains_calls_adapter_with_grains_items() -> None:
    adapter = _make_adapter()
    get_grains_logic(adapter)
    adapter.call.assert_called_once_with("grains.items")
