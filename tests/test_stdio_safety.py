"""Stdio safety: server.py and transports.py must never call print()."""

from __future__ import annotations

import ast
import pathlib


def _find_print_calls(source: str) -> list[int]:
    """Return line numbers of print() calls in source."""
    tree = ast.parse(source)
    lines = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            lines.append(node.lineno)
    return lines


_PKG = pathlib.Path(__file__).parent.parent / "salt_cisco_mcp"
_SERVER_MODULES = [
    _PKG / "server.py",
    _PKG / "transports.py",
]


def test_server_py_has_no_print_calls() -> None:
    path = _PKG / "server.py"
    assert path.exists(), f"{path} does not exist"
    hits = _find_print_calls(path.read_text())
    assert hits == [], f"server.py has print() at lines {hits} — use structlog instead"


def test_transports_py_has_no_print_calls() -> None:
    path = _PKG / "transports.py"
    assert path.exists(), f"{path} does not exist"
    hits = _find_print_calls(path.read_text())
    assert hits == [], f"transports.py has print() at lines {hits} — use structlog instead"
