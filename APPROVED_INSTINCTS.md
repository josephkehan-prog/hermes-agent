# Approved Instincts — Plain-English Summary

_What "instincts" are: small notes the learning system watched me do over and over, then saved so future sessions repeat the good habit automatically. Each one is a "when X, do Y" rule with a confidence score (how sure the system is). Below is everything you approved, per project._

_Generated 2026-07-11._

---

## hermes-agent (2 approved)

These two are notes about the learning tool itself — the exact bugs I hit while setting it up.

| Habit | What it means | Confidence |
|---|---|---|
| Unset `CLAUDE_PROJECT_DIR` before looping over folders | When running a script across many project folders, an old environment variable was silently sending every run to the wrong project. Clear it first. | 0.7 |
| One-shot backfills must call the analyzer directly | The observer refuses to run outside a live session, so a manual "catch up on old data" run does nothing. Call the analysis step straight instead. Also: macOS has no `timeout` command — use a background watchdog. | 0.7 |

## agentic-os (3 approved)

Build/tooling habits for the Rust + hub project.

| Habit | What it means | Confidence |
|---|---|---|
| Load the Node path before npm in `hub/` | Node isn't on the default PATH; add the mise Node folder to PATH first or npm commands fail. | 0.85 |
| Filter zoxide noise from `hub/` output | A shell add-on spams warning lines; pipe output through a filter to keep it readable. | 0.7 |
| Always build/test with `--release` | Every cargo build and test used `--release`, never plain debug. | 0.7 |
| _(dropped)_ python3-for-JSON | Not kept for this project. | — |

## Config (~/.claude setup work) (4 approved)

Habits for editing Claude's own config files.

| Habit | What it means | Confidence |
|---|---|---|
| Use `python3` over `jq` for JSON | Inspect/validate config JSON with a python one-liner, not jq — even though jq is installed. Seen 46 times. | 0.85 |
| Back up before editing config | Copy the file to a timestamped `.bak` before changing settings.json or a hook script. | 0.7 |
| Strip color codes before parsing | Colorized CLI output breaks `grep`; strip the color codes first. | 0.7 |
| Filter zoxide noise | Same shell-add-on spam filter as above, for `claude`/`gh` commands. | 0.5 |

## game-studios (1 approved)

| Habit | What it means | Confidence |
|---|---|---|
| Careful, scoped commits | Stage only the specific files for one change (never "add everything"), write a proper conventional-commit message, then confirm with `git log`. Seen 11+ times. | 0.85 |

## KDP-Ebook-Studio (2 approved)

A book/writing project — mostly markdown, so habits are about readable command output.

| Habit | What it means | Confidence |
|---|---|---|
| `echo === section headers` | Print `=== label ===` separators between steps of a combined bash command so the output is readable. Seen 27 times. | 0.85 |
| Absolute `cd` to project root | Use the full path when changing into the project root, not relative paths. Seen 70 times. | 0.85 |

---

## Totals: 12 instincts across 5 projects

## Not approved / no result

- **mac** — analyzed, nothing repeated 3+ times cleanly. No instincts.
- **agentic-os python3-for-JSON**; **game-studios** pytest-tail / TDD-coverage / Ren'Py-lint — you chose not to keep these.
- All 12 written files validated (YAML frontmatter parses, required fields present).

## Where they live

Each project's instincts are stored at:
`~/.local/share/ecc-homunculus/projects/<project-id>/instincts/personal/`

The background observer is now **on** (`observer.enabled: true`), so future sessions keep learning new habits automatically.
