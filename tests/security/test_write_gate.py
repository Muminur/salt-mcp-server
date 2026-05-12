"""Security: allow-write startup warnings and gate tests."""

from __future__ import annotations

from salt_cisco_mcp.config import ServerConfig, Settings


def test_no_warnings_when_allow_write_false() -> None:
    from salt_cisco_mcp.server import _check_write_mode

    settings = Settings()
    assert _check_write_mode(settings) == []


def test_write_mode_warning_emitted() -> None:
    from salt_cisco_mcp.server import _check_write_mode

    settings = Settings(server=ServerConfig(allow_write=True, confirm_token="tok"))
    warnings = _check_write_mode(settings)
    assert len(warnings) >= 1
    assert any("write" in w.lower() for w in warnings)


def test_missing_token_warning_emitted() -> None:
    from salt_cisco_mcp.server import _check_write_mode

    settings = Settings(server=ServerConfig(allow_write=True, confirm_token=""))
    warnings = _check_write_mode(settings)
    assert any("confirm_token" in w or "token" in w.lower() for w in warnings)


def test_bearer_token_comparison_uses_hmac() -> None:
    """BearerTokenMiddleware must use hmac.compare_digest, not plain ==."""
    import inspect

    from salt_cisco_mcp.transports import BearerTokenMiddleware

    source = inspect.getsource(BearerTokenMiddleware.dispatch)
    assert "compare_digest" in source, (
        "Bearer token comparison must use hmac.compare_digest to prevent timing attacks"
    )
