"""Tests for list_loaded_functions tool logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from salt_cisco_mcp.tools.list_loaded_functions import list_loaded_functions_logic

_FUNCTIONS = ["grains.get", "ntp.set_servers", "ntp.show_ntp_info", "pillar.get", "state.apply"]


def _make_cache(functions: list[str] | None = None) -> MagicMock:
    cache = MagicMock()
    cache.list_functions.return_value = functions or _FUNCTIONS
    return cache


def test_list_loaded_functions_returns_dict() -> None:
    result = list_loaded_functions_logic(_make_cache())
    assert isinstance(result, dict)


def test_list_loaded_functions_has_functions_key() -> None:
    result = list_loaded_functions_logic(_make_cache())
    assert "functions" in result


def test_list_loaded_functions_has_total_key() -> None:
    result = list_loaded_functions_logic(_make_cache())
    assert "total" in result


def test_list_loaded_functions_total_matches_count() -> None:
    result = list_loaded_functions_logic(_make_cache())
    assert result["total"] == len(result["functions"])


def test_list_loaded_functions_no_prefix_returns_all() -> None:
    result = list_loaded_functions_logic(_make_cache(_FUNCTIONS))
    assert set(result["functions"]) == set(_FUNCTIONS)


def test_list_loaded_functions_prefix_filters() -> None:
    cache = _make_cache()
    cache.list_functions.return_value = ["ntp.set_servers", "ntp.show_ntp_info"]
    result = list_loaded_functions_logic(cache, prefix="ntp")
    assert all(f.startswith("ntp.") for f in result["functions"])


def test_list_loaded_functions_prefix_calls_cache_with_prefix() -> None:
    cache = _make_cache()
    list_loaded_functions_logic(cache, prefix="ntp")
    cache.list_functions.assert_called_once_with(prefix="ntp")


def test_list_loaded_functions_no_prefix_calls_cache_without_prefix() -> None:
    cache = _make_cache()
    list_loaded_functions_logic(cache)
    cache.list_functions.assert_called_once_with(prefix=None)
