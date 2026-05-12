import subprocess
import sys
from unittest.mock import patch

import pytest

from salt_cisco_mcp.cli import main


def test_cli_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "salt_cisco_mcp.cli", "--help"],
        capture_output=True,
    )
    assert result.returncode == 0
    combined = result.stdout.lower()
    assert b"salt-cisco-mcp" in combined or b"usage" in combined


def test_cli_version_prints_version() -> None:
    from salt_cisco_mcp import __version__

    result = subprocess.run(
        [sys.executable, "-m", "salt_cisco_mcp.cli", "version"],
        capture_output=True,
    )
    assert result.returncode == 0
    assert __version__.encode() in result.stdout


def test_cli_unknown_subcommand_exits_nonzero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "salt_cisco_mcp.cli", "nonexistent"],
        capture_output=True,
    )
    assert result.returncode != 0


def test_cli_serve_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "salt_cisco_mcp.cli", "serve", "--help"],
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"serve" in result.stdout.lower()


def test_cli_verify_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "salt_cisco_mcp.cli", "verify", "--help"],
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"verify" in result.stdout.lower()


def test_cli_verify_prints_config_summary(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(SystemExit) as exc:
            main(argv=["verify"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "transport" in out
    assert "config file" in out


def test_cli_serve_invokes_run_server() -> None:
    """serve subcommand delegates to transports.run_server."""
    with patch("salt_cisco_mcp.transports.run_server") as mock_run:
        main(argv=["serve"])
    mock_run.assert_called_once()
