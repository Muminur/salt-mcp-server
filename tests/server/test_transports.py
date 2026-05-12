"""Tests for salt_cisco_mcp.transports — transport selection logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from salt_cisco_mcp.config import ServerConfig, Settings
from salt_cisco_mcp.transports import run_server


def _settings_with_transport(transport: str) -> Settings:
    return Settings(server=ServerConfig(transport=transport))  # type: ignore[arg-type]


def test_run_server_stdio_calls_run_with_stdio() -> None:
    settings = _settings_with_transport("stdio")
    mock_srv = MagicMock()
    with patch("salt_cisco_mcp.transports.create_server", return_value=mock_srv):
        run_server(settings)
    mock_srv.run.assert_called_once_with(transport="stdio")


def test_run_server_http_calls_run_with_streamable_http() -> None:
    settings = _settings_with_transport("http")
    mock_srv = MagicMock()
    with patch("salt_cisco_mcp.transports.create_server", return_value=mock_srv):
        run_server(settings)
    mock_srv.run.assert_called_once_with(transport="streamable-http")


def test_run_server_passes_settings_to_create_server() -> None:
    settings = _settings_with_transport("stdio")
    mock_srv = MagicMock()
    with patch("salt_cisco_mcp.transports.create_server", return_value=mock_srv) as mock_create:
        run_server(settings)
    mock_create.assert_called_once_with(settings)


def test_run_server_is_callable() -> None:
    assert callable(run_server)
