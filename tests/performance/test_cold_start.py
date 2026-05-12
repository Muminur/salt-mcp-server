"""Performance gate: cold-start import time < 1.5 s without embeddings."""
from __future__ import annotations

import subprocess
import sys
import time


def test_package_import_under_1500ms() -> None:
    """Importing salt_cisco_mcp must complete in under 1.5 s (no embeddings)."""
    script = "import salt_cisco_mcp; import salt_cisco_mcp.config"
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        timeout=10,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert result.returncode == 0, f"import failed: {result.stderr.decode()}"
    assert elapsed_ms < 1500.0, f"cold-start import took {elapsed_ms:.0f} ms (gate: 1500 ms)"


def test_cli_version_under_2000ms() -> None:
    """'salt-cisco-mcp version' must print and exit in under 2 s."""
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "salt_cisco_mcp.cli", "version"],
        capture_output=True,
        timeout=10,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert result.returncode == 0, f"CLI failed: {result.stderr.decode()}"
    assert elapsed_ms < 2000.0, f"CLI version took {elapsed_ms:.0f} ms (gate: 2000 ms)"


def test_docstore_init_schema_under_100ms() -> None:
    """Opening an in-memory DocStore and running init_schema must be under 100 ms."""
    from salt_cisco_mcp.docs.store import DocStore

    t0 = time.perf_counter()
    store = DocStore(":memory:")
    store.init_schema()
    store.close()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 100.0, f"DocStore init took {elapsed_ms:.1f} ms (gate: 100 ms)"
