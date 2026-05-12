# OpenAI Codex CLI Integration

Configure Codex CLI to use salt-cisco-mcp as an MCP server.

## Configuration

Add the server to your Codex CLI configuration (`~/.codex/config.yaml`):

```yaml
mcpServers:
  - name: salt-cisco-mcp
    command: salt-cisco-mcp
    args:
      - serve
      - --transport
      - stdio
```

## HTTP transport

For a remotely hosted server:

```yaml
mcpServers:
  - name: salt-cisco-mcp
    type: http
    url: http://salt-master.internal:7842/mcp
    headers:
      Authorization: "Bearer <your-token>"
```

## Usage

Once configured, Codex can invoke salt-cisco-mcp tools directly:

```bash
codex "List all Cisco IOS proxy minions and show their grains"
```

The server provides the same tool surface as described in the Claude Code integration doc.

## Notes

- salt-cisco-mcp must be installed and on `PATH` for stdio transport.
- The `scrape` command must be run at least once before `search_docs` returns results.
- All pillar data is automatically redacted before being returned to the agent.
