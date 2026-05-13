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
        title="X",
        anchor="#x",
        breadcrumb="",
        kind="module",
        salt_version="3007",
        url="https://docs.saltproject.io/en/3007/x.html",
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


def test_store_load_vec_extension() -> None:
    """load_vec_extension() succeeds and enables sqlite-vec."""
    store = DocStore(":memory:")
    store.init_schema()
    store.load_vec_extension()
    store.close()


def test_store_init_vec_table_creates_chunks_vec() -> None:
    """init_vec_schema() creates the chunks_vec virtual table."""
    store = DocStore(":memory:")
    store.init_schema()
    store.load_vec_extension()
    store.init_vec_schema(dim=4)
    count = store.count_chunks()
    assert count == 0
    store.close()


def test_store_upsert_embedding_and_vec_search() -> None:
    """upsert_embedding() stores a vector; vec_search() returns it as nearest neighbor."""
    store = DocStore(":memory:")
    store.init_schema()
    store.load_vec_extension()
    store.init_vec_schema(dim=4)

    chunk_id = store.upsert_chunk(_CHUNK, _META, doc_hash="vec-test")
    embedding = [1.0, 0.0, 0.0, 0.0]
    store.upsert_embedding(chunk_id, embedding)

    results = store.vec_search(embedding, limit=5)
    assert len(results) >= 1
    assert results[0]["chunk_id"] == chunk_id
    store.close()


def test_store_vec_search_nearest_neighbor_ordering() -> None:
    """vec_search() returns closest vector first."""
    from salt_cisco_mcp.docs.normalizer import PageMeta as PM

    store = DocStore(":memory:")
    store.init_schema()
    store.load_vec_extension()
    store.init_vec_schema(dim=4)

    meta_a = PM(
        title="A", anchor="#a", breadcrumb="", kind="module",
        salt_version="3007",
        url="https://docs.saltproject.io/en/3007/a.html",
    )
    meta_b = PM(
        title="B", anchor="#b", breadcrumb="", kind="module",
        salt_version="3007",
        url="https://docs.saltproject.io/en/3007/b.html",
    )
    chunk_a = Chunk(text="AAA", heading="A", anchor="#a-0", token_count=1, kind="module")
    chunk_b = Chunk(text="BBB", heading="B", anchor="#b-0", token_count=1, kind="module")

    id_a = store.upsert_chunk(chunk_a, meta_a, doc_hash="ha")
    id_b = store.upsert_chunk(chunk_b, meta_b, doc_hash="hb")

    store.upsert_embedding(id_a, [1.0, 0.0, 0.0, 0.0])
    store.upsert_embedding(id_b, [0.0, 1.0, 0.0, 0.0])

    # Query near A
    results = store.vec_search([0.9, 0.1, 0.0, 0.0], limit=2)
    assert results[0]["chunk_id"] == id_a

    # Query near B
    results = store.vec_search([0.1, 0.9, 0.0, 0.0], limit=2)
    assert results[0]["chunk_id"] == id_b

    store.close()
