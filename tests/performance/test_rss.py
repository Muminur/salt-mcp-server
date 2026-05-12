"""Performance gate: idle RSS < 100 MB after DocStore init (measured in subprocess)."""
from __future__ import annotations

import subprocess
import sys

import psutil

from salt_cisco_mcp.docs.store import DocStore

_MAX_RSS_MB = 100

_RSS_SCRIPT = """\
import os, psutil

proc = psutil.Process(os.getpid())

from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta

store = DocStore(":memory:")
store.init_schema()

for i in range(1000):
    mod = f"module{i % 20}"
    text = f"config text {i} " + "word " * 10
    chunk = Chunk(text=text, heading=f"fn{i}", anchor=f"#fn-{i}",
                  token_count=12, kind="module")
    meta = PageMeta(title=f"salt.modules.{mod}", anchor=f"#fn-{i}", breadcrumb="",
                    kind="module", salt_version="3007",
                    url=f"https://docs.saltproject.io/en/3007/ref/modules/{mod}{i % 8}.html")
    store.upsert_chunk(chunk, meta, doc_hash=f"hash{i:06d}")

rss_mb = proc.memory_info().rss / (1024 * 1024)
print(f"{rss_mb:.1f}")
store.close()
"""


def test_idle_rss_under_100mb() -> None:
    """Fresh-process RSS with 1000-chunk DocStore must stay under 100 MB."""
    result = subprocess.run(
        [sys.executable, "-c", _RSS_SCRIPT],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, f"RSS script failed: {result.stderr.decode()}"
    rss_mb = float(result.stdout.decode().strip())
    assert rss_mb < _MAX_RSS_MB, (
        f"RSS {rss_mb:.1f} MB exceeds {_MAX_RSS_MB} MB gate after 1000-chunk store"
    )


def test_rss_does_not_grow_unbounded_across_queries() -> None:
    """RSS must not grow by more than 20 MB across 500 search_docs calls."""
    import os

    from salt_cisco_mcp.tools.search_docs import search_docs_logic

    proc = psutil.Process(os.getpid())
    rss_before_mb = proc.memory_info().rss / (1024 * 1024)

    fresh_store = DocStore(":memory:")
    fresh_store.init_schema()
    for i in range(500):
        search_docs_logic(fresh_store, f"query number {i}")
    fresh_store.close()

    rss_after_mb = proc.memory_info().rss / (1024 * 1024)
    growth_mb = rss_after_mb - rss_before_mb
    assert growth_mb < 20.0, (
        f"RSS grew by {growth_mb:.1f} MB over 500 queries (gate: 20 MB)"
    )
