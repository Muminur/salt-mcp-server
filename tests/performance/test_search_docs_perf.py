"""Performance gate: search_docs P50 < 50 ms, P95 < 250 ms over 200 queries."""
from __future__ import annotations

import time

from salt_cisco_mcp.docs.store import DocStore
from salt_cisco_mcp.tools.search_docs import search_docs_logic

_QUERIES = [
    "NTP server configuration",
    "BGP neighbor routing",
    "OSPF interface configuration",
    "SNMP community string",
    "VLAN trunk port",
    "ACL access control list",
    "NAT translation",
    "interface ip address",
    "spanning tree protocol",
    "QoS policy map",
    "proxy minion napalm",
    "grains cisco ios",
    "salt state apply",
    "pillar data device",
    "module list functions",
    "IOS XR configuration",
    "NX-OS feature enable",
    "validate pillar yaml",
    "render jinja template",
    "push config device",
    "state apply target",
    "dry run test",
    "audit cisco config",
    "generate pillar proxy",
    "confirm function exists",
    "list minions filter",
    "get grains minion",
    "search docs retrieval",
    "live fetch url",
    "bearer token auth",
]

_N_QUERIES = 200


def test_search_docs_p50_under_50ms(large_store: DocStore) -> None:
    """P50 latency for search_docs must be under 50 ms."""
    timings: list[float] = []
    for i in range(_N_QUERIES):
        q = _QUERIES[i % len(_QUERIES)]
        t0 = time.perf_counter()
        search_docs_logic(large_store, q)
        timings.append(time.perf_counter() - t0)

    timings.sort()
    p50 = timings[int(0.50 * len(timings))] * 1000
    assert p50 < 50.0, f"P50 latency {p50:.1f} ms exceeds 50 ms gate"


def test_search_docs_p95_under_250ms(large_store: DocStore) -> None:
    """P95 latency for search_docs must be under 250 ms."""
    timings: list[float] = []
    for i in range(_N_QUERIES):
        q = _QUERIES[i % len(_QUERIES)]
        t0 = time.perf_counter()
        search_docs_logic(large_store, q)
        timings.append(time.perf_counter() - t0)

    timings.sort()
    p95 = timings[int(0.95 * len(timings))] * 1000
    assert p95 < 250.0, f"P95 latency {p95:.1f} ms exceeds 250 ms gate"


def test_search_docs_benchmark(benchmark: object, large_store: DocStore) -> None:
    """pytest-benchmark baseline: single search_docs call (for regression tracking)."""
    result = benchmark(search_docs_logic, large_store, "BGP routing configuration")  # type: ignore[call-arg,operator]
    assert "results" in result


def test_search_docs_200_queries_total_under_5s(large_store: DocStore) -> None:
    """200 sequential search_docs calls must complete in under 5 s total."""
    t0 = time.perf_counter()
    for i in range(_N_QUERIES):
        search_docs_logic(large_store, _QUERIES[i % len(_QUERIES)])
    total_s = time.perf_counter() - t0
    assert total_s < 5.0, f"200 queries took {total_s:.2f} s (gate: 5 s)"
