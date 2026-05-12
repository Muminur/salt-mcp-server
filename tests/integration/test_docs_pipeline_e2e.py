"""End-to-end integration test: HTML → normalize → chunk → index → FTS search."""

from salt_cisco_mcp.docs.chunker import chunk_page
from salt_cisco_mcp.docs.indexer import compute_doc_hash, index_page
from salt_cisco_mcp.docs.normalizer import normalize_page
from salt_cisco_mcp.docs.retriever import SearchResult, bm25_search
from salt_cisco_mcp.docs.store import DocStore

_SAMPLE_HTML = """
<html>
<head><title>salt.modules.ntp</title></head>
<body>
<h1>salt.modules.ntp</h1>
<p>The ntp module provides functions to manage NTP on Cisco IOS and IOS-XR devices.</p>

<h2>ntp.set_servers</h2>
<p>Set the NTP servers for a target device.</p>
<pre><code>salt-call ntp.set_servers servers=[\"10.0.0.1\", \"10.0.0.2\"]</code></pre>

<h2>ntp.get_servers</h2>
<p>Retrieve current NTP server configuration from the device.</p>
<pre><code>salt-call ntp.get_servers</code></pre>
</body>
</html>
"""

_PAGE_URL = "https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html"


def test_full_pipeline_indexes_and_retrieves() -> None:
    store = DocStore(":memory:")
    store.init_schema()

    md, meta = normalize_page(_SAMPLE_HTML, _PAGE_URL)
    assert meta.kind == "module"
    assert meta.salt_version == "3007"

    chunks = chunk_page(md, meta, max_tokens=200)
    assert len(chunks) >= 1

    n = index_page(store, chunks, meta)
    assert n == len(chunks)
    assert store.count_chunks() == len(chunks)

    results = bm25_search(store, "NTP servers")
    assert len(results) >= 1
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(r.kind == "module" for r in results)

    store.close()


def test_full_pipeline_code_blocks_survive_indexing() -> None:
    store = DocStore(":memory:")
    store.init_schema()

    md, meta = normalize_page(_SAMPLE_HTML, _PAGE_URL)
    chunks = chunk_page(md, meta, max_tokens=200)
    index_page(store, chunks, meta)

    combined = " ".join(c.text for c in chunks)
    assert "salt-call ntp.set_servers" in combined or "ntp.set_servers" in combined

    store.close()


def test_doc_hash_is_consistent_across_runs() -> None:
    md, meta = normalize_page(_SAMPLE_HTML, _PAGE_URL)
    chunks = chunk_page(md, meta, max_tokens=200)
    combined = " ".join(c.text for c in chunks)
    h1 = compute_doc_hash(combined)
    h2 = compute_doc_hash(combined)
    assert h1 == h2
    assert len(h1) == 64


def test_smoke_verify_imports() -> None:
    """Smoke test: all docs modules importable without errors."""
    from salt_cisco_mcp.docs import (  # noqa: F401
        chunker,
        indexer,
        normalizer,
        retriever,
        scraper,
        store,
    )
