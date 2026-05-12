"""Unit tests for redaction layer — every default keyword must be hit."""

from __future__ import annotations

import pytest

from salt_cisco_mcp.salt_master.redactor import REDACTED, redact_dict, should_redact

_REDACTED = REDACTED


# --- should_redact ---


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "Password",
        "PASSWORD",
        "enable_password",
        "secret",
        "SECRET",
        "enable_secret",
        "community",
        "snmp_community",
        "token",
        "auth_token",
        "api_token",
        "key",
        "api_key",
        "private_key",
        "passphrase",
        "ssh_passphrase",
    ],
)
def test_should_redact_default_keys(key: str) -> None:
    assert should_redact(key) is True


@pytest.mark.parametrize(
    "key",
    ["username", "host", "port", "driver", "proxytype", "description", "ip_address"],
)
def test_should_not_redact_safe_keys(key: str) -> None:
    assert should_redact(key) is False


def test_should_redact_custom_extra_keys() -> None:
    assert should_redact("mysecret_custom", extra_keys={"custom"}) is True


def test_should_not_redact_extra_key_not_in_set() -> None:
    assert should_redact("username", extra_keys={"custom"}) is False


# --- redact_dict ---


def test_redact_dict_replaces_password() -> None:
    d = {"password": "hunter2", "username": "admin"}
    result = redact_dict(d)
    assert result["password"] == _REDACTED
    assert result["username"] == "admin"


def test_redact_dict_replaces_secret() -> None:
    d = {"secret": "mysecret"}
    assert redact_dict(d)["secret"] == _REDACTED


def test_redact_dict_replaces_enable_password() -> None:
    d = {"enable_password": "cisco"}
    assert redact_dict(d)["enable_password"] == _REDACTED


def test_redact_dict_replaces_community() -> None:
    d = {"community": "public"}
    assert redact_dict(d)["community"] == _REDACTED


def test_redact_dict_replaces_token() -> None:
    d = {"token": "abc123"}
    assert redact_dict(d)["token"] == _REDACTED


def test_redact_dict_replaces_key() -> None:
    d = {"key": "abc123"}
    assert redact_dict(d)["key"] == _REDACTED


def test_redact_dict_replaces_passphrase() -> None:
    d = {"passphrase": "mypass"}
    assert redact_dict(d)["passphrase"] == _REDACTED


def test_redact_dict_nested() -> None:
    d = {"proxy": {"password": "secret", "host": "1.2.3.4"}}
    result = redact_dict(d)
    assert result["proxy"]["password"] == _REDACTED
    assert result["proxy"]["host"] == "1.2.3.4"


def test_redact_dict_list_of_dicts() -> None:
    data = [{"password": "x"}, {"username": "admin"}]
    result = redact_dict(data)
    assert isinstance(result, list)
    assert result[0]["password"] == _REDACTED
    assert result[1]["username"] == "admin"


def test_redact_dict_preserves_non_sensitive() -> None:
    d = {"host": "router1", "port": 22, "driver": "ios", "proxytype": "napalm"}
    result = redact_dict(d)
    assert result == d


def test_redact_dict_handles_none_value() -> None:
    d = {"password": None, "host": "x"}
    result = redact_dict(d)
    assert result["password"] == _REDACTED


def test_redact_dict_handles_integer_value() -> None:
    d = {"password": 12345}
    result = redact_dict(d)
    assert result["password"] == _REDACTED


def test_redact_dict_extra_keys() -> None:
    d = {"custom_field": "secret_value"}
    assert redact_dict(d, extra_keys={"custom_field"})["custom_field"] == _REDACTED


def test_redact_dict_deeply_nested() -> None:
    d = {"level1": {"level2": {"level3": {"password": "deep_secret"}}}}
    result = redact_dict(d)
    assert result["level1"]["level2"]["level3"]["password"] == _REDACTED


def test_redact_dict_passthrough_scalar() -> None:
    assert redact_dict("plain string") == "plain string"
    assert redact_dict(42) == 42
    assert redact_dict(None) is None
