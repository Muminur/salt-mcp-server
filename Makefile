.PHONY: install test lint typecheck fmt scrape serve

install:
	pip install -e ".[dev]"

test:
	pytest -vv

lint:
	ruff check .

typecheck:
	mypy salt_cisco_mcp/ --strict

fmt:
	ruff check . --fix && ruff format .

scrape:
	python -m salt_cisco_mcp.cli scrape

serve:
	python -m salt_cisco_mcp.cli serve
