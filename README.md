# salt-cisco-mcp

An offline-first [Model Context Protocol](https://modelcontextprotocol.io) server for Salt-driven Cisco IOS / IOS-XR / NX-OS automation. Grounds coding agents (Claude Code, Codex CLI, GitHub Copilot) in the official Salt 3007 documentation so they stop hallucinating module names and pillar shapes.

## Install

```bash
pip install salt-cisco-mcp
salt-cisco-mcp install   # bootstrap the doc index on the Salt master
```

## Quickstart

```bash
# stdio transport (Claude Code / Codex CLI)
salt-cisco-mcp serve --transport stdio

# HTTP transport (Copilot Chat / Continue / Cursor)
salt-cisco-mcp serve --transport http --host 127.0.0.1 --port 7842
```

Add to your agent config and call `search_docs`, `validate_pillar`, `confirm_function_exists` before writing any Salt state.

## Development

```bash
pip install -e ".[dev]"
make test       # run tests
make lint       # ruff check
make typecheck  # mypy --strict
```

## License

Apache-2.0
