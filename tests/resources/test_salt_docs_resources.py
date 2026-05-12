"""Unit tests for salt_docs resource logic functions."""

from __future__ import annotations

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.resources.salt_docs import (
    contents_logic,
    function_doc_logic,
    module_doc_logic,
)

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
    text="NTP configuration for IOS devices.",
    heading="ntp.set_servers",
    anchor="#ntp-set-servers-0",
    token_count=6,
    kind="module",
)


def _populated_store() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="deadbeef")
    return store


def test_contents_logic_returns_list() -> None:
    store = _populated_store()
    result = contents_logic(store)
    assert isinstance(result, list)
    store.close()


def test_contents_logic_includes_module_entry() -> None:
    store = _populated_store()
    result = contents_logic(store)
    assert len(result) == 1
    entry = result[0]
    assert "url" in entry
    assert "kind" in entry
    assert "name" in entry
    store.close()


def test_contents_logic_extracts_module_name() -> None:
    store = _populated_store()
    result = contents_logic(store)
    assert result[0]["name"] == "salt.modules.ntp"
    store.close()


def test_module_doc_logic_returns_chunks_for_matching_kind_and_name() -> None:
    store = _populated_store()
    result = module_doc_logic(store, "module", "salt.modules.ntp")
    assert len(result) >= 1
    store.close()


def test_module_doc_logic_returns_empty_for_wrong_name() -> None:
    store = _populated_store()
    result = module_doc_logic(store, "module", "salt.modules.nonexistent")
    assert result == []
    store.close()


def test_module_doc_logic_returns_empty_for_wrong_kind() -> None:
    store = _populated_store()
    result = module_doc_logic(store, "state", "salt.modules.ntp")
    assert result == []
    store.close()


def test_function_doc_logic_returns_chunk_for_known_heading() -> None:
    store = _populated_store()
    result = function_doc_logic(store, "ntp.set_servers")
    assert result is not None
    assert result["heading"] == "ntp.set_servers"
    store.close()


def test_function_doc_logic_returns_none_for_unknown_heading() -> None:
    store = _populated_store()
    result = function_doc_logic(store, "ntp.nonexistent_function")
    assert result is None
    store.close()
