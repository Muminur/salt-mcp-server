"""Tests for MCP prompt handlers — logic functions only (no FastMCP wiring needed)."""

from __future__ import annotations


def test_draft_state_for_cisco_returns_string() -> None:
    from salt_cisco_mcp.prompts.draft_state_for_cisco import draft_state_for_cisco_logic

    result = draft_state_for_cisco_logic(task="deny SSH from RFC1918", vendor="ios")
    assert isinstance(result, str)


def test_draft_state_for_cisco_mentions_vendor() -> None:
    from salt_cisco_mcp.prompts.draft_state_for_cisco import draft_state_for_cisco_logic

    result = draft_state_for_cisco_logic(task="configure NTP", vendor="nxos")
    assert "nxos" in result.lower() or "nx-os" in result.lower()


def test_draft_state_for_cisco_mentions_task() -> None:
    from salt_cisco_mcp.prompts.draft_state_for_cisco import draft_state_for_cisco_logic

    result = draft_state_for_cisco_logic(task="configure NTP servers", vendor="ios")
    assert "ntp" in result.lower()


def test_draft_state_for_cisco_mentions_salt() -> None:
    from salt_cisco_mcp.prompts.draft_state_for_cisco import draft_state_for_cisco_logic

    result = draft_state_for_cisco_logic(task="configure NTP", vendor="ios")
    assert "salt" in result.lower() or "sls" in result.lower()


def test_debug_failing_state_returns_string() -> None:
    from salt_cisco_mcp.prompts.debug_failing_state import debug_failing_state_logic

    result = debug_failing_state_logic(error="TypeError: 'NoneType'", sls="ntp.servers")
    assert isinstance(result, str)


def test_debug_failing_state_mentions_error() -> None:
    from salt_cisco_mcp.prompts.debug_failing_state import debug_failing_state_logic

    result = debug_failing_state_logic(error="KeyError: proxytype", sls="proxy.minion")
    assert "keyerror" in result.lower() or "proxytype" in result.lower()


def test_debug_failing_state_mentions_sls() -> None:
    from salt_cisco_mcp.prompts.debug_failing_state import debug_failing_state_logic

    result = debug_failing_state_logic(error="Timeout", sls="cisco.acl.edge")
    assert "cisco.acl.edge" in result


def test_debug_failing_state_diagnostic_content() -> None:
    from salt_cisco_mcp.prompts.debug_failing_state import debug_failing_state_logic

    result = debug_failing_state_logic(error="Timeout", sls="ntp.config")
    assert len(result) > 50


def test_migrate_legacy_syntax_returns_string() -> None:
    from salt_cisco_mcp.prompts.migrate_legacy_syntax import migrate_legacy_syntax_logic

    result = migrate_legacy_syntax_logic(sls_content="include:\n  - old_style")
    assert isinstance(result, str)


def test_migrate_legacy_syntax_mentions_3007() -> None:
    from salt_cisco_mcp.prompts.migrate_legacy_syntax import migrate_legacy_syntax_logic

    result = migrate_legacy_syntax_logic(sls_content="some_state:\n  cmd.run:\n    - name: echo hi")
    assert "3007" in result


def test_migrate_legacy_syntax_has_content() -> None:
    from salt_cisco_mcp.prompts.migrate_legacy_syntax import migrate_legacy_syntax_logic

    result = migrate_legacy_syntax_logic(sls_content="old_state:\n  cmd.run:\n    - name: echo")
    assert len(result) > 50


def test_generate_proxy_pillar_prompt_returns_string() -> None:
    from salt_cisco_mcp.prompts.generate_proxy_pillar import generate_proxy_pillar_logic

    result = generate_proxy_pillar_logic(proxytype="napalm", host="192.168.1.1")
    assert isinstance(result, str)


def test_generate_proxy_pillar_prompt_mentions_proxytype() -> None:
    from salt_cisco_mcp.prompts.generate_proxy_pillar import generate_proxy_pillar_logic

    result = generate_proxy_pillar_logic(proxytype="napalm", host="10.0.0.1")
    assert "napalm" in result.lower()


def test_generate_proxy_pillar_prompt_mentions_host() -> None:
    from salt_cisco_mcp.prompts.generate_proxy_pillar import generate_proxy_pillar_logic

    result = generate_proxy_pillar_logic(proxytype="nxos", host="10.0.0.5")
    assert "10.0.0.5" in result


def test_generate_proxy_pillar_prompt_warns_password() -> None:
    from salt_cisco_mcp.prompts.generate_proxy_pillar import generate_proxy_pillar_logic

    result = generate_proxy_pillar_logic(proxytype="napalm", host="10.0.0.1")
    assert "password" in result.lower()
