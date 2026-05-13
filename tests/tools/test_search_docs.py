"""Unit tests for search_docs tool logic."""

from __future__ import annotations

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.tools.search_docs import search_docs_logic

_URL = "https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html"

_META = PageMeta(
    title="salt.modules.ntp",
    anchor="#ntp",
    breadcrumb="Salt 3007 > Modules > ntp",
    kind="module",
    salt_version="3007",
    url=_URL,
)

_CHUNK = Chunk(
    text="NTP configuration for IOS devices. Use ntp.set_servers to configure NTP.",
    heading="ntp.set_servers",
    anchor="#ntp-set-servers-0",
    token_count=14,
    kind="module",
)


def _populated_store() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="deadbeef")
    return store


def test_search_docs_logic_returns_dict() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "NTP")
    assert isinstance(result, dict)
    store.close()


def test_search_docs_logic_has_required_top_level_keys() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "NTP")
    assert "results" in result
    assert "low_confidence" in result
    assert "total" in result
    store.close()


def test_search_docs_logic_result_items_have_citation_fields() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "NTP")
    assert len(result["results"]) >= 1
    r = result["results"][0]
    expected_fields = (
        "text",
        "anchor_url",
        "heading",
        "kind",
        "doc_hash",
        "module",
        "function",
    )
    for field in expected_fields:
        assert field in r, f"Citation field missing: {field}"
    store.close()


def test_search_docs_logic_anchor_url_combines_url_and_anchor() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "NTP")
    assert len(result["results"]) >= 1
    r = result["results"][0]
    assert r["anchor_url"].startswith("https://")
    assert "#" in r["anchor_url"]
    store.close()


def test_search_docs_logic_module_extracted_from_url() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "NTP")
    assert len(result["results"]) >= 1
    r = result["results"][0]
    assert "ntp" in r["module"].lower()
    store.close()


def test_search_docs_logic_empty_query_returns_empty() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "")
    assert result["results"] == []
    assert result["total"] == 0
    assert result["low_confidence"] is False
    store.close()


def test_search_docs_logic_enforces_token_budget() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    # Add multiple chunks with substantial text
    for i in range(5):
        c = Chunk(
            text=f"NTP server chunk {i} " + "word " * 30,
            heading=f"ntp.function{i}",
            anchor=f"#ntp-{i}",
            token_count=32,
            kind="module",
        )
        m = PageMeta(
            title="salt.modules.ntp",
            anchor=f"#ntp-{i}",
            breadcrumb="",
            kind="module",
            salt_version="3007",
            url=f"https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp{i}.html",
        )
        store.upsert_chunk(c, m, doc_hash=f"hash{i}")

    result_full = search_docs_logic(store, "NTP", top_k=10, token_budget=None)
    result_trimmed = search_docs_logic(store, "NTP", top_k=10, token_budget=40)
    assert len(result_trimmed["results"]) < len(result_full["results"])
    store.close()


def test_search_docs_logic_low_confidence_flag() -> None:
    store = _populated_store()
    # With very high threshold, any score should be low-confidence
    result = search_docs_logic(store, "NTP", low_confidence_threshold=9999.0)
    assert result["low_confidence"] is True
    store.close()


def test_search_docs_logic_high_confidence_when_threshold_is_zero() -> None:
    store = _populated_store()
    result = search_docs_logic(store, "NTP", low_confidence_threshold=0.0)
    assert result["low_confidence"] is False
    store.close()


def test_search_docs_logic_respects_top_k() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    for i in range(10):
        c = Chunk(
            text=f"NTP configuration item {i}",
            heading=f"ntp.item{i}",
            anchor=f"#ntp-item-{i}",
            token_count=4,
            kind="module",
        )
        m = PageMeta(
            title="salt.modules.ntp",
            anchor=f"#ntp-item-{i}",
            breadcrumb="",
            kind="module",
            salt_version="3007",
            url=f"https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp{i}.html",
        )
        store.upsert_chunk(c, m, doc_hash=f"hash{i}")

    result = search_docs_logic(store, "NTP", top_k=3)
    assert len(result["results"]) <= 3
    store.close()
