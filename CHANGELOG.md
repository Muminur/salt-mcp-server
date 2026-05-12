# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Project scaffold: `pyproject.toml`, hatchling build backend
- `salt_cisco_mcp` package with `__version__ = "0.1.0"`
- Core dependencies: mcp, pydantic, pydantic-settings, httpx, anyio, structlog
- Development toolchain: ruff, mypy --strict, pytest, pytest-asyncio, pytest-benchmark
- GitHub Actions CI: lint, typecheck, test matrix (Python 3.11, 3.12)
- Makefile with install, test, lint, typecheck, fmt, scrape, serve targets
- pre-commit hooks: ruff, trailing-whitespace
