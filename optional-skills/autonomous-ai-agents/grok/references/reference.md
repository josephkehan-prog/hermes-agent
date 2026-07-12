# Grok Build CLI — Command Reference

Detailed flags, output formats, background/session mechanics, subcommands, and
config. Read this when constructing a non-trivial `grok` invocation or tuning
persistent config.

## Headless Deep Dive

### Common Flags

| Flag | Effect |
|------|--------|
| `-p, --single <PROMPT>` | Send one prompt, run headless, exit |
| `-m, --model <MODEL>` | Choose a model |
| `-s, --session-id <ID>` | Create or resume a named headless session |
| `-r, --resume <ID>` | Resume an existing session |
| `-c, --continue` | Continue the most recent session in the current directory |
| `--cwd <PATH>` | Set the working directory |
| `--output-format <FMT>` | `plain` (default), `json`, or `streaming-json` |
| `--always-approve` | Auto-approve all tool executions (the `--full-auto` / `--yolo` equivalent) |
| `--no-alt-screen` | Run inline, no fullscreen TUI takeover |
| `--no-auto-update` | Skip background update checks (use in all automation) |

### Output Formats

- `plain` — human-readable text (default)
- `json` — one JSON object at the end of the run (parse the result cleanly)
- `streaming-json` — newline-delimited JSON events as they arrive

```
# Structured result for parsing
terminal(command="grok --no-auto-update -p 'List all TODO comments in src/' --output-format json", workdir="/project", timeout=120)

# Auto-approve for autonomous building
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the database layer and run the tests'", workdir="/project", timeout=300)
```

### Background Mode (Long Tasks)

```
# Start headless in background
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the auth module'", workdir="/project", background=true, notify_on_complete=true)
# Returns session_id

# Monitor
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Kill if needed
process(action="kill", session_id="<id>")
```

For an interactive (TUI) background session, use `pty=true` + tmux and monitor
with `tmux capture-pane`, exactly like the `claude-code` / `codex` skills.

### Session Continuation

```
# Start a named session
terminal(command="grok --no-auto-update -s refactor-db -p 'Start refactoring the database layer' --always-approve", workdir="/project", timeout=240)

# Resume it later
terminal(command="grok --no-auto-update -r refactor-db -p 'Now add connection pooling' --always-approve", workdir="/project", timeout=180)

# Or continue the most recent session in this directory
terminal(command="grok --no-auto-update -c -p 'What did you change last time?'", workdir="/project", timeout=60)
```

## Useful Subcommands & TUI Commands

| Command | Purpose |
|---------|---------|
| `grok` | Start the interactive TUI |
| `grok -p "query"` | Headless one-shot |
| `grok login` / `grok logout` | Sign in / out (SuperGrok / X Premium+ OAuth) |
| `grok inspect` | Show what Grok discovered in cwd: config sources, instructions, skills, plugins, hooks, MCP servers |
| `grok agent stdio` | Run as an ACP agent over JSON-RPC (for IDE/tool integration) |
| `grok update` | Update the CLI (needs the `x.ai` host; skip in automation) |

TUI slash commands (interactive only): `/model <name>`, `/always-approve`,
`/plan`, `/context`, `/compact`, `/resume`, `/sessions`, `/fork`, `/usage`,
`/quit`. `Shift+Tab` cycles session modes (including Plan mode, which blocks
write tools except the session plan file).

## Config (`~/.grok/config.toml`)

```toml
[cli]
auto_update = false          # skip background update checks persistently

[ui]
permission_mode = "ask"      # or "always-approve" to skip tool prompts by default

[models]
default = "grok-build-0.1"
```

Put global preferences in `~/.grok/config.toml` (not project-scoped
`.grok/config.toml`). `permission_mode` supersedes the legacy `approval_mode` /
`yolo = true` keys.
