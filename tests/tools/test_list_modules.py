"""Unit tests for list_modules tool logic."""

from __future__ import annotations

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.tools.list_modules import list_modules_logic

_MODULE_URL = "https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.ntp.html"
_STATE_URL = "https://docs.saltproject.io/en/3007/ref/states/all/salt.states.ntp.html"


def _populated_store() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    module_meta = PageMeta(
        title="salt.modules.ntp",
        anchor="#ntp",
        breadcrumb="",
        kind="module",
        salt_version="3007",
        url=_MODULE_URL,
    )
    state_meta = PageMeta(
        title="salt.states.ntp",
        anchor="#ntp-state",
        breadcrumb="",
        kind="state",
        salt_version="3007",
        url=_STATE_URL,
    )
    module_chunk = Chunk(
        text="NTP module functions.", heading="ntp", anchor="#ntp-0", token_count=3, kind="module"
    )
    state_chunk = Chunk(
        text="NTP state functions.",
        heading="ntp state",
        anchor="#ntp-state-0",
        token_count=3,
        kind="state",
    )
    store.upsert_chunk(module_chunk, module_meta, doc_hash="m1")
    store.upsert_chunk(state_chunk, state_meta, doc_hash="s1")
    return store


def test_list_modules_logic_returns_list() -> None:
    store = _populated_store()
    result = list_modules_logic(store)
    assert isinstance(result, list)
    store.close()


def test_list_modules_logic_returns_all_kinds() -> None:
    store = _populated_store()
    result = list_modules_logic(store)
    kinds = {r["kind"] for r in result}
    assert "module" in kinds
    assert "state" in kinds
    store.close()


def test_list_modules_logic_filters_by_kind() -> None:
    store = _populated_store()
    modules = list_modules_logic(store, kind="module")
    assert all(r["kind"] == "module" for r in modules)
    states = list_modules_logic(store, kind="state")
    assert all(r["kind"] == "state" for r in states)
    store.close()


def test_list_modules_logic_result_items_have_required_fields() -> None:
    store = _populated_store()
    result = list_modules_logic(store)
    assert len(result) >= 1
    r = result[0]
    for field in ("url", "kind", "name"):
        assert field in r, f"Missing field: {field}"
    store.close()


def test_list_modules_logic_name_extracted_from_url() -> None:
    store = _populated_store()
    result = list_modules_logic(store, kind="module")
    assert len(result) >= 1
    assert "ntp" in result[0]["name"].lower()
    store.close()


def test_list_modules_logic_empty_store_returns_empty() -> None:
    store = DocStore(":memory:")
    store.init_schema()
    result = list_modules_logic(store)
    assert result == []
    store.close()
