"""Unit tests for SaltCallAdapter."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from salt_cisco_mcp.salt_master.adapter import (
    AdapterError,
    ParseError,
    SaltCallAdapter,
    SaltCallTimeoutError,
)

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


# --- basic call ---


def test_call_returns_dict() -> None:
    result = _adapter().call("grains.items")
    assert isinstance(result, dict)


def test_call_grains_items_has_local_key() -> None:
    result = _adapter().call("grains.items")
    assert "local" in result


def test_call_grains_items_has_expected_grains() -> None:
    result = _adapter().call("grains.items")
    grains = result["local"]
    assert "saltversion" in grains
    assert grains["saltversion"].startswith("3007")


def test_call_pillar_items_returns_dict() -> None:
    result = _adapter().call("pillar.items")
    assert isinstance(result["local"], dict)


def test_call_sys_list_functions_returns_list() -> None:
    result = _adapter().call("sys.list_functions")
    assert isinstance(result["local"], list)
    assert len(result["local"]) > 0


def test_call_sys_list_functions_contains_known_fn() -> None:
    result = _adapter().call("sys.list_functions")
    assert "test.ping" in result["local"]


def test_call_with_args() -> None:
    result = _adapter().call("grains.get", "saltversion")
    assert result["local"] == "3007.0"


def test_call_test_ping_returns_true() -> None:
    result = _adapter().call("test.ping")
    assert result["local"] is True


# --- key_list ---


def test_key_list_returns_dict() -> None:
    result = _adapter().key_list()
    assert isinstance(result, dict)


def test_key_list_has_minions_key() -> None:
    result = _adapter().key_list()
    assert "minions" in result


def test_key_list_minions_is_list() -> None:
    result = _adapter().key_list()
    assert isinstance(result["minions"], list)


def test_key_list_contains_expected_minions() -> None:
    result = _adapter().key_list()
    assert "router1.example.com" in result["minions"]


def test_key_list_has_pre_and_rejected() -> None:
    result = _adapter().key_list()
    assert "minions_pre" in result
    assert "minions_rejected" in result


# --- error handling ---


def test_call_nonzero_exit_raises_adapter_error() -> None:
    adapter = SaltCallAdapter(salt_call_cmd=_STUB_CMD, timeout=10)
    with pytest.raises(AdapterError):
        adapter.call("error.unknown_fn")


def test_call_timeout_raises_timeout_error() -> None:
    adapter = SaltCallAdapter(salt_call_cmd=_STUB_CMD, timeout=1)
    with pytest.raises(SaltCallTimeoutError):
        adapter.call("--timeout-test")


def test_parse_error_on_bad_output() -> None:
    import subprocess

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="NOT JSON OR YAML: {{{{", stderr=""
        )
        adapter = SaltCallAdapter(timeout=10)
        with pytest.raises(ParseError):
            adapter.call("grains.items")


# --- fallback to YAML parsing ---


def test_parses_yaml_fallback() -> None:
    import subprocess

    yaml_output = "local:\n  id: myminion\n  os: Linux\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=yaml_output, stderr=""
        )
        adapter = SaltCallAdapter(timeout=10)
        result = adapter.call("grains.items")
        assert result["local"]["id"] == "myminion"


# --- security: list form only (no shell=True) ---


def test_subprocess_never_uses_shell() -> None:
    import subprocess

    calls: list[dict] = []  # type: ignore[type-arg]

    original_run = subprocess.run

    def spy_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return original_run(*args, **kwargs)

    with patch("subprocess.run", side_effect=spy_run):
        _adapter().call("test.ping")

    assert all(not c.get("shell", False) for c in calls), "shell=True must never be used"
