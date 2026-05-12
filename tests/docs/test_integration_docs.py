"""Validates that integration doc files exist with expected content."""
from __future__ import annotations

import pathlib

import pytest

_ROOT = pathlib.Path(__file__).parent.parent.parent
_INTEGRATIONS = _ROOT / "docs" / "integrations"


@pytest.mark.parametrize(
    "fname",
    ["claude-code.md", "codex.md", "copilot.md", "continue.md", "cursor.md"],
)
def test_integration_doc_exists(fname: str) -> None:
    assert (_INTEGRATIONS / fname).exists(), f"docs/integrations/{fname} must exist"


def test_claude_code_doc_mentions_server() -> None:
    content = (_INTEGRATIONS / "claude-code.md").read_text(encoding="utf-8")
    assert "salt-cisco-mcp" in content


def test_claude_code_doc_has_config_snippet() -> None:
    content = (_INTEGRATIONS / "claude-code.md").read_text(encoding="utf-8")
    assert "mcpServers" in content or "mcp" in content.lower()


def test_copilot_doc_uses_http_transport() -> None:
    content = (_INTEGRATIONS / "copilot.md").read_text(encoding="utf-8")
    assert "http" in content.lower() or "streamable" in content.lower()


def test_codex_doc_has_config_snippet() -> None:
    content = (_INTEGRATIONS / "codex.md").read_text(encoding="utf-8")
    assert "salt-cisco-mcp" in content


def test_install_md_exists() -> None:
    assert (_ROOT / "docs" / "install.md").exists()


def test_runbook_md_exists() -> None:
    assert (_ROOT / "docs" / "runbook.md").exists()


def test_install_md_covers_prerequisites() -> None:
    content = (_ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    assert any(
        word in content.lower()
        for word in ("prerequisite", "requirement", "python", "salt-call")
    )


def test_install_md_covers_permissions() -> None:
    content = (_ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    lower = content.lower()
    assert "permission" in lower or "chmod" in lower or "chown" in lower


def test_runbook_md_covers_rescrape() -> None:
    content = (_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    assert "scrape" in content.lower()


def test_runbook_md_covers_token_rotation() -> None:
    content = (_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    assert "token" in content.lower()


def test_runbook_md_covers_index_recovery() -> None:
    content = (_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    lower = content.lower()
    assert "index" in lower or "corrupt" in lower or "recover" in lower
