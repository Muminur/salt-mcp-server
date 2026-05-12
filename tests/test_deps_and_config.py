import importlib
from pathlib import Path

import tomllib  # type: ignore[import-not-found]


def test_import_mcp() -> None:
    importlib.import_module("mcp")


def test_import_pydantic_settings() -> None:
    importlib.import_module("pydantic_settings")


def test_import_structlog() -> None:
    importlib.import_module("structlog")


def test_import_pytest_asyncio() -> None:
    importlib.import_module("pytest_asyncio")


def test_import_pytest_benchmark() -> None:
    importlib.import_module("pytest_benchmark")


def test_ruff_config_in_pyproject() -> None:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    assert "ruff" in data.get("tool", {})
    assert "line-length" in data["tool"]["ruff"]
    assert "target-version" in data["tool"]["ruff"]


def test_mypy_config_strict_in_pyproject() -> None:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    assert "mypy" in data.get("tool", {})
    assert data["tool"]["mypy"]["strict"] is True
