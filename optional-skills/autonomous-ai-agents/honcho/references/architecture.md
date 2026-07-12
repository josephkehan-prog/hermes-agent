# Architecture Detail

## Base Context Injection

When Honcho injects context into the system prompt (in `hybrid` or `context` recall modes), it assembles the base context block in this order:

1. **Session summary** -- a short digest of the current session so far (placed first so the model has immediate conversational continuity)
2. **User representation** -- Honcho's accumulated model of the user (preferences, facts, patterns)
3. **AI peer card** -- the identity card for this Hermes profile's AI peer

The session summary is generated automatically by Honcho at the start of each turn (when a prior session exists). It gives the model a warm start without replaying full history.

## Cold / Warm Prompt Selection

Honcho automatically selects between two prompt strategies:

| Condition | Strategy | What happens |
|-----------|----------|--------------|
| No prior session or empty representation | **Cold start** | Lightweight intro prompt; skips summary injection; encourages the model to learn about the user |
| Existing representation and/or session history | **Warm start** | Full base context injection (summary → representation → card); richer system prompt |

You do not need to configure this -- it is automatic based on session state.

## Peers

Honcho models conversations as interactions between **peers**. Hermes creates two peers per session:

- **User peer** (`peerName`): represents the human. Honcho builds a user representation from observed messages.
- **AI peer** (`aiPeer`): represents this Hermes instance. Each profile gets its own AI peer so agents develop independent views.

## Observation

Each peer has two observation toggles that control what Honcho learns from:

| Toggle | What it does |
|--------|-------------|
| `observeMe` | Peer's own messages are observed (builds self-representation) |
| `observeOthers` | Other peers' messages are observed (builds cross-peer understanding) |

Default: all four toggles **on** (full bidirectional observation).

Configure per-peer in `honcho.json`:

```json
{
  "observation": {
    "user": { "observeMe": true, "observeOthers": true },
    "ai":   { "observeMe": true, "observeOthers": true }
  }
}
```

Or use the shorthand presets:

| Preset | User | AI | Use case |
|--------|------|----|----------|
| `"directional"` (default) | me:on, others:on | me:on, others:on | Multi-agent, full memory |
| `"unified"` | me:on, others:off | me:off, others:on | Single agent, user-only modeling |

Settings changed in the [Honcho dashboard](https://app.honcho.dev) are synced back on session init -- server-side config wins over local defaults.

## Sessions

Honcho sessions scope where messages and observations land. Strategy options:

| Strategy | Behavior |
|----------|----------|
| `per-directory` (default) | One session per working directory |
| `per-repo` | One session per git repository root |
| `per-session` | New Honcho session each Hermes run |
| `global` | Single session across all directories |

Manual override: `hermes honcho map my-project-name`

## Recall Modes

How the agent accesses Honcho memory:

| Mode | Auto-inject context? | Tools available? | Use case |
|------|---------------------|-----------------|----------|
| `hybrid` (default) | Yes | Yes | Agent decides when to use tools vs auto context |
| `context` | Yes | No (hidden) | Minimal token cost, no tool calls |
| `tools` | No | Yes | Agent controls all memory access explicitly |
