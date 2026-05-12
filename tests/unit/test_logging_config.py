import logging

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.logging_config import configure_logging


def test_configure_logging_does_not_raise() -> None:
    configure_logging(Settings())


def test_configure_logging_sets_up_handler() -> None:
    s = Settings()
    configure_logging(s)
    root = logging.getLogger()
    assert len(root.handlers) >= 1
