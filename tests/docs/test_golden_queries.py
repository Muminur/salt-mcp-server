"""Golden-query regression tests for BM25 retrieval quality."""
from __future__ import annotations

import pathlib

import pytest
import yaml

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.retriever import bm25_search
from salt_cisco_mcp.docs.store import DocStore

_CASES_PATH = pathlib.Path(__file__).parent / "golden_queries.yaml"

_BASE_URL = "https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules."


def _build_store(chunk_spec: dict[str, str]) -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    anchor = chunk_spec["anchor"]
    heading = chunk_spec["heading"]
    text = chunk_spec["text"]
    kind = chunk_spec["kind"]
    url = _BASE_URL + heading.split(".")[0] + ".html"
    chunk = Chunk(
        text=text,
        heading=heading,
        anchor=anchor,
        token_count=len(text.split()),
        kind=kind,
    )
    meta = PageMeta(
        title=heading,
        anchor=anchor,
        breadcrumb=f"Salt 3007 > {heading}",
        kind=kind,
        salt_version="3007",
        url=url,
    )
    store.upsert_chunk(chunk, meta, doc_hash=f"golden-{anchor}")
    return store


def _load_cases() -> list[dict[str, object]]:
    data = yaml.safe_load(_CASES_PATH.read_text(encoding="utf-8"))
    return list(data["queries"])


@pytest.mark.parametrize("case", _load_cases(), ids=[c["id"] for c in _load_cases()])
def test_golden_query_top1_matches_expected_anchor(case: dict[str, object]) -> None:
    """BM25 search for each golden query returns a result with the expected anchor fragment."""
    query = str(case["query"])
    fragment = str(case["expected_anchor_fragment"])
    chunk_spec = dict(case["chunk"])  # type: ignore[arg-type]

    store = _build_store(chunk_spec)
    results = bm25_search(store, query, limit=5)
    store.close()

    assert results, f"[{case['id']}] No results for query: {query!r}"
    top_anchor = results[0].anchor
    assert fragment in top_anchor, (
        f"[{case['id']}] Expected {fragment!r} in top-1 anchor {top_anchor!r} "
        f"for query {query!r}"
    )
