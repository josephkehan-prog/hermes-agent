---
title: "Openclaw Migration — Migrate a user's OpenClaw customization footprint into Hermes Agent"
sidebar_label: "Openclaw Migration"
description: "Migrate a user's OpenClaw customization footprint into Hermes Agent"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Openclaw Migration

Migrate a user's OpenClaw customization footprint into Hermes Agent. Imports Hermes-compatible memories, SOUL.md, command allowlists, user skills, and selected workspace assets from ~/.openclaw, then reports exactly what could not be migrated and why.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/migration/openclaw-migration` |
| Path | `optional-skills/migration/openclaw-migration` |
| Version | `1.0.0` |
| Author | Hermes Agent (Nous Research) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Migration`, `OpenClaw`, `Hermes`, `Memory`, `Persona`, `Import` |
| Related skills | [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# OpenClaw -> Hermes Migration

Use this skill when a user wants to move their OpenClaw setup into Hermes Agent with minimal manual cleanup.

**Reference files:** `references/commands.md` — path resolution, preset category lists, and the full command set. `references/clarify-payloads.md` — exact copy-paste `clarify` JSON payloads.

## CLI Command

For a quick, non-interactive migration, use the built-in CLI command:

```bash
hermes claw migrate              # Full interactive migration
hermes claw migrate --dry-run    # Preview what would be migrated
hermes claw migrate --preset user-data   # Migrate without secrets
hermes claw migrate --overwrite  # Overwrite existing conflicts
hermes claw migrate --source /custom/path/.openclaw  # Custom source
```

The CLI command runs the same migration script described below. Use this skill (via the agent) when you want an interactive, guided migration with dry-run previews and per-item conflict resolution.

**First-time setup:** The `hermes setup` wizard automatically detects `~/.openclaw` and offers migration before configuration begins.

## What this skill does

It uses `scripts/openclaw_to_hermes.py` to:

- import `SOUL.md` into the Hermes home directory as `SOUL.md`
- transform OpenClaw `MEMORY.md` and `USER.md` into Hermes memory entries
- merge OpenClaw command approval patterns into Hermes `command_allowlist`
- migrate Hermes-compatible messaging settings such as `TELEGRAM_ALLOWED_USERS`, and map OpenClaw workspace settings to Hermes working-directory configuration
- copy OpenClaw skills into `~/.hermes/skills/openclaw-imports/`
- optionally copy the OpenClaw workspace instructions file into a chosen Hermes workspace
- mirror compatible workspace assets such as `workspace/tts/` into `~/.hermes/tts/`
- archive non-secret docs that do not have a direct Hermes destination
- produce a structured report listing migrated items, conflicts, skipped items, and reasons

## Path resolution

The helper script lives in this skill directory at `scripts/openclaw_to_hermes.py`
(installed normally at `~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py`
— do not guess a shorter path). Prefer that installed path; fall back to
resolving relative to the installed `SKILL.md`, then `find`, only if it's
missing or the skill was moved manually. When calling the terminal tool, do
not pass `workdir: "~"` — use an absolute directory or omit `workdir`.
Full resolution steps and the `--migrate-secrets` allowlist: read
`references/commands.md`.

## Default workflow

1. Inspect first with a dry run.
2. Present a simple summary of what can be migrated, what cannot be migrated, and what would be archived.
3. If the `clarify` tool is available, use it for user decisions instead of asking for a free-form prose reply.
4. If the dry run finds imported skill directory conflicts, ask how those should be handled before executing.
5. Ask the user to choose between the two supported migration modes before executing.
6. Ask for a target workspace path only if the user wants the workspace instructions file brought over.
7. Execute the migration with the matching preset and flags.
8. Summarize the results, especially:
   - what was migrated
   - what was archived for manual review
   - what was skipped and why

## User interaction protocol

Hermes CLI supports the `clarify` tool for interactive prompts (one choice at
a time, up to 4 predefined choices, no true multi-select). When `clarify` is
available and the dry run reveals any required user decision, your **next
action must be a `clarify` tool call** — never end the turn with a normal
prose message like "What would you like to do?" instead. `clarify` call
formatting hygiene (required fields, forbidden placeholder patterns, retry-
on-error): read `references/clarify-payloads.md`.

Treat `workspace-agents` as an unresolved decision whenever the dry run reports:

- `kind="workspace-agents"`
- `status="skipped"`
- reason containing `No workspace target was provided`

In that case, you must ask about workspace instructions before execution. Do not silently treat that as a decision to skip.

Because of that limitation, use this simplified decision flow: (1) `SOUL.md`
conflicts → choices `keep existing` / `overwrite with backup` / `review
first`; (2) skill conflicts (`kind="skill"`, `status="conflict"`) → `keep
existing skills` / `overwrite conflicting skills with backup` / `import
conflicting skills under renamed folders`; (3) workspace instructions →
`skip workspace instructions` / `copy to a workspace path` / `decide later`,
followed by an open-ended absolute-path question if they chose to copy (skip
`--workspace-target` for the other two choices); (4) migration mode →
`user-data only` (migrate user data + compatible config, no secrets) /
`full compatible migration` (same plus allowlisted secrets) / `cancel`. If
`clarify` is unavailable, ask the same questions in plain text but still
constrain the answer to those exact options.

**Execution gate:** do not execute while a `workspace-agents` skip caused by
`No workspace target was provided` remains unresolved (resolved only by the
user choosing `skip`/`decide later`, or supplying a path after `copy to a
workspace path` — absence of a target in the dry run is not itself
permission to execute), or while any other required `clarify` decision is
unresolved.

Exact copy-paste `clarify` payload shapes for all five decision points: read
`references/clarify-payloads.md`.

## Decision-to-command mapping

Map user decisions to command flags exactly:

- If the user chooses `keep existing` for `SOUL.md`, do **not** add `--overwrite`.
- If the user chooses `overwrite with backup`, add `--overwrite`.
- If the user chooses `review first`, stop before execution and review the relevant files.
- If the user chooses `keep existing skills`, add `--skill-conflict skip`.
- If the user chooses `overwrite conflicting skills with backup`, add `--skill-conflict overwrite`.
- If the user chooses `import conflicting skills under renamed folders`, add `--skill-conflict rename`.
- If the user chooses `user-data only`, execute with `--preset user-data` and do **not** add `--migrate-secrets`.
- If the user chooses `full compatible migration`, execute with `--preset full --migrate-secrets`.
- Only add `--workspace-target` if the user explicitly provided an absolute workspace path.
- If the user chooses `skip workspace instructions` or `decide later`, do not add `--workspace-target`.

Before executing, restate the exact command plan in plain language and make sure it matches the user's choices.

## Post-run reporting rules

After execution, treat the script's JSON output as the source of truth.

1. Base all counts on `report.summary`.
2. Only list an item under "Successfully Migrated" if its `status` is exactly `migrated`.
3. Do not claim a conflict was resolved unless the report shows that item as `migrated`.
4. Do not say `SOUL.md` was overwritten unless the report item for `kind="soul"` has `status="migrated"`.
5. If `report.summary.conflict > 0`, include a conflict section instead of silently implying success.
6. If counts and listed items disagree, fix the list to match the report before responding.
7. Include the `output_dir` path from the report when available so the user can inspect `report.json`, `summary.md`, backups, and archived files.
8. For memory or user-profile overflow, do not say the entries were archived unless the report explicitly shows an archive path. If `details.overflow_file` exists, say the full overflow list was exported there.
9. If a skill was imported under a renamed folder, report the final destination and mention `details.renamed_from`.
10. If `report.skill_conflict_mode` is present, use it as the source of truth for the selected imported-skill conflict policy.
11. If an item has `status="skipped"`, do not describe it as overwritten, backed up, migrated, or resolved.
12. If `kind="soul"` has `status="skipped"` with reason `Target already matches source`, say it was left unchanged and do not mention a backup.
13. If a renamed imported skill has an empty `details.backup`, do not imply the existing Hermes skill was renamed or backed up. Say only that the imported copy was placed in the new destination and reference `details.renamed_from` as the pre-existing folder that remained in place.

## Migration presets

Prefer two presets in normal use: `user-data` (soul, workspace-agents, memory,
user-profile, messaging-settings, command-allowlist, skills, tts-assets,
archive) and `full` (everything in `user-data` plus `secret-settings`). The
helper script also supports category-level `--include`/`--exclude`, but
treat that as an advanced fallback rather than the default UX. Full category
list: `references/commands.md`.

## Commands

Dry run with full discovery:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py
```

Execute a user-data migration:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict skip
```

Do not use `$PWD` or the home directory as the workspace target by default —
ask for an explicit workspace path first. Full command set (full/dry-run
presets, workspace-target execution, terminal-tool invocation pattern):
read `references/commands.md`.

## Important rules

1. Run a dry run before writing unless the user explicitly says to proceed immediately.
2. Do not migrate secrets by default — tokens, auth blobs, device credentials, and raw gateway config stay out of Hermes unless the user explicitly asks for secret migration.
3. Do not silently overwrite non-empty Hermes targets unless the user explicitly wants that (the helper script preserves backups when overwriting is enabled).
4. Always give the user the skipped-items report — it's part of the migration, not an optional extra.
5. Prefer the primary OpenClaw workspace (`~/.openclaw/workspace/`) over `workspace.default/`; use the default only as fallback when primary files are missing.
6. Even in secret-migration mode, only migrate secrets with a clean Hermes destination — unsupported auth blobs must still be reported as skipped.
7. If the dry run shows a large asset copy, a conflicting `SOUL.md`, or overflowed memory entries, call those out separately before execution.
8. Default to `user-data only` if the user is unsure.
9. Only include `workspace-agents` when the user has explicitly provided a destination workspace path.
10. Treat category-level `--include`/`--exclude` as an advanced escape hatch, not the normal flow.
11. Do not end the dry-run summary with a vague "What would you like to do?" if `clarify` is available — use structured follow-up prompts instead, and never an open-ended prompt when a real choice prompt would work (free text only for absolute paths or file review requests).
12. After a dry run, never stop after summarizing if a decision is unresolved — use `clarify` immediately for the highest-priority blocking one. Priority order: `SOUL.md` conflict, imported skill conflicts, migration mode, workspace instructions destination.
13. Do not promise to present choices later in the same message — present them by actually calling `clarify`. After the migration-mode answer, explicitly check whether `workspace-agents` is still unresolved and if so make the workspace-instructions `clarify` call next. After any `clarify` answer, if another required decision remains, do not narrate what was just decided — ask the next required question immediately.

## Expected result

After a successful run, the user should have:

- Hermes persona state imported
- Hermes memory files populated with converted OpenClaw knowledge
- OpenClaw skills available under `~/.hermes/skills/openclaw-imports/`
- a migration report showing any conflicts, omissions, or unsupported data
