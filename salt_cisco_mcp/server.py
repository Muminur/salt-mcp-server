"""FastMCP server instance, AppState, and lifespan for salt-cisco-mcp."""

from __future__ import annotations

import logging
import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp import FastMCP

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.salt_master.adapter import SaltCallAdapter
from salt_cisco_mcp.salt_master.module_introspect import FunctionCache

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
    adapter: SaltCallAdapter | None = field(default=None)
    function_cache: FunctionCache | None = field(default=None)


def _make_lifespan(settings: Settings) -> Any:
    """Return a lifespan context manager bound to *settings*."""

    @asynccontextmanager
    async def _lifespan(app: FastMCP[AppState]) -> AsyncGenerator[AppState, None]:
        # Verify salt-call is reachable
        salt_call_path = settings.salt_master.salt_call_path
        salt_call_found = shutil.which(salt_call_path)
        if salt_call_found:
            logger.info("salt-call verified", extra={"path": salt_call_found})
        else:
            logger.warning(
                "salt-call not found on PATH",
                extra={"configured": salt_call_path},
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

        # Create Salt adapter (best-effort; tools degrade gracefully if unavailable)
        adapter: SaltCallAdapter | None = None
        function_cache: FunctionCache | None = None
        if salt_call_found:
            adapter = SaltCallAdapter(
                salt_call_cmd=[salt_call_path],
                salt_key_cmd=[settings.salt_master.salt_key_path],
                timeout=settings.salt_master.command_timeout_s,
            )
            function_cache = FunctionCache(adapter)

        try:
            yield AppState(
                store=store,
                settings=settings,
                adapter=adapter,
                function_cache=function_cache,
            )
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

    # Register docs tools
    from salt_cisco_mcp.tools import get_doc, list_modules, live_fetch, search_docs

    search_docs.register(mcp, settings)
    get_doc.register(mcp, settings)
    list_modules.register(mcp, settings)
    live_fetch.register(mcp, settings)

    # Register master tools
    from salt_cisco_mcp.tools import (
        confirm_function_exists,
        get_grains,
        get_pillar,
        list_loaded_functions,
        list_minions,
    )

    list_minions.register(mcp, settings)
    get_grains.register(mcp, settings)
    get_pillar.register(mcp, settings)
    list_loaded_functions.register(mcp, settings)
    confirm_function_exists.register(mcp, settings)

    # Register docs resources
    from salt_cisco_mcp.resources import salt_docs as salt_docs_resources

    salt_docs_resources.register(mcp, settings)

    # Register master resources
    from salt_cisco_mcp.resources import salt_master as salt_master_resources

    salt_master_resources.register(mcp, settings)

    return mcp
