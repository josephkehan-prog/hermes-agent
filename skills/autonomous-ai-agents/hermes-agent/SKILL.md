---
name: hermes-agent
description: "Configure, extend, or contribute to Hermes Agent."
version: 2.3.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, a native desktop app, messaging platforms, and IDEs. It's in the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, Google, DeepSeek, xAI, local models, and 20+ others) and runs on Linux, macOS, Windows, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, iMessage, Signal, Matrix, Teams, Email, and a dozen more platforms with full tool access, not just chat.
- **Many surfaces** — the same agent core drives the CLI, the Ink TUI, a native Electron desktop app, a web dashboard, and an ACP server for IDEs (VS Code / Zed / JetBrains).
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Scope & Verification

This skill is a concise operating guide, not the complete source of truth for every Hermes feature. If a Hermes feature, command, or setting is not mentioned here, do not treat that absence as evidence that it does not exist. Check the live repository and official docs before giving a negative answer.

Good verification targets:

- CLI commands: `hermes --help`, `hermes <command> --help`, and `hermes_cli/main.py`
- User documentation: https://hermes-agent.nousresearch.com/docs/
- Source tree: https://github.com/NousResearch/hermes-agent

## Quick Start

```bash
# Install (shell installer — sets up uv, Python, the venv, and the launcher)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Or via PyPI (ships the TUI bundle + shell launcher)
pip install hermes-agent       # or: uv pip install hermes-agent

# Interactive chat (default surface; set display.interface: tui to launch the Ink TUI instead)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard  /  pick model+provider  /  health check
hermes setup
hermes model
hermes doctor

# Other surfaces
hermes desktop                 # launch the native desktop app (alias: hermes gui)
hermes dashboard               # web admin panel + embedded chat
hermes proxy                   # OpenAI-compatible local proxy backed by your OAuth provider
```

---

## CLI Quick Reference

```
hermes                       Interactive chat (default surface)
hermes chat -q "..."         Single non-interactive query
hermes setup / model / doctor / status   Wizard, model picker, health check
hermes tools / skills / mcp / gateway / sessions / cron / webhook / profile / auth
                              Subcommand groups — each has list/add/remove/etc.
hermes desktop / dashboard / proxy / kanban / insights / update
```

`hermes <command> --help` gives exact flags for any subcommand. Full CLI
flag-by-flag reference (Chat flags, all `hermes config`/`tools`/`skills`/
`mcp`/`gateway`/`sessions`/`cron`/`webhook`/`profile`/`auth` subcommands) and
the complete in-session **slash command** list: read
`references/cli-and-commands.md` when you need an exact flag or command name.

Native MCP client details (stdio/HTTP discovery, `hermes mcp install`):
`references/native-mcp.md`. Webhook route setup and payload templating:
`references/webhooks.md`.

---

## Key Paths

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets (under $HERMES_HOME if set)
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Gateway routing index, transcripts
~/.hermes/state.db          Canonical session store (SQLite + FTS5)
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout. Edit config
with `hermes config edit` or `hermes config set section.key value`; full
config-section table, the 20+ provider list with env vars, the full toolset
table, project context file discovery (`.hermes.md`/`AGENTS.md`/`CLAUDE.md`),
security/privacy toggles (secret redaction, PII redaction, approval modes),
and voice (STT/TTS) setup: read `references/configuration.md` when tuning
any of these.

**Hard rule:** tool/skill changes take effect on `/reset` (new session) only
— they do NOT apply mid-conversation, to preserve prompt caching.

---

## Multi-Agent & Background Work

- **`delegate_task`** — spawn an isolated subagent (single, batch, or
  background) for quick parallel subtasks within the parent process.
- **Spawning a separate `hermes` process** (via `terminal`/tmux) — for
  long-running, fully independent, or interactive agent instances.
- **`cronjob` tool / `hermes cron`** — durable scheduled jobs that survive
  process restarts.
- **Curator** — background lifecycle maintenance for agent-created skills
  (never deletes; only archives).
- **Kanban** — durable SQLite work-queue board for multi-profile/worker
  collaboration.

Full walkthroughs (one-shot vs interactive PTY spawning, multi-agent
coordination patterns, session resume, delegation/cron/curator/kanban
config knobs and invariants, plus the desktop app, web dashboard, and OpenAI-
compatible proxy): read `references/advanced-features.md` before spawning
or orchestrating multiple agents.

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Profiles | `hermes profile list` or [Profiles docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron jobs | `hermes cron list` or [Cron docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Memory | `hermes memory status` or [Memory docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Env variables | `hermes config env-path` or [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI commands | `hermes --help` or [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Session files | `hermes sessions browse` (reads state.db) |
| Source code | `~/.hermes/hermes-agent/` |

---

## Troubleshooting

Fast triage for the common cases: voice not working, tool not available,
model/provider issues (including the Copilot 403 OAuth gotcha), changes not
taking effect, skills not showing, gateway issues (SSH logout, WSL2 close,
crash loop), platform-specific issues (Discord Message Content Intent, Slack
`message.channels`), and auxiliary-model (vision/compression/session_search)
failures. Windows has its own set of gotchas (Alt+Enter, WinError 10106,
UTF-8 BOM config, POSIX-only test runner, line endings). Read
`references/troubleshooting-and-dev.md` when something isn't working or
when running Hermes on Windows.

---

## Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs:
https://hermes-agent.nousresearch.com/docs/developer-guide/

**Hard rules (violating these gets a PR rejected):**

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met
- Always run tests via `scripts/run_tests.sh` (enforces CI-parity — hermetic env, unset credentials, TZ=UTC), never bare `pytest`

Project layout, the two-file "adding a tool" recipe (with a full
`registry.register()` example), adding a slash command, the high-level
agent-loop shape, testing details (cross-platform skip guards, the
`sys.platform` monkeypatch trap), the system prompt's execution-environment
block, and commit conventions: read `references/troubleshooting-and-dev.md`
when contributing a patch.
