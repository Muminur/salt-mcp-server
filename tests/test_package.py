import importlib.metadata
import re


def test_import() -> None:
    import salt_cisco_mcp  # noqa: F401


def test_version_is_semver_string() -> None:
    import salt_cisco_mcp
    assert isinstance(salt_cisco_mcp.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.+\-]+)?", salt_cisco_mcp.__version__)


def test_cli_main_callable() -> None:
    from salt_cisco_mcp.cli import main
    assert callable(main)


def test_installed_metadata_version_matches_module() -> None:
    import salt_cisco_mcp
    assert importlib.metadata.version("salt-cisco-mcp") == salt_cisco_mcp.__version__
