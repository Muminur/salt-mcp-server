"""Structured log helper for MCP tool calls."""

from __future__ import annotations

import structlog

_log = structlog.get_logger()


def log_tool_call(
    *,
    tool: str,
    duration_ms: float,
    tokens_returned: int,
    tokens_budget: int | None,
    source: str | None,
    low_confidence: bool | None,
    client_id: str,
) -> None:
    """Emit a structured INFO log entry for a completed tool invocation."""
    _log.info(
        "tool_call",
        tool=tool,
        duration_ms=round(duration_ms, 1),
        tokens_returned=tokens_returned,
        tokens_budget=tokens_budget,
        source=source,
        low_confidence=low_confidence,
        client_session_id=client_id,
    )
