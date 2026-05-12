"""Tests for pillar schema validation."""

from __future__ import annotations

from salt_cisco_mcp.validate.pillar_schema import (
    SUPPORTED_PROXYTYPES,
    ValidationResult,
    validate_pillar_dict,
)

# --- napalm proxy ---

_NAPALM_VALID = {
    "proxy": {
        "proxytype": "napalm",
        "driver": "ios",
        "host": "192.168.1.1",
        "username": "admin",
        "password": "secret",
    }
}

_NAPALM_MINIMAL = {
    "proxy": {
        "proxytype": "napalm",
        "driver": "iosxr",
        "host": "10.0.0.1",
        "username": "user",
        "password": "pass",
    }
}

_NAPALM_MISSING_DRIVER = {
    "proxy": {
        "proxytype": "napalm",
        "host": "192.168.1.1",
        "username": "admin",
        "password": "secret",
    }
}

_NAPALM_MISSING_HOST = {
    "proxy": {
        "proxytype": "napalm",
        "driver": "ios",
        "username": "admin",
        "password": "secret",
    }
}


def test_validate_napalm_valid() -> None:
    result = validate_pillar_dict(_NAPALM_VALID)
    assert isinstance(result, ValidationResult)
    assert result.valid is True


def test_validate_napalm_errors_is_empty_on_valid() -> None:
    result = validate_pillar_dict(_NAPALM_VALID)
    assert result.errors == []


def test_validate_napalm_minimal_passes() -> None:
    result = validate_pillar_dict(_NAPALM_MINIMAL)
    assert result.valid is True


def test_validate_napalm_missing_driver_fails() -> None:
    result = validate_pillar_dict(_NAPALM_MISSING_DRIVER)
    assert result.valid is False


def test_validate_napalm_missing_host_fails() -> None:
    result = validate_pillar_dict(_NAPALM_MISSING_HOST)
    assert result.valid is False


def test_validate_napalm_error_has_field_info() -> None:
    result = validate_pillar_dict(_NAPALM_MISSING_DRIVER)
    error_text = " ".join(e["message"] for e in result.errors)
    assert "driver" in error_text.lower()


# --- nxos proxy ---

_NXOS_VALID = {
    "proxy": {
        "proxytype": "nxos",
        "host": "192.168.2.1",
        "username": "admin",
        "password": "secret",
    }
}

_NXOS_MISSING_USERNAME = {
    "proxy": {
        "proxytype": "nxos",
        "host": "192.168.2.1",
        "password": "secret",
    }
}


def test_validate_nxos_valid() -> None:
    result = validate_pillar_dict(_NXOS_VALID)
    assert result.valid is True


def test_validate_nxos_missing_username_fails() -> None:
    result = validate_pillar_dict(_NXOS_MISSING_USERNAME)
    assert result.valid is False


# --- nxos_api proxy ---

_NXOS_API_VALID = {
    "proxy": {
        "proxytype": "nxos_api",
        "host": "192.168.3.1",
        "username": "admin",
        "password": "secret",
    }
}


def test_validate_nxos_api_valid() -> None:
    result = validate_pillar_dict(_NXOS_API_VALID)
    assert result.valid is True


# --- cisconso proxy ---

_CISCONSO_VALID = {
    "proxy": {
        "proxytype": "cisconso",
        "host": "192.168.4.1",
        "username": "admin",
        "password": "secret",
    }
}


def test_validate_cisconso_valid() -> None:
    result = validate_pillar_dict(_CISCONSO_VALID)
    assert result.valid is True


# --- unknown proxytype ---


def test_validate_unknown_proxytype_fails() -> None:
    pillar = {"proxy": {"proxytype": "unknown_proxy", "host": "x"}}
    result = validate_pillar_dict(pillar)
    assert result.valid is False


def test_validate_unknown_proxytype_error_lists_supported() -> None:
    pillar = {"proxy": {"proxytype": "unknown_proxy", "host": "x"}}
    result = validate_pillar_dict(pillar)
    error_text = " ".join(e["message"] for e in result.errors)
    assert any(pt in error_text for pt in SUPPORTED_PROXYTYPES)


# --- missing proxy key ---


def test_validate_missing_proxy_key_fails() -> None:
    result = validate_pillar_dict({"not_proxy": {}})
    assert result.valid is False


def test_validate_empty_dict_fails() -> None:
    result = validate_pillar_dict({})
    assert result.valid is False


# --- ValidationResult shape ---


def test_validation_result_has_valid_field() -> None:
    result = validate_pillar_dict(_NAPALM_VALID)
    assert hasattr(result, "valid")


def test_validation_result_has_errors_list() -> None:
    result = validate_pillar_dict(_NAPALM_VALID)
    assert isinstance(result.errors, list)


def test_validation_result_errors_have_message_field() -> None:
    result = validate_pillar_dict(_NAPALM_MISSING_DRIVER)
    for err in result.errors:
        assert "message" in err


def test_validation_result_errors_may_have_anchor_url() -> None:
    result = validate_pillar_dict(_NAPALM_MISSING_DRIVER)
    for err in result.errors:
        assert "anchor_url" in err


def test_supported_proxytypes_contains_all_four() -> None:
    assert "napalm" in SUPPORTED_PROXYTYPES
    assert "nxos" in SUPPORTED_PROXYTYPES
    assert "nxos_api" in SUPPORTED_PROXYTYPES
    assert "cisconso" in SUPPORTED_PROXYTYPES
