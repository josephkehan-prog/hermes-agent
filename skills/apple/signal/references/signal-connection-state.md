# Signal Connection State (discovered 2026-07-06)

## Environment

- **signal-cli**: v0.14.5, installed via Homebrew at `/opt/homebrew/bin/signal-cli`
- **Config**: `~/.local/share/signal-cli/` with account data in `data/934890`
- **Account**: Registered (LIVE environment), phone number 934890
- **Daemon**: Running (PID 1105)
- **MCP Server**: `googlarz/signal-mcp` available on aggregator, not yet in registry

## Key Commands

```bash
# Check daemon
pgrep -f signal-cli

# List accounts
signal-cli --config ~/.local/share/signal-cli listAccounts

# Send message
signal-cli --config ~/.local/share/signal-cli send -a <account> -p <phone> -m "text"

# Start daemon if needed
signal-cli --config ~/.local/share/signal-cli daemon -n <phone>
```

## Adoption Note

To enable the MCP server: `hub trust signal-mcp` (googlarz/signal-mcp).
This adds it to the registry for gateway access.
