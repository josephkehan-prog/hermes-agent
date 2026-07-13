---
title: "Honcho"
sidebar_label: "Honcho"
description: "Configure and use Honcho memory with Hermes -- cross-session user modeling, multi-profile peer isolation, observation config, dialectic reasoning, session su..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Honcho

Configure and use Honcho memory with Hermes -- cross-session user modeling, multi-profile peer isolation, observation config, dialectic reasoning, session summaries, and context budget enforcement. Use when setting up Honcho, troubleshooting memory, managing profiles with Honcho peers, or tuning observation, recall, and dialectic settings.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/autonomous-ai-agents/honcho` |
| Path | `optional-skills/autonomous-ai-agents/honcho` |
| Version | `2.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Honcho`, `Memory`, `Profiles`, `Observation`, `Dialectic`, `User-Modeling`, `Session-Summary` |
| Related skills | [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Honcho Memory for Hermes

Honcho provides AI-native cross-session user modeling. It learns who the user is across conversations and gives every Hermes profile its own peer identity while sharing a unified view of the user.

## When to Use

- Setting up Honcho (cloud or self-hosted)
- Troubleshooting memory not working / peers not syncing
- Creating multi-profile setups where each agent has its own Honcho peer
- Tuning observation, recall, dialectic depth, or write frequency settings
- Understanding what the 5 Honcho tools do and when to use them
- Configuring context budgets and session summary injection

## Setup

### Cloud (app.honcho.dev)

```bash
hermes memory setup honcho
# select "cloud", paste API key from https://app.honcho.dev
```

### Self-hosted

```bash
hermes memory setup honcho
# select "local", enter base URL (e.g. http://localhost:8000)
```

See: https://docs.honcho.dev/v3/guides/integrations/hermes#running-honcho-locally-with-hermes

### Verify

```bash
hermes honcho status    # shows resolved config, connection test, peer info
```

## Architecture

Honcho injects a base context block (session summary → user representation → AI
peer card) into the system prompt in `hybrid`/`context` recall modes, automatically
choosing a cold-start (lightweight, no summary) or warm-start (full injection)
prompt based on session state. Conversations are modeled as **peers** — a user
peer and a per-profile AI peer, each with `observeMe`/`observeOthers` toggles
(default: all on). Sessions scope where messages land (`per-directory` default;
override with `hermes honcho map <name>`). Recall mode controls whether context
auto-injects and whether tools are exposed (`hybrid` both, `context` inject-only,
`tools` explicit-only).

Full detail — base context injection order, cold/warm selection table, peer
observation presets (`directional`/`unified`) and JSON config, session strategy
table, recall mode table: read [references/architecture.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/autonomous-ai-agents/honcho/references/architecture.md).

## Three Orthogonal Knobs

Honcho's dialectic behavior is controlled by three independent dimensions. Each can be tuned without affecting the others:

### Cadence (when)

Controls **how often** dialectic and context calls happen.

| Key | Default | Description |
|-----|---------|-------------|
| `contextCadence` | `1` | Min turns between context API calls |
| `dialecticCadence` | `2` | Min turns between dialectic API calls. Recommended 1–5 |
| `injectionFrequency` | `every-turn` | `every-turn` or `first-turn` for base context injection |

Higher cadence values fire the dialectic LLM less often. `dialecticCadence: 2` means the engine fires every other turn. Setting it to `1` fires every turn.

### Depth (how many)

Controls **how many rounds** of dialectic reasoning Honcho performs per query.

| Key | Default | Range | Description |
|-----|---------|-------|-------------|
| `dialecticDepth` | `1` | 1-3 | Number of dialectic reasoning rounds per query |
| `dialecticDepthLevels` | -- | array | Optional per-depth-round level overrides (see below) |

`dialecticDepth: 2` means Honcho runs two rounds of dialectic synthesis. The first round produces an initial answer; the second refines it. If `dialecticDepthLevels` is omitted, rounds use proportional levels derived from `dialecticReasoningLevel` (cheap early passes, full depth on the final synthesis). Full table, the session-start prewarm behavior, and manual per-round level overrides: read [references/config.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/autonomous-ai-agents/honcho/references/config.md).

### Level (how hard)

Controls the **intensity** of each dialectic reasoning round.

| Key | Default | Description |
|-----|---------|-------------|
| `dialecticReasoningLevel` | `low` | `minimal`, `low`, `medium`, `high`, `max` |
| `dialecticDynamic` | `true` | When `true`, the model can pass `reasoning_level` to `honcho_reasoning` to override the default per-call. `false` = always use `dialecticReasoningLevel`, model overrides ignored |

Higher levels produce richer synthesis but cost more tokens on Honcho's backend.

## Multi-Profile Setup

Each Hermes profile gets its own Honcho AI peer while sharing the same workspace (user context). This means:

- All profiles see the same user representation
- Each profile builds its own AI identity and observations
- Conclusions written by one profile are visible to others via the shared workspace

### Create a profile with Honcho peer

```bash
hermes profile create coder --clone
# creates host block hermes.coder, AI peer "coder", inherits config from default
```

What `--clone` does for Honcho:
1. Creates a `hermes.coder` host block in `honcho.json`
2. Sets `aiPeer: "coder"` (the profile name)
3. Inherits `workspace`, `peerName`, `writeFrequency`, `recallMode`, etc. from default
4. Eagerly creates the peer in Honcho so it exists before first message

### Backfill existing profiles

```bash
hermes honcho sync    # creates host blocks for all profiles that don't have one yet
```

### Per-profile config

Override any setting in the host block:

```json
{
  "hosts": {
    "hermes.coder": {
      "aiPeer": "coder",
      "recallMode": "tools",
      "dialecticDepth": 2,
      "observation": {
        "user": { "observeMe": true, "observeOthers": false },
        "ai": { "observeMe": true, "observeOthers": true }
      }
    }
  }
}
```

## Tools

The agent has 5 bidirectional Honcho tools (hidden in `context` recall mode):

| Tool | LLM call? | Cost | Use when |
|------|-----------|------|----------|
| `honcho_profile` | No | minimal | Quick factual snapshot at conversation start or for fast name/role/pref lookups |
| `honcho_search` | No | low | Fetch specific past facts to reason over yourself — raw excerpts, no synthesis |
| `honcho_context` | No | low | Full session context snapshot: summary, representation, card, recent messages |
| `honcho_reasoning` | Yes | medium–high | Natural language question synthesized by Honcho's dialectic engine |
| `honcho_conclude` | No | minimal | Write or delete a persistent fact; pass `peer: "ai"` for AI self-knowledge |

Per-tool detail (exact params, token limits, defaults): read [references/tools.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/autonomous-ai-agents/honcho/references/tools.md).

### Bidirectional peer targeting

All 5 tools accept an optional `peer` parameter:
- `peer: "user"` (default) — operates on the user peer
- `peer: "ai"` — operates on this profile's AI peer
- `peer: "<explicit-id>"` — any peer ID in the workspace

Examples:
```
honcho_profile                        # read user's card
honcho_profile peer="ai"              # read AI peer's card
honcho_reasoning query="What does this user care about most?"
honcho_reasoning query="What are my interaction patterns?" peer="ai" reasoning_level="medium"
honcho_conclude conclusion="Prefers terse answers"
honcho_conclude conclusion="I tend to over-explain code" peer="ai"
honcho_conclude delete_id="abc123"    # PII removal
```

## Agent Usage Patterns

Guidelines for Hermes when Honcho memory is active.

### On conversation start

```
1. honcho_profile                  → fast warmup, no LLM cost
2. If context looks thin → honcho_context  (full snapshot, still no LLM)
3. If deep synthesis needed → honcho_reasoning  (LLM call, use sparingly)
```

Do NOT call `honcho_reasoning` on every turn. Auto-injection already handles ongoing context refresh. Use the reasoning tool only when you genuinely need synthesized insight the base context doesn't provide.

### When the user shares something to remember

```
honcho_conclude conclusion="<specific, actionable fact>"
```

Good conclusions: "Prefers code examples over prose explanations", "Working on a Rust async project through April 2026"
Bad conclusions: "User said something about Rust" (too vague), "User seems technical" (already in representation)

### When the user asks about past context / you need to recall specifics

```
honcho_search query="<topic>"       → fast, no LLM, good for specific facts
honcho_context                       → full snapshot with summary + messages
honcho_reasoning query="<question>"  → synthesized answer, use when search isn't enough
```

### When to use `peer: "ai"`

Use AI peer targeting to build and query the agent's own self-knowledge:
- `honcho_conclude conclusion="I tend to be verbose when explaining architecture" peer="ai"` — self-correction
- `honcho_reasoning query="How do I typically handle ambiguous requests?" peer="ai"` — self-audit
- `honcho_profile peer="ai"` — review own identity card

### When NOT to call tools

In `hybrid` and `context` modes, base context (user representation + card + session summary) is auto-injected before every turn. Do not re-fetch what was already injected. Call tools only when:
- You need something the injected context doesn't have
- The user explicitly asks you to recall or check memory
- You're writing a conclusion about something new

### Cadence awareness

`honcho_reasoning` on the tool side shares the same cost as auto-injection dialectic. After an explicit tool call, the auto-injection cadence resets — avoiding double-charging the same turn.

## Config Reference

Config file: `$HERMES_HOME/honcho.json` (profile-local) or `~/.honcho/config.json` (global).
Most commonly tuned keys: `recallMode` (`hybrid`/`context`/`tools`), `dialecticReasoningLevel`
(`minimal`→`max`), `dialecticDepth` (1-3), `contextTokens` (injection budget cap), `writeFrequency`,
`sessionStrategy`. Full key/default/description tables for base settings, dialectic settings,
context budget and injection, plus how memory-context sanitization strips XML/HTML and escapes
delimiter sequences before injection: read [references/config.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/autonomous-ai-agents/honcho/references/config.md).

## Troubleshooting

Common issues: "Honcho not configured" (run `hermes honcho setup`), memory not persisting
(`writeFrequency: session` only writes on exit), a profile not getting its own peer (use
`--clone` or `hermes honcho sync`), and context injection too large (lower `contextTokens` or
`dialecticDepth`). Full troubleshooting guide (6 issues with root causes): read
[references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/autonomous-ai-agents/honcho/references/troubleshooting.md).

## CLI Commands

| Command | Description |
|---------|-------------|
| `hermes honcho setup` | Interactive setup wizard (cloud/local, identity, observation, recall, sessions) |
| `hermes honcho status` | Show resolved config, connection test, peer info for active profile |
| `hermes honcho enable` | Enable Honcho for the active profile (creates host block if needed) |
| `hermes honcho disable` | Disable Honcho for the active profile |
| `hermes honcho peer` | Show or update peer names (`--user <name>`, `--ai <name>`, `--reasoning <level>`) |
| `hermes honcho peers` | Show peer identities across all profiles |
| `hermes honcho mode` | Show or set recall mode (`hybrid`, `context`, `tools`) |
| `hermes honcho tokens` | Show or set token budgets (`--context <N>`, `--dialectic <N>`) |
| `hermes honcho sessions` | List known directory-to-session-name mappings |
| `hermes honcho map <name>` | Map current working directory to a Honcho session name |
| `hermes honcho identity` | Seed AI peer identity or show both peer representations |
| `hermes honcho sync` | Create host blocks for all Hermes profiles that don't have one yet |
| `hermes honcho migrate` | Step-by-step migration guide from OpenClaw native memory to Hermes + Honcho |
| `hermes memory setup` | Generic memory provider picker (selecting "honcho" runs the same wizard) |
| `hermes memory status` | Show active memory provider and config |
| `hermes memory off` | Disable external memory provider |
