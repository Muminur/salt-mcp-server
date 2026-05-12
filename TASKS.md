# TASKS.md — `salt-cisco-mcp`

> Single source of truth for work status. Tasks use `- [ ]` (open) and `- [x]` (done). Mark tasks complete the moment they are finished. Append newly discovered tasks under the appropriate milestone. New milestones go at the bottom.
>
> Reference: `PLANNING.md` (orientation) and `PRD-salt-cisco-mcp.md` (authoritative spec).

---

## Milestone 0 — Project Foundation

**Goal:** A repo a developer can clone, install, lint, type-check, and test in under five minutes. No product logic yet.

- [x] Create repo skeleton with `pyproject.toml` (hatchling backend, Python `>=3.10,<3.13`)
- [x] Add `salt_cisco_mcp/` package with `__init__.py` exposing `__version__`
- [ ] Pin core deps: `mcp>=1.2.0`, `pydantic>=2`, `pydantic-settings`, `httpx`, `anyio`, `structlog`
- [ ] Pin dev deps: `pytest`, `pytest-asyncio`, `pytest-benchmark`, `ruff`, `mypy`, `hatch`
- [ ] Configure `ruff` (line length, target version) and `mypy --strict` in `pyproject.toml`
- [ ] Add `Makefile` with `install`, `test`, `lint`, `typecheck`, `fmt`, `scrape`, `serve` targets
- [ ] Add GitHub Actions CI: lint → typecheck → unit tests → integration tests on push/PR
- [ ] Add `LICENSE` (Apache-2.0), `README.md` (one-paragraph + install + quickstart), `CHANGELOG.md`
- [ ] Add `.gitignore`, `.editorconfig`, `.python-version`
- [ ] Add `CLAUDE.md`, `PLANNING.md`, `TASKS.md`, `PRD-salt-cisco-mcp.md` to the repo root
- [ ] Add `pre-commit` config (ruff + mypy + trailing whitespace)
- [ ] Smoke-test: `make install && make lint && make test` passes on a fresh clone

---

## Milestone 1 — Configuration & CLI Skeleton

**Goal:** `salt-cisco-mcp --help` works, config loads from YAML + env, no MCP behavior yet.

- [ ] Implement `config.py` with Pydantic settings: paths, transport, write-gate, redaction keys, token budgets, telemetry
- [ ] Load order: defaults → `/etc/salt/mcp/config.yaml` → env (`SALT_MCP_*`) → CLI flags
- [ ] Implement `cli.py` with subcommands: `serve`, `install`, `scrape`, `verify`, `version`
- [ ] `verify` subcommand: checks `salt-call` on PATH, prints config, prints index status
- [ ] Wire structlog: JSON logs to stderr by default, file path configurable
- [ ] Unit tests for config parsing (defaults, override precedence, validation errors)
- [ ] Unit tests for `verify` happy-path and missing-`salt-call` path

---

## Milestone 2 — Documentation Pipeline (offline-first index)

**Goal:** `salt-cisco-mcp scrape` produces a queryable SQLite index of Salt 3007 docs.

- [ ] `docs/scraper.py`: async crawler seeded from `https://docs.saltproject.io/en/3007/contents.html`
- [ ] Respect `robots.txt`, polite rate limiting (configurable, default 2 req/s), ETag caching
- [ ] `docs/normalizer.py`: HTML → clean Markdown via `selectolax` + `markdownify`; preserve code blocks verbatim
- [ ] Extract per-page metadata: title, anchor, breadcrumb, kind (module/state/proxy/etc.), Salt version
- [ ] `docs/chunker.py`: heading-aware semantic chunker; never splits inside a code block
- [ ] `docs/indexer.py`: write chunks to SQLite with FTS5 virtual table; compute `doc_hash` per chunk
- [ ] Add `sqlite-vec` extension loading; persist embeddings alongside FTS5 rows
- [ ] Pluggable embedding backend (`fastembed` ONNX default); allow `--no-embeddings` flag for fast cold-start
- [ ] `docs/retriever.py`: hybrid retrieval (BM25 + vector) with score normalization
- [ ] Optional reranker (`bge-reranker-base` ONNX); on/off via config
- [ ] `docs/store.py`: data access layer (no business logic above SQL)
- [ ] Token-budget-aware result trimmer (drop low-rank chunks until under budget)
- [ ] Unit tests: chunker preserves code blocks, anchors round-trip correctly
- [ ] Golden-query test set (`tests/docs/golden_queries.yaml`) with expected top-1 anchors
- [ ] Performance test: `search_docs` P50 < 50 ms, P95 < 250 ms over 200-query suite

---

## Milestone 3 — MCP Server Core (FastMCP scaffold)

**Goal:** `salt-cisco-mcp serve --transport stdio` boots, advertises capabilities, returns nothing useful yet.

- [ ] `server.py`: FastMCP instance with name, version, description
- [ ] `transports.py`: stdio / streamable-http selection via CLI flag
- [ ] Implement `app_lifespan`: open SQLite, lazy-load embeddings, verify `salt-call` on PATH, register shutdown flush
- [ ] **stdio safety:** assert no `print()` calls in package; route every log to stderr
- [ ] HTTP transport: bind `127.0.0.1` by default; bearer token auth; configurable host/port
- [ ] In-memory MCP client test harness (use `mcp` SDK testing utils) — boot server, list tools, assert empty surface
- [ ] Integration test: stdio transport round-trip with mock client
- [ ] Integration test: HTTP transport round-trip with auth challenge

---

## Milestone 4 — Retrieval Tools (the anti-hallucination spine)

**Goal:** Agents can ground every Salt claim in a citable doc chunk.

- [ ] Implement tool: `search_docs(query, top_k?, token_budget?)` → returns chunks with `{module, function, anchor_url, doc_hash}`
- [ ] Implement tool: `get_doc(anchor_url)` → full normalized chunk for an anchor
- [ ] Implement tool: `list_modules(kind?)` → enumerate state/execution/proxy/runner/grain modules from index
- [ ] Implement tool: `live_fetch(url)` (gated by config) → live `docs.saltproject.io` fallback with ETag cache
- [ ] Implement resources: `salt-docs://contents`, `salt-docs://module/{kind}/{name}`, `salt-docs://function/{mod}.{fn}`
- [ ] Add `low_confidence: bool` flag to retrieval responses when top score is below threshold
- [ ] Wire token-budget enforcement at the tool boundary (hard cap from config)
- [ ] Unit tests: retrieval shape, citation tuple presence, budget enforcement
- [ ] Hallucination smoke test: 10 prompts, assert generated function names resolve

---

## Milestone 5 — Hallucination Regression Suite (built early, per PRD §14.3)

**Goal:** A CI gate that blocks any regression in agent grounding accuracy.

- [ ] Define harvest format for prompts (`tests/hallucination/*.yaml`: prompt, expected modules, must-not-hallucinate list)
- [ ] Seed with 30 prompts derived from real agent sessions (Maya persona cases from PRD §4.1)
- [ ] Build runner: drive a configured agent with only this MCP server, parse `salt.<module>.<function>` tokens from output
- [ ] Resolution check: each parsed function must appear in `sys.list_functions` output (use stub master fixture)
- [ ] Score: `unresolved_function_rate`, `validation_pass_rate`
- [ ] CI gate: fail if `unresolved_function_rate > 5%` (G1) or `validation_pass_rate < 95%` (G2)
- [ ] Grow corpus to 100+ prompts before v1.0

---

## Milestone 6 — Salt Master Adapter (subprocess, read-only)

**Goal:** The server can introspect the live master without holding open sockets.

- [ ] `salt_master/adapter.py`: subprocess wrapper for `salt-call --local` and `salt-key --list-all`
- [ ] Robust JSON parsing with fallback to YAML; timeouts; structured errors
- [ ] `salt_master/pillar_reader.py`: load pillar via `salt-call --local pillar.items`
- [ ] **Redaction layer** (mandatory): regex + key-name match for `password`, `secret`, `enable_password`, `community`, `token`, `key`, `passphrase`; configurable add-ons
- [ ] `salt_master/module_introspect.py`: cache `sys.list_functions` and `sys.argspec` per-master-version
- [ ] Implement tool: `list_minions(filter?)` → minion IDs + cached grains summary
- [ ] Implement tool: `get_grains(minion_id, keys?)`
- [ ] Implement tool: `get_pillar(minion_id)` (always redacted)
- [ ] Implement tool: `list_loaded_functions(prefix?)`
- [ ] Implement tool: `confirm_function_exists(name)` — the canonical anti-hallucination call
- [ ] Implement resources: `salt-master://minions`, `salt-master://pillar/{id}`, `salt-master://grains/{id}`
- [ ] Fixture: `tests/fixtures/fake_master/` with stub `salt-call` returning canned JSON
- [ ] Unit tests: redaction (every keyword hit), subprocess timeout handling
- [ ] Integration tests: adapter against fake-master fixture

---

## Milestone 7 — Validation Tools (no side effects)

**Goal:** The agent can verify pillar/state/Jinja/config before suggesting any change.

- [ ] `validate/pillar_schema.py`: JSON Schemas for `napalm`, `nxos`, `nxos_api`, `cisconso` proxytypes
- [ ] Implement tool: `validate_pillar(yaml)` → structured pass/fail with anchored doc URLs on failure
- [ ] `validate/state_lint.py`: SLS structural lint (top-level keys, ID dec, required args)
- [ ] Implement tool: `validate_state(sls)`
- [ ] `validate/jinja_preview.py`: sandboxed Jinja2 environment with safe globals
- [ ] Implement tool: `render_jinja(template, context)` with warnings for unsafe constructs
- [ ] `validate/cisco_audit.py`: `ciscoconfparse2` hooks for IOS/IOS-XR/NX-OS audit rules
- [ ] Implement tool: `audit_cisco_config(config, vendor)`
- [ ] Implement tool: `generate_pillar(proxytype, driver, host, username, ...)` → known-good template with `<<password>>` placeholder
- [ ] Unit tests: known-bad SLS cases fail with helpful messages and doc anchors
- [ ] Unit tests: every proxytype schema accepts the example from upstream Salt docs

---

## Milestone 8 — Dry-Run Tools & Prompts

**Goal:** Agents can preview compiled state and test-mode results without changing anything.

- [ ] `salt_master/dry_run.py`: wrap `state.show_sls` and `state.sls test=True`
- [ ] Implement tool: `state_show_sls(target, sls)` → compiled state object
- [ ] Implement tool: `state_test(target, sls)` → predicted changes + success flag
- [ ] Implement prompt: `draft_state_for_cisco` (guided SLS authoring)
- [ ] Implement prompt: `debug_failing_state` (diagnostic walkthrough)
- [ ] Implement prompt: `migrate_legacy_syntax` (pre-3000 → 3007)
- [ ] Implement prompt: `generate_proxy_pillar` (proxy pillar bootstrap)
- [ ] Integration tests: dry-run tools against fake-master fixture
- [ ] End-to-end test: persona case A1 from PRD §4.1 (ACL state for edge routers) runs green

---

## Milestone 9 — Write Tools (gated, human-in-the-loop)

**Goal:** When and only when explicitly enabled, agents can apply changes with full auditability.

- [ ] Implement `--allow-write` CLI flag; tools below are registered only when set
- [ ] `confirm_token` issuance flow: operator generates token, agent must echo it per call
- [ ] Implement tool: `state_apply(target, sls, confirm_token)` — fails closed on token mismatch
- [ ] Implement tool: `push_config(target, config_text, mode, confirm_token)` — emits diff before apply
- [ ] Audit log writer: append one JSONL line per write call to `/var/log/salt-mcp/audit.jsonl` (immutable mode where supported)
- [ ] Audit fields: timestamp, tool, target, operator token hash, SLS/config hash, result, agent client id
- [ ] Unit tests: token mismatch → 401-equivalent error; redaction in audit payload
- [ ] Integration test: full apply round-trip against fake-master, audit line written and parseable

---

## Milestone 10 — Live Fallback & Air-Gap Mode

**Goal:** Graceful degradation when the offline index is incomplete; clean operation when network is forbidden.

- [ ] `live/fallback.py`: `httpx` client with ETag/`If-None-Match` and on-disk cache at `/var/lib/salt-mcp/live-cache/`
- [ ] Domain allowlist (default: `docs.saltproject.io`); reject everything else
- [ ] Cache TTL configurable; `--no-network` flag disables the fallback tool entirely
- [ ] Surface `source: "cache" | "live" | "live-cache"` in tool responses
- [ ] Update `search_docs` and `get_doc` to call live fallback only on index miss + threshold
- [ ] Tests: air-gap mode (no egress) — all retrieval tools still work, live tools return informative error
- [ ] Tests: live integration (network-required, opt-in via env flag)

---

## Milestone 11 — Observability

**Goal:** A working install is debuggable in production without code changes.

- [ ] Structured log per tool call: `{ts, level, event, tool, duration_ms, tokens_returned, tokens_budget, source, low_confidence, client_session_id}`
- [ ] Prometheus textfile exporter writing to `/var/lib/salt-mcp/metrics.prom`
- [ ] Metrics: `salt_mcp_tool_calls_total`, `salt_mcp_tool_latency_ms_bucket`, `salt_mcp_doc_chunks_total`, `salt_mcp_live_fallback_calls_total`, `salt_mcp_validation_failures_total`
- [ ] Audit log rotation policy documented
- [ ] `verify` subcommand prints index size, last-scrape time, master reachability, metrics path
- [ ] Tests: log shape, metric increments

---

## Milestone 12 — Security Hardening

**Goal:** Pass an internal security review.

- [ ] Redaction unit tests cover every default key + a fuzz set of variants (`Password`, `PASSWORD`, etc.)
- [ ] Path-traversal tests on every URL/anchor input
- [ ] Subprocess argv assembly uses list form (never shell strings); no user input ever interpolated
- [ ] HTTP transport: bearer token required, mTLS optional, rate limiting per token
- [ ] Bearer tokens stored hashed in audit log
- [ ] `--allow-write` requires interactive operator confirmation on first start
- [ ] Threat model document in `docs/security.md`
- [ ] Dependency scan in CI (`pip-audit` or equivalent)

---

## Milestone 13 — Packaging, Installation, Agent Integration

**Goal:** A network engineer can `pipx install salt-cisco-mcp && salt-cisco-mcp install` and be done.

- [ ] `salt-cisco-mcp install` subcommand: runs initial scrape, builds index, writes default config, verifies prerequisites
- [ ] systemd unit file for HTTP transport mode (`packaging/salt-cisco-mcp.service`)
- [ ] PyPI release workflow (GitHub Actions → trusted publisher)
- [ ] Claude Code config snippet (`docs/integrations/claude-code.md`): how to register the stdio server
- [ ] Codex CLI config snippet (`docs/integrations/codex.md`)
- [ ] GitHub Copilot Chat / VS Code config snippet (`docs/integrations/copilot.md`) using streamable-http
- [ ] Continue / Cursor config snippets
- [ ] `docs/install.md`: master prerequisites, install paths, file permissions, SELinux notes
- [ ] `docs/runbook.md`: re-scrape on Salt version bump, rotate tokens, recover from corrupted index

---

## Milestone 14 — Performance Gates

**Goal:** Enforce the PRD's performance goals as CI gates.

- [ ] `pytest-benchmark` runs `search_docs` over 200 queries — assert P50 < 50 ms, P95 < 250 ms
- [ ] Benchmark `validate_state` over 1 KB SLS — assert < 100 ms
- [ ] Cold-start benchmark: < 1.5 s without embeddings, < 4 s with embeddings
- [ ] Idle RSS check: < 100 MB
- [ ] CPU during scrape: ≤ 5% (measured average over 60 s)
- [ ] CI fails on any regression beyond 10% of target

---

## Milestone 15 — v1.0 Release

**Goal:** Ship.

- [ ] All goals G1–G7 from PRD §3.1 measured and met in CI
- [ ] Hallucination regression suite has ≥ 100 prompts
- [ ] Security review sign-off
- [ ] PyPI 1.0.0 published; tag in Git; release notes in CHANGELOG
- [ ] Announcement post + minimal demo GIF in README
- [ ] Backlog file `IDEAS.md` opened for post-v1 work (Junos/EOS expansion, schema generation from upstream YANG, etc.)

---

## Discovered Tasks

<!-- New tasks found mid-work go here when they don't fit cleanly into an existing milestone yet. Promote them into the right milestone when scope is clear. -->
