"""Load and redact Salt pillar data via salt-call --local."""

from __future__ import annotations

from typing import Any, cast

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.redactor import redact_dict


def read_pillar(
    adapter: SaltCallAdapter,
    extra_redact_keys: set[str] | None = None,
) -> dict[str, Any]:
    """Return redacted pillar from ``salt-call --local pillar.items``."""
    raw = adapter.call("pillar.items")
    pillar: dict[str, Any] = raw.get("local") or {}
    return cast(dict[str, Any], redact_dict(pillar, extra_keys=extra_redact_keys))
