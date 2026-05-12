# Runbook — salt-cisco-mcp

Operational procedures for maintaining a production salt-cisco-mcp deployment.

---

## Re-scrape after a Salt version bump

When Salt is upgraded, rebuild the documentation index to reflect new module signatures:

```bash
# Stop the server (optional but recommended for index consistency)
sudo systemctl stop salt-cisco-mcp

# Remove the old index
rm /var/lib/salt-mcp/docs.db

# Re-scrape
salt-cisco-mcp scrape

# Verify the new index
salt-cisco-mcp verify

# Restart
sudo systemctl start salt-cisco-mcp
```

**When to do this:** After any `salt` package upgrade (`salt-minion`, `salt-master`, `salt-common`).

---

## Rotate the HTTP bearer token

```bash
# Generate a new token
NEW_TOKEN=$(openssl rand -hex 32)

# Write to the token file (atomic replacement)
echo "$NEW_TOKEN" | sudo tee /etc/salt/mcp/bearer.token.tmp
sudo mv /etc/salt/mcp/bearer.token.tmp /etc/salt/mcp/bearer.token
sudo chmod 600 /etc/salt/mcp/bearer.token

# Reload the server (reads token on each request — no restart needed for HTTP mode)
# If using stdio mode, restart is required:
sudo systemctl restart salt-cisco-mcp

# Update your agent config with the new token
echo "New token: $NEW_TOKEN"
```

**When to do this:**
- On a schedule (quarterly minimum).
- Immediately after any suspected token exposure.
- After removing a user who had token access.

---

## Rotate the confirm_token (write operations)

The `confirm_token` gates write operations (`state_apply`, `push_config`).

```bash
# Generate a new token
NEW_CONFIRM=$(openssl rand -hex 16)

# Update config.yaml
sudo sed -i "s/confirm_token:.*/confirm_token: \"$NEW_CONFIRM\"/" /etc/salt/mcp/config.yaml

# Restart to pick up the new value
sudo systemctl restart salt-cisco-mcp

# Inform the agent of the new token
echo "New confirm_token: $NEW_CONFIRM"
```

**Security note:** The audit log stores a SHA-256 hash of the confirm_token, never the raw value. Historical audit records remain valid after rotation.

---

## Recover from a corrupted index

Symptoms: `search_docs` returns 0 results for all queries; `verify` reports an error reading the index.

```bash
# Stop the server
sudo systemctl stop salt-cisco-mcp

# Back up the corrupt file (for diagnosis)
cp /var/lib/salt-mcp/docs.db /var/lib/salt-mcp/docs.db.corrupt.$(date +%s)

# Remove and rebuild
rm /var/lib/salt-mcp/docs.db
salt-cisco-mcp scrape

# Verify
salt-cisco-mcp verify

# Restart
sudo systemctl start salt-cisco-mcp
```

**Root cause investigation:**

```bash
# Check if SQLite can read the file
sqlite3 /var/lib/salt-mcp/docs.db.corrupt.* "PRAGMA integrity_check;"

# Check disk space
df -h /var/lib/salt-mcp
```

A full filesystem during scrape is the most common cause of corruption.

---

## Audit log rotation

The audit log at `~/.salt-mcp/audit.jsonl` (default) grows unbounded. Configure `logrotate`:

```
# /etc/logrotate.d/salt-cisco-mcp
~/.salt-mcp/audit.jsonl {
    weekly
    rotate 52
    compress
    missingok
    notifempty
    copytruncate
}
```

Or override the path in config:

```yaml
paths:
  audit_log: /var/log/salt-mcp/audit.jsonl
```

Then configure `logrotate` for that path instead.

---

## Check Prometheus metrics

```bash
# View the current metrics textfile
cat /var/lib/salt-mcp/metrics.prom

# Useful metrics
grep salt_mcp_tool_calls_total /var/lib/salt-mcp/metrics.prom
grep salt_mcp_doc_chunks_total /var/lib/salt-mcp/metrics.prom
grep salt_mcp_validation_failures_total /var/lib/salt-mcp/metrics.prom
```

---

## Dependency security scan

```bash
# Run from the project root
make scan
# or directly:
pip-audit --strict
```

Run weekly and after any `pip upgrade`. File issues at https://github.com/Muminur/salt-mcp-server/issues for CVEs in core dependencies.

---

## Diagnose a failed tool call

```bash
# Tail the structured JSON log
tail -f /var/log/salt-mcp/server.log | python3 -m json.tool

# Filter for errors only
tail -f /var/log/salt-mcp/server.log | grep '"level":"error"'

# Check last 50 tool calls
grep '"event":"tool_call"' /var/log/salt-mcp/server.log | tail -50 | python3 -m json.tool
```
