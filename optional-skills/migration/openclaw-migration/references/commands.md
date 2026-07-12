# Command Reference, Path Resolution & Preset Contents

Full CLI invocations, script-path resolution rules, and the exact category
list per preset. SKILL.md keeps only the two most common invocations —
read this before running anything non-standard.

## Path resolution

The helper script lives in this skill directory at `scripts/openclaw_to_hermes.py`.
When this skill is installed from the Skills Hub, the normal location is:

```
~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py
```

Do not guess a shorter path like `~/.hermes/skills/openclaw-migration/...`.

Before running the helper:

1. Prefer the installed path under `~/.hermes/skills/migration/openclaw-migration/`.
2. If that path fails, inspect the installed skill directory and resolve the script relative to the installed `SKILL.md`.
3. Only use `find` as a fallback if the installed location is missing or the skill was moved manually.
4. When calling the terminal tool, do not pass `workdir: "~"`. Use an absolute directory such as the user's home directory, or omit `workdir` entirely.

With `--migrate-secrets`, it will also import a small allowlisted set of
Hermes-compatible secrets, currently: `TELEGRAM_BOT_TOKEN`.

## Migration preset contents

Prefer the two presets `user-data` and `full` in normal use; treat
category-level `--include`/`--exclude` as an advanced fallback, not the
default UX.

`user-data` includes:

- `soul`
- `workspace-agents`
- `memory`
- `user-profile`
- `messaging-settings`
- `command-allowlist`
- `skills`
- `tts-assets`
- `archive`

`full` includes everything in `user-data` plus:

- `secret-settings`

## Commands

Dry run with full discovery:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py
```

When using the terminal tool, prefer an absolute invocation pattern such as:

```json
{"command":"python3 /home/USER/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py","workdir":"/home/USER"}
```

Dry run with the user-data preset:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --preset user-data
```

Execute a user-data migration:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict skip
```

Execute a full compatible migration:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset full --migrate-secrets --skill-conflict skip
```

Execute with workspace instructions included:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict rename --workspace-target "/absolute/workspace/path"
```

Do not use `$PWD` or the home directory as the workspace target by default. Ask for an explicit workspace path first.
