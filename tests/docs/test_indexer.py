from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.indexer import compute_doc_hash, index_page
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore

_META = PageMeta(
    title="IOS Module",
    anchor="#ios",
    breadcrumb="Salt 3007 > Modules > ios",
    kind="module",
    salt_version="3007",
    url="https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ios.html",
)

_CHUNKS = [
    Chunk(text="Configure IOS interface.", heading="IOS", anchor="#ios-0", token_count=3,
          kind="module"),
    Chunk(text="Apply IOS ACL rules.", heading="IOS", anchor="#ios-1", token_count=4,
          kind="module"),
]


def _empty_store() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    return store


def test_compute_doc_hash_is_hex_string() -> None:
    h = compute_doc_hash("some content")
    assert isinstance(h, str)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_doc_hash_deterministic() -> None:
    assert compute_doc_hash("hello") == compute_doc_hash("hello")


def test_compute_doc_hash_different_inputs_differ() -> None:
    assert compute_doc_hash("text A") != compute_doc_hash("text B")


def test_index_page_returns_chunk_count() -> None:
    store = _empty_store()
    count = index_page(store, _CHUNKS, _META)
    assert count == len(_CHUNKS)
    store.close()


def test_index_page_chunks_are_searchable() -> None:
    store = _empty_store()
    index_page(store, _CHUNKS, _META)
    results = store.fts_search("interface")
    assert len(results) >= 1
    store.close()


def test_index_page_empty_chunks_returns_zero() -> None:
    store = _empty_store()
    assert index_page(store, [], _META) == 0
    store.close()
