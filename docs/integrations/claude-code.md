# Claude Code Integration

Configure Claude Code to use salt-cisco-mcp as an MCP server.

## stdio transport (recommended for local use)

Add the following to your Claude Code MCP configuration (`~/.claude/mcp.json` or via `claude mcp add`):

```json
{
  "mcpServers": {
    "salt-cisco-mcp": {
      "command": "salt-cisco-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {}
    }
  }
}
```

Or register via the CLI:

```bash
claude mcp add salt-cisco-mcp -- salt-cisco-mcp serve --transport stdio
```

## HTTP transport (for remote Salt masters)

If the server runs on a remote host:

```json
{
  "mcpServers": {
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

## Available tools

Once connected, Claude Code has access to:

| Tool | Purpose |
|---|---|
| `search_docs` | Semantic search over Salt 3007 module docs |
| `get_doc` | Full doc chunk for a specific anchor URL |
| `list_modules` | Enumerate available Salt modules |
| `live_fetch` | Fetch a live page from docs.saltproject.io |
| `list_minions` | List connected Salt minions |
| `get_grains` | Retrieve minion grains |
| `get_pillar` | Retrieve (redacted) pillar data |
| `confirm_function_exists` | Verify a Salt function is loaded |
| `validate_pillar` | Validate proxy pillar YAML |
| `validate_state` | Lint an SLS state file |
| `render_jinja` | Preview Jinja template output |
| `audit_cisco_config` | Security audit Cisco IOS config |

Write tools (`state_apply`, `push_config`) are only available when `allow_write: true` in config.

## Verifying the connection

```bash
# Check the server is reachable
salt-cisco-mcp verify

# In Claude Code, ask:
# "List the Salt modules available for Cisco IOS"
```
