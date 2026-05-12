"""Tests for MetricsStore: counters, histograms, gauges, textfile export."""

from __future__ import annotations

from pathlib import Path


def test_counter_starts_at_zero() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    assert store.get_counter("salt_mcp_tool_calls_total") == 0.0


def test_counter_increments() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("salt_mcp_tool_calls_total", {"tool": "search_docs"})
    assert store.get_counter("salt_mcp_tool_calls_total", {"tool": "search_docs"}) == 1.0


def test_counter_multiple_increments() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("salt_mcp_tool_calls_total", {"tool": "search_docs"}, amount=3.0)
    assert store.get_counter("salt_mcp_tool_calls_total", {"tool": "search_docs"}) == 3.0


def test_counter_labels_separate() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("x", {"a": "1"})
    store.inc("x", {"a": "2"})
    assert store.get_counter("x", {"a": "1"}) == 1.0
    assert store.get_counter("x", {"a": "2"}) == 1.0
    assert store.get_counter("x", {"a": "3"}) == 0.0


def test_counter_no_labels() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("mymetric")
    assert store.get_counter("mymetric") == 1.0


def test_set_gauge() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.set_gauge("salt_mcp_doc_chunks_total", 1234.0)
    snap = store.snapshot()
    assert snap["gauges"]["salt_mcp_doc_chunks_total"] == 1234.0


def test_histogram_observe() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.observe("salt_mcp_tool_latency_ms", 42.0)
    store.observe("salt_mcp_tool_latency_ms", 100.0)
    snap = store.snapshot()
    assert snap["histograms"]["salt_mcp_tool_latency_ms"]["count"] == 2


def test_histogram_sum() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.observe("lat", 10.0)
    store.observe("lat", 20.0)
    snap = store.snapshot()
    assert snap["histograms"]["lat"]["sum"] == 30.0


def test_write_textfile_creates_file(tmp_path: Path) -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("salt_mcp_tool_calls_total", {"tool": "test"})
    path = tmp_path / "metrics.prom"
    store.write_textfile(str(path))
    assert path.exists()


def test_write_textfile_contains_counter(tmp_path: Path) -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("salt_mcp_tool_calls_total", {"tool": "search_docs"}, amount=3.0)
    path = tmp_path / "metrics.prom"
    store.write_textfile(str(path))
    content = path.read_text()
    assert "salt_mcp_tool_calls_total" in content
    assert "3" in content


def test_write_textfile_contains_histogram(tmp_path: Path) -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.observe("salt_mcp_tool_latency_ms", 50.0)
    path = tmp_path / "metrics.prom"
    store.write_textfile(str(path))
    content = path.read_text()
    assert "salt_mcp_tool_latency_ms" in content


def test_write_textfile_unwritable_no_crash() -> None:
    from salt_cisco_mcp.observability.metrics import MetricsStore

    store = MetricsStore()
    store.inc("x")
    store.write_textfile("/nonexistent/path/cannot/write/here/metrics.prom")
    # must not raise
