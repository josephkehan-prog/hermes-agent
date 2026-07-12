---
name: run-hermes-agent
description: "Build, launch, smoke-test, and drive the Hermes Agent Python CLI/gateway. Use to run hermes, screenshot or exercise a tool, invoke agent internals directly, or verify a change before committing."
version: 1.0.0
metadata:
  hermes:
    domain: run
    tags: [run, launch, smoke-test, cli, gateway, driver]
---

# Run Hermes Agent

Hermes Agent is a Python 3.11–3.13 CLI + messaging gateway + agent core. It is
**not a GUI** — you drive it three ways: the `hermes` CLI (subcommands), direct
Python invocation of a tool/function (the path most PRs touch), and the
registry dispatch the agent itself uses. The committed driver
`.claude/skills/run-hermes-agent/smoke.sh` exercises all three headless-safe
and prints `SMOKE PASS`/`SMOKE FAIL`.

All paths below are relative to the repo root (`hermes-agent/`).

## Prerequisites

Python 3.11–3.13 and a venv with deps installed. The repo ships a `.venv`; if
missing, create one (uses `uv`):

```bash
uv pip install -e ".[all,dev]"   # exact-pinned; regenerate uv.lock after any bump
```

No OS packages are needed for the CLI/library paths (no GUI, no xvfb). macOS and
Linux both work.

## Run (agent path) — the driver

One command, headless-safe (no TTY, no network, isolated `HERMES_HOME`):

```bash
.claude/skills/run-hermes-agent/smoke.sh
```

It runs, in order: `hermes --version`, `hermes doctor`, a **direct
tool-invocation** block (imports `json_diff`/`uptime`/`notify` internals and
asserts their output), the **registry dispatch** path, and one test file via
the CI-parity wrapper. Ends with `SMOKE PASS`. Use it as the pre-commit check
and as the template for driving whatever a change touches.

## Direct invocation — how most PRs are exercised

Most changes here are internal (`tools/`, `agent/`, `gateway/`). Import the
function and call it; no full app boot. Activate the venv and set an isolated
home first:

```bash
. .venv/bin/activate
export HERMES_HOME=$(mktemp -d)
python - <<'PY'
import json, tools.json_diff_tool          # importing registers 'json_diff'
from tools.registry import registry
entry = registry.get_entry("json_diff")    # the ToolEntry the agent dispatches
print(entry.handler({"old_json": json.dumps({"n": 1}),
                     "new_json": json.dumps({"n": 2})}))
PY
```

Every tool self-registers at import via `registry.register(...)`; fetch it with
`registry.get_entry("<name>")` and call `.handler(args_dict, **kw)` — handlers
always return a JSON string.

## CLI surface

```bash
. .venv/bin/activate
hermes --version          # version, install dir, carried-commit count
hermes --help             # full subcommand list (chat, gateway, doctor, tools, ...)
hermes doctor             # health snapshot; exits 0 even when it lists findings
```

`hermes doctor` reports one finding on a fresh `HERMES_HOME` ("Run 'hermes setup'
to create .env") — expected, not a failure.

## Gateway (long-running)

The messaging gateway is a persistent process, normally run via launchd/systemd,
not driven inline:

```bash
hermes gateway run        # foreground; connects Telegram/Signal/etc., Ctrl-C to stop
```

On this machine it already runs as launchd job `ai.hermes.gateway`. Deploy flow
(from `~/mac/CLAUDE.md`): push `fork main`, then in the live install
`~/.hermes/hermes-agent` run `git fetch fork && git merge fork/main`, then
`launchctl kickstart -k gui/501/ai.hermes.gateway`. Reinstall deps only if
`pyproject.toml`/`uv.lock` changed.

## Test

Always use the wrapper (CI-parity: per-file subprocess isolation, unset creds,
temp `HERMES_HOME`, `TZ=UTC`) — never bare `pytest`:

```bash
scripts/run_tests.sh tests/tools/test_json_diff_tool.py   # one file
scripts/run_tests.sh tests/tools/ tests/test_plugin_skills.py  # blast-radius subset
```

## Gotchas

- **`hermes tools` needs a TTY** — it errors ("requires an interactive
  terminal") when piped or in a subprocess. Don't put it in a driver; use
  direct registry invocation instead (see above).
- **`timeout` is absent on macOS** — the GNU `timeout` binary isn't there
  (`gtimeout` via coreutils, or none). Driver avoids it.
- **The full test suite gets killed under load** — running all ~340 test files
  at once (36 workers) can be OOM-killed by the host with zero output. For code
  changes gate on a targeted subset (`scripts/run_tests.sh tests/tools/ ...`),
  not the whole suite in the background.
- **Some tests fail only on macOS/dev boxes** — they read real host state
  (macOS Keychain OAuth token, `/tmp`→`/private/tmp` symlink, a running Ollama
  on :11434, the running gateway). These pass on Linux CI; fork CI is the
  arbiter. Don't treat them as regressions from your change.
- **`.venv` vs `venv` vs live install** — the runner probes `.venv`, then
  `venv`, then `~/.hermes/hermes-agent/venv`. Bare `python3` lacks dev deps
  (e.g. `pytest-asyncio`) — always activate a venv.

## Troubleshooting

- `hermes: command not found` → activate the venv (`. .venv/bin/activate`) or
  run `python -m hermes_cli.main <args>`.
- `ModuleNotFoundError` importing a tool → you're on ambient python3; activate a
  venv with `.[all,dev]` installed.
- Driver prints `SMOKE FAIL` → the failing `=== section ===` names the layer;
  re-run that block standalone to see the assertion.
