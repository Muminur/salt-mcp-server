"""Transport selection for salt-cisco-mcp: stdio or streamable-http."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import anyio
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.server import create_server

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces a static bearer token on every request."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth = request.headers.get("Authorization", "")
        if auth == f"Bearer {self._token}":
            return await call_next(request)
        return Response("Unauthorized", status_code=401, media_type="text/plain")


def _read_bearer_token(settings: Settings) -> str | None:
    """Return the bearer token from the configured file, or None if auth is disabled."""
    http_auth = settings.security.http_auth
    if http_auth.mode != "bearer":
        return None
    path = Path(http_auth.bearer_token_file)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def build_http_app(mcp: FastMCP[None], settings: Settings) -> ASGIApp:
    """Build the Starlette ASGI app, wrapping with bearer auth when configured."""
    base_app: ASGIApp = mcp.streamable_http_app()
    token = _read_bearer_token(settings)
    if token is not None:
        return BearerTokenMiddleware(base_app, token)
    return base_app


def run_server(settings: Settings) -> None:
    """Select and start the appropriate MCP transport.

    Blocks until the server shuts down.
    """
    mcp = create_server(settings)
    if settings.server.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        import uvicorn

        app = build_http_app(mcp, settings)

        async def _serve() -> None:
            config = uvicorn.Config(
                app,
                host=settings.server.http_host,
                port=settings.server.http_port,
            )
            server = uvicorn.Server(config)
            await server.serve()

        anyio.run(_serve)
