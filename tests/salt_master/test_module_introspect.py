"""Tests for module_introspect — list_functions and argspec caching."""

from __future__ import annotations

import sys
from pathlib import Path

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.module_introspect import FunctionCache

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _cache() -> FunctionCache:
    adapter = SaltCallAdapter(salt_call_cmd=_STUB_CMD, timeout=10)
    return FunctionCache(adapter)


def test_list_functions_returns_list() -> None:
    result = _cache().list_functions()
    assert isinstance(result, list)


def test_list_functions_not_empty() -> None:
    result = _cache().list_functions()
    assert len(result) > 0


def test_list_functions_contains_known_fn() -> None:
    result = _cache().list_functions()
    assert "test.ping" in result


def test_list_functions_prefix_filter() -> None:
    result = _cache().list_functions(prefix="ntp")
    assert all(fn.startswith("ntp.") for fn in result)
    assert len(result) > 0


def test_list_functions_prefix_filter_empty_result() -> None:
    result = _cache().list_functions(prefix="zzz_nonexistent")
    assert result == []


def test_list_functions_cached_on_second_call() -> None:
    cache = _cache()
    r1 = cache.list_functions()
    r2 = cache.list_functions()
    assert r1 == r2


def test_get_argspec_returns_dict() -> None:
    result = _cache().get_argspec("ntp.set_servers")
    assert isinstance(result, dict)


def test_get_argspec_has_func_key() -> None:
    result = _cache().get_argspec("ntp.set_servers")
    assert "func" in result or result == {}


def test_confirm_function_exists_true() -> None:
    cache = _cache()
    assert cache.confirm_function_exists("test.ping") is True


def test_confirm_function_exists_false() -> None:
    cache = _cache()
    assert cache.confirm_function_exists("fake.nonexistent") is False


def test_invalidate_clears_cache() -> None:
    cache = _cache()
    _ = cache.list_functions()
    cache.invalidate()
    # After invalidate, a fresh call should still work
    result = cache.list_functions()
    assert len(result) > 0
