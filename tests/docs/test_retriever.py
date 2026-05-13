import sys
from unittest.mock import MagicMock, patch

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.embedder import Embedder
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.retriever import SearchResult, bm25_search, hybrid_search, trim_to_budget
from salt_cisco_mcp.docs.store import DocStore

_META = PageMeta(
    title="NAPALM Module",
    anchor="#napalm",
    breadcrumb="Salt 3007 > Proxy > napalm",
    kind="proxy",
    salt_version="3007",
    url="https://docs.saltproject.io/en/3007/ref/proxy/all/salt.proxy.napalm.html",
)

_CHUNK = Chunk(
    text="NAPALM proxy configuration for Cisco IOS.",
    heading="NAPALM Proxy",
    anchor="#napalm-0",
    token_count=7,
    kind="proxy",
)


def _populated_store() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="deadbeef")
    return store


def test_bm25_search_returns_search_results() -> None:
    store = _populated_store()
    results = bm25_search(store, "NAPALM")
    assert len(results) >= 1
    store.close()


def test_bm25_search_result_fields() -> None:
    store = _populated_store()
    results = bm25_search(store, "NAPALM")
    assert len(results) >= 1
    r = results[0]
    assert isinstance(r, SearchResult)
    assert isinstance(r.chunk_id, int)
    assert isinstance(r.text, str)
    assert isinstance(r.anchor, str)
    assert isinstance(r.heading, str)
    assert isinstance(r.kind, str)
    assert isinstance(r.score, float)
    assert isinstance(r.doc_hash, str)
    store.close()


def test_bm25_search_empty_store_returns_empty() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    results = bm25_search(store, "anything")
    assert results == []
    store.close()


def test_trim_to_budget_respects_limit() -> None:
    sr_with_tokens = [
        SearchResult(
            chunk_id=i,
            text="word " * 50,
            anchor=f"#a{i}",
            heading="h",
            kind="module",
            score=1.0,
            doc_hash="h",
        )
        for i in range(10)
    ]
    trimmed = trim_to_budget(sr_with_tokens, token_budget=100)
    total_tokens = sum(len(r.text.split()) for r in trimmed)
    assert total_tokens <= 150


def test_trim_to_budget_empty_input_returns_empty() -> None:
    assert trim_to_budget([], 100) == []


def test_trim_to_budget_keeps_all_if_under_budget() -> None:
    results = [
        SearchResult(
            chunk_id=i,
            text=f"short text {i}",
            anchor=f"#a{i}",
            heading="h",
            kind="module",
            score=1.0,
            doc_hash="h",
        )
        for i in range(3)
    ]
    trimmed = trim_to_budget(results, token_budget=10000)
    assert len(trimmed) == 3


def test_hybrid_search_bm25_only_when_embedder_unavailable() -> None:
    """hybrid_search() falls back to BM25 when embedder is unavailable."""
    with patch.dict(sys.modules, {"fastembed": None}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        store = _populated_store()
        results = hybrid_search(store, "NAPALM proxy", embedder=emb, limit=5)
        store.close()
    assert len(results) >= 1
    assert all(isinstance(r, SearchResult) for r in results)


def test_hybrid_search_with_mock_embedder() -> None:
    """hybrid_search() merges BM25 + vector results via RRF when embedder is available."""
    dim = 4

    mock_model = MagicMock()
    mock_model.embed.return_value = iter([[[0.1] * dim]])

    mock_fe = MagicMock()
    mock_fe.TextEmbedding.return_value = mock_model

    with patch.dict(sys.modules, {"fastembed": mock_fe}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")

        store = DocStore(":memory:")
        store.init_schema()
        store.load_vec_extension()
        store.init_vec_schema(dim=dim)
        chunk_id = store.upsert_chunk(_CHUNK, _META, doc_hash="hybrid-test")
        store.upsert_embedding(chunk_id, [0.1] * dim)

        results = hybrid_search(store, "NAPALM proxy", embedder=emb, limit=5)
        store.close()

    assert len(results) >= 1
    assert isinstance(results[0], SearchResult)


def test_hybrid_search_deduplicates_results() -> None:
    """hybrid_search() should not return the same chunk_id more than once."""
    with patch.dict(sys.modules, {"fastembed": None}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        store = _populated_store()
        results = hybrid_search(store, "NAPALM", embedder=emb, limit=10)
        store.close()
    chunk_ids = [r.chunk_id for r in results]
    assert len(chunk_ids) == len(set(chunk_ids))
