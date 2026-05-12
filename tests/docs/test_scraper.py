"""Tests for the async scraper (mocked HTTP — no real network calls)."""
from __future__ import annotations

import httpx
import pytest

from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.docs.scraper import CrawlStats, _is_doc_page, compute_url_hash, scrape_docs


def test_is_doc_page_accepts_valid_html() -> None:
    assert _is_doc_page("https://docs.saltproject.io/en/3007/topics/foo.html")


def test_is_doc_page_rejects_other_host() -> None:
    assert not _is_doc_page("https://example.com/en/3007/topics/foo.html")


def test_is_doc_page_rejects_non_3007_path() -> None:
    assert not _is_doc_page("https://docs.saltproject.io/en/3006/topics/foo.html")


def test_compute_url_hash_is_16_hex_chars() -> None:
    h = compute_url_hash("https://docs.saltproject.io/en/3007/contents.html")
    assert len(h) == 16
    assert all(c in "0123456789abcdef" for c in h)


def test_crawl_stats_defaults_are_zero() -> None:
    stats = CrawlStats()
    assert stats.pages_fetched == 0
    assert stats.pages_indexed == 0
    assert stats.chunks_written == 0
    assert stats.errors == 0


@pytest.mark.anyio
async def test_scrape_docs_with_mock_transport(tmp_path: pytest.TempPathFactory) -> None:
    """Full scrape_docs call against a mock HTTP transport — no network."""
    seed_html = (
        "<html><head><title>Salt 3007 Docs</title></head>"
        "<body><h1>Contents</h1><p>Welcome to Salt documentation.</p></body></html>"
    )

    class _MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=seed_html.encode(), headers={})

    settings = Settings()
    db_path = str(tmp_path / "test_scrape.db")  # type: ignore[operator]
    client = httpx.AsyncClient(transport=_MockTransport())

    stats = await scrape_docs(
        settings,
        db_path,
        seed_url="https://docs.saltproject.io/en/3007/contents.html",
        client=client,
    )
    await client.aclose()

    assert stats.pages_fetched >= 1
    assert stats.chunks_written >= 1
    assert stats.errors == 0
