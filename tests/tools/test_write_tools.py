"""Tests for state_apply and push_config tool logic, plus audit module."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]

_TOKEN = "fake-test-token-not-a-real-credential"
_WRONG = "wrong-token-value"


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


# ---------------------------------------------------------------------------
# audit module
# ---------------------------------------------------------------------------


def test_hash_str_is_sha256() -> None:
    from salt_cisco_mcp.audit import hash_str

    assert hash_str("hello") == hashlib.sha256(b"hello").hexdigest()


def test_hash_str_deterministic() -> None:
    from salt_cisco_mcp.audit import hash_str

    assert hash_str("test-value") == hash_str("test-value")


def test_verify_token_match() -> None:
    from salt_cisco_mcp.audit import verify_token

    assert verify_token(_TOKEN, _TOKEN) is True


def test_verify_token_mismatch() -> None:
    from salt_cisco_mcp.audit import verify_token

    assert verify_token(_WRONG, _TOKEN) is False


def test_verify_token_empty_vs_nonempty() -> None:
    from salt_cisco_mcp.audit import verify_token

    assert verify_token("", _TOKEN) is False


def test_append_audit_creates_file(tmp_path: Path) -> None:
    from salt_cisco_mcp.audit import append_audit

    log = str(tmp_path / "audit.jsonl")
    append_audit(
        log, tool="state_apply", target="r1", token_hash="abc", sls_hash="def", result=True
    )
    assert Path(log).exists()


def test_append_audit_line_is_valid_json(tmp_path: Path) -> None:
    from salt_cisco_mcp.audit import append_audit

    log = str(tmp_path / "audit.jsonl")
    append_audit(
        log, tool="state_apply", target="r1", token_hash="abc", sls_hash="def", result=True
    )
    record = json.loads(Path(log).read_text().strip())
    assert isinstance(record, dict)


def test_append_audit_has_required_fields(tmp_path: Path) -> None:
    from salt_cisco_mcp.audit import append_audit

    log = str(tmp_path / "audit.jsonl")
    append_audit(
        log, tool="push_config", target="r1", token_hash="abc", sls_hash="def", result=None
    )
    record = json.loads(Path(log).read_text().strip())
    fields = ("timestamp", "tool", "target", "operator_token_hash", "sls_or_config_hash", "result")
    for field in fields:
        assert field in record, f"missing field: {field}"


def test_append_audit_multiple_lines(tmp_path: Path) -> None:
    from salt_cisco_mcp.audit import append_audit

    log = str(tmp_path / "audit.jsonl")
    for i in range(3):
        append_audit(
            log, tool="state_apply", target=f"r{i}", token_hash="h", sls_hash="s", result=True
        )
    lines = Path(log).read_text().strip().split("\n")
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# state_apply_logic
# ---------------------------------------------------------------------------


def test_state_apply_logic_no_adapter_returns_error() -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    result = state_apply_logic(None, "cisco.acl.edge", "r1", _TOKEN, _TOKEN, "/tmp/a.jsonl")
    assert "error" in result


def test_state_apply_logic_token_not_configured_returns_error() -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    result = state_apply_logic(_adapter(), "cisco.acl.edge", "r1", _TOKEN, "", "/tmp/a.jsonl")
    assert "error" in result


def test_state_apply_logic_token_mismatch_returns_error() -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    result = state_apply_logic(_adapter(), "cisco.acl.edge", "r1", _WRONG, _TOKEN, "/tmp/a.jsonl")
    assert "error" in result


def test_state_apply_logic_token_match_returns_dict(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    result = state_apply_logic(
        _adapter(), "cisco.acl.edge", "r1", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert isinstance(result, dict)
    assert "error" not in result


def test_state_apply_logic_success_true(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    result = state_apply_logic(
        _adapter(), "cisco.acl.edge", "r1", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert result["success"] is True


def test_state_apply_logic_writes_audit_log(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    log = tmp_path / "audit.jsonl"
    state_apply_logic(_adapter(), "cisco.acl.edge", "r1", _TOKEN, _TOKEN, str(log))
    assert log.exists()


def test_state_apply_audit_no_raw_token(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    log = tmp_path / "audit.jsonl"
    state_apply_logic(_adapter(), "cisco.acl.edge", "r1", _TOKEN, _TOKEN, str(log))
    assert _TOKEN not in log.read_text()


def test_state_apply_audit_no_raw_sls(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    log = tmp_path / "audit.jsonl"
    state_apply_logic(_adapter(), "cisco.acl.edge", "r1", _TOKEN, _TOKEN, str(log))
    assert "cisco.acl.edge" not in log.read_text()


# ---------------------------------------------------------------------------
# push_config_logic
# ---------------------------------------------------------------------------


def test_push_config_logic_no_adapter_returns_error() -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(None, "hostname r1\n", "r1", "merge", _TOKEN, _TOKEN, "/tmp/a.jsonl")
    assert "error" in result


def test_push_config_logic_token_not_configured_returns_error() -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), "hostname r1\n", "r1", "merge", _TOKEN, "", "/tmp/a.jsonl"
    )
    assert "error" in result


def test_push_config_logic_token_mismatch_returns_error() -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), "hostname r1\n", "r1", "merge", _WRONG, _TOKEN, "/tmp/a.jsonl"
    )
    assert "error" in result


def test_push_config_logic_invalid_mode_returns_error(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), "hostname r1\n", "r1", "bad-mode", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert "error" in result


def test_push_config_logic_merge_returns_dict(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), "hostname r1\n", "r1", "merge", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert isinstance(result, dict)
    assert "error" not in result


def test_push_config_logic_replace_returns_dict(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), "hostname r1\n", "r1", "replace", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert isinstance(result, dict)
    assert "error" not in result


def test_push_config_logic_writes_audit_log(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    log = tmp_path / "audit.jsonl"
    push_config_logic(_adapter(), "hostname r1\n", "r1", "merge", _TOKEN, _TOKEN, str(log))
    assert log.exists()


def test_push_config_audit_no_raw_token(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    log = tmp_path / "audit.jsonl"
    push_config_logic(_adapter(), "hostname r1\n", "r1", "merge", _TOKEN, _TOKEN, str(log))
    assert _TOKEN not in log.read_text()


def test_push_config_audit_no_raw_config(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    log = tmp_path / "audit.jsonl"
    push_config_logic(_adapter(), "hostname r1\n", "r1", "merge", _TOKEN, _TOKEN, str(log))
    assert "hostname r1" not in log.read_text()


# ---------------------------------------------------------------------------
# Server-level: write tools registration gate
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_write_tools_absent_when_allow_write_false() -> None:
    from salt_cisco_mcp.config import Settings
    from salt_cisco_mcp.server import create_server

    srv = create_server(Settings())
    tools = await srv.list_tools()
    names = {t.name for t in tools}
    assert "state_apply" not in names
    assert "push_config" not in names


@pytest.mark.anyio
async def test_write_tools_present_when_allow_write_true() -> None:
    from salt_cisco_mcp.config import ServerConfig, Settings
    from salt_cisco_mcp.server import create_server

    settings = Settings(server=ServerConfig(allow_write=True, confirm_token=_TOKEN))
    srv = create_server(settings)
    tools = await srv.list_tools()
    names = {t.name for t in tools}
    assert "state_apply" in names
    assert "push_config" in names
