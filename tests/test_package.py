import re


def test_import():
    import salt_cisco_mcp  # noqa: F401


def test_version_is_semver_string():
    import salt_cisco_mcp
    assert isinstance(salt_cisco_mcp.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", salt_cisco_mcp.__version__)


def test_cli_main_callable():
    from salt_cisco_mcp.cli import main
    assert callable(main)
