# Continue Integration

[Continue](https://continue.dev) is an open-source AI coding assistant that supports MCP servers.

## Configuration

Add the following to `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "salt-cisco-mcp",
      "command": "salt-cisco-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  ]
}
```

## HTTP transport

```json
{
  "mcpServers": [
    {
      "name": "salt-cisco-mcp",
      "type": "http",
      "url": "http://127.0.0.1:7842/mcp",
      "requestOptions": {
        "headers": {
          "Authorization": "Bearer <your-token>"
        }
      }
    }
  ]
}
```

## Usage

Continue will automatically invoke salt-cisco-mcp tools when you ask about Salt states or Cisco device configuration. It has access to the full tool surface: documentation search, master introspection, validation, dry-run, and (if enabled) write operations.
