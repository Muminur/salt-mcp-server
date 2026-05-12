"""Cache sys.list_functions and sys.argspec per adapter instance."""

from __future__ import annotations

from typing import Any

from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter


class FunctionCache:
    """Lazy, invalidatable cache for Salt function introspection."""

    def __init__(self, adapter: SaltCallAdapter) -> None:
        self._adapter = adapter
        self._functions: list[str] | None = None

    def _load(self) -> list[str]:
        if self._functions is None:
            raw = self._adapter.call("sys.list_functions")
            self._functions = list(raw.get("local") or [])
        return self._functions

    def list_functions(self, prefix: str | None = None) -> list[str]:
        """Return known functions, optionally filtered by *prefix*."""
        fns = self._load()
        if prefix:
            return [f for f in fns if f.startswith(f"{prefix}.")]
        return list(fns)

    def get_argspec(self, name: str) -> dict[str, Any]:
        """Return argspec dict for *name*, or empty dict if not found."""
        raw = self._adapter.call("sys.argspec", name)
        result: dict[str, Any] = raw.get("local") or {}
        return result

    def confirm_function_exists(self, name: str) -> bool:
        """Return True if *name* appears in the loaded function list."""
        return name in self._load()

    def invalidate(self) -> None:
        """Clear the cached function list so the next call re-fetches."""
        self._functions = None
