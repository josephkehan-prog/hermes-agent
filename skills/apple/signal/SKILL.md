---
name: signal
description: Send and receive messages via Signal using signal-cli CLI or the Signal MCP server. Covers account status, sending, receiving, groups, and contacts.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [Signal, messaging, signal-cli, MCP]
prerequisites:
  commands: [signal-cli]
---

# Signal

Send and receive messages via Signal using `signal-cli` CLI or the `signal-mcp` server.

## Prerequisites

- **signal-cli** installed (Homebrew: `brew install signal-cli`, or via npm)
- Signal account registered and linked to a phone number
- signal-cli daemon running (check with `pgrep -f signal-cli`)
- Config directory: `~/.local/share/signal-cli/` (default)

## When to Use

- User asks to send or receive a Signal message
- Checking Signal account status or contacts
- Sending to phone numbers or Signal usernames
- Working with Signal groups
- User mentions "Signal", "send via Signal", or "Signal message"

## Connection Approaches

### 1. Direct CLI (immediate, no setup)
Use `signal-cli` commands directly via terminal. Fastest path — no MCP server needed.

```bash
# Send a message
signal-cli --config ~/.local/share/signal-cli send -a <account> -p <phone_number> -m "Hello"

# List registered accounts
signal-cli --config ~/.local/share/signal-cli listAccounts

# Receive messages (daemon mode)
signal-cli --config ~/.local/share/signal-cli daemon
```

### 2. MCP Server (integrated, tool-based)
Use `googlarz/signal-mcp` via the hub gateway for structured tool calls. Add to registry with `hub trust signal-mcp`.

## Quick Reference

### Send Message (CLI)
```bash
signal-cli --config ~/.local/share/signal-cli send -a <account> -p <phone_number> -m "message text"
```

### Send to Group
```bash
signal-cli --config ~/.local/share/signal-cli send -a <account> -g <group_id> -m "message text"
```

### List Accounts
```bash
signal-cli --config ~/.local/share/signal-cli listAccounts
```

### List Contacts
```bash
signal-cli --config ~/.local/share/signal-cli listContacts
```

### List Groups
```bash
signal-cli --config ~/.local/share/signal-cli listGroups
```

### Receive Messages (daemon)
```bash
signal-cli --config ~/.local/share/signal-cli daemon -n <phone_number>
```

## Pitfalls

1. **signal-cli timeout** — `listAccounts` can hang if the daemon isn't running. Check with `pgrep -f signal-cli` first.
2. **Config path** — signal-cli uses `~/.local/share/signal-cli/` by default. If your account is elsewhere, pass `--config <path>`.
3. **Phone number format** — use E.164 format (+1XXXXXXXXXX) for reliable delivery.
4. **Daemon vs direct** — `send` works without the daemon, but `receive` requires it. Start the daemon if you need to read incoming messages.
5. **MCP server availability** — `googlarz/signal-mcp` is discoverable but not yet in the registry. Trust it with `hub trust signal-mcp` to enable gateway access.

## Rules

1. **Always confirm recipient** before sending (phone number or group name).
2. **Verify signal-cli is running** before expensive operations.
3. **Use E.164 format** for phone numbers.
4. **Prefer CLI for one-off sends**, MCP for repeated/structured interactions.

## Example Workflow

User: "Send a Signal message to +14155551212"

```bash
# 1. Check daemon is running
pgrep -f signal-cli

# 2. Send message
signal-cli --config ~/.local/share/signal-cli send -a <account> -p +14155551212 -m "Hello from Signal!"

# 3. Confirm success
```
