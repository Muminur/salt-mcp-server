"""Security: subprocess calls use list argv, never shell strings."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter


def test_adapter_run_uses_shell_false() -> None:
    """_run() must always pass shell=False to subprocess.run."""
    source = inspect.getsource(SaltCallAdapter._run)
    assert "shell=False" in source


def test_adapter_call_builds_list_not_string() -> None:
    """adapter.call() must pass a list to subprocess, not a joined string."""
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> object:
        captured.append(cmd)
        m = MagicMock()
        m.returncode = 0
        m.stdout = '{"local": true}'
        return m

    with patch("salt_cisco_mcp.salt_master.adapter.subprocess.run", side_effect=fake_run):
        adapter = SaltCallAdapter(
            salt_call_cmd=["salt-call"],
            salt_key_cmd=["salt-key"],
            timeout=5,
        )
        adapter.call("test.ping")

    assert len(captured) == 1
    assert isinstance(captured[0], list), "cmd must be a list, not a string"


def test_adapter_key_list_builds_list_not_string() -> None:
    """adapter.key_list() must pass a list to subprocess."""
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> object:
        captured.append(cmd)
        m = MagicMock()
        m.returncode = 0
        m.stdout = '{"minions": []}'
        return m

    with patch("salt_cisco_mcp.salt_master.adapter.subprocess.run", side_effect=fake_run):
        adapter = SaltCallAdapter(
            salt_call_cmd=["salt-call"],
            salt_key_cmd=["salt-key"],
            timeout=5,
        )
        adapter.key_list()

    assert len(captured) == 1
    assert isinstance(captured[0], list), "cmd must be a list, not a string"


def test_adapter_user_input_not_joined_with_shell() -> None:
    """Malicious function name must not be shell-injected."""
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> object:
        captured.append(cmd)
        m = MagicMock()
        m.returncode = 0
        m.stdout = '{"local": null}'
        return m

    malicious = "test.ping; rm -rf /"
    with patch("salt_cisco_mcp.salt_master.adapter.subprocess.run", side_effect=fake_run):
        adapter = SaltCallAdapter(
            salt_call_cmd=["salt-call"],
            salt_key_cmd=["salt-key"],
            timeout=5,
        )
        adapter.call(malicious)

    assert malicious in captured[0], "malicious input must appear verbatim as an element"
    assert isinstance(captured[0], list)
