"""Tests for hallucination resolution checker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from salt_cisco_mcp.hallucination.corpus_loader import PromptCase
from salt_cisco_mcp.hallucination.resolution import (
    ResolutionResult,
    check_resolution,
    compute_metrics,
    load_known_functions,
)

_KNOWN = {"ntp.set_servers", "ntp.show_ntp_info", "grains.get", "pillar.get", "state.apply"}


def _make_case(
    id: str = "case-001",
    expected_functions: list[str] | None = None,
    must_not_hallucinate: list[str] | None = None,
) -> PromptCase:
    return PromptCase(
        id=id,
        prompt="test prompt",
        expected_modules=[],
        expected_functions=expected_functions or [],
        must_not_hallucinate=must_not_hallucinate or [],
    )


# --- check_resolution ---


def test_check_resolution_returns_result(  # noqa: D103
) -> None:
    case = _make_case(expected_functions=["ntp.set_servers"])
    result = check_resolution(case, _KNOWN)
    assert isinstance(result, ResolutionResult)


def test_check_resolution_case_id_preserved() -> None:
    case = _make_case(id="my-id", expected_functions=["ntp.set_servers"])
    result = check_resolution(case, _KNOWN)
    assert result.case_id == "my-id"


def test_check_resolution_all_resolved() -> None:
    case = _make_case(expected_functions=["ntp.set_servers", "grains.get"])
    result = check_resolution(case, _KNOWN)
    assert result.unresolved == []
    assert set(result.resolved) == {"ntp.set_servers", "grains.get"}


def test_check_resolution_all_unresolved() -> None:
    case = _make_case(expected_functions=["fake.function", "ghost.call"])
    result = check_resolution(case, _KNOWN)
    assert set(result.unresolved) == {"fake.function", "ghost.call"}
    assert result.resolved == []


def test_check_resolution_partial() -> None:
    case = _make_case(expected_functions=["ntp.set_servers", "ghost.call"])
    result = check_resolution(case, _KNOWN)
    assert "ntp.set_servers" in result.resolved
    assert "ghost.call" in result.unresolved


def test_check_resolution_empty_expected_functions() -> None:
    case = _make_case(expected_functions=[])
    result = check_resolution(case, _KNOWN)
    assert result.resolved == []
    assert result.unresolved == []


def test_check_resolution_must_not_hallucinate_not_in_expected() -> None:
    """must_not_hallucinate list does not affect resolution of expected_functions."""
    case = _make_case(
        expected_functions=["ntp.set_servers"],
        must_not_hallucinate=["ntp.configure_server"],
    )
    result = check_resolution(case, _KNOWN)
    assert result.unresolved == []


# --- compute_metrics ---


def test_compute_metrics_returns_dict() -> None:
    result = ResolutionResult(
        case_id="c1",
        expected_functions=["ntp.set_servers"],
        resolved=["ntp.set_servers"],
        unresolved=[],
    )
    metrics = compute_metrics([result])
    assert isinstance(metrics, dict)


def test_compute_metrics_has_required_keys() -> None:
    result = ResolutionResult(
        case_id="c1",
        expected_functions=[],
        resolved=[],
        unresolved=[],
    )
    metrics = compute_metrics([result])
    assert "unresolved_function_rate" in metrics
    assert "validation_pass_rate" in metrics
    assert "total_cases" in metrics
    assert "total_functions" in metrics


def test_compute_metrics_perfect_resolution() -> None:
    result = ResolutionResult(
        case_id="c1",
        expected_functions=["ntp.set_servers"],
        resolved=["ntp.set_servers"],
        unresolved=[],
    )
    metrics = compute_metrics([result])
    assert metrics["unresolved_function_rate"] == 0.0
    assert metrics["validation_pass_rate"] == 1.0


def test_compute_metrics_all_unresolved() -> None:
    result = ResolutionResult(
        case_id="c1",
        expected_functions=["fake.fn"],
        resolved=[],
        unresolved=["fake.fn"],
    )
    metrics = compute_metrics([result])
    assert metrics["unresolved_function_rate"] == 1.0
    assert metrics["validation_pass_rate"] == 0.0


def test_compute_metrics_partial() -> None:
    r1 = ResolutionResult("c1", ["a", "b"], ["a"], ["b"])
    r2 = ResolutionResult("c2", ["c"], ["c"], [])
    metrics = compute_metrics([r1, r2])
    # 1 unresolved / 3 total functions
    assert abs(metrics["unresolved_function_rate"] - 1 / 3) < 1e-9
    # 1 passing case (c2) / 2 total cases
    assert abs(metrics["validation_pass_rate"] - 0.5) < 1e-9


def test_compute_metrics_empty_list() -> None:
    metrics = compute_metrics([])
    assert metrics["unresolved_function_rate"] == 0.0
    assert metrics["validation_pass_rate"] == 1.0
    assert metrics["total_cases"] == 0


def test_compute_metrics_case_with_no_expected_functions_passes() -> None:
    """A case with no expected_functions counts as passing."""
    result = ResolutionResult("c1", [], [], [])
    metrics = compute_metrics([result])
    assert metrics["validation_pass_rate"] == 1.0


# --- load_known_functions ---


def test_load_known_functions_returns_set(tmp_path: Path) -> None:
    f = tmp_path / "sys_list_functions.json"
    f.write_text(json.dumps(["ntp.set_servers", "grains.get"]))
    known = load_known_functions(f)
    assert isinstance(known, set)


def test_load_known_functions_contains_all(tmp_path: Path) -> None:
    fns = ["ntp.set_servers", "grains.get", "pillar.get"]
    f = tmp_path / "sys_list_functions.json"
    f.write_text(json.dumps(fns))
    known = load_known_functions(f)
    assert known == set(fns)


def test_load_known_functions_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "sys_list_functions.json"
    f.write_text("[]")
    assert load_known_functions(f) == set()


def test_load_known_functions_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_known_functions(tmp_path / "missing.json")
