"""Tests validating the v1.0 release criteria."""
from __future__ import annotations

import importlib.metadata
import pathlib
import re

_ROOT = pathlib.Path(__file__).parent.parent
_CASES = _ROOT / "tests" / "hallucination" / "cases"


def test_version_is_1_0_0() -> None:
    """Package version must be exactly 1.0.0 for v1.0 release."""
    from salt_cisco_mcp import __version__

    assert __version__ == "1.0.0", f"Expected 1.0.0, got {__version__}"


def test_metadata_version_matches_package() -> None:
    """Installed metadata version must match __version__."""
    from salt_cisco_mcp import __version__

    meta_version = importlib.metadata.version("salt-cisco-mcp")
    assert meta_version == __version__


def test_hallucination_corpus_has_at_least_100_cases() -> None:
    """Hallucination corpus must have ≥ 100 YAML case files."""
    cases = sorted(_CASES.glob("case_*.yaml"))
    assert len(cases) >= 100, (
        f"Hallucination corpus has {len(cases)} cases; need ≥ 100"
    )


def test_hallucination_cases_are_valid_yaml() -> None:
    """All hallucination case files must be valid YAML with required fields."""
    import yaml

    cases = sorted(_CASES.glob("case_*.yaml"))
    assert len(cases) >= 100

    for path in cases:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path.name}: expected dict"
        assert "id" in data, f"{path.name}: missing 'id'"
        assert "prompt" in data, f"{path.name}: missing 'prompt'"
        assert "expected_modules" in data, f"{path.name}: missing 'expected_modules'"
        assert isinstance(data["expected_modules"], list), (
            f"{path.name}: 'expected_modules' must be a list"
        )


def test_changelog_has_v1_0_0_entry() -> None:
    """CHANGELOG.md must contain a v1.0.0 release entry."""
    cl = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "1.0.0" in cl, "CHANGELOG.md must have a 1.0.0 entry"


def test_changelog_v1_0_0_has_date() -> None:
    """v1.0.0 changelog entry must include a date."""
    cl = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(r"1\.0\.0.*20\d{2}-\d{2}-\d{2}", cl) or re.search(
        r"20\d{2}-\d{2}-\d{2}.*1\.0\.0", cl
    ), "CHANGELOG.md 1.0.0 entry must contain a date (YYYY-MM-DD)"


def test_ideas_md_exists() -> None:
    """IDEAS.md must exist as a post-v1 backlog file."""
    assert (_ROOT / "IDEAS.md").exists(), "IDEAS.md must exist"


def test_ideas_md_mentions_junos_or_eos() -> None:
    """IDEAS.md must mention post-v1 platform expansion (Junos or EOS)."""
    content = (_ROOT / "IDEAS.md").read_text(encoding="utf-8")
    assert "junos" in content.lower() or "eos" in content.lower() or "arista" in content.lower()


def test_readme_mentions_salt_cisco_mcp() -> None:
    """README.md must reference salt-cisco-mcp prominently."""
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert "salt-cisco-mcp" in readme.lower()


def test_readme_has_quickstart() -> None:
    """README.md must have a quickstart or install section."""
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    lower = readme.lower()
    assert "quickstart" in lower or "install" in lower or "getting started" in lower


def test_g1_hallucination_ci_gate_present() -> None:
    """G1: CI gate for hallucination rates must be tested."""
    gate_file = _ROOT / "tests" / "hallucination" / "test_ci_gate.py"
    assert gate_file.exists()
    content = gate_file.read_text(encoding="utf-8")
    assert "unresolved_function_rate" in content or "validation_pass_rate" in content


def test_g3_air_gap_tests_present() -> None:
    """G3: Air-gap (offline) test suite must be present."""
    airgap = _ROOT / "tests" / "integration" / "test_air_gap.py"
    assert airgap.exists()


def test_g5_rss_gate_present() -> None:
    """G5: RSS < 100 MB gate must be tested."""
    rss_test = _ROOT / "tests" / "performance" / "test_rss.py"
    assert rss_test.exists()
    content = rss_test.read_text(encoding="utf-8")
    assert "100" in content


def test_g6_transports_present() -> None:
    """G6: Both stdio and HTTP transports must be implemented."""
    transports = _ROOT / "salt_cisco_mcp" / "transports.py"
    assert transports.exists()
    content = transports.read_text(encoding="utf-8")
    assert "stdio" in content.lower()
    assert "http" in content.lower()


def test_g7_cisco_pillar_schemas_present() -> None:
    """G7: Cisco device pillar schemas must be present."""
    schemas = _ROOT / "salt_cisco_mcp" / "validate" / "pillar_schema.py"
    assert schemas.exists()
    content = schemas.read_text(encoding="utf-8")
    assert "napalm" in content.lower() or "nxos" in content.lower()
