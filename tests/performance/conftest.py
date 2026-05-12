"""Shared fixtures for performance tests."""
from __future__ import annotations

import pytest

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore

_MODULES = [
    "ntp", "interface", "routing", "acl", "bgp", "ospf", "snmp", "vlan",
    "spanning_tree", "qos", "nat", "firewall", "aaa", "nxos", "ios_xr",
    "napalm", "netmiko", "salt_cisco", "proxy", "grains",
]
_KINDS = ["module", "state", "runner", "grain", "proxy"]
_VERBS = ["configure", "set", "get", "apply", "validate", "list", "show"]


@pytest.fixture(scope="module")
def large_store() -> DocStore:  # type: ignore[misc]
    """In-memory DocStore populated with 1000 synthetic chunks (1 per fixture run)."""
    store = DocStore(":memory:")
    store.init_schema()
    idx = 0
    for mod in _MODULES:
        for verb in _VERBS:
            for i in range(8):
                text = (
                    f"{mod}.{verb} configuration chunk {i}. "
                    f"Use salt.modules.{mod}.{verb} to manage network settings. "
                    f"Supports IOS and IOS-XR. Example: salt '*' {mod}.{verb} value={i}"
                )
                chunk = Chunk(
                    text=text,
                    heading=f"{mod}.{verb}_{i}",
                    anchor=f"#{mod}-{verb}-{i}",
                    token_count=len(text.split()),
                    kind=_KINDS[idx % len(_KINDS)],
                )
                meta = PageMeta(
                    title=f"salt.modules.{mod}",
                    anchor=f"#{mod}-{verb}-{i}",
                    breadcrumb=f"Salt 3007 > Modules > {mod}",
                    kind=_KINDS[idx % len(_KINDS)],
                    salt_version="3007",
                    url=(
                        f"https://docs.saltproject.io/en/3007/ref/modules/all/"
                        f"salt.modules.{mod}{i}.html"
                    ),
                )
                store.upsert_chunk(chunk, meta, doc_hash=f"hash{idx:06d}")
                idx += 1
    return store
