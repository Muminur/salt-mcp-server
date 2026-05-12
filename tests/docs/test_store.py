from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore

_META = PageMeta(
    title="NTP Module",
    anchor="#ntp",
    breadcrumb="Salt 3007 > Modules > ntp",
    kind="module",
    salt_version="3007",
    url="https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html",
)

_CHUNK = Chunk(
    text="NTP configuration for IOS devices.",
    heading="NTP Module",
    anchor="#ntp-0",
    token_count=6,
    kind="module",
)


def test_store_init_creates_tables() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    store.close()


def test_store_upsert_and_retrieve() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    chunk_id = store.upsert_chunk(_CHUNK, _META, doc_hash="abc123")
    assert chunk_id > 0
    row = store.get_chunk_by_id(chunk_id)
    assert row is not None
    for key in ("text", "heading", "anchor", "kind", "doc_hash"):
        assert key in row
    assert row["text"] == _CHUNK.text
    assert row["doc_hash"] == "abc123"
    store.close()


def test_store_fts_search_returns_results() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="abc123")
    results = store.fts_search("NTP")
    assert len(results) >= 1
    assert any("NTP" in r.get("text", "") or "ntp" in r.get("text", "").lower() for r in results)
    store.close()


def test_store_count_chunks_increments() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    assert store.count_chunks() == 0
    store.upsert_chunk(_CHUNK, _META, doc_hash="h1")
    assert store.count_chunks() == 1
    chunk2 = Chunk(text="Another chunk.", heading="X", anchor="#x-0", token_count=2, kind="module")
    meta2 = PageMeta(
        title="X", anchor="#x", breadcrumb="", kind="module",
        salt_version="3007", url="https://docs.saltproject.io/en/3007/x.html"
    )
    store.upsert_chunk(chunk2, meta2, doc_hash="h2")
    assert store.count_chunks() == 2
    store.close()


def test_store_upsert_is_idempotent() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="h1")
    store.upsert_chunk(_CHUNK, _META, doc_hash="h1")
    assert store.count_chunks() == 1
    store.close()


def test_store_empty_query_returns_empty_list() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="h1")
    results = store.fts_search("")
    assert results == []
    store.close()


def test_store_uses_in_memory_when_path_is_colon_memory() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    assert store.count_chunks() == 0
    store.close()


def test_store_anchor_round_trips_through_search() -> None:
    """Anchor value survives the full upsert → FTS search → result cycle."""
    expected_anchor = "#ntp-module-special"
    chunk = Chunk(
        text="Special NTP anchor test",
        heading="NTP Module",
        anchor=expected_anchor,
        token_count=4,
        kind="module",
    )
    meta = PageMeta(
        title="NTP Module",
        anchor=expected_anchor,
        breadcrumb="Salt 3007 > ntp",
        kind="module",
        salt_version="3007",
        url="https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html",
    )
    store = DocStore(":memory:")
    store.init_schema()
    chunk_id = store.upsert_chunk(chunk, meta, doc_hash="roundtrip")
    results = store.fts_search("Special NTP anchor")
    assert len(results) >= 1
    assert results[0]["anchor"] == expected_anchor
    retrieved = store.get_chunk_by_id(chunk_id)
    assert retrieved is not None
    assert retrieved["anchor"] == expected_anchor
    store.close()
