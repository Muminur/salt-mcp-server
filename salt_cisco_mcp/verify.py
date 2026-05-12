import shutil
from pathlib import Path


def run_verify(salt_call_path: str = "salt-call", doc_db_path: str = "") -> int:
    """Check salt-call availability and index status. Returns 0=OK, 1=error."""
    exit_code = 0

    which_result = shutil.which(salt_call_path)
    if which_result:
        print(f"salt-call: FOUND at {which_result}")
    else:
        print(f"salt-call: MISSING -- '{salt_call_path}' not found on PATH")
        exit_code = 1

    if doc_db_path:
        if Path(doc_db_path).exists():
            print(f"index: ready at {doc_db_path}")
        else:
            print("index: not built — run `salt-cisco-mcp scrape` to build it")

    return exit_code
