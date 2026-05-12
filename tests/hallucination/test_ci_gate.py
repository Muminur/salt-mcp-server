"""CI gate: hallucination regression metrics must meet PRD §14 thresholds."""

from __future__ import annotations

from pathlib import Path

from salt_cisco_mcp.hallucination.corpus_loader import load_corpus
from salt_cisco_mcp.hallucination.resolution import (
    check_resolution,
    compute_metrics,
    load_known_functions,
)

_CASES_DIR = Path(__file__).parent / "cases"
_KNOWN_FUNCTIONS_FILE = (
    Path(__file__).parent.parent / "fixtures" / "fake_master" / "sys_list_functions.json"
)


def test_corpus_has_minimum_cases() -> None:
    cases = load_corpus(_CASES_DIR)
    assert len(cases) >= 30, f"Corpus must have ≥30 cases, got {len(cases)}"


def test_ci_gate_unresolved_function_rate() -> None:
    """G1: unresolved_function_rate must be ≤ 5%."""
    cases = load_corpus(_CASES_DIR)
    known = load_known_functions(_KNOWN_FUNCTIONS_FILE)
    results = [check_resolution(c, known) for c in cases]
    metrics = compute_metrics(results)
    rate = metrics["unresolved_function_rate"]
    assert rate <= 0.05, (
        f"G1 FAILED: unresolved_function_rate={rate:.1%} (threshold: ≤5%). "
        f"Unresolved functions in corpus:\n"
        + "\n".join(
            f"  [{r.case_id}] {fn}"
            for r in results
            for fn in r.unresolved
        )
    )


def test_ci_gate_validation_pass_rate() -> None:
    """G2: validation_pass_rate must be ≥ 95%."""
    cases = load_corpus(_CASES_DIR)
    known = load_known_functions(_KNOWN_FUNCTIONS_FILE)
    results = [check_resolution(c, known) for c in cases]
    metrics = compute_metrics(results)
    rate = metrics["validation_pass_rate"]
    assert rate >= 0.95, (
        f"G2 FAILED: validation_pass_rate={rate:.1%} (threshold: ≥95%). "
        f"Failing cases:\n"
        + "\n".join(
            f"  [{r.case_id}] unresolved={r.unresolved}"
            for r in results
            if r.unresolved
        )
    )
