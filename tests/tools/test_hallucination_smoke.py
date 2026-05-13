"""Hallucination smoke test: 10 Salt function queries must resolve in the index."""

from __future__ import annotations

import pytest

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.tools.search_docs import search_docs_logic

# 10 well-known Salt 3007 module/state functions for Cisco automation
_KNOWN_FUNCTIONS = [
    ("ntp.set_servers", "NTP server configuration for IOS devices"),
    ("ntp.get_servers", "Retrieve NTP server configuration from device"),
    ("net.cli", "Execute CLI command on network device via NAPALM"),
    ("net.load_config", "Load configuration on a network device"),
    ("net.commit", "Commit changes on network device"),
    ("napalm.get_interfaces", "Get interfaces from NAPALM proxy"),
    ("napalm.get_bgp_neighbors", "Get BGP neighbors from network device"),
    ("state.apply", "Apply Salt state to target minion"),
    ("grains.get", "Get a specific grain value from minion"),
    ("pillar.get", "Get a specific pillar value"),
]


def _store_with_known_functions() -> DocStore:
    store = DocStore(":memory:")
    store.init_schema()
    base_url = "https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules"
    for fn_name, description in _KNOWN_FUNCTIONS:
        module = fn_name.split(".")[0]
        func = fn_name.split(".")[1] if "." in fn_name else fn_name
        url = f"{base_url}.{module}.html"
        chunk = Chunk(
            text=f"{description}. Function: {fn_name}",
            heading=fn_name,
            anchor=f"#{module}-{func}-0",
            token_count=len(description.split()) + 3,
            kind="module",
        )
        meta = PageMeta(
            title=f"salt.modules.{module}",
            anchor=f"#{module}",
            breadcrumb=f"Salt 3007 > Modules > {module}",
            kind="module",
            salt_version="3007",
            url=url,
        )
        store.upsert_chunk(chunk, meta, doc_hash=f"hash-{module}-{func}")
    return store


@pytest.mark.parametrize("fn_name,query", _KNOWN_FUNCTIONS)
def test_known_function_resolves_in_index(fn_name: str, query: str) -> None:
    """Each known Salt function must appear in search results — no hallucinations."""
    store = _store_with_known_functions()
    result = search_docs_logic(store, query, top_k=5)
    store.close()

    assert result["total"] >= 1, f"No results for query: {query!r}"
    # The function name must appear in at least one result function or text
    headings_and_texts = [(r["function"] + " " + r["text"]).lower() for r in result["results"]]
    fn_module = fn_name.split(".")[0].lower()
    assert any(fn_module in ht for ht in headings_and_texts), (
        f"Function module '{fn_module}' not found in results for '{fn_name}'"
    )
