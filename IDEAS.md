# IDEAS — post-v1.0 backlog

This file tracks ideas and enhancements that were explicitly deferred from the v1.0.0 roadmap. Items here are not committed to any timeline; they exist to avoid losing context.

---

## Platform Expansion

- **Junos support**: Add Salt proxy pillar schemas for `junos` proxytype; add Junos-specific audit rules to `audit_cisco_config`; extend hallucination corpus with JunOS prompts
- **Arista EOS support**: Add `eapi` / `napalm` Arista pillar schemas; EOS-specific `show` command helpers
- **Nokia SR-OS**: Probe community interest before implementing
- **F5 BIG-IP**: Salt `bigip` execution module documentation indexing

---

## Schema Generation

- **YANG-derived schemas**: Generate pillar JSON Schemas from upstream Cisco YANG models (Cisco IOSXR YANG repo) — avoids hand-maintaining schemas that drift with IOS versions
- **Auto-diff pillar schema**: Generate diff when Salt module upgrades change default argument names

---

## Retrieval Improvements

- **Full Prometheus histogram buckets** (`le=` bucket series) in `MetricsStore.write_textfile()` — enables `histogram_quantile()` in Grafana
- **Optional reranker** (`bge-reranker-base` ONNX): on/off via config; benchmarked against BM25-only baseline
- **sqlite-vec embeddings**: Persist ONNX embeddings alongside FTS5 rows for vector search
- **Sparse + dense hybrid** RRF: combine FTS5 BM25 rank with cosine similarity via Reciprocal Rank Fusion
- **Golden-query test set**: `tests/docs/golden_queries.yaml` with expected top-1 anchors across 50 queries

---

## Security

- **mTLS transport option**: Client certificate verification for high-security environments
- **Per-token rate limiting**: Reject > N requests/min per bearer token (prevents brute force at application layer)
- **Audit log signing**: HMAC-signed JSONL entries so audit log tampering is detectable
- **SELinux policy module**: Ship a `salt_mcp.te` policy file for RHEL/Fedora deployments

---

## Operational

- **CPU during scrape CI gate**: ≤ 5% average over 60 seconds — deferred from M14 because it requires real network access
- **Scrape scheduling**: Cron-driven weekly re-scrape with change detection (avoid full rebuild if docs unchanged)
- **Multi-master support**: Route introspection queries to the correct master when multiple masters are configured
- **Web UI**: Lightweight read-only dashboard for metrics and recent tool calls (stretch goal)

---

## Agent Integrations

- **Gemini CLI integration doc** (`docs/integrations/gemini.md`)
- **Aider integration doc**
- **VS Code MCP marketplace listing**

---

## Test & Quality

- **Hallucination corpus ≥ 200 prompts**: Grow from 100 to 200 before v1.1
- **Playwright smoke tests**: Real browser test of MCP JSON-RPC over HTTP transport
- **Property-based tests**: Hypothesis for chunker, FTS query builder, redactor
