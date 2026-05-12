"""Async crawler for docs.saltproject.io/en/3007."""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import structlog

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.docs.chunker import chunk_page
from salt_cisco_mcp.docs.indexer import index_page
from salt_cisco_mcp.docs.normalizer import normalize_page
from salt_cisco_mcp.docs.store import DocStore

_SEED_URL = "https://docs.saltproject.io/en/3007/contents.html"
_ALLOWED_HOST = "docs.saltproject.io"
_USER_AGENT = "salt-cisco-mcp/1.0 (offline indexer)"

log = structlog.get_logger(__name__)


@dataclass
class CrawlStats:
    pages_fetched: int = 0
    pages_indexed: int = 0
    chunks_written: int = 0
    errors: int = 0


@dataclass
class _ETagCache:
    """In-memory ETag → body cache to avoid re-downloading unchanged pages."""

    _store: dict[str, tuple[str, bytes]] = field(default_factory=dict)

    def get_etag(self, url: str) -> str | None:
        entry = self._store.get(url)
        return entry[0] if entry else None

    def get_body(self, url: str) -> bytes | None:
        entry = self._store.get(url)
        return entry[1] if entry else None

    def set(self, url: str, etag: str, body: bytes) -> None:
        self._store[url] = (etag, body)


def _is_doc_page(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != _ALLOWED_HOST:
        return False
    if "/en/3007/" not in parsed.path:
        return False
    path = parsed.path.lower()
    return path.endswith(".html") or path.endswith("/")


def _extract_links(html: str, base_url: str) -> list[str]:
    """Extract href links from HTML and resolve them against base_url."""
    import re

    hrefs = re.findall(r'href=["\']([^"\'#][^"\']*)["\']', html)
    links: list[str] = []
    for href in hrefs:
        resolved = urljoin(base_url, href)
        if _is_doc_page(resolved):
            links.append(resolved.split("#")[0])
    return links


def _load_robots(base_url: str) -> RobotFileParser:
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        pass
    return rp


async def scrape_docs(
    settings: Settings,
    db_path: str,
    *,
    seed_url: str = _SEED_URL,
    client: httpx.AsyncClient | None = None,
) -> CrawlStats:
    """Crawl docs.saltproject.io and index pages into the SQLite store.

    Respects robots.txt, applies per-request rate limiting, and uses
    ETag-based caching to skip unchanged pages on re-scrapes.
    """
    stats = CrawlStats()
    store = DocStore(db_path)
    store.init_schema()

    rps = max(1, settings.scrape.rps)
    min_delay = 1.0 / rps
    max_pages = settings.scrape.max_pages

    etag_cache = _ETagCache()
    visited: set[str] = set()
    queue: deque[str] = deque([seed_url])

    robots = _load_robots(seed_url)

    close_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            headers={"User-Agent": settings.network.user_agent or _USER_AGENT},
            timeout=settings.network.request_timeout_s,
            follow_redirects=settings.scrape.follow_redirects,
        )

    try:
        while queue and stats.pages_fetched < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            if not robots.can_fetch(_USER_AGENT, url):
                log.debug("robots_blocked", url=url)
                continue

            visited.add(url)
            t0 = time.monotonic()

            headers: dict[str, str] = {}
            cached_etag = etag_cache.get_etag(url)
            if cached_etag:
                headers["If-None-Match"] = cached_etag

            try:
                resp = await client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                log.warning("fetch_error", url=url, error=str(exc))
                stats.errors += 1
                continue

            if resp.status_code == 304:
                cached_body = etag_cache.get_body(url)
                if cached_body is not None:
                    html = cached_body.decode("utf-8", errors="replace")
                    stats.pages_fetched += 1
                else:
                    continue
            elif resp.status_code == 200:
                body = resp.content
                etag = resp.headers.get("ETag", "")
                if etag:
                    etag_cache.set(url, etag, body)
                html = body.decode("utf-8", errors="replace")
                stats.pages_fetched += 1

                links = _extract_links(html, url)
                for link in links:
                    if link not in visited:
                        queue.append(link)
            else:
                log.warning("bad_status", url=url, status=resp.status_code)
                stats.errors += 1
                continue

            md, meta = normalize_page(html, url)
            if md.strip():
                chunks = chunk_page(md, meta, max_tokens=settings.retrieval.default_max_tokens)
                n = index_page(store, chunks, meta)
                stats.chunks_written += n
                stats.pages_indexed += 1
                log.info("indexed", url=url, chunks=n)

            elapsed = time.monotonic() - t0
            delay = max(0.0, min_delay - elapsed)
            if delay > 0:
                await asyncio.sleep(delay)

    finally:
        if close_client:
            await client.aclose()
        store.close()

    return stats


def compute_url_hash(url: str) -> str:
    """Stable short ID for a URL (first 16 hex chars of SHA-256)."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
