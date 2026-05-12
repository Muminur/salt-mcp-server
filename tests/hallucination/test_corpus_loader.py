"""Tests for hallucination corpus loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from salt_cisco_mcp.hallucination.corpus_loader import PromptCase, load_corpus


def _write_case(tmp_path: Path, name: str, data: dict) -> Path:  # type: ignore[type-arg]
    p = tmp_path / name
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


_VALID_CASE = {
    "id": "case-001",
    "prompt": "How do I configure NTP on a Cisco IOS device with Salt?",
    "expected_modules": ["ntp"],
    "expected_functions": ["ntp.set_servers", "ntp.show_ntp_info"],
    "must_not_hallucinate": ["ntp.configure_server"],
}


def test_load_corpus_returns_list(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert isinstance(cases, list)


def test_load_corpus_single_case(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert len(cases) == 1


def test_load_corpus_returns_prompt_case_instances(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert isinstance(cases[0], PromptCase)


def test_load_corpus_parses_id(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert cases[0].id == "case-001"


def test_load_corpus_parses_prompt(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert "NTP" in cases[0].prompt


def test_load_corpus_parses_expected_modules(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert cases[0].expected_modules == ["ntp"]


def test_load_corpus_parses_expected_functions(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert "ntp.set_servers" in cases[0].expected_functions


def test_load_corpus_parses_must_not_hallucinate(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    cases = load_corpus(tmp_path)
    assert cases[0].must_not_hallucinate == ["ntp.configure_server"]


def test_load_corpus_empty_directory(tmp_path: Path) -> None:
    cases = load_corpus(tmp_path)
    assert cases == []


def test_load_corpus_multiple_files(tmp_path: Path) -> None:
    for i in range(3):
        data = dict(_VALID_CASE)
        data["id"] = f"case-{i:03d}"
        _write_case(tmp_path, f"case{i:03d}.yaml", data)
    cases = load_corpus(tmp_path)
    assert len(cases) == 3


def test_load_corpus_ignores_non_yaml_files(tmp_path: Path) -> None:
    _write_case(tmp_path, "case001.yaml", _VALID_CASE)
    (tmp_path / "README.md").write_text("# ignore me")
    (tmp_path / "notes.txt").write_text("notes")
    cases = load_corpus(tmp_path)
    assert len(cases) == 1


def test_load_corpus_raises_on_missing_id(tmp_path: Path) -> None:
    bad = dict(_VALID_CASE)
    del bad["id"]
    _write_case(tmp_path, "bad.yaml", bad)
    with pytest.raises(ValueError, match="id"):
        load_corpus(tmp_path)


def test_load_corpus_raises_on_missing_prompt(tmp_path: Path) -> None:
    bad = dict(_VALID_CASE)
    del bad["prompt"]
    _write_case(tmp_path, "bad.yaml", bad)
    with pytest.raises(ValueError, match="prompt"):
        load_corpus(tmp_path)


def test_load_corpus_default_empty_lists(tmp_path: Path) -> None:
    minimal = {"id": "case-min", "prompt": "minimal prompt"}
    _write_case(tmp_path, "minimal.yaml", minimal)
    cases = load_corpus(tmp_path)
    assert cases[0].expected_modules == []
    assert cases[0].expected_functions == []
    assert cases[0].must_not_hallucinate == []


def test_load_corpus_sorted_by_id(tmp_path: Path) -> None:
    for i in [3, 1, 2]:
        data = dict(_VALID_CASE)
        data["id"] = f"case-{i:03d}"
        _write_case(tmp_path, f"case{i}.yaml", data)
    cases = load_corpus(tmp_path)
    ids = [c.id for c in cases]
    assert ids == sorted(ids)
