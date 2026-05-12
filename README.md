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

## Audit Log

When write tools (`state_apply`, `push_config`) are enabled, every operation is recorded as a JSON line in `~/.salt-mcp/audit.jsonl` (configurable via `settings.paths.audit_log`). The log contains hashed tokens — never raw credentials.

**Rotation:** Use `logrotate` or a cron job to archive the file. Example `/etc/logrotate.d/salt-mcp`:

```
~/.salt-mcp/audit.jsonl {
    rotate 12
    monthly
    compress
    missingok
    notifempty
}
```

The server appends to the existing file on startup. Safe to truncate or rotate at any time.

## Observability

Tool call metrics are written to `$telemetry.metrics_dir/metrics.prom` (default `/var/lib/salt-mcp/metrics.prom`) in Prometheus textfile format after each tool invocation. Metrics include:

- `salt_mcp_tool_calls_total{tool="..."}` — cumulative call count per tool
- `salt_mcp_tool_latency_ms_sum/count` — total and count for latency histogram
- `salt_mcp_doc_chunks_total` — index size on startup
- `salt_mcp_live_fallback_calls_total` — live fetch invocations
- `salt_mcp_validation_failures_total` — low-confidence search results

Every tool call also emits a structured JSON log line via structlog with fields:
`event, tool, duration_ms, tokens_returned, tokens_budget, source, low_confidence, client_session_id`.

## License

Apache-2.0
