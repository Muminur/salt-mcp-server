# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] — 2026-05-13

### Added

**Milestone 16 — Vector Search & Reranker**
- `salt_cisco_mcp/docs/embedder.py`: fastembed ONNX embedding wrapper with graceful BM25-only fallback when fastembed is not installed
- `salt_cisco_mcp/docs/reranker.py`: optional bge-reranker-base wrapper; falls through to original ranking when fastembed is absent
- `salt_cisco_mcp/docs/store.py`: sqlite-vec extension support — `load_vec_extension()`, `init_vec_schema(dim)`, `upsert_embedding()`, `vec_search()` for nearest-neighbour lookup
- `salt_cisco_mcp/docs/retriever.py`: `hybrid_search()` combining BM25 + vector results via Reciprocal Rank Fusion; falls back to BM25 automatically when embedder unavailable
- `salt_cisco_mcp/config.py`: `RerankerConfig` model; `RetrievalConfig.reranker` field (disabled by default)
- CLI `--no-embeddings` flag for `serve` — forces BM25-only mode, skips model download
- `tests/docs/golden_queries.yaml`: 10 declarative BM25 retrieval quality cases
- `tests/docs/test_golden_queries.py`: parametrised golden-query regression tests
- `jinja2>=3` added to core dependencies (required by `validate/jinja_preview.py`)
- `types-PyYAML`, `types-jsonschema` added to dev dependencies for mypy 2.x compatibility

### Fixed
- CI type-check job now passes under mypy 2.x (stricter `import-untyped` handling)
- CI integration test job: added `--override-ini="addopts="` to resolve pytest-cov conflict
- `[[tool.mypy.overrides]]` added for `jinja2`, `sqlite_vec`, `fastembed` to suppress `ignore_missing_imports`

---

## [1.0.0] — 2026-05-13

### Added

**Milestone 0 — Project Foundation**
- Project scaffold: `pyproject.toml`, hatchling build backend, Apache-2.0 license
- `salt_cisco_mcp` package with `__version__`, `cli.py` entry point
- Core dependencies: mcp, pydantic, pydantic-settings, httpx, anyio, structlog
- Development toolchain: ruff, mypy --strict, pytest, pytest-asyncio, pytest-benchmark, psutil
- GitHub Actions CI: lint, typecheck, unit tests (Python 3.10/3.11/3.12), integration, performance
- Makefile with install, test, lint, typecheck, fmt, scrape, serve, scan targets
- pre-commit hooks: ruff, trailing-whitespace

**Milestone 1 — Configuration & CLI Skeleton**
- Pydantic settings with YAML + env override precedence (`SALT_MCP_*`)
- CLI subcommands: `serve`, `install`, `scrape`, `verify`, `version`
- structlog JSON/console logging with per-key redaction processor

**Milestone 2 — Documentation Pipeline**
- Async crawler for `docs.saltproject.io` (ETag caching, `robots.txt`, rate limiting)
- HTML → Markdown normalizer (selectolax + markdownify)
- Heading-aware semantic chunker (never splits code blocks)
- SQLite/FTS5 indexer with `doc_hash` per chunk
- Hybrid BM25 retrieval with score normalization

**Milestone 3 — MCP Server Core**
- FastMCP server with stdio and streamable-HTTP transports
- stdio safety: no `print()` calls; all logs to stderr
- HTTP transport: bearer token auth, `127.0.0.1` bind-only default

**Milestone 4 — Retrieval Tools**
- `search_docs(query, top_k?, token_budget?)` with citation tuples
- `get_doc(anchor_url)` with live-fallback auto-fetch
- `list_modules(kind?)` for module enumeration
- `live_fetch(url)` with domain allowlist (docs.saltproject.io only)
- MCP resources: `salt-docs://contents`, `salt-docs://module/*`, `salt-docs://function/*`
- Token-budget enforcement; `low_confidence` flag

**Milestone 5 — Hallucination Regression Suite**
- 100-case YAML corpus (prompt + expected_modules + must_not_hallucinate)
- CI gates: `unresolved_function_rate < 5%` (G1), `validation_pass_rate ≥ 95%` (G2)

**Milestone 6 — Salt Master Adapter**
- `salt-call --local` and `salt-key` subprocess wrappers (list argv, `shell=False`)
- Pillar reader with comprehensive redaction (password, secret, token, bearer, psk, etc.)
- Module introspection cache (`sys.list_functions`, `sys.argspec`)
- Tools: `list_minions`, `get_grains`, `get_pillar`, `list_loaded_functions`, `confirm_function_exists`
- Resources: `salt-master://minions`, `salt-master://pillar/{id}`, `salt-master://grains/{id}`

**Milestone 7 — Validation Tools**
- JSON Schema validators for napalm, nxos, nxos_api, cisconso proxy pillars
- Tools: `validate_pillar`, `validate_state`, `render_jinja`, `audit_cisco_config`, `generate_pillar`
- Sandboxed Jinja2 environment for `render_jinja`
- Regex-based IOS/NX-OS audit rules

**Milestone 8 — Dry-Run Tools & Prompts**
- Tools: `state_show_sls`, `state_test` (compiled state, predicted changes)
- Prompts: `draft_state_for_cisco`, `debug_failing_state`, `migrate_legacy_syntax`, `generate_proxy_pillar`

**Milestone 9 — Write Tools (gated)**
- `--allow-write` gate: tools registered only when explicitly enabled
- `confirm_token` issuance flow; `hmac.compare_digest` token comparison
- Tools: `state_apply(target, sls, confirm_token)`, `push_config(target, config_text, mode, confirm_token)`
- JSONL audit log: timestamp, tool, target, operator token hash, SLS/config hash, result

**Milestone 10 — Live Fallback & Air-Gap Mode**
- ETag/If-None-Match on-disk cache (`/var/lib/salt-mcp/live-cache/`)
- Domain allowlist: rejects file://, localhost, private IPs; `docs.saltproject.io` only
- `source: "live" | "live-cache" | "cache"` in all fallback responses
- Air-gap integration tests (all retrieval works offline)

**Milestone 11 — Observability**
- Structured JSON log per tool call (tool, duration_ms, tokens, source, low_confidence)
- Prometheus textfile exporter: 5 metrics including `salt_mcp_tool_calls_total`
- `verify` subcommand reports chunk count and metrics path

**Milestone 12 — Security Hardening**
- `hmac.compare_digest` for bearer token comparison (fixes timing oracle)
- Expanded redactor: passwd, bearer, psk, credential added to default key set
- Startup WARNINGs for write mode and missing confirm_token
- Threat model: `docs/security.md` (T1–T6)
- `make scan` target: `pip-audit --strict`

**Milestone 13 — Packaging & Installation**
- `salt-cisco-mcp install` subcommand: creates config dirs, writes starter config.yaml
- systemd unit file (`packaging/salt-cisco-mcp.service`) with security hardening
- PyPI trusted publisher workflow (`.github/workflows/publish.yml`)
- Integration docs for Claude Code, Codex, Copilot, Continue, Cursor
- `docs/install.md` and `docs/runbook.md`

**Milestone 14 — Performance Gates**
- P50 < 50ms, P95 < 250ms for `search_docs` over 200 queries
- `validate_state` < 100ms per call
- Cold-start import < 1.5s; CLI version < 2s
- Idle RSS < 100MB (measured in fresh subprocess)
- CI performance job with `--benchmark-json` artifact upload

**Milestone 15 — v1.0.0 Release**
- Version bumped to 1.0.0
- Hallucination corpus grown to 100 cases
- `IDEAS.md` backlog for post-v1 work

### Changed

- `__version__` updated from `0.1.0` to `1.0.0`
- README.md updated with full feature list, install instructions, and tool reference

---

## [0.1.0] — 2026-05-12

### Added

- Initial project scaffold
- `salt_cisco_mcp` package with `__version__ = "0.1.0"`
