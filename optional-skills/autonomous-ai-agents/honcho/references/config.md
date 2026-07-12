# Config Reference

Config file: `$HERMES_HOME/honcho.json` (profile-local) or `~/.honcho/config.json` (global).

## Key settings

| Key | Default | Description |
|-----|---------|-------------|
| `apiKey` | -- | API key ([get one](https://app.honcho.dev)) |
| `baseUrl` | -- | Base URL for self-hosted Honcho |
| `peerName` | -- | User peer identity |
| `aiPeer` | host key | AI peer identity |
| `workspace` | host key | Shared workspace ID |
| `recallMode` | `hybrid` | `hybrid`, `context`, or `tools` |
| `observation` | all on | Per-peer `observeMe`/`observeOthers` booleans |
| `writeFrequency` | `async` | `async`, `turn`, `session`, or integer N |
| `sessionStrategy` | `per-directory` | `per-directory`, `per-repo`, `per-session`, `global` |
| `messageMaxChars` | `25000` | Max chars per message (chunked if exceeded) |

## Dialectic settings

| Key | Default | Description |
|-----|---------|-------------|
| `dialecticReasoningLevel` | `low` | `minimal`, `low`, `medium`, `high`, `max` |
| `dialecticDynamic` | `true` | Auto-bump reasoning by query complexity. `false` = fixed level |
| `dialecticDepth` | `1` | Number of dialectic rounds per query (1-3) |
| `dialecticDepthLevels` | -- | Optional array of per-round levels, e.g. `["low", "high"]` |
| `dialecticMaxInputChars` | `10000` | Max chars for dialectic query input |

## Context budget and injection

| Key | Default | Description |
|-----|---------|-------------|
| `contextTokens` | uncapped | Max tokens for the combined base context injection (summary + representation + card). Opt-in cap — omit to leave uncapped, set to an integer to bound injection size. |
| `injectionFrequency` | `every-turn` | `every-turn` or `first-turn` |
| `contextCadence` | `1` | Min turns between context API calls |
| `dialecticCadence` | `2` | Min turns between dialectic LLM calls (recommended 1–5) |

The `contextTokens` budget is enforced at injection time. If the session summary + representation + card exceed the budget, Honcho trims the summary first, then the representation, preserving the card. This prevents context blowup in long sessions.

## Memory-context sanitization

Honcho sanitizes the `memory-context` block before injection to prevent prompt injection and malformed content:

- Strips XML/HTML tags from user-authored conclusions
- Normalizes whitespace and control characters
- Truncates individual conclusions that exceed `messageMaxChars`
- Escapes delimiter sequences that could break the system prompt structure

This fix addresses edge cases where raw user conclusions containing markup or special characters could corrupt the injected context block.

## Dialectic Depth Levels (detail)

`dialecticDepthLevels` lets you set the reasoning level for each round independently:

```json
{
  "dialecticDepth": 3,
  "dialecticDepthLevels": ["low", "medium", "high"]
}
```

If `dialecticDepthLevels` is omitted, rounds use **proportional levels** derived from `dialecticReasoningLevel` (the base):

| Depth | Pass levels |
|-------|-------------|
| 1 | [base] |
| 2 | [minimal, base] |
| 3 | [minimal, base, low] |

This keeps earlier passes cheap while using full depth on the final synthesis.

**Depth at session start.** The session-start prewarm runs the full configured `dialecticDepth` in the background before turn 1. A single-pass prewarm on a cold peer often returns thin output — multi-pass depth runs the audit/reconcile cycle before the user ever speaks. Turn 1 consumes the prewarm result directly; if prewarm hasn't landed in time, turn 1 falls back to a synchronous call with a bounded timeout.
