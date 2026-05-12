"""Redaction layer for sensitive Salt pillar/grain data."""

from __future__ import annotations

from typing import Any

REDACTED = "<<REDACTED>>"

_DEFAULT_REDACT_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "enable_password",
        "community",
        "token",
        "key",
        "passphrase",
        "bearer",
        "psk",
        "credential",
    }
)


def should_redact(key: str, extra_keys: set[str] | None = None) -> bool:
    """Return True if *key* matches any default or extra redaction keyword (case-insensitive)."""
    lower = key.lower()
    all_keys = _DEFAULT_REDACT_KEYS | (extra_keys or set())
    return any(k in lower for k in all_keys)


def redact_dict(data: Any, extra_keys: set[str] | None = None) -> Any:
    """Recursively replace sensitive values with REDACTED sentinel."""
    if isinstance(data, dict):
        return {
            k: (REDACTED if should_redact(k, extra_keys) else redact_dict(v, extra_keys))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact_dict(item, extra_keys) for item in data]
    return data
