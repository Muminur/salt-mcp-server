"""Validates the systemd unit file."""
from __future__ import annotations

import pathlib

_ROOT = pathlib.Path(__file__).parent.parent.parent
_UNIT = _ROOT / "packaging" / "salt-cisco-mcp.service"


def test_systemd_unit_exists() -> None:
    assert _UNIT.exists(), "packaging/salt-cisco-mcp.service must exist"


def test_systemd_unit_has_unit_section() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "[Unit]" in content


def test_systemd_unit_has_service_section() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "[Service]" in content


def test_systemd_unit_has_install_section() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "[Install]" in content


def test_systemd_unit_has_exec_start() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "ExecStart=" in content


def test_systemd_unit_has_restart_policy() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "Restart=" in content


def test_systemd_unit_references_http_transport() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "http" in content.lower()


def test_systemd_unit_has_description() -> None:
    content = _UNIT.read_text(encoding="utf-8")
    assert "Description=" in content
