from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent


def test_makefile_exists_with_targets() -> None:
    makefile = REPO_ROOT / "Makefile"
    assert makefile.exists()
    content = makefile.read_text()
    for target in ("install", "test", "lint", "typecheck", "fmt", "scrape", "serve"):
        assert target in content


def test_ci_workflow_exists_and_valid() -> None:
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci.exists()
    content = ci.read_text()
    parsed = yaml.safe_load(content)
    assert parsed is not None
    for needle in ("ubuntu-latest", "python-version", "ruff", "mypy", "pytest"):
        assert needle in content


def test_license_exists() -> None:
    lic = REPO_ROOT / "LICENSE"
    assert lic.exists()
    content = lic.read_text()
    assert "Apache-2.0" in content or "Apache License" in content


def test_readme_has_quickstart_content() -> None:
    readme = REPO_ROOT / "README.md"
    assert readme.exists()
    content = readme.read_text()
    keywords = ["install", "quickstart", "salt-cisco-mcp", "pip"]
    matches = sum(1 for kw in keywords if kw in content)
    assert matches >= 3


def test_changelog_exists() -> None:
    assert (REPO_ROOT / "CHANGELOG.md").exists()


def test_editorconfig_exists() -> None:
    assert (REPO_ROOT / ".editorconfig").exists()


def test_python_version_file() -> None:
    pv = REPO_ROOT / ".python-version"
    assert pv.exists()
    assert pv.read_text().strip() == "3.11"


def test_docs_present_at_repo_root() -> None:
    for f in ("CLAUDE.md", "PLANNING.md", "TASKS.md", "PRD-salt-cisco-mcp.md"):
        assert (REPO_ROOT / f).exists(), f"{f} is missing from repo root"


def test_precommit_config_exists() -> None:
    pc = REPO_ROOT / ".pre-commit-config.yaml"
    assert pc.exists()
    content = pc.read_text()
    assert "ruff" in content
    assert "trailing-whitespace" in content
