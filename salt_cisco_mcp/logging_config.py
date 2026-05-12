import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog

from salt_cisco_mcp.config import Settings

_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _make_redact_processor(
    redact_keys: list[str],
) -> Callable[[Any, str, dict[str, Any]], dict[str, Any]]:
    lower_keys = frozenset(k.lower() for k in redact_keys)

    def _processor(_logger: Any, _method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        for key in list(event_dict):
            if isinstance(key, str) and key.lower() in lower_keys:
                event_dict[key] = "***"
        return event_dict

    return _processor


def configure_logging(settings: Settings) -> None:
    level = _LEVEL_MAP[settings.logging.level]

    handler: logging.Handler
    if settings.paths.log_file and settings.server.transport != "stdio":
        log_path = Path(settings.paths.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(settings.paths.log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setLevel(level)
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)

    redact_proc = _make_redact_processor(settings.security.redact_keys)

    processors: list[Any]
    structlog.reset_defaults()
    if settings.logging.format == "json":
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            redact_proc,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.stdlib.add_log_level,
            structlog.processors.format_exc_info,
            redact_proc,
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
