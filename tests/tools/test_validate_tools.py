"""Tests for M7 validation tool logic functions."""

from __future__ import annotations

from salt_cisco_mcp.tools.audit_cisco_config import audit_cisco_config_logic
from salt_cisco_mcp.tools.generate_pillar import generate_pillar_logic
from salt_cisco_mcp.tools.render_jinja import render_jinja_logic
from salt_cisco_mcp.tools.validate_pillar import validate_pillar_logic
from salt_cisco_mcp.tools.validate_state import validate_state_logic

_VALID_NAPALM_YAML = """\
proxy:
  proxytype: napalm
  driver: ios
  host: 192.168.1.1
  username: admin
  password: secret
"""

_INVALID_PILLAR_YAML = """\
proxy:
  proxytype: napalm
  host: 192.168.1.1
"""

_VALID_SLS = """\
configure_ntp:
  napalm.managed:
    - name: ntp
"""


# --- validate_pillar ---


def test_validate_pillar_logic_returns_dict() -> None:
    result = validate_pillar_logic(_VALID_NAPALM_YAML)
    assert isinstance(result, dict)


def test_validate_pillar_logic_valid_yaml_passes() -> None:
    result = validate_pillar_logic(_VALID_NAPALM_YAML)
    assert result["valid"] is True


def test_validate_pillar_logic_invalid_yaml_fails() -> None:
    result = validate_pillar_logic(_INVALID_PILLAR_YAML)
    assert result["valid"] is False


def test_validate_pillar_logic_has_errors_key() -> None:
    result = validate_pillar_logic(_INVALID_PILLAR_YAML)
    assert "errors" in result


def test_validate_pillar_logic_bad_yaml_syntax() -> None:
    result = validate_pillar_logic("invalid: yaml: [")
    assert result["valid"] is False


# --- validate_state ---


def test_validate_state_logic_returns_dict() -> None:
    result = validate_state_logic(_VALID_SLS)
    assert isinstance(result, dict)


def test_validate_state_logic_valid_sls_passes() -> None:
    result = validate_state_logic(_VALID_SLS)
    assert result["valid"] is True


def test_validate_state_logic_empty_sls_fails() -> None:
    result = validate_state_logic("")
    assert result["valid"] is False


def test_validate_state_logic_has_errors_key() -> None:
    result = validate_state_logic("")
    assert "errors" in result


# --- render_jinja ---


def test_render_jinja_logic_returns_dict() -> None:
    result = render_jinja_logic("Hello {{ name }}!", {"name": "Salt"})
    assert isinstance(result, dict)


def test_render_jinja_logic_success() -> None:
    result = render_jinja_logic("Hello {{ name }}!", {"name": "Salt"})
    assert result["success"] is True
    assert "Salt" in result["output"]


def test_render_jinja_logic_syntax_error() -> None:
    result = render_jinja_logic("{% if %}broken", {})
    assert result["success"] is False


def test_render_jinja_logic_has_output_key() -> None:
    result = render_jinja_logic("test", {})
    assert "output" in result


# --- audit_cisco_config ---


def test_audit_cisco_config_logic_returns_dict() -> None:
    result = audit_cisco_config_logic("hostname r1\n", "ios")
    assert isinstance(result, dict)


def test_audit_cisco_config_logic_has_passed_key() -> None:
    result = audit_cisco_config_logic("hostname r1\n", "ios")
    assert "passed" in result


def test_audit_cisco_config_logic_has_findings_key() -> None:
    result = audit_cisco_config_logic("hostname r1\n", "ios")
    assert "findings" in result


# --- generate_pillar ---


def test_generate_pillar_logic_napalm_ios() -> None:
    result = generate_pillar_logic(
        proxytype="napalm", driver="ios", host="1.2.3.4", username="admin"
    )
    assert isinstance(result, dict)


def test_generate_pillar_logic_has_pillar_key() -> None:
    result = generate_pillar_logic(
        proxytype="napalm", driver="ios", host="1.2.3.4", username="admin"
    )
    assert "pillar" in result


def test_generate_pillar_logic_has_password_placeholder() -> None:
    result = generate_pillar_logic(
        proxytype="napalm", driver="ios", host="1.2.3.4", username="admin"
    )
    assert "<<password>>" in result["pillar"]


def test_generate_pillar_logic_contains_proxytype() -> None:
    result = generate_pillar_logic(
        proxytype="napalm", driver="ios", host="1.2.3.4", username="admin"
    )
    assert "napalm" in result["pillar"]


def test_generate_pillar_logic_nxos() -> None:
    result = generate_pillar_logic(proxytype="nxos", driver=None, host="1.2.3.4", username="admin")
    assert result["pillar"]
    assert "nxos" in result["pillar"]


def test_generate_pillar_logic_has_proxytype_in_result() -> None:
    result = generate_pillar_logic(
        proxytype="napalm", driver="ios", host="1.2.3.4", username="admin"
    )
    assert result.get("proxytype") == "napalm"
