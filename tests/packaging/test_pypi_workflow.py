"""Validates the PyPI publish GitHub Actions workflow."""
from __future__ import annotations

import pathlib

_ROOT = pathlib.Path(__file__).parent.parent.parent
_WF = _ROOT / ".github" / "workflows" / "publish.yml"


def test_publish_workflow_exists() -> None:
    assert _WF.exists(), ".github/workflows/publish.yml must exist"


def test_publish_workflow_triggers_on_release() -> None:
    # PyYAML parses bare `on:` as True (YAML 1.1 boolean); check content directly
    content = _WF.read_text(encoding="utf-8")
    assert "release:" in content, "workflow must trigger on release events"


def test_publish_workflow_uses_trusted_publisher() -> None:
    content = _WF.read_text(encoding="utf-8")
    assert "pypa/gh-action-pypi-publish" in content


def test_publish_workflow_has_id_token_write_permission() -> None:
    content = _WF.read_text(encoding="utf-8")
    assert "id-token: write" in content


def test_publish_workflow_has_build_step() -> None:
    content = _WF.read_text(encoding="utf-8")
    assert "build" in content.lower()


def test_publish_workflow_has_environment() -> None:
    content = _WF.read_text(encoding="utf-8")
    assert "environment:" in content
