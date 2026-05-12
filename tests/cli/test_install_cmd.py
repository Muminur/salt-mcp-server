"""Tests for the `salt-cisco-mcp install` subcommand."""
from __future__ import annotations

import pathlib

import pytest

from salt_cisco_mcp.install_cmd import InstallResult, install_logic


def test_install_creates_config_dir(tmp_path: pathlib.Path) -> None:
    """install_logic creates the config directory."""
    config_dir = str(tmp_path / "config")
    result = install_logic(
        config_dir=config_dir,
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
    )
    assert result.success
    assert pathlib.Path(config_dir).is_dir()


def test_install_creates_data_dir(tmp_path: pathlib.Path) -> None:
    """install_logic creates the data directory."""
    data_dir = str(tmp_path / "data")
    result = install_logic(
        config_dir=str(tmp_path / "config"),
        data_dir=data_dir,
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
    )
    assert result.success
    assert pathlib.Path(data_dir).is_dir()


def test_install_creates_log_dir(tmp_path: pathlib.Path) -> None:
    """install_logic creates the log directory."""
    log_dir = str(tmp_path / "log")
    result = install_logic(
        config_dir=str(tmp_path / "config"),
        data_dir=str(tmp_path / "data"),
        log_dir=log_dir,
        audit_dir=str(tmp_path / "audit"),
    )
    assert result.success
    assert pathlib.Path(log_dir).is_dir()


def test_install_writes_default_config(tmp_path: pathlib.Path) -> None:
    """install_logic writes config.yaml with server defaults."""
    config_dir = str(tmp_path / "config")
    result = install_logic(
        config_dir=config_dir,
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
    )
    assert result.success
    cfg = pathlib.Path(config_dir) / "config.yaml"
    assert cfg.exists()
    content = cfg.read_text(encoding="utf-8")
    assert "transport" in content


def test_install_config_contains_data_dir(tmp_path: pathlib.Path) -> None:
    """Written config.yaml references the data_dir for doc_db."""
    config_dir = str(tmp_path / "config")
    data_dir = str(tmp_path / "data")
    install_logic(
        config_dir=config_dir,
        data_dir=data_dir,
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
    )
    content = (pathlib.Path(config_dir) / "config.yaml").read_text(encoding="utf-8")
    assert "doc_db" in content


def test_install_does_not_overwrite_existing_config(tmp_path: pathlib.Path) -> None:
    """install_logic skips config.yaml if it already exists."""
    config_dir = str(tmp_path / "config")
    pathlib.Path(config_dir).mkdir(parents=True)
    existing = pathlib.Path(config_dir) / "config.yaml"
    existing.write_text("existing: true\n", encoding="utf-8")
    install_logic(
        config_dir=config_dir,
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
    )
    assert existing.read_text(encoding="utf-8") == "existing: true\n"


def test_install_dry_run_creates_nothing(tmp_path: pathlib.Path) -> None:
    """install_logic dry_run=True creates no directories or files."""
    config_dir = str(tmp_path / "config")
    install_logic(
        config_dir=config_dir,
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
        dry_run=True,
    )
    assert not pathlib.Path(config_dir).exists()


def test_install_dry_run_result_lists_would_create(tmp_path: pathlib.Path) -> None:
    """dry_run=True still populates created_dirs so the user can preview."""
    result = install_logic(
        config_dir=str(tmp_path / "config"),
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
        dry_run=True,
    )
    assert len(result.created_dirs) >= 3


def test_install_result_lists_created_dirs(tmp_path: pathlib.Path) -> None:
    """InstallResult.created_dirs lists every directory that was created."""
    result = install_logic(
        config_dir=str(tmp_path / "config"),
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
    )
    assert len(result.created_dirs) >= 3


def test_install_warns_when_salt_call_missing(tmp_path: pathlib.Path) -> None:
    """install_logic emits a warning when salt_call_cmd is not found on PATH."""
    result = install_logic(
        config_dir=str(tmp_path / "config"),
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
        salt_call_cmd="/no/such/binary/salt-call-xyz",
    )
    assert any("salt-call" in w.lower() for w in result.warnings)


def test_install_no_warning_when_salt_call_present(tmp_path: pathlib.Path) -> None:
    """install_logic emits no salt-call warning when the binary exists."""
    import shutil

    python = shutil.which("python") or shutil.which("python3")
    if python is None:
        pytest.skip("python not on PATH")
    result = install_logic(
        config_dir=str(tmp_path / "config"),
        data_dir=str(tmp_path / "data"),
        log_dir=str(tmp_path / "log"),
        audit_dir=str(tmp_path / "audit"),
        salt_call_cmd=python,
    )
    assert not any("salt-call" in w.lower() for w in result.warnings)


def test_install_result_is_dataclass() -> None:
    """InstallResult is a proper dataclass with expected fields."""
    from dataclasses import fields

    field_names = {f.name for f in fields(InstallResult)}
    assert "success" in field_names
    assert "created_dirs" in field_names
    assert "warnings" in field_names
    assert "config_file" in field_names


def test_install_cli_subcommand_runs(tmp_path: pathlib.Path) -> None:
    """'salt-cisco-mcp install' CLI subcommand accepts dir flags without error."""
    from salt_cisco_mcp.cli import main

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "install",
                "--config-dir",
                str(tmp_path / "etc"),
                "--data-dir",
                str(tmp_path / "var"),
                "--log-dir",
                str(tmp_path / "log"),
                "--audit-dir",
                str(tmp_path / "audit"),
            ]
        )
    assert exc_info.value.code == 0
    assert (tmp_path / "etc").is_dir()
