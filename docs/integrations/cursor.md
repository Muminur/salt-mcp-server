# Cursor Integration

[Cursor](https://cursor.sh) supports MCP servers for context-aware code generation.

## Configuration

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "salt-cisco-mcp": {
      "command": "salt-cisco-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

## HTTP transport

```json
{
  "mcpServers": {
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

## Usage

Once configured, Cursor can use salt-cisco-mcp to:

- Look up Salt module documentation while writing SLS files
- Validate pillar YAML before committing
- Check that Salt functions referenced in code actually exist
- Generate proxy pillar templates for Cisco devices

salt-cisco-mcp must be on `PATH` for stdio transport to work. Run `salt-cisco-mcp verify` to confirm the server is ready.
