"""Security: redaction covers every config default key + case/variant fuzz."""

from __future__ import annotations

import pytest

from salt_cisco_mcp.salt_master.redactor import REDACTED, redact_dict, should_redact

# All keys from config.py._DEFAULT_REDACT_KEYS that must be caught by the redactor
_ALL_SENSITIVE_KEYS = [
    "password",
    "passwd",
    "secret",
    "enable_password",
    "enable_secret",
    "api_key",
    "api-key",
    "token",
    "auth_token",
    "bearer",
    "bearer_token",
    "community",
    "snmp_community",
    "tacacs_key",
    "radius_key",
    "shared_secret",
    "pre_shared_key",
    "psk",
    "passphrase",
    "private_key",
    "credential",
    "credentials",
]

_SAFE_KEYS = [
    "username",
    "host",
    "port",
    "driver",
    "proxytype",
    "description",
    "ip_address",
    "interface",
    "vrf",
    "protocol",
]

_CASE_VARIANTS = [
    "Password",
    "PASSWORD",
    "MyPassword",
    "ENABLE_PASSWORD",
    "enable_Password",
    "API_KEY",
    "Api_Key",
    "BEARER_TOKEN",
    "Bearer_Token",
    "my_secret",
    "MY_SECRET",
    "Secret",
    "SNMP_COMMUNITY",
    "PrivateKey",
]


@pytest.mark.parametrize("key", _ALL_SENSITIVE_KEYS)
def test_should_redact_all_config_default_keys(key: str) -> None:
    assert should_redact(key) is True, f"Expected {key!r} to be redacted"


@pytest.mark.parametrize("key", _SAFE_KEYS)
def test_should_not_redact_safe_keys(key: str) -> None:
    assert should_redact(key) is False, f"Expected {key!r} NOT to be redacted"


@pytest.mark.parametrize("key", _CASE_VARIANTS)
def test_should_redact_case_variants(key: str) -> None:
    assert should_redact(key) is True, f"Expected case variant {key!r} to be redacted"


def test_redact_dict_passwd_key() -> None:
    d = {"passwd": "hunter2"}
    assert redact_dict(d)["passwd"] == REDACTED


def test_redact_dict_bearer_key() -> None:
    d = {"bearer": "my-http-token"}
    assert redact_dict(d)["bearer"] == REDACTED


def test_redact_dict_psk_key() -> None:
    d = {"psk": "pre-shared-key"}
    assert redact_dict(d)["psk"] == REDACTED


def test_redact_dict_credential_key() -> None:
    d = {"credential": "secret"}
    assert redact_dict(d)["credential"] == REDACTED


def test_redact_dict_credentials_key() -> None:
    d = {"credentials": {"username": "admin", "password": "x"}}
    assert redact_dict(d)["credentials"] == REDACTED


def test_redact_dict_full_pillar_shape() -> None:
    """Simulate a real NAPALM proxy pillar — all secrets must be redacted."""
    pillar = {
        "proxy": {
            "proxytype": "napalm",
            "driver": "ios",
            "host": "192.168.1.1",
            "username": "admin",
            "password": "TopSecret",
            "enable_password": "EnablePass",
        },
        "snmp": {
            "community": "public",
            "token": "snmp-token",
        },
    }
    result = redact_dict(pillar)
    assert result["proxy"]["password"] == REDACTED
    assert result["proxy"]["enable_password"] == REDACTED
    assert result["proxy"]["username"] == "admin"
    assert result["proxy"]["host"] == "192.168.1.1"
    assert result["snmp"]["community"] == REDACTED
    assert result["snmp"]["token"] == REDACTED
