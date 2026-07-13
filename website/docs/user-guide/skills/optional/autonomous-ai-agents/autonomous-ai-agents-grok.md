---
title: "Grok — Delegate coding to xAI Grok Build CLI (features, PRs)"
sidebar_label: "Grok"
description: "Delegate coding to xAI Grok Build CLI (features, PRs)"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Grok

Delegate coding to xAI Grok Build CLI (features, PRs).

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/autonomous-ai-agents/grok` |
| Path | `optional-skills/autonomous-ai-agents/grok` |
| Version | `0.1.0` |
| Author | Matt Maximo (MattMaximo), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Coding-Agent`, `Grok`, `xAI`, `Code-Review`, `Refactoring`, `Automation` |
| Related skills | [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Grok Build CLI — Hermes Orchestration Guide

Delegate coding tasks to [Grok Build](https://docs.x.ai/build/overview) (xAI's
autonomous coding agent CLI, the `grok` command) via the Hermes terminal. Grok
can read files, write code, run shell commands, spawn subagents, and manage git
workflows. It runs three ways: an interactive TUI, **headless** (`-p`), and as
an **ACP agent** over JSON-RPC.

This is the third sibling to `codex` and `claude-code`. The orchestration
pattern is nearly identical — **prefer headless `-p` for one-shots**, use a PTY
for interactive sessions.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing
- Any task where you'd otherwise reach for Codex / Claude Code but want Grok

## Prerequisites

- **Install (preferred):** `npm install -g @xai-official/grok`
  - The official installer `curl -fsSL https://x.ai/cli/install.sh | bash` also
    works, but the `x.ai` host is Cloudflare-walled in some environments. The
    npm path avoids that dependency entirely.
- **Auth — SuperGrok / X Premium+ subscription (primary path):**
  - Run `grok login` once → opens a browser for OAuth → token cached in
    `~/.grok/auth.json`. This uses your **SuperGrok or X Premium+** subscription
    (no per-token API billing).
  - Check sign-in state by looking for `~/.grok/auth.json`, or run a cheap
    headless smoke test: `grok --no-auto-update -p "Say ok."`
  - In the TUI, `/logout` signs out and `/login` (or relaunching) signs back in.
- **No git repo required** — unlike Codex, Grok runs fine outside a git
  directory (good for scratch/throwaway tasks).
- **Claude Code / AGENTS.md compatible with zero config** — Grok auto-reads
  `CLAUDE.md`, `.claude/` (skills, agents, MCPs, hooks, rules), and the
  `AGENTS.md` family. Existing project context just works.

> **API-key fallback (not the default for this user):** Grok also supports
> setting the `XAI_API_KEY` environment variable for pay-as-you-go billing
> via `api.x.ai`. Only use
> this if `grok login` / SuperGrok auth is unavailable. The subscription path
> (`grok login`) is the intended setup here.

## Two Orchestration Modes

### Mode 1: Headless (`-p`) — Non-Interactive (PREFERRED)

Runs a one-shot task, prints the result, and exits. No PTY, no interactive
dialogs to navigate. This is the cleanest integration path — the analog of
`claude -p` and `codex exec`.

```
terminal(command="grok --no-auto-update -p 'Add a dark mode toggle to settings'", workdir="/path/to/project", timeout=180)
```

Always pass `--no-auto-update` in automation to skip background update checks.

**When to use headless:**
- One-shot coding tasks (fix a bug, add a feature, refactor)
- CI/CD automation and scripting
- Structured output parsing with `--output-format json`
- Any task that doesn't need multi-turn conversation

### Mode 2: Interactive PTY — Multi-Turn TUI Sessions

The TUI is a fullscreen, mouse-interactive app. Drive it with `pty=true`. For
robust monitoring/input use tmux (same pattern as the `claude-code` skill).

```
# Launch in a tmux session for capture-pane monitoring
terminal(command="tmux new-session -d -s grok-work -x 140 -y 40")
terminal(command="tmux send-keys -t grok-work 'cd /path/to/project && grok' Enter")

# Wait for startup, then send a task
terminal(command="sleep 5 && tmux send-keys -t grok-work 'Refactor the auth module to use JWT' Enter")

# Monitor progress
terminal(command="sleep 15 && tmux capture-pane -t grok-work -p -S -50")

# Exit when done
terminal(command="tmux send-keys -t grok-work '/quit' Enter && sleep 1 && tmux kill-session -t grok-work")
```

**Tip for headless-but-inline output:** if you want TUI-style output without the
fullscreen alt-screen takeover (e.g. for cleaner logs), add `--no-alt-screen`.
For pure automation, headless `-p` is still cleaner than the TUI.

## References

- `references/reference.md` — full flags table, output formats, background
  mode, session continuation, subcommands/TUI commands, and config file.
  Read it when constructing a non-trivial `grok` invocation or tuning
  `~/.grok/config.toml`.
- `references/workflows.md` — copy-paste patterns for read-only audit notes,
  PR review, and parallel worktree issue-fixing, plus the full pitfalls list.
  Read it before running one of those workflows or when something's not
  behaving as expected.

Quick flags to know now: `--no-auto-update` (always, in automation),
`--always-approve` (autonomous writes; omit for read-only work),
`--output-format json` (structured parsing), `-s/-r/-c` (session
create/resume/continue).

## Rules for Hermes Agents

1. **Prefer headless `-p`** for single tasks — cleanest integration, structured
   output via `--output-format json`.
2. **Always set `workdir`** (or `--cwd`) so Grok targets the right project.
3. **Pass `--no-auto-update`** in every automated invocation.
4. **Use `--always-approve` only when Grok should write autonomously**; omit it
   for read-only reviews and audits.
5. **Background long tasks** with `background=true, notify_on_complete=true` and
   monitor via the `process` tool.
6. **Use tmux for multi-turn interactive work** and monitor with
   `tmux capture-pane -t <session> -p -S -50`.
7. **Verify auth before relying on it** — check `~/.grok/auth.json` or run a
   cheap `grok -p "Say ok."` smoke test; don't assume Hermes' xAI auth carries
   over.
8. **Report results to the user** — summarize what Grok changed and what's left.
