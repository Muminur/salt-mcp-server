"""Sandboxed Jinja2 template rendering with safety warnings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jinja2 import Undefined
from jinja2.sandbox import SandboxedEnvironment


@dataclass
class RenderResult:
    success: bool
    output: str = ""
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "warnings": self.warnings,
        }


_UNSAFE_PATTERNS = ("__class__", "__mro__", "__subclasses__", "__builtins__")
_SALT_GLOBALS = ("__salt__", "__grains__", "__pillar__", "__opts__", "__env__")


def _check_warnings(template_str: str) -> list[str]:
    warnings: list[str] = []
    for pat in _SALT_GLOBALS:
        if pat in template_str:
            warnings.append(f"Template references Salt global '{pat}' — unavailable in sandbox")
    return warnings


def render_jinja_safe(
    template_str: str,
    context: dict[str, Any],
) -> RenderResult:
    """Render *template_str* in a sandboxed Jinja2 environment."""
    warnings = _check_warnings(template_str)

    env = SandboxedEnvironment(undefined=_SilentUndefined)
    try:
        tmpl = env.from_string(template_str)
        output = tmpl.render(**context)
        return RenderResult(success=True, output=output, warnings=warnings)
    except Exception as exc:
        return RenderResult(success=False, error=str(exc), warnings=warnings)


class _SilentUndefined(Undefined):
    """Jinja2 Undefined subclass that renders to empty string instead of raising."""

    def __str__(self) -> str:
        return ""

    def __iter__(self) -> Any:
        return iter([])

    def __bool__(self) -> bool:
        return False
