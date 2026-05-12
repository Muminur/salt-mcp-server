"""Simple thread-safe in-memory metrics store with Prometheus textfile export."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


def _label_key(labels: dict[str, str] | None) -> str:
    if not labels:
        return ""
    parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return "{" + parts + "}"


class MetricsStore:
    """Thread-safe counter / gauge / histogram store.

    Uses a simple float dict rather than a heavy Prometheus library.
    Call write_textfile() to flush a Prometheus-compatible textfile.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: dict[str, float] = {}
        self._hist_count: dict[str, int] = defaultdict(int)
        self._hist_sum: dict[str, float] = defaultdict(float)

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def inc(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        amount: float = 1.0,
    ) -> None:
        key = _label_key(labels)
        with self._lock:
            self._counters[name][key] += amount

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self._hist_count[name] += 1
            self._hist_sum[name] += value

    # ------------------------------------------------------------------
    # Read API (primarily for tests)
    # ------------------------------------------------------------------

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        key = _label_key(labels)
        with self._lock:
            return self._counters[name].get(key, 0.0)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            gauges = dict(self._gauges)
            histograms = {
                n: {"count": self._hist_count[n], "sum": self._hist_sum[n]}
                for n in self._hist_count
            }
            counters = {n: dict(d) for n, d in self._counters.items()}
        return {"counters": counters, "gauges": gauges, "histograms": histograms}

    # ------------------------------------------------------------------
    # Prometheus textfile export
    # ------------------------------------------------------------------

    def write_textfile(self, path: str) -> None:
        """Write a Prometheus textfile to *path*. Silently ignores write errors."""
        lines: list[str] = []
        ts = int(time.time() * 1000)
        with self._lock:
            for name, label_vals in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                for key, val in label_vals.items():
                    lines.append(f"{name}{key} {val} {ts}")
            for name, val in self._gauges.items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {val} {ts}")
            for name in self._hist_count:
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{name}_count {self._hist_count[name]} {ts}")
                lines.append(f"{name}_sum {self._hist_sum[name]} {ts}")
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError:
            pass
