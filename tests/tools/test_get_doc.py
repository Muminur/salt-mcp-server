"""Unit tests for get_doc tool logic."""

from __future__ import annotations

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.tools.get_doc import get_doc_logic

_URL = "https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html"
_ANCHOR = "#ntp-set-servers-0"
_ANCHOR_URL = _URL + _ANCHOR

_META = PageMeta(
    title="salt.modules.ntp",
    anchor="#ntp",
    breadcrumb="",
    kind="module",
    salt_version="3007",
    url=_URL,
)
_CHUNK = Chunk(
    text="Set NTP servers for IOS devices.",
    heading="ntp.set_servers",
    anchor=_ANCHOR,
    token_count=7,
    kind="module",
)


def _populated_store() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    store.upsert_chunk(_CHUNK, _META, doc_hash="abc123")
    return store


def test_get_doc_logic_returns_dict_for_known_anchor() -> None:
    store = _populated_store()
    result = get_doc_logic(store, _ANCHOR_URL)
    assert isinstance(result, dict)
    store.close()


def test_get_doc_logic_result_has_required_fields() -> None:
    store = _populated_store()
    result = get_doc_logic(store, _ANCHOR_URL)
    assert result is not None
    for field in ("text", "heading", "anchor_url", "kind", "doc_hash"):
        assert field in result, f"Missing field: {field}"
    store.close()


def test_get_doc_logic_returns_correct_text() -> None:
    store = _populated_store()
    result = get_doc_logic(store, _ANCHOR_URL)
    assert result is not None
    assert "NTP" in result["text"]
    store.close()


def test_get_doc_logic_returns_none_for_unknown_anchor() -> None:
    store = _populated_store()
    result = get_doc_logic(store, "https://docs.saltproject.io/unknown.html#no-such-anchor")
    assert result is None
    store.close()


def test_get_doc_logic_handles_url_without_fragment() -> None:
    store = _populated_store()
    result = get_doc_logic(store, "https://docs.saltproject.io/nothing.html")
    assert result is None
    store.close()
