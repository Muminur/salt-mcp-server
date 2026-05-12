import pytest

from salt_cisco_mcp.config import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.server.transport == "stdio"
    assert s.server.http_host == "127.0.0.1"
    assert s.server.http_port == 7842
    assert s.server.allow_write is False
    assert s.salt_master.salt_call_path == "salt-call"
    assert s.salt_master.command_timeout_s == 30
    assert s.retrieval.default_max_tokens == 1500
    assert s.retrieval.hard_cap_tokens == 8000
    assert s.network.enabled is True
    assert s.security.bind_local_only is True
    assert "password" in s.security.redact_keys
    assert "secret" in s.security.redact_keys
    assert s.logging.level == "INFO"
    assert s.logging.format == "json"
    assert s.telemetry.enabled is True
    assert s.telemetry.metrics_dir == "/var/lib/salt-mcp"


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SALT_MCP_SERVER__TRANSPORT", "http")
    s = Settings()
    assert s.server.transport == "http"


def test_settings_allow_write_default_false() -> None:
    assert Settings().server.allow_write is False


def test_settings_yaml_file_load(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_file = tmp_path / "config.yaml"  # type: ignore[operator]
    config_file.write_text("server:\n  transport: http\n  http_port: 9999\n")
    monkeypatch.setenv("SALT_MCP_CONFIG_FILE", str(config_file))
    s = Settings()
    assert s.server.transport == "http"
    assert s.server.http_port == 9999


def test_settings_invalid_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SALT_MCP_SERVER__TRANSPORT", "invalid")
    with pytest.raises(Exception):
        Settings()
