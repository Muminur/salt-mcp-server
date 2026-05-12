"""Tests for confirm_function_exists tool — anti-hallucination gate."""

from __future__ import annotations

from unittest.mock import MagicMock

from salt_cisco_mcp.tools.confirm_function_exists import confirm_function_exists_logic

_FUNCTIONS = ["ntp.set_servers", "grains.get", "test.ping", "state.apply"]


def _make_cache(functions: list[str] | None = None) -> MagicMock:
    cache = MagicMock()
    fns = set(functions or _FUNCTIONS)
    cache.confirm_function_exists.side_effect = lambda name: name in fns
    cache.list_functions.return_value = list(fns)
    return cache


def test_confirm_function_exists_returns_dict() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.set_servers")
    assert isinstance(result, dict)


def test_confirm_function_exists_true() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.set_servers")
    assert result["exists"] is True


def test_confirm_function_exists_false() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.configure_server")
    assert result["exists"] is False


def test_confirm_function_exists_has_name_field() -> None:
    result = confirm_function_exists_logic(_make_cache(), "test.ping")
    assert result["name"] == "test.ping"


def test_confirm_function_exists_has_suggestion_on_miss() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.set_server")
    # When function doesn't exist, suggestions should be provided
    assert "suggestions" in result


def test_confirm_function_exists_suggestions_are_list() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.set_server")
    assert isinstance(result["suggestions"], list)


def test_confirm_function_exists_no_suggestions_on_hit() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.set_servers")
    # Suggestions empty or absent when function exists
    assert result.get("suggestions", []) == []


def test_confirm_function_exists_suggestions_contain_similar() -> None:
    result = confirm_function_exists_logic(_make_cache(), "ntp.set_server")
    # "ntp.set_servers" should appear in suggestions since it's close
    suggestions = result.get("suggestions", [])
    assert any("ntp" in s for s in suggestions)
