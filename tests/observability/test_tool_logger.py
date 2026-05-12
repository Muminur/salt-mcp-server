"""Tests for structured tool-call log emission."""

from __future__ import annotations

import structlog.testing


def test_log_tool_call_emits_event() -> None:
    from salt_cisco_mcp.observability.log import log_tool_call

    with structlog.testing.capture_logs() as logs:
        log_tool_call(
            tool="search_docs",
            duration_ms=12.5,
            tokens_returned=100,
            tokens_budget=1500,
            source="index",
            low_confidence=False,
            client_id="test-client",
        )
    assert len(logs) == 1


def test_log_tool_call_event_name() -> None:
    from salt_cisco_mcp.observability.log import log_tool_call

    with structlog.testing.capture_logs() as logs:
        log_tool_call(
            tool="get_doc",
            duration_ms=1.0,
            tokens_returned=50,
            tokens_budget=1500,
            source="cache",
            low_confidence=None,
            client_id="",
        )
    assert logs[0]["event"] == "tool_call"


def test_log_tool_call_has_required_fields() -> None:
    from salt_cisco_mcp.observability.log import log_tool_call

    required = {
        "event",
        "tool",
        "duration_ms",
        "tokens_returned",
        "tokens_budget",
        "source",
        "low_confidence",
        "client_session_id",
    }
    with structlog.testing.capture_logs() as logs:
        log_tool_call(
            tool="live_fetch",
            duration_ms=55.0,
            tokens_returned=0,
            tokens_budget=None,
            source="live",
            low_confidence=None,
            client_id="",
        )
    record = logs[0]
    for field in required:
        assert field in record, f"missing field: {field}"


def test_log_tool_call_values_correct() -> None:
    from salt_cisco_mcp.observability.log import log_tool_call

    with structlog.testing.capture_logs() as logs:
        log_tool_call(
            tool="search_docs",
            duration_ms=42.7,
            tokens_returned=200,
            tokens_budget=1500,
            source="index",
            low_confidence=True,
            client_id="agent-1",
        )
    r = logs[0]
    assert r["tool"] == "search_docs"
    assert r["tokens_returned"] == 200
    assert r["source"] == "index"
    assert r["low_confidence"] is True
    assert r["client_session_id"] == "agent-1"
