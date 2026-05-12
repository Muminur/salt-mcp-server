from unittest.mock import patch

from salt_cisco_mcp.verify import run_verify


def test_verify_salt_call_found(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    with patch("shutil.which", return_value="/usr/bin/salt-call"):
        with patch("pathlib.Path.exists", return_value=True):
            exit_code = run_verify(
                salt_call_path="salt-call",
                doc_db_path=str(tmp_path / "docs.db"),
            )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "salt-call" in captured.out or "FOUND" in captured.out


def test_verify_salt_call_missing(capsys) -> None:  # type: ignore[no-untyped-def]
    with patch("shutil.which", return_value=None):
        exit_code = run_verify(
            salt_call_path="salt-call",
            doc_db_path="/nonexistent/docs.db",
        )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "MISSING" in captured.out or "not found" in captured.out.lower()


def test_verify_db_missing_prints_advisory(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    with patch("shutil.which", return_value="/usr/bin/salt-call"):
        exit_code = run_verify(
            salt_call_path="salt-call",
            doc_db_path=str(tmp_path / "nonexistent.db"),
        )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "scrape" in captured.out.lower() or "not built" in captured.out.lower()
