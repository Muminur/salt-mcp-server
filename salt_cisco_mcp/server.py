"""FastMCP server instance and lifespan for salt-cisco-mcp."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.docs.store import DocStore

logger = logging.getLogger(__name__)

_INSTRUCTIONS = (
    "Offline-first MCP server for Salt 3007 Cisco IOS/IOS-XR/NX-OS automation. "
    "Always call search_docs before writing any Salt code. "
    "Every doc-derived answer must carry a citation tuple "
    "{module, function, anchor_url, doc_hash}."
)


def _make_lifespan(settings: Settings) -> Any:
    """Return a lifespan context manager bound to *settings*."""

    @asynccontextmanager
    async def _lifespan(app: FastMCP[None]) -> AsyncGenerator[None, None]:
        store = DocStore(settings.paths.doc_db)
        store.init_schema()
        logger.info("DocStore opened", extra={"db": settings.paths.doc_db})
        try:
            yield
        finally:
            store.close()
            logger.info("DocStore closed")

    return _lifespan


def create_server(settings: Settings | None = None) -> FastMCP[None]:
    """Create and return the FastMCP server instance."""
    if settings is None:
        settings = Settings()
    return FastMCP(
        name="salt-cisco-mcp",
        instructions=_INSTRUCTIONS,
        lifespan=_make_lifespan(settings),
        host=settings.server.http_host,
        port=settings.server.http_port,
    )
