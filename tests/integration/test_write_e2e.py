"""Integration tests: write-tool round-trips against fake-master, audit JSONL written."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter

_STUB = Path(__file__).parent.parent / "fixtures" / "fake_master" / "salt_call_stub.py"
_STUB_CMD = [sys.executable, str(_STUB)]

_TOKEN = "fake-test-token-not-a-real-credential"
_SLS = "cisco.acl.edge"
_CFG = "hostname router1\n"


def _adapter() -> SaltCallAdapter:
    return SaltCallAdapter(salt_call_cmd=_STUB_CMD, salt_key_cmd=_STUB_CMD, timeout=10)


# --- state_apply full round-trip ---


def test_state_apply_round_trip_success(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    result = state_apply_logic(
        _adapter(), _SLS, "router1", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert result["success"] is True


def test_state_apply_round_trip_writes_audit(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    log = tmp_path / "audit.jsonl"
    state_apply_logic(_adapter(), _SLS, "router1", _TOKEN, _TOKEN, str(log))
    assert log.exists()
    record = json.loads(log.read_text().strip())
    assert record["tool"] == "state_apply"
    assert record["target"] == "router1"
    assert "operator_token_hash" in record
    assert "sls_or_config_hash" in record
    assert record["result"] is True


def test_state_apply_audit_no_raw_secrets(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.state_apply import state_apply_logic

    log = tmp_path / "audit.jsonl"
    state_apply_logic(_adapter(), _SLS, "router1", _TOKEN, _TOKEN, str(log))
    content = log.read_text()
    assert _TOKEN not in content
    assert _SLS not in content


# --- push_config full round-trip ---


def test_push_config_merge_round_trip(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), _CFG, "router1", "merge", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert "error" not in result
    assert result["mode"] == "merge"


def test_push_config_replace_round_trip(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    result = push_config_logic(
        _adapter(), _CFG, "router1", "replace", _TOKEN, _TOKEN, str(tmp_path / "a.jsonl")
    )
    assert "error" not in result
    assert result["mode"] == "replace"


def test_push_config_audit_parseable(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    log = tmp_path / "audit.jsonl"
    push_config_logic(_adapter(), _CFG, "router1", "merge", _TOKEN, _TOKEN, str(log))
    record = json.loads(log.read_text().strip())
    assert record["tool"] == "push_config"
    assert "operator_token_hash" in record
    assert "sls_or_config_hash" in record


def test_push_config_audit_no_raw_config(tmp_path: Path) -> None:
    from salt_cisco_mcp.tools.push_config import push_config_logic

    log = tmp_path / "audit.jsonl"
    push_config_logic(_adapter(), _CFG, "router1", "merge", _TOKEN, _TOKEN, str(log))
    content = log.read_text()
    assert _TOKEN not in content
    assert "hostname r1" not in content


# --- Server registration gate ---


@pytest.mark.anyio
async def test_write_tools_absent_by_default() -> None:
    from salt_cisco_mcp.config import Settings
    from salt_cisco_mcp.server import create_server

    srv = create_server(Settings())
    tools = await srv.list_tools()
    names = {t.name for t in tools}
    assert "state_apply" not in names
    assert "push_config" not in names


@pytest.mark.anyio
async def test_write_tools_present_when_enabled() -> None:
    from salt_cisco_mcp.config import ServerConfig, Settings
    from salt_cisco_mcp.server import create_server

    settings = Settings(server=ServerConfig(allow_write=True, confirm_token=_TOKEN))
    srv = create_server(settings)
    tools = await srv.list_tools()
    names = {t.name for t in tools}
    assert "state_apply" in names
    assert "push_config" in names
