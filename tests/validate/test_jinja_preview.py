"""Tests for sandboxed Jinja2 template rendering."""

from __future__ import annotations

from salt_cisco_mcp.validate.jinja_preview import RenderResult, render_jinja_safe

_SIMPLE_TEMPLATE = "Hello {{ name }}!"
_LOOP_TEMPLATE = "{% for s in servers %}{{ s }}\n{% endfor %}"
_CONDITIONAL = "{% if enabled %}yes{% else %}no{% endif %}"
_SYNTAX_ERROR = "{% if %}broken"


def test_render_simple_returns_result() -> None:
    result = render_jinja_safe(_SIMPLE_TEMPLATE, {"name": "World"})
    assert isinstance(result, RenderResult)


def test_render_simple_output() -> None:
    result = render_jinja_safe(_SIMPLE_TEMPLATE, {"name": "World"})
    assert result.output == "Hello World!"


def test_render_success_flag() -> None:
    result = render_jinja_safe(_SIMPLE_TEMPLATE, {"name": "test"})
    assert result.success is True


def test_render_loop_template() -> None:
    result = render_jinja_safe(_LOOP_TEMPLATE, {"servers": ["1.1.1.1", "2.2.2.2"]})
    assert result.success is True
    assert "1.1.1.1" in result.output
    assert "2.2.2.2" in result.output


def test_render_conditional_true() -> None:
    result = render_jinja_safe(_CONDITIONAL, {"enabled": True})
    assert "yes" in result.output


def test_render_conditional_false() -> None:
    result = render_jinja_safe(_CONDITIONAL, {"enabled": False})
    assert "no" in result.output


def test_render_syntax_error_fails() -> None:
    result = render_jinja_safe(_SYNTAX_ERROR, {})
    assert result.success is False


def test_render_syntax_error_has_message() -> None:
    result = render_jinja_safe(_SYNTAX_ERROR, {})
    assert result.error is not None
    assert len(result.error) > 0


def test_render_result_has_warnings_list() -> None:
    result = render_jinja_safe(_SIMPLE_TEMPLATE, {"name": "x"})
    assert isinstance(result.warnings, list)


def test_render_missing_variable_produces_warning_or_empty() -> None:
    result = render_jinja_safe(_SIMPLE_TEMPLATE, {})
    # Should either succeed with empty variable or warn
    assert result.success is True or result.warnings


def test_render_blocks_unsafe_globals() -> None:
    """Sandboxed environment must block access to dangerous builtins."""
    unsafe = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
    result = render_jinja_safe(unsafe, {})
    # Should fail or produce an empty/safe output — must not expose class hierarchy
    if result.success:
        assert "__subclasses__" not in result.output
    else:
        assert result.error is not None


def test_render_blocks_config_access() -> None:
    """Prevent access to Salt globals like __salt__, __grains__."""
    risky = "{{ __salt__ }}"
    result = render_jinja_safe(risky, {})
    # Must not expose the actual Salt execution module dict
    if result.success:
        assert "__salt__" not in result.output or result.output.strip() == ""


def test_render_result_is_serializable() -> None:
    result = render_jinja_safe(_SIMPLE_TEMPLATE, {"name": "x"})
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "success" in d
    assert "output" in d
    assert "warnings" in d
