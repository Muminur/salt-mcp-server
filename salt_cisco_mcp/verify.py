import shutil
from pathlib import Path


def run_verify(
    salt_call_path: str = "salt-call",
    doc_db_path: str = "",
    metrics_dir: str = "",
) -> int:
    """Check salt-call availability and index/metrics status. Returns 0=OK, 1=error."""
    exit_code = 0

    which_result = shutil.which(salt_call_path)
    if which_result:
        print(f"salt-call: FOUND at {which_result}")
    else:
        print(f"salt-call: MISSING -- '{salt_call_path}' not found on PATH")
        exit_code = 1

    if doc_db_path:
        db = Path(doc_db_path)
        if db.exists():
            try:
                from salt_cisco_mcp.docs.store import DocStore

                store = DocStore(doc_db_path)
                store.init_schema()
                count = store.count_chunks()
                store.close()
                print(f"index: ready at {doc_db_path} ({count} chunks)")
            except Exception:  # noqa: BLE001
                print(f"index: file present but could not read ({doc_db_path})")
        else:
            print("index: not built — run `salt-cisco-mcp scrape` to build it")

    if metrics_dir:
        metrics_file = Path(metrics_dir) / "metrics.prom"
        if metrics_file.exists():
            print(f"metrics: {metrics_file}")
        else:
            print(f"metrics: not written yet (will appear at {metrics_file})")

    return exit_code
