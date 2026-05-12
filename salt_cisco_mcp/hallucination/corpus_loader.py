"""Hallucination regression corpus loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class PromptCase:
    id: str
    prompt: str
    expected_modules: list[str] = field(default_factory=list)
    expected_functions: list[str] = field(default_factory=list)
    must_not_hallucinate: list[str] = field(default_factory=list)


def _parse_case(data: object, source: Path) -> PromptCase:
    if not isinstance(data, dict):
        raise ValueError(f"{source}: YAML root must be a mapping")
    if "id" not in data:
        raise ValueError(f"{source}: missing required field 'id'")
    if "prompt" not in data:
        raise ValueError(f"{source}: missing required field 'prompt'")
    return PromptCase(
        id=str(data["id"]),
        prompt=str(data["prompt"]),
        expected_modules=list(data.get("expected_modules") or []),
        expected_functions=list(data.get("expected_functions") or []),
        must_not_hallucinate=list(data.get("must_not_hallucinate") or []),
    )


def load_corpus(cases_dir: Path) -> list[PromptCase]:
    """Load all YAML prompt cases from *cases_dir*, sorted by id."""
    cases: list[PromptCase] = []
    for yaml_file in sorted(cases_dir.glob("*.yaml")):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        cases.append(_parse_case(raw, yaml_file))
    return sorted(cases, key=lambda c: c.id)
