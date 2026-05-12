"""Tests for salt_cisco_mcp.transports — transport selection and HTTP auth."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from salt_cisco_mcp.config import SecurityConfig, ServerConfig, Settings
from salt_cisco_mcp.transports import (
    BearerTokenMiddleware,
    _read_bearer_token,
    build_http_app,
    run_server,
)


def _settings_with_transport(transport: str) -> Settings:
    return Settings(server=ServerConfig(transport=transport))  # type: ignore[arg-type]


def test_run_server_stdio_calls_run_with_stdio() -> None:
    settings = _settings_with_transport("stdio")
    mock_srv = MagicMock()
    with patch("salt_cisco_mcp.transports.create_server", return_value=mock_srv):
        run_server(settings)
    mock_srv.run.assert_called_once_with(transport="stdio")


def test_run_server_http_calls_build_http_app() -> None:
    settings = _settings_with_transport("http")
    mock_srv = MagicMock()
    mock_srv.streamable_http_app.return_value = MagicMock()
    with (
        patch("salt_cisco_mcp.transports.create_server", return_value=mock_srv),
        patch("salt_cisco_mcp.transports.anyio") as mock_anyio,
    ):
        run_server(settings)
    mock_anyio.run.assert_called_once()


def test_run_server_passes_settings_to_create_server() -> None:
    settings = _settings_with_transport("stdio")
    mock_srv = MagicMock()
    with patch("salt_cisco_mcp.transports.create_server", return_value=mock_srv) as mock_create:
        run_server(settings)
    mock_create.assert_called_once_with(settings)


def test_run_server_is_callable() -> None:
    assert callable(run_server)


def test_read_bearer_token_returns_none_when_mode_is_not_bearer(
    tmp_path: Path,
) -> None:
    settings = Settings()
    assert _read_bearer_token(settings) is None


def test_read_bearer_token_returns_none_when_file_missing(tmp_path: Path) -> None:
    settings = Settings(
        security=SecurityConfig(  # type: ignore[arg-type]
            http_auth={"mode": "bearer", "bearer_token_file": str(tmp_path / "missing.token")}
        )
    )
    assert _read_bearer_token(settings) is None


def test_read_bearer_token_returns_token_from_file(tmp_path: Path) -> None:
    token_file = tmp_path / "bearer.token"
    token_file.write_text("my-secret-token\n")
    settings = Settings(
        security=SecurityConfig(  # type: ignore[arg-type]
            http_auth={"mode": "bearer", "bearer_token_file": str(token_file)}
        )
    )
    assert _read_bearer_token(settings) == "my-secret-token"


def test_build_http_app_no_auth_returns_base_app() -> None:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(name="test")
    settings = Settings()
    app = build_http_app(mcp, settings)
    assert app is not None


def test_build_http_app_with_bearer_wraps_middleware(tmp_path: Path) -> None:
    from mcp.server.fastmcp import FastMCP

    token_file = tmp_path / "bearer.token"
    token_file.write_text("s3cr3t")

    mcp = FastMCP(name="test")
    settings = Settings(
        security=SecurityConfig(  # type: ignore[arg-type]
            http_auth={"mode": "bearer", "bearer_token_file": str(token_file)}
        )
    )
    app = build_http_app(mcp, settings)
    assert isinstance(app, BearerTokenMiddleware)


def test_bearer_token_middleware_blocks_unauthenticated() -> None:
    from mcp.server.fastmcp import FastMCP
    from starlette.testclient import TestClient

    mcp = FastMCP(name="test")
    base_app = mcp.streamable_http_app()
    app = BearerTokenMiddleware(base_app, "secret")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/mcp")
    assert r.status_code == 401


def test_bearer_token_middleware_blocks_wrong_token() -> None:
    from mcp.server.fastmcp import FastMCP
    from starlette.testclient import TestClient

    mcp = FastMCP(name="test")
    base_app = mcp.streamable_http_app()
    app = BearerTokenMiddleware(base_app, "correct-token")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/mcp", headers={"Authorization": "Bearer wrong-token"})
    assert r.status_code == 401


def test_bearer_token_middleware_allows_valid_token() -> None:
    from mcp.server.fastmcp import FastMCP
    from starlette.testclient import TestClient

    mcp = FastMCP(name="test")
    base_app = mcp.streamable_http_app()
    app = BearerTokenMiddleware(base_app, "valid-token")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/mcp", headers={"Authorization": "Bearer valid-token"})
    # 200/404/500 all acceptable — middleware passed the request through
    assert r.status_code != 401
