"""FastMCP server instance, AppState, and lifespan for salt-cisco-mcp."""

from __future__ import annotations

import logging
import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
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


@dataclass
class AppState:
    """Lifespan state shared across all tool handlers."""

    store: DocStore
    settings: Settings


def _make_lifespan(settings: Settings) -> Any:
    """Return a lifespan context manager bound to *settings*."""

    @asynccontextmanager
    async def _lifespan(app: FastMCP[AppState]) -> AsyncGenerator[AppState, None]:
        # Verify salt-call is reachable
        salt_call_found = shutil.which(settings.salt_master.salt_call_path)
        if salt_call_found:
            logger.info("salt-call verified", extra={"path": salt_call_found})
        else:
            logger.warning(
                "salt-call not found on PATH",
                extra={"configured": settings.salt_master.salt_call_path},
            )

        # Lazy-load embeddings availability check
        if settings.retrieval.embeddings.enabled:
            try:
                import fastembed  # type: ignore[import-not-found]  # noqa: F401

                logger.info("fastembed available; vector search enabled")
            except ImportError:
                logger.info("fastembed not installed; BM25-only search active")

        # Open DocStore
        store = DocStore(settings.paths.doc_db)
        store.init_schema()
        logger.info("DocStore opened", extra={"db": settings.paths.doc_db})
        try:
            yield AppState(store=store, settings=settings)
        finally:
            store.close()
            logger.info("DocStore closed")

    return _lifespan


def create_server(settings: Settings | None = None) -> FastMCP[AppState]:
    """Create and return the FastMCP server instance with all tools registered."""
    if settings is None:
        settings = Settings()

    mcp: FastMCP[AppState] = FastMCP(
        name="salt-cisco-mcp",
        instructions=_INSTRUCTIONS,
        lifespan=_make_lifespan(settings),
        host=settings.server.http_host,
        port=settings.server.http_port,
    )

    # Register tools
    from salt_cisco_mcp.tools import get_doc, list_modules, live_fetch, search_docs

    search_docs.register(mcp, settings)
    get_doc.register(mcp, settings)
    list_modules.register(mcp, settings)
    live_fetch.register(mcp, settings)

    return mcp
