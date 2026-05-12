"""SLS structural linter — validates top-level structure without running Salt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

_DOC_STATES = "https://docs.saltproject.io/en/3007/ref/states/writing.html"


@dataclass
class LintResult:
    valid: bool
    errors: list[dict[str, str]] = field(default_factory=list)
    state_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "state_ids": self.state_ids,
        }


def lint_sls_text(sls: str) -> LintResult:
    """Lint an SLS string for structural validity."""
    if not sls or not sls.strip():
        return LintResult(
            valid=False,
            errors=[
                {
                    "message": "SLS content is empty",
                    "anchor_url": _DOC_STATES,
                }
            ],
        )

    try:
        parsed = yaml.safe_load(sls)
    except yaml.YAMLError as exc:
        return LintResult(
            valid=False,
            errors=[
                {
                    "message": f"YAML parse error: {exc}",
                    "anchor_url": _DOC_STATES,
                }
            ],
        )

    if not isinstance(parsed, dict):
        return LintResult(
            valid=False,
            errors=[
                {
                    "message": "SLS top-level must be a YAML mapping (got list or scalar)",
                    "anchor_url": _DOC_STATES,
                }
            ],
        )

    errors: list[dict[str, str]] = []
    state_ids: list[str] = []

    for state_id, state_body in parsed.items():
        state_ids.append(str(state_id))
        if not isinstance(state_body, dict):
            errors.append(
                {
                    "message": f"State '{state_id}': body must be a mapping",
                    "anchor_url": _DOC_STATES,
                }
            )

    return LintResult(valid=len(errors) == 0, errors=errors, state_ids=state_ids)
