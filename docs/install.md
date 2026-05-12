# Installation Guide — salt-cisco-mcp

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.10, < 3.13 | CPython recommended |
| salt-minion / salt-call | ≥ 3007 | Must be on `PATH` |
| SQLite | ≥ 3.35 | Bundled with Python ≥ 3.10 |
| Linux | Any modern distro | systemd optional |

> **Windows / macOS:** `salt-call` is not officially supported on these platforms. The documentation retrieval tools work everywhere; Salt master tools require a Linux host.

---

## Install via pipx (recommended)

```bash
pipx install salt-cisco-mcp
salt-cisco-mcp version
```

## Install via pip

```bash
pip install salt-cisco-mcp
```

## Install from source

```bash
git clone https://github.com/Muminur/salt-mcp-server.git
cd salt-mcp-server
pip install -e ".[dev]"
```

---

## Bootstrap

Run the install subcommand to create config directories and write a starter `config.yaml`:

```bash
sudo salt-cisco-mcp install \
  --config-dir /etc/salt/mcp \
  --data-dir /var/lib/salt-mcp \
  --log-dir /var/log/salt-mcp \
  --audit-dir /root/.salt-mcp
```

Use `--dry-run` to preview what will be created without making changes:

```bash
sudo salt-cisco-mcp install --dry-run
```

---

## Install paths

| Path | Purpose | Default |
|---|---|---|
| `/etc/salt/mcp/config.yaml` | Server configuration | Written by `install` |
| `/etc/salt/mcp/bearer.token` | HTTP bearer token | Create manually (see below) |
| `/var/lib/salt-mcp/docs.db` | SQLite documentation index | Written by `scrape` |
| `/var/lib/salt-mcp/live-cache/` | ETag disk cache for live fetch | Auto-created |
| `/var/lib/salt-mcp/metrics.prom` | Prometheus textfile metrics | Written at runtime |
| `/var/log/salt-mcp/server.log` | Structured JSON log | Written at runtime |
| `~/.salt-mcp/audit.jsonl` | Write-operation audit log | Written at runtime |

---

## File permissions

```bash
# Create a dedicated service user
sudo useradd -r -s /sbin/nologin -d /var/lib/salt-mcp salt-mcp

# Set ownership
sudo chown -R salt-mcp:salt-mcp /var/lib/salt-mcp /var/log/salt-mcp
sudo chmod 750 /etc/salt/mcp
sudo chmod 640 /etc/salt/mcp/config.yaml

# Protect the bearer token file
sudo chmod 600 /etc/salt/mcp/bearer.token
sudo chown salt-mcp:salt-mcp /etc/salt/mcp/bearer.token
```

---

## Generate a bearer token

```bash
openssl rand -hex 32 | sudo tee /etc/salt/mcp/bearer.token
sudo chmod 600 /etc/salt/mcp/bearer.token
```

Make sure `config.yaml` references this file:

```yaml
security:
  http_auth:
    mode: bearer
    bearer_token_file: /etc/salt/mcp/bearer.token
```

---

## Build the documentation index

```bash
salt-cisco-mcp scrape
```

This crawls `docs.saltproject.io`, extracts Salt 3007 module documentation, and writes a searchable SQLite index to `doc_db`. Expect ~5,000 pages; takes 3–10 minutes depending on network speed.

Verify the index:

```bash
salt-cisco-mcp verify
```

---

## systemd service (HTTP transport)

Copy the included unit file and enable the service:

```bash
sudo cp packaging/salt-cisco-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable salt-cisco-mcp
sudo systemctl start salt-cisco-mcp
sudo systemctl status salt-cisco-mcp
```

---

## SELinux notes

If running on an SELinux-enforcing system (RHEL, CentOS, Fedora):

```bash
# Allow salt-cisco-mcp to bind to port 7842
sudo semanage port -a -t http_port_t -p tcp 7842

# Allow read access to /etc/salt/mcp
sudo semanage fcontext -a -t etc_t "/etc/salt/mcp(/.*)?"
sudo restorecon -Rv /etc/salt/mcp
```

---

## Upgrade

```bash
pipx upgrade salt-cisco-mcp
# Re-scrape if the Salt version changed
salt-cisco-mcp scrape
```

---

## Uninstall

```bash
sudo systemctl stop salt-cisco-mcp
sudo systemctl disable salt-cisco-mcp
sudo rm /etc/systemd/system/salt-cisco-mcp.service
pipx uninstall salt-cisco-mcp
sudo rm -rf /etc/salt/mcp /var/lib/salt-mcp /var/log/salt-mcp
```
