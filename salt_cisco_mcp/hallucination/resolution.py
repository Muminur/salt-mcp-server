"""Hallucination resolution checker and metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from salt_cisco_mcp.hallucination.corpus_loader import PromptCase


@dataclass
class ResolutionResult:
    case_id: str
    expected_functions: list[str]
    resolved: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)


def check_resolution(case: PromptCase, known_functions: set[str]) -> ResolutionResult:
    """Check which expected functions appear in *known_functions*."""
    resolved = [fn for fn in case.expected_functions if fn in known_functions]
    unresolved = [fn for fn in case.expected_functions if fn not in known_functions]
    return ResolutionResult(
        case_id=case.id,
        expected_functions=list(case.expected_functions),
        resolved=resolved,
        unresolved=unresolved,
    )


def compute_metrics(results: list[ResolutionResult]) -> dict[str, float | int]:
    """Compute unresolved_function_rate and validation_pass_rate."""
    total_cases = len(results)
    total_functions = sum(len(r.expected_functions) for r in results)
    total_unresolved = sum(len(r.unresolved) for r in results)
    passing_cases = sum(1 for r in results if not r.unresolved)

    unresolved_rate = total_unresolved / total_functions if total_functions > 0 else 0.0
    pass_rate = passing_cases / total_cases if total_cases > 0 else 1.0

    return {
        "unresolved_function_rate": unresolved_rate,
        "validation_pass_rate": pass_rate,
        "total_cases": total_cases,
        "total_functions": total_functions,
        "total_unresolved": total_unresolved,
        "passing_cases": passing_cases,
    }


def load_known_functions(path: Path) -> set[str]:
    """Load the set of known Salt functions from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Known functions file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data)
