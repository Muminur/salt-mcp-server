from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.retriever import SearchResult, bm25_search, trim_to_budget
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
