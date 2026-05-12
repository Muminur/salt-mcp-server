"""Tests for SLS state structural linter."""

from __future__ import annotations

from salt_cisco_mcp.validate.state_lint import LintResult, lint_sls_text

_VALID_SLS = """\
install_ntp:
  pkg.installed:
    - name: ntp

configure_ntp:
  file.managed:
    - name: /etc/ntp.conf
    - source: salt://ntp/ntp.conf
"""

_EMPTY_SLS = ""

_NO_STATE_FUNCTION = """\
just_a_key:
  some_dict_value:
    key: value
"""

_SYNTAX_ERROR_SLS = """\
invalid: yaml: [
"""

_VALID_NAPALM_SLS = """\
set_ntp_servers:
  napalm.managed:
    - name: ntp_servers
    - template_name: salt://templates/ntp.jinja
"""


def test_lint_valid_sls_passes() -> None:
    result = lint_sls_text(_VALID_SLS)
    assert isinstance(result, LintResult)
    assert result.valid is True


def test_lint_valid_sls_no_errors() -> None:
    result = lint_sls_text(_VALID_SLS)
    assert result.errors == []


def test_lint_empty_sls_fails() -> None:
    result = lint_sls_text(_EMPTY_SLS)
    assert result.valid is False


def test_lint_empty_sls_has_error() -> None:
    result = lint_sls_text(_EMPTY_SLS)
    assert len(result.errors) > 0


def test_lint_syntax_error_fails() -> None:
    result = lint_sls_text(_SYNTAX_ERROR_SLS)
    assert result.valid is False


def test_lint_syntax_error_message_mentions_yaml() -> None:
    result = lint_sls_text(_SYNTAX_ERROR_SLS)
    error_text = " ".join(e["message"] for e in result.errors).lower()
    assert "yaml" in error_text or "parse" in error_text or "syntax" in error_text


def test_lint_napalm_state_passes() -> None:
    result = lint_sls_text(_VALID_NAPALM_SLS)
    assert result.valid is True


def test_lint_result_has_state_ids() -> None:
    result = lint_sls_text(_VALID_SLS)
    assert hasattr(result, "state_ids")
    assert isinstance(result.state_ids, list)


def test_lint_result_state_ids_populated() -> None:
    result = lint_sls_text(_VALID_SLS)
    assert "install_ntp" in result.state_ids
    assert "configure_ntp" in result.state_ids


def test_lint_errors_have_message_field() -> None:
    result = lint_sls_text(_EMPTY_SLS)
    for err in result.errors:
        assert "message" in err


def test_lint_errors_may_have_anchor_url() -> None:
    result = lint_sls_text(_EMPTY_SLS)
    for err in result.errors:
        assert "anchor_url" in err


def test_lint_valid_result_is_dict_serializable() -> None:
    result = lint_sls_text(_VALID_SLS)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "valid" in d
    assert "errors" in d
    assert "state_ids" in d


def test_lint_non_dict_top_level_fails() -> None:
    result = lint_sls_text("- item1\n- item2\n")
    assert result.valid is False
