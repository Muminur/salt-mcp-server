# Security Threat Model — salt-cisco-mcp

## Scope

`salt-cisco-mcp` is an MCP server that connects AI coding agents to a Salt Master managing Cisco network devices. It exposes read-only documentation retrieval and Salt Master introspection by default, with opt-in write operations gated by a confirm_token.

---

## Assets

| Asset | Classification | Notes |
|---|---|---|
| Pillar data (passwords, SNMP communities) | Critical | Always redacted before returning to agents |
| Confirm token | High | Used to authorize write operations; stored as SHA-256 hash in audit log |
| HTTP bearer token | High | Stored in a file outside the config; never logged |
| Salt state files | High | Applied to network devices; requires allow_write=True |
| Network device credentials | Critical | Accessed only via Salt pillar; never returned in plaintext |
| Audit log | Medium | Contains hashed tokens and operation summaries |

---

## Threat Catalogue

### T1 — Unauthorized Write Operations

**Threat:** An agent or attacker issues `state_apply` / `push_config` to modify network device config.

**Mitigation:**
- Write tools are not registered unless `server.allow_write=True` (explicit opt-in).
- Every write call requires a `confirm_token` matching the server-side value (constant-time comparison via `hmac.compare_digest`).
- All write calls are appended to an audit log with hashed tokens.
- A startup WARNING is logged whenever write mode is enabled.

**Residual risk:** An operator who sets `allow_write=True` AND shares the `confirm_token` with the agent accepts full responsibility.

---

### T2 — Pillar Secret Leakage

**Threat:** An agent reads device passwords, SNMP communities, or bearer tokens from pillar data.

**Mitigation:**
- `get_pillar` and `salt-master://pillar/{id}` always call `redact_dict()` before returning data.
- Redaction covers a comprehensive key set including: `password`, `passwd`, `secret`, `token`, `community`, `bearer`, `psk`, `credential`, `key`, `passphrase` (and all case variants and substrings).
- `structlog` log processor also redacts these keys from every log line.

**Residual risk:** Custom pillar key names that don't match any redaction pattern. Operators should add custom keys to `security.redact_keys` in config.

---

### T3 — HTTP Bearer Token Brute Force

**Threat:** An attacker brute-forces the HTTP bearer token to bypass authentication.

**Mitigation:**
- Bearer token comparison uses `hmac.compare_digest` (constant-time) to prevent timing oracle attacks.
- Token is read from a file (`security.http_auth.bearer_token_file`), not stored in config.
- Recommend: use a cryptographically random token (e.g., `openssl rand -hex 32`).
- Bind to `127.0.0.1` by default (`server.bind_local_only=True`).

**Not yet implemented:** rate limiting per token, mTLS. These are tracked in Milestone 12.

---

### T4 — Command Injection via Salt Function Name

**Threat:** A malicious function name like `test.ping; rm -rf /` is passed to `salt-call`.

**Mitigation:**
- `SaltCallAdapter` always uses `shell=False` and passes `cmd` as a list.
- User-supplied strings become individual list elements, never shell-interpreted.

---

### T5 — Path Traversal via URL / Anchor Input

**Threat:** A malicious URL like `https://docs.saltproject.io/../../../etc/passwd` accesses unintended files.

**Mitigation:**
- `fallback.fetch()` enforces a strict domain allowlist (default: `docs.saltproject.io`).
- Cache keys are SHA-256 hex digests of the URL — no path component from user input appears in the filesystem path.
- SQLite queries use parameterized placeholders; anchor URLs are not interpolated into SQL.
- `file://`, `http://localhost`, and private IP ranges are rejected by the domain allowlist.

---

### T6 — Log Injection / Prompt Injection

**Threat:** User-supplied text in log fields manipulates log aggregators or downstream AI processing.

**Mitigation:**
- Logs are JSON-formatted via structlog — no shell-interpreted log formats.
- Sensitive values in log events are stripped by the redact processor before rendering.

---

## Not In Scope

- Physical access to the Salt Master host.
- Compromise of the Salt Master itself (pre-existing privileged access).
- Attacks on the AI agent's reasoning (jailbreaking).

---

## Dependency Scanning

Run `make scan` to check for known CVEs in installed packages:

```bash
make scan
```

This requires `pip-audit` (`pip install pip-audit`).

---

## Recommendations for Production Deployment

1. Run as a dedicated non-root user.
2. Set `server.transport=http` and configure a strong bearer token (≥32 random bytes).
3. Keep `server.allow_write=False` unless actively applying changes; re-enable only for maintenance windows.
4. Configure `logrotate` for `~/.salt-mcp/audit.jsonl` (see README.md).
5. Run `make scan` as part of your weekly maintenance.
6. Restrict `security.redact_keys` to also cover any custom pillar keys used in your environment.
