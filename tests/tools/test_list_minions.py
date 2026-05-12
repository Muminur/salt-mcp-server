"""Tests for list_minions tool logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from salt_cisco_mcp.tools.list_minions import list_minions_logic


def _make_adapter(minions: list[str] | None = None) -> MagicMock:
    adapter = MagicMock()
    adapter.key_list.return_value = {
        "minions": ["router1.example.com", "router2.example.com"] if minions is None else minions,
        "minions_pre": [],
        "minions_rejected": [],
    }
    return adapter


def test_list_minions_returns_dict() -> None:
    result = list_minions_logic(_make_adapter())
    assert isinstance(result, dict)


def test_list_minions_has_minions_key() -> None:
    result = list_minions_logic(_make_adapter())
    assert "minions" in result


def test_list_minions_has_total_key() -> None:
    result = list_minions_logic(_make_adapter())
    assert "total" in result


def test_list_minions_total_matches_count() -> None:
    result = list_minions_logic(_make_adapter(["r1", "r2", "r3"]))
    assert result["total"] == 3


def test_list_minions_returns_all_by_default() -> None:
    minions = ["r1.ex.com", "r2.ex.com"]
    result = list_minions_logic(_make_adapter(minions))
    assert result["minions"] == minions


def test_list_minions_filter_by_prefix() -> None:
    minions = ["router1.ex.com", "router2.ex.com", "switch1.ex.com"]
    result = list_minions_logic(_make_adapter(minions), filter="router")
    assert all("router" in m for m in result["minions"])
    assert "switch1.ex.com" not in result["minions"]


def test_list_minions_filter_no_match_returns_empty() -> None:
    result = list_minions_logic(_make_adapter(["r1.ex.com"]), filter="zzz")
    assert result["minions"] == []
    assert result["total"] == 0


def test_list_minions_has_pending_and_rejected() -> None:
    adapter = MagicMock()
    adapter.key_list.return_value = {
        "minions": ["r1"],
        "minions_pre": ["pending"],
        "minions_rejected": ["rejected"],
    }
    result = list_minions_logic(adapter)
    assert "pending" in result
    assert "rejected" in result


def test_list_minions_empty_returns_empty_list() -> None:
    result = list_minions_logic(_make_adapter([]))
    assert result["minions"] == []
    assert result["total"] == 0
