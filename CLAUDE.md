# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Canonical guide

`AGENTS.md` (repo root) is the authoritative development guide — contribution
rubric, footprint ladder, hard rules, known pitfalls, testing policy.
Per-subsystem deep dives live in `docs/dev/` (agent core, CLI, TUI, tools,
configuration, skins, plugins, delegation, curator, cron, kanban). Read the
relevant ones before non-trivial work. This file is the fast-start summary;
AGENTS.md wins on any conflict.

## What Hermes is

A self-improving personal AI agent (Python 3.11–3.13) that runs ONE agent core
across a CLI, a messaging gateway (~20 platforms), an Ink/React TUI, and an
Electron desktop app. Extended primarily through **skills and plugins**, not by
growing the core. Two invariants shape every design decision:

- **Per-conversation prompt caching is sacred.** Never mutate past context, swap
  toolsets, or rebuild the system prompt mid-conversation (only exception:
  context compression). The system prompt must be byte-stable for a
  conversation's life.
- **The core is a narrow waist; capability lives at the edges.** Every core
  model-tool ships on every API call, so the bar for a new core tool is high.
  Prefer, in order: extend existing code → CLI command + skill → service-gated
  tool (`check_fn`) → plugin → MCP server → new core tool (last resort).

## Commands

**Setup / install (Python):**
```bash
source .venv/bin/activate        # runner probes .venv, then venv, then ~/.hermes/hermes-agent/venv
uv pip install -e ".[all,dev]"   # deps are exact-pinned; regenerate uv.lock after any bump
```

**Tests — ALWAYS use the wrapper, never bare `pytest`:**
```bash
scripts/run_tests.sh                                  # full suite, CI-parity
scripts/run_tests.sh tests/gateway/                   # one directory
scripts/run_tests.sh tests/agent/test_foo.py::test_x  # one test
scripts/run_tests.sh -v --tb=long                     # pass-through pytest flags
```
The wrapper enforces CI parity: per-test-file subprocess isolation, unset
credential env vars, temp `HERMES_HOME`, `TZ=UTC`, `LANG=C.UTF-8`. Bare pytest
on a dev box with API keys set diverges from CI. Integration tests are excluded
by default (`-m 'not integration'`).

**Lint / typecheck (Python):**
```bash
ruff check .   # only PLW1514 (unspecified-encoding) is enabled — always pass encoding= to open()/read_text()/write_text()
ty check       # type checker (config in [tool.ty])
```

**TUI (TypeScript, in `ui-tui/`):**
```bash
cd ui-tui && npm install
npm run dev        # watch  |  npm run build  |  npm run typecheck  |  npm run lint  |  npm run fmt  |  npm test (vitest)
```

**Run it:** `hermes` (CLI) · `hermes gateway` (messaging) · `hermes --tui` ·
`hermes model` / `hermes tools` / `hermes setup` / `hermes doctor`.
Entry points: `hermes`→`hermes_cli.main:main`, `hermes-agent`→`run_agent:main`,
`hermes-acp`→`acp_adapter.entry:main`.

## Architecture (big picture)

**Agent core** — `run_agent.py` `AIAgent` (~12k LOC) is the god-object; its
`run_conversation()` delegates to `agent/conversation_loop.py::run_conversation`
(the real orchestrator), a bounded tool-call `while` loop (capped by
`max_iterations` + `iteration_budget`). Provider abstraction ("use any model")
works by normalizing every provider into an `api_mode` (`chat_completions`,
`anthropic_messages`, `codex_responses`, `bedrock_converse`, …) in
`agent/agent_init.py`; `agent/chat_completion_helpers.py` is the provider-agnostic
request/response seam (builds payload, dispatches to a per-vendor adapter like
`agent/anthropic_adapter.py`, normalizes back to OpenAI-chat shape, owns
retry/failover). Context window kept in bounds by `agent/context_compressor.py`
+ `agent/conversation_compression.py`; long-term memory/user-profile via
pluggable `agent/memory_manager.py` → `MemoryProvider` (Honcho/Hindsight/Mem0,
wired through `plugins/memory/`). `hermes_state.py` = `SessionDB`, a SQLite store
with FTS5 session search.

**Tools** — no base class; a tool self-registers by calling `registry.register()`
(`tools/registry.py`) at module top level. Discovery is AST-based: any `tools/*.py`
with a module-body `registry.register(...)` is imported automatically (calls
inside functions are NOT discovered). A tool is exposed to an agent only if its
name is in a toolset — either listed in `toolsets.py` (`_HERMES_CORE_TOOLS` =
default bundle) or attached to an existing toolset via the `toolset=` field at
registration (the registry overlay: `get_toolset()` unions both). All handlers
MUST return a JSON string. Optional deps go through `LAZY_DEPS` + `ensure()` in
`tools/lazy_deps.py`, NOT core `pyproject`. Dependency chain: `tools/registry.py`
← `tools/*.py` ← `model_tools.py` ← `run_agent.py`/`cli.py`.

**CLI** — `hermes` → `hermes_cli/main.py:main` (**argparse**, not fire; ~15k-LOC
god-file). Subcommand parsers are decomposed into `hermes_cli/subcommands/*`
(`build_<group>_parser(...)`), but the `cmd_*` handlers stay in `main.py` and are
injected in to avoid an import cycle. The interactive chat CLI is `cli.py`
(`HermesCLI`, ~11k LOC). Slash commands live in ONE central `COMMAND_REGISTRY`
in `hermes_cli/commands.py`; CLI/gateway/Telegram/Slack/autocomplete/help all
derive from it. Adding a command touches the registry + `process_command()` in
`cli.py` (+ `gateway/run.py` if gateway-available).

**Gateway** — `gateway/run.py` (`_create_adapter()` dispatch) + `gateway/session.py`.
Adapters implement `BasePlatformAdapter` (`gateway/platforms/base.py`) and
self-register via `platform_registry` (`gateway/platform_registry.py`). Note the
**two locations**: built-in adapters (signal, whatsapp_cloud, webhook, api_server,
…) in `gateway/platforms/`; the major ones (telegram, discord, slack, whatsapp,
matrix, teams, feishu, email, …) actually live in `plugins/platforms/<name>/adapter.py`.
Registry (plugin) platforms are checked first. See `gateway/platforms/ADDING_A_PLATFORM.md`.

**Terminal backends** — `tools/environments/` (`BaseEnvironment` ABC, consumed by
`tools/terminal_tool.py`) abstracts local, docker, ssh, singularity, modal,
daytona (serverless persistence via modal/daytona; backend chosen by `env_type`/
`TERMINAL_ENV`).

**MCP** — client in `tools/mcp_tool.py` (reads `mcp_servers` in config.yaml,
connects stdio/HTTP/SSE, registers remote tools into the same `registry`);
non-blocking startup via `hermes_cli/mcp_startup.py`. Hermes-as-MCP-server: `mcp_serve.py`.

**TUI surfaces (3 distinct, don't conflate):** `ui-tui/` = Ink/React terminal
UI (`hermes --tui`) backed by `tui_gateway/` (Python JSON-RPC). The dashboard
(`hermes dashboard`) EMBEDS the real `hermes --tui` over a PTY bridge — do not
re-implement chat in React. `apps/desktop/` = separate Electron app with its own
composer. `acp_adapter/` = ACP server for VS Code/Zed/JetBrains.

**Extension systems:** `skills/` (built-in, default-on) vs `optional-skills/`
(heavy/niche, `hermes skills install ...`); `plugins/` (memory providers, model
providers, context engines, kanban, …); `cron/` (scheduler, driven by the
gateway's tick loop); `delegate_task` (`tools/delegate_tool.py`) spawns isolated
subagents (leaf vs orchestrator roles).

## Hard rules (from AGENTS.md — violating these gets a PR rejected)

- **Prompt caching / role alternation:** never break the cached prefix; never
  two same-role messages in a row; never inject a synthetic user message
  mid-loop.
- **`config.yaml` vs `.env`:** `.env` is SECRETS ONLY (API keys/tokens/passwords,
  registered in `OPTIONAL_ENV_VARS`). All behavioral config (timeouts, flags,
  thresholds, paths) goes in `config.yaml` `DEFAULT_CONFIG` (`hermes_cli/config.py`).
  No new `HERMES_*` env var for non-secret config.
- **Profile-aware paths:** use `get_hermes_home()` / `display_hermes_home()`
  (`hermes_constants.py`) — never hardcode `~/.hermes` or `Path.home()/".hermes"`.
- **No change-detector tests:** don't assert on model lists, config version
  literals, or enumeration counts. Assert invariants/relationships instead.
- **Tests must not write to real `~/.hermes/`** — use the temp `HERMES_HOME` the
  wrapper provides.
- **Skill authoring:** SKILL.md `description` ≤ 60 chars, one sentence, ends with
  a period, no marketing words. Frontmatter fields under `metadata.hermes.*`.
- **Dependencies are exact-pinned** on purpose (supply-chain blast radius);
  bump the pin AND regenerate `uv.lock`. Only every-session deps go in core
  `dependencies`; provider-specific ones are extras, lazy-installed via
  `tools/lazy_deps.py`.
- **Config loader trap:** `load_cli_config()` (CLI) vs `load_config()` (subcommands)
  vs raw YAML (gateway) — if CLI sees a key but gateway doesn't, you're on the
  wrong loader / missing `DEFAULT_CONFIG` coverage.

## Autonomous-work rules (this fork)

- **Never commit directly to `main`.** Autonomous loops and multi-commit work go
  on a feature branch with a **green `scripts/run_tests.sh` gate before merge**.
  (A prior feature-loop landed ~22k lines straight on `main`; the rollback tag
  `pre-feature-loop` marks the point before it.)
- **New capability defaults to skills/plugins**, per the footprint ladder above.
  A new *core* tool needs explicit justification — it costs schema tokens on
  every API call and widens the rebase gap against `origin` (Nous upstream).

## Local runtime (this machine)

This checkout is the **dev copy** — the running gateway is the live install at
`~/.hermes/hermes-agent` (launchd `ai.hermes.gateway`). Live logs:
`~/.hermes/logs/`. Restart: `launchctl kickstart -k gui/501/ai.hermes.gateway`
(never `kill` — launchd respawns). Local models are served by llama-swap on
`localhost:1235` (roster + config: `~/mac/Hermes/llama-swap/config.yaml`).
Deploy flow (dev → live) and runtime triage notes: `~/mac/Hermes/CLAUDE.md`
and `~/mac/Hermes/claude-Hermes.md`.

## Verification

After changes: `scripts/run_tests.sh <relevant test path>`, then `ruff check .`
and `ty check` for touched Python; for TUI changes `cd ui-tui && npm run typecheck && npm test`.
Smoke-run the affected surface (`hermes`, `hermes gateway`, or `hermes --tui`)
against a temp `HERMES_HOME`.
