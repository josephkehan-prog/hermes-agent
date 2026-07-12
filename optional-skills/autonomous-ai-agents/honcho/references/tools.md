# Tool Detail

Per-tool detail for the 5 bidirectional Honcho tools summarized in SKILL.md.

## `honcho_profile`
Read or update a peer card — curated key facts (name, role, preferences, communication style). Pass `card: [...]` to update; omit to read. No LLM call.

## `honcho_search`
Semantic search over stored context for a specific peer. Returns raw excerpts ranked by relevance, no synthesis. Default 800 tokens, max 2000. Good when you need specific past facts to reason over yourself rather than a synthesized answer.

## `honcho_context`
Full session context snapshot from Honcho — session summary, peer representation, peer card, and recent messages. No LLM call. Use when you want to see everything Honcho knows about the current session and peer in one shot.

## `honcho_reasoning`
Natural language question answered by Honcho's dialectic reasoning engine (LLM call on Honcho's backend). Higher cost, higher quality. Pass `reasoning_level` to control depth: `minimal` (fast/cheap) → `low` → `medium` → `high` → `max` (thorough). Omit to use the configured default (`low`). Use for synthesized understanding of the user's patterns, goals, or current state.

## `honcho_conclude`
Write or delete a persistent conclusion about a peer. Pass `conclusion: "..."` to create. Pass `delete_id: "..."` to remove a conclusion (for PII removal — Honcho self-heals incorrect conclusions over time, so deletion is only needed for PII). You MUST pass exactly one of the two.
