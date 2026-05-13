# salt-cisco-mcp

An offline-first [Model Context Protocol](https://modelcontextprotocol.io) server for Salt-driven Cisco IOS / IOS-XR / NX-OS automation. Grounds coding agents (Claude Code, Codex CLI, GitHub Copilot, Continue, Cursor) in the official Salt 3007 documentation so they stop hallucinating module names and pillar shapes.

[![CI](https://github.com/Muminur/salt-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Muminur/salt-mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/salt-cisco-mcp)](https://pypi.org/project/salt-cisco-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/salt-cisco-mcp)](https://pypi.org/project/salt-cisco-mcp/)

---

## Install

```bash
pipx install salt-cisco-mcp
sudo salt-cisco-mcp install   # create config dirs and starter config.yaml
salt-cisco-mcp scrape         # build the offline documentation index (~5 min)
salt-cisco-mcp verify         # confirm everything is ready
```

See [docs/install.md](docs/install.md) for full installation instructions, file permissions, and SELinux notes.

---

## Quickstart

### stdio transport (Claude Code / Codex CLI)

```bash
salt-cisco-mcp serve --transport stdio
```

Add to Claude Code:
```bash
claude mcp add salt-cisco-mcp -- salt-cisco-mcp serve --transport stdio
```

### HTTP transport (Copilot Chat / Continue / Cursor)

```bash
salt-cisco-mcp serve --transport http --host 127.0.0.1 --port 7842
```

See `docs/integrations/` for per-agent config snippets.

---

## What it does

Once connected, your agent can call:

| Tool | Purpose |
|---|---|
| `search_docs(query, top_k?, brief?)` | Hybrid BM25 + vector search over Salt 3007 module docs. `brief=True` returns citations only (no text) for fast scanning. |
| `get_doc(anchor_url)` | Full doc chunk for a specific anchor URL |
| `list_modules(kind?, limit?)` | Enumerate available Salt modules by kind (default limit: 200) |
| `list_loaded_functions(prefix?, limit?)` | List functions loaded on the master (default limit: 200) |
| `live_fetch(url)` | Fetch a live page from docs.saltproject.io, capped at 16 KB |
| `confirm_function_exists` | Verify a Salt function is actually loaded |
| `list_minions` | List connected Salt proxy minions |
| `get_grains(minion_id?, keys?)` | Retrieve minion grains (capped at 50 keys) |
| `get_pillar(minion_id?)` | Retrieve redacted pillar data (capped at 50 top-level keys) |
| `validate_pillar` | Validate proxy pillar YAML against JSON schema |
| `validate_state` | Lint SLS state structure |
| `render_jinja` | Preview Jinja template output (sandboxed) |
| `audit_cisco_config` | Security audit Cisco IOS/NX-OS config |
| `generate_pillar` | Generate a known-good pillar template |
| `state_show_sls` | Show compiled state object (dry-run) |
| `state_test` | Preview changes in test mode |
| `state_apply`* | Apply a state (requires `--allow-write`) |
| `push_config`* | Push config snippet (requires `--allow-write`) |

*Write tools are only registered when `allow_write: true` in config. Every write call requires a `confirm_token`.

---

## Token efficiency

All tool responses are designed for minimal LLM token consumption:

| Mode | Typical P50 | Typical P95 |
|---|---|---|
| Standard `search_docs` | ~223 tokens | ~1 200 tokens |
| `search_docs(brief=True)` | ~90 tokens | ~305 tokens |

`brief=True` returns only citation fields (`module`, `function`, `anchor_url`, `doc_hash`) with no body text — useful for scan-then-read workflows where the agent first finds the right anchor, then calls `get_doc` for the full text.

Response caps that prevent runaway token use:

- `live_fetch` — content capped at 16 000 characters
- `get_grains` — capped at 50 keys; returns `total` + `truncated: true` when exceeded
- `get_pillar` — capped at 50 top-level keys; returns `total_keys` + `truncated: true`
- `list_loaded_functions` / `list_modules` — default limit 200, configurable up to 500/1000

---

## Vector search (optional)

By default `search_docs` uses BM25 full-text search. Install the optional embedding backend for hybrid BM25 + vector search with Reciprocal Rank Fusion:

```bash
pip install "salt-cisco-mcp[embeddings]"   # installs fastembed (ONNX, ~200 MB model download on first use)
```

To keep BM25-only mode and skip the model download:

```bash
salt-cisco-mcp serve --no-embeddings
```

An optional reranker (BAAI/bge-reranker-base) can be enabled in `config.yaml`:

```yaml
retrieval:
  reranker:
    enabled: true
    model: "BAAI/bge-reranker-base"
```

All three modes (BM25-only, hybrid, hybrid + reranker) work on Windows, macOS, and Linux.

---

## Agent integration docs

- [Claude Code](docs/integrations/claude-code.md)
- [Codex CLI](docs/integrations/codex.md)
- [GitHub Copilot / VS Code](docs/integrations/copilot.md)
- [Continue](docs/integrations/continue.md)
- [Cursor](docs/integrations/cursor.md)

---

## Development

```bash
git clone https://github.com/Muminur/salt-mcp-server.git
cd salt-mcp-server
pip install -e ".[dev]"
make test       # run all tests + coverage
make lint       # ruff check
make typecheck  # mypy --strict
make scan       # pip-audit --strict (dependency CVE scan)
```

### Test coverage

```
706 tests passing | 89.8% line coverage | Python 3.10 / 3.11 / 3.12
```

---

## Security

- All subprocess calls use list argv with `shell=False` — no command injection
- Bearer token comparison uses `hmac.compare_digest` — no timing oracle
- Pillar data is always redacted before returning to agents
- Threat model: [docs/security.md](docs/security.md)

---

## Audit log

When write tools are enabled, every operation is recorded as a JSONL line in `~/.salt-mcp/audit.jsonl`. The log contains hashed tokens — never raw credentials. See [docs/runbook.md](docs/runbook.md) for rotation instructions.

---

## Observability

Tool call metrics are written to `$telemetry.metrics_dir/metrics.prom` in Prometheus textfile format after each tool invocation. Metrics:

- `salt_mcp_tool_calls_total{tool="..."}` — cumulative call count per tool
- `salt_mcp_tool_latency_ms_sum/count` — latency histogram (sum + count)
- `salt_mcp_doc_chunks_total` — index size on startup
- `salt_mcp_live_fallback_calls_total` — live fetch invocations
- `salt_mcp_validation_failures_total` — low-confidence search results

Every tool call also emits a structured JSON log line via structlog.

---

## License

Apache-2.0 — see [LICENSE](LICENSE)
