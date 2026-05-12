# GitHub Copilot / VS Code Integration

GitHub Copilot Chat supports MCP servers via the streamable-http transport.

## Prerequisites

- VS Code ≥ 1.90
- GitHub Copilot Chat extension
- salt-cisco-mcp running in HTTP mode on an accessible host

## Start the server in HTTP mode

```bash
salt-cisco-mcp serve --transport http --host 127.0.0.1 --port 7842
```

Or use the systemd service (see `docs/install.md`).

## VS Code configuration

Add to `.vscode/mcp.json` in your workspace (or to user settings):

```json
{
  "servers": {
    "salt-cisco-mcp": {
      "type": "http",
      "url": "http://127.0.0.1:7842/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

For a remote Salt master:

```json
{
  "servers": {
    "salt-cisco-mcp": {
      "type": "http",
      "url": "http://salt-master.internal:7842/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

## Usage

Once configured, Copilot Chat can call salt-cisco-mcp tools when you ask about Cisco network automation:

```
@workspace Draft an SLS state to configure OSPF on all IOS-XR routers
```

Copilot will automatically invoke `search_docs` to ground its answer in real Salt documentation.

## Security note

The HTTP transport requires a bearer token. Generate one with:

```bash
openssl rand -hex 32
```

Store it in `/etc/salt/mcp/bearer.token` and reference it in `config.yaml` under `security.http_auth.bearer_token_file`.
