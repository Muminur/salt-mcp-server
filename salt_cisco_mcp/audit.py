"""Audit log writer for write operations."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def hash_str(s: str) -> str:
    """SHA256 hex digest of a UTF-8 string."""
    return hashlib.sha256(s.encode()).hexdigest()


def verify_token(provided: str, expected: str) -> bool:
    """Constant-time comparison to prevent timing side-channel attacks."""
    return hmac.compare_digest(provided, expected)


def append_audit(
    audit_log_path: str,
    *,
    tool: str,
    target: str,
    token_hash: str,
    sls_hash: str,
    result: Any,
    client_id: str = "",
) -> None:
    """Append one JSONL line to the audit log; never logs raw tokens or content."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "target": target,
        "operator_token_hash": token_hash,
        "sls_or_config_hash": sls_hash,
        "result": result,
        "agent_client_id": client_id,
    }
    path = Path(audit_log_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
