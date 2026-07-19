# Hermes Agent - Development Guide

Instructions for AI coding assistants and developers working on the hermes-agent codebase.

**Never give up on the right solution.**

## What Hermes Is

A personal AI agent: one agent core across CLI, messaging gateway (~20
platforms), TUI, and Electron desktop app. Extended primarily through
**plugins and skills**, not by growing the core. (Fast-start summary:
`CLAUDE.md`.) Two invariants are the lens for reviewing any change:

- **Per-conversation prompt caching is sacred.** Never mutate past context,
  swap toolsets, or rebuild the system prompt mid-conversation — it breaks the
  cached prefix and multiplies cost. Sole exception: context compression.
- **The core is a narrow waist; capability lives at the edges.** Every core
  model tool ships on every API call, so the bar is high. New capability
  arrives as CLI command + skill, service-gated tool, or plugin.

## Contribution Rubric — What We Want / What We Don't

The project's intent layer, for humans AND the automated triage sweeper. The
sweeper may close PRs only on `implemented_on_main`, `cannot_reproduce`, or
`incoherent`; taste-based "out of scope" closes stay with a human maintainer —
the sweeper's job is to recognize design intent and avoid wrongly closing a
legitimate contribution. Balance: Hermes ships a lot — product surface
(platforms, providers, models, desktop/TUI) expands aggressively on purpose.
Restraint targets the **core agent + model tool schema**, where every addition
is paid on every API call. Expansive at the edges, conservative at the waist.

### What we want

- **Fix real bugs, well** — reproduce on current `main`, point to the exact
  line, fix the whole bug class (sibling call paths included).
- **Expand reach at the edges** — new adapters, channels, providers, models,
  desktop/TUI features land routinely, even large ones, as long as they
  integrate with the existing setup/config UX (`hermes tools`, `hermes setup`,
  auto-install) rather than bolting on a raw env var.
- **Refactor god-files into clean modules** — extracting clusters from
  `cli.py` / `run_agent.py` / `gateway/run.py` is wanted work, even huge
  mechanical diffs. "Every line traces to the request" applies to *feature*
  PRs; a declared refactor's request IS the extraction.
- **Keep the core narrow** — new model tools are the expensive exception.
  Prefer, in order: extend existing code → CLI command + skill → service-gated
  tool (`check_fn`) → plugin → MCP server in catalog → new core tool (last
  resort). See "The Footprint Ladder."
- **Extend, don't duplicate** — check existing infrastructure first; when
  several PRs integrate the same *category*, design one shared interface (ABC
  + orchestrator) instead of merging them one at a time.
- **Behavior contracts over snapshots** — assert invariants, never freeze
  current values. See "Don't write change-detector tests."
- **E2E validation, not just green unit mocks** — for resolution chains,
  config propagation, security boundaries, remote backends, file/network I/O:
  real imports against a temp `HERMES_HOME`.
- **Cache-, alternation-, and invariant-safe** — preserve prompt caching,
  strict role alternation (never two same-role messages in a row; never a
  synthetic user message mid-loop), byte-stable system prompt.
- **Contributor credit preserved** — salvage external work by cherry-picking
  so authorship survives; build on top, don't reimplement.

### What we don't want (rejected even when well-built)

- **Speculative infrastructure** — hooks/extension points with no concrete
  consumer. NOT speculative if a contributor has a real, stated use case, even
  if the consumer ships separately.
- **New `HERMES_*` env vars for non-secret config** — `.env` is secrets only.
  Behavioral settings go in `config.yaml`; bridge internally if the mechanism
  needs an env var. Reject "set X in your .env" docs unless X is a credential.
- **A new core tool when terminal + file already do the job, or a skill
  would** — if the barrier is file visibility on a remote backend, fix the
  mount, not the toolset.
- **Lazy-reading escape hatches on instructional tools** — no `offset`/`limit`
  pagination on content the agent must read fully (skills, prompts,
  playbooks); models read page 1 and skip the rest.
- **"Fixes" that destroy the feature they secure** — read the original
  commit's intent (`git log -p -S`) before restricting behavior; find a fix
  that preserves the feature.
- **Outbound telemetry / usage attribution without opt-in gating** — no
  analytics or identifier tagging until a generic user-facing opt-in (config
  gate + setup prompt + `hermes tools` toggle) exists. Park, don't merge.
- **Change-detector tests, cache-breaking mid-conversation, dead code wired in
  without E2E proof, plugins that touch core files** — plugins work within the
  ABCs/hooks we provide; if one needs more, widen the generic plugin surface.
- **Third-party products integrated into the core tree** — observability
  backends, vendor SaaS connectors, analytics dashboards do NOT land under
  `plugins/` here (ongoing maintenance burden for a backend we don't own).
  Ship as a standalone plugin repo installed into `~/.hermes/plugins/` (or pip
  entry point); promote in Nous Discord `#plugins-skills-and-skins`. Coupling
  decision, not a quality bar — such PRs are closed with a pointer to publish
  as their own repo.

### Before you call it a bug — verify the premise (and when NOT to close)

The most common close reason for well-written PRs: a **wrong premise**, or
treating **intentional design as a gap**. These patterns tell reviewers what
to scrutinize and tell the sweeper when a PR is NOT safe to auto-close (when
in doubt, leave it open for a human):

- **"Intentional design, not a gap."** Ask whether the isolation IS the design
  (e.g. profiles are independent islands on purpose; a live config-inheritance
  PR was closed — `--clone` already covers "start from my default"). Read the
  original commit's intent (`git log -p -S "<symbol>"`) first.
- **"The premise doesn't hold against how X actually works."** Trace the real
  code/runtime before accepting the rationale (real closes: a cooldown
  re-probe that hammers a confirmed-empty bucket; a fix whose new branch never
  executes because an earlier guard popped the state). If you can't point to
  the exact line where the bug manifests AND show the fix changes that line's
  behavior, the premise is unverified.
- **"The absence/omission was deliberate."** Adding the obvious missing piece
  can break what the omission protected (restoring "missing" `__init__.py`
  files shadowed a real plugin and deleted its `register()` at import time).
- **"Overreached / resurrected a closed direction."** Keep the change to the
  narrow agreed piece; offer the rest as a focused follow-up.

Throughline: **verify the claim AND the intent against the codebase first.**
Confirmed repro on `main` + line-level account of where the fix acts beats a
plausible rationale. When in doubt about intent, ask — don't fight the design.

### The Footprint Ladder (new capability decision)

Choose the highest (least-footprint) rung that correctly solves the problem:

1. **Extend existing code** — zero new surface.
2. **CLI command + skill** — agent runs `hermes <subcommand>` guided by a
   skill; zero model-tool footprint. Default for subscriptions, scheduled
   tasks, service setup (`hermes webhook`, `hermes cron`, `hermes tools`).
3. **Service-gated tool (`check_fn`)** — structured params/returns, appears
   only when a prerequisite is configured (Home Assistant, memory providers).
4. **Plugin** — third-party/niche/user-specific; `~/.hermes/plugins/` or pip,
   discovered at runtime.
5. **MCP server (in the catalog)** — needs structured tool I/O but isn't
   core-fundamental; zero permanent core-schema footprint, reusable anywhere.
6. **New core tool** — only when fundamental, broadly useful to nearly every
   user, and unreachable via terminal + file or an MCP server (correct
   examples: terminal, read_file, web_search, browser_navigate).

When 3+ open PRs integrate the same *category* (memory backends, providers,
notifiers): design an ABC + orchestrator, wrap the built-in as the first
provider, turn the competing PRs into plugins against that interface.

## Development Environment

```bash
# Prefer .venv; fall back to venv if that's what your checkout has.
source .venv/bin/activate   # or: source venv/bin/activate
```

`scripts/run_tests.sh` probes `.venv` first, then `venv`, then
`$HOME/.hermes/hermes-agent/venv` (for worktrees that share a venv with the
main checkout).

## Project Structure

File counts shift constantly — don't treat the tree below as exhaustive.
The canonical source is the filesystem. The notes call out the load-bearing
entry points you'll actually edit.

```
hermes-agent/
├── run_agent.py          # AIAgent class — core conversation loop (~12k LOC)
├── model_tools.py        # Tool orchestration, discover_builtin_tools(), handle_function_call()
├── toolsets.py           # Toolset definitions, _HERMES_CORE_TOOLS list
├── cli.py                # HermesCLI class — interactive CLI orchestrator (~11k LOC)
├── hermes_state.py       # SessionDB — SQLite session store (FTS5 search)
├── hermes_constants.py   # get_hermes_home(), display_hermes_home() — profile-aware paths
├── hermes_logging.py     # setup_logging() — agent.log / errors.log / gateway.log (profile-aware)
├── batch_runner.py       # Parallel batch processing
├── agent/                # Agent internals (provider adapters, memory, caching, compression, etc.)
├── hermes_cli/           # CLI subcommands, setup wizard, plugins loader, skin engine
├── tools/                # Tool implementations — auto-discovered via tools/registry.py
│   └── environments/     # Terminal backends (local, docker, ssh, modal, daytona, singularity)
├── gateway/              # Messaging gateway — run.py + session.py + platforms/
│   ├── platforms/        # Adapter per platform (telegram, discord, slack, whatsapp,
│   │                     #   homeassistant, signal, matrix, mattermost, email, sms,
│   │                     #   dingtalk, wecom, weixin, feishu, qqbot, bluebubbles,
│   │                     #   yuanbao, webhook, api_server, ...). See ADDING_A_PLATFORM.md.
│   └── builtin_hooks/    # Extension point for always-registered gateway hooks (none shipped)
├── plugins/              # Plugin system (see "Plugins" section below)
│   ├── memory/           # Memory-provider plugins (honcho, mem0, supermemory, ...)
│   ├── context_engine/   # Context-engine plugins
│   ├── model-providers/  # Inference backend plugins (openrouter, anthropic, gmi, ...)
│   ├── kanban/           # Multi-agent board dispatcher + worker plugin
│   ├── hermes-achievements/  # Gamified achievement tracking
│   ├── observability/    # Metrics / traces / logs plugin
│   ├── image_gen/        # Image-generation providers
│   └── <others>/         # disk-cleanup, google_meet, platforms, spotify,
│                         #   strike-freedom-cockpit, ...
├── optional-skills/      # Heavier/niche skills shipped but NOT active by default
├── skills/               # Built-in skills bundled with the repo
├── ui-tui/               # Ink (React) terminal UI — `hermes --tui`
│   └── src/              # entry.tsx, app.tsx, gatewayClient.ts + app/components/hooks/lib
├── tui_gateway/          # Python JSON-RPC backend for the TUI
├── acp_adapter/          # ACP server (VS Code / Zed / JetBrains integration)
├── cron/                 # Scheduler — jobs.py, scheduler.py
├── scripts/              # run_tests.sh, release.py, auxiliary scripts
├── website/              # Docusaurus docs site
└── tests/                # Pytest suite (~17k tests across ~900 files as of May 2026)
```

**User config:** `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys only).
**Logs:** `~/.hermes/logs/` — `agent.log` (INFO+), `errors.log` (WARNING+),
`gateway.log` when running the gateway. Profile-aware via `get_hermes_home()`.
Browse with `hermes logs [--follow] [--level ...] [--session ...]`.

## TypeScript Style

Applies to TypeScript across Hermes: desktop, TUI, website, and future TS packages.

- Prefer small nanostores over component state when state is shared, reused, or read by distant UI.
- Let each feature own its atoms. Chat state belongs near chat, shell state near shell, shared state in `src/store`.
- Components that render from an atom should use `useStore`. Non-rendering actions should read with `$atom.get()`.
- Do not pass state through three components when the leaf can subscribe to the atom.
- Keep persistence beside the atom that owns it.
- Keep route roots thin. They compose routes and shell; they should not become controllers.
- No monolithic hooks. A hook should own one narrow job.
- Prefer colocated action modules over hidden god hooks.
- If a callback is pure side effect, use the terse void form:
  `onState={st => void setGatewayState(st)}`.
- Async UI handlers should make intent explicit:
  `onClick={() => void save()}`.
- Prefer interfaces for public props and shared object shapes. Avoid `type X = { ... }` for object props.
- Extend React primitives for props: `React.ComponentProps<'button'>`, `React.ComponentProps<typeof Dialog>`, `Omit<...>`, `Pick<...>`.
- Table-driven beats condition ladders when mapping ids, routes, or views.
- `src/app` owns routes, pages, and page-specific components.
- `src/store` owns shared atoms.
- `src/lib` owns shared pure helpers.

## File Dependency Chain

```
tools/registry.py  (no deps — imported by all tool files)
       ↑
tools/*.py  (each calls registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry + triggers tool discovery)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

---

## Architecture & subsystem deep dives (`docs/dev/`)

Per-subsystem guides live in `docs/dev/` — read the relevant one before
touching that subsystem. Inline below: only the invariants that get PRs
rejected on their own.

- **Agent core** (`docs/dev/agent-core.md`) — `AIAgent` god-object, the
  conversation loop, provider `api_mode` normalization, context compression,
  memory providers.
- **CLI** (`docs/dev/cli-architecture.md`) — argparse god-file decomposition.
  Slash commands live in ONE central `COMMAND_REGISTRY`
  (`hermes_cli/commands.py`); every surface derives from it.
- **TUI** (`docs/dev/tui-architecture.md`) — 3 distinct surfaces: Ink TUI,
  dashboard (embeds the REAL TUI over a PTY bridge — never re-implement chat
  in React), Electron desktop app.
- **Tools** (`docs/dev/adding-tools.md`) — tools self-register via
  module-top-level `registry.register()` (AST-discovered; calls inside
  functions are invisible); handlers MUST return JSON strings; optional deps
  go through `tools/lazy_deps.py`, never core `pyproject`.
- **Configuration** (`docs/dev/adding-configuration.md`) — `.env` is SECRETS
  ONLY; behavioral config goes in `config.yaml` `DEFAULT_CONFIG`; know which
  of the three loaders (`load_cli_config` / `load_config` / raw YAML) your
  code path uses.
- **Skins** (`docs/dev/skins.md`) — pure-data YAML theming; adding a skin
  never requires code changes.
- **Plugins** (`docs/dev/plugins.md`) — general / memory-provider /
  model-provider plugin surfaces; plugins work within the provided ABCs and
  hooks, never by touching core files.
- **Delegation** (`docs/dev/delegation.md`) — `delegate_task` isolated
  subagents, leaf vs orchestrator roles.
- **Curator** (`docs/dev/curator.md`) — automated skill lifecycle sweeps.
- **Cron** (`docs/dev/cron.md`) — scheduler driven by the gateway tick loop.
- **Kanban** (`docs/dev/kanban.md`) — SQLite multi-agent work queue; the
  board is the hard isolation boundary.

---

## Dependency Pinning Policy

All dependencies must have upper bounds to limit supply-chain attack surface.
This policy was established after the litellm compromise (PR #2796, #2810) and
reinforced after the Mini Shai-Hulud worm campaign (May 2026).

| Source type | Treatment | Example |
|---|---|---|
| PyPI package | `>=floor,<next_major` | `"httpx>=0.28.1,<1"` |
| Git URL | Commit SHA | `git+https://...@<40-char-sha>` |
| GitHub Actions | Commit SHA + comment | `uses: actions/checkout@<sha>  # v4` |
| CI-only pip | `==exact` | `pyyaml==6.0.2` |

**When adding a new dependency to `pyproject.toml`:**
1. Pin to `>=current_version,<next_major` for post-1.0 (e.g. `>=1.5.0,<2`).
2. For pre-1.0 packages, use `<0.(current_minor + 2)` (e.g. `>=0.29,<0.32`).
3. Never commit a bare `>=X.Y.Z` without a ceiling — CI and reviewers will reject it.
4. Run `uv lock` to regenerate `uv.lock` with hashes.

Reference: #2810 (bounds pass), #9801 (SHA pinning + audit CI).

---

## Skills

Two parallel surfaces:

- **`skills/`** — built-in skills shipped and loadable by default.
  Organized by category directories (e.g. `skills/github/`, `skills/mlops/`).
- **`optional-skills/`** — heavier or niche skills shipped with the repo but
  NOT active by default. Installed explicitly via
  `hermes skills install official/<category>/<skill>`. Adapter lives in
  `tools/skills_hub.py` (`OptionalSkillSource`). Categories include
  `autonomous-ai-agents`, `blockchain`, `communication`, `creative`,
  `devops`, `email`, `health`, `mcp`, `migration`, `mlops`, `productivity`,
  `research`, `security`, `web-development`.

When reviewing skill PRs, check which directory they target — heavy-dep or
niche skills belong in `optional-skills/`.

### SKILL.md frontmatter

Standard fields: `name`, `description`, `version`, `author`, `license`,
`platforms` (OS-gating list: `[macos]`, `[linux, macos]`, ...),
`metadata.hermes.tags`, `metadata.hermes.category`,
`metadata.hermes.related_skills`, `metadata.hermes.config` (config.yaml
settings the skill needs — stored under `skills.config.<key>`, prompted
during setup, injected at load time).

Top-level `tags:` and `category:` are also accepted and mirrored from
`metadata.hermes.*` by the loader.

### Skill authoring standards (HARDLINE)

Every new or modernized skill — bundled, optional, or contributed —
must meet these standards before merge. Reviewers reject PRs that
violate them.

1. **`description` ≤ 60 characters, one sentence, ends with a period.**
   State the capability, not the implementation. No marketing words
   ("powerful", "comprehensive", "seamless", "advanced"). Don't repeat
   the skill name.

2. **Tools referenced in SKILL.md prose must be native Hermes tools or
   MCP servers the skill explicitly expects**, named in backticks
   (`` `terminal` ``, `` `web_extract` ``, `` `read_file` ``,
   `` `patch` ``, `` `search_files` ``, `` `delegate_task` ``, …). Do
   NOT name shell utilities the agent already has wrapped: `grep` →
   `search_files`, `cat`/`head`/`tail` → `read_file`, `sed`/`awk` →
   `patch`, `find`/`ls` → `search_files target='files'`. MCP
   dependencies documented in `## Prerequisites`. Third-party CLIs and
   pipelines are fine inside script files, not as the headline
   interaction surface.

3. **`platforms:` gating audited against actual script imports.**
   POSIX-only primitives (`fcntl`, `termios`, `os.setsid`, `/proc`,
   hardcoded `/tmp`, `signal.SIGKILL`, bash heredocs, `osascript`,
   `apt`, `systemctl`) require declared platforms. Fix cross-platform
   first (`tempfile.gettempdir`, `pathlib.Path`, `psutil.pid_exists`);
   gate only when genuinely platform-bound.

4. **`author` credits the human contributor first** (real name + GitHub
   handle); "Hermes Agent" is the secondary collaborator. Replace
   "Hermes Agent" authorship with the human's name — credit the human,
   not the tool.

5. **SKILL.md body uses the modern section order:** `# <Skill> Skill`
   title, 2-3 sentence intro (does and doesn't do), `## When to Use`,
   `## Prerequisites`, `## How to Run`, `## Quick Reference`,
   `## Procedure`, `## Pitfalls`, `## Verification`. Target ~200 lines
   complex / ~100 simple. Body ≤ 12,000 chars (validator ERROR; WARN
   over 8,000; limits defined in the skill-authoring skill's
   `scripts/validate_skills.py`) — split detail into `references/`.

6. **Scripts go in `scripts/`, references in `references/`, templates
   in `templates/`.** Ship helper scripts for non-trivial logic;
   reference by path relative to the skill directory.

7. **Tests live at `tests/skills/test_<skill>_skill.py`** — stdlib +
   pytest + `unittest.mock` only, no live network. Run via
   `scripts/run_tests.sh tests/skills/test_<skill>_skill.py -q`.

8. **`.env.example` additions are isolated to a clearly delimited
   block** — edits outside the skill's own block are dropped during
   salvage.

The full salvage / modernization checklist for external skill PRs
lives in the `hermes-agent-dev` skill at
`references/new-skill-pr-salvage.md` — load it before polishing
contributor skill PRs.

---

## Toolsets

All toolsets are defined in `toolsets.py` as a single `TOOLSETS` dict.
Each platform's adapter picks a base toolset (e.g. Telegram uses
`"messaging"`); `_HERMES_CORE_TOOLS` is the default bundle most
platforms inherit from.

Current toolset keys: `browser`, `clarify`, `code_execution`, `cronjob`,
`debugging`, `delegation`, `discord`, `discord_admin`, `feishu_doc`,
`feishu_drive`, `file`, `homeassistant`, `image_gen`, `kanban`, `memory`,
`messaging`, `moa`, `rl`, `safe`, `search`, `session_search`, `skills`,
`spotify`, `terminal`, `todo`, `tts`, `video`, `vision`, `web`, `yuanbao`.

Enable/disable per platform via `hermes tools` (the curses UI) or the
`tools.<platform>.enabled` / `tools.<platform>.disabled` lists in
`config.yaml`.

---

## Important Policies

### Prompt Caching Must Not Break

Never alter past context, change toolsets, or reload memories / rebuild
system prompts mid-conversation (sole exception: context compression). Slash
commands that mutate system-prompt state (skills, tools, memory) must be
**cache-aware**: deferred invalidation by default (takes effect next
session), opt-in `--now` flag for immediate — see `/skills install --now`.

### Background Process Notifications (Gateway)

When `terminal(background=true, notify_on_complete=true)` is used, the gateway runs a watcher that
detects process completion and triggers a new agent turn. Control verbosity of background process
messages with `display.background_process_notifications`
in config.yaml (or `HERMES_BACKGROUND_NOTIFICATIONS` env var):

- `all` — running-output updates + final message (default)
- `result` — only the final completion message
- `error` — only the final message when exit code != 0
- `off` — no watcher messages at all

---

## Profiles: Multi-Instance Support

Hermes supports **profiles** — multiple fully isolated instances, each with its own
`HERMES_HOME` directory (config, API keys, memory, sessions, skills, gateway, etc.).

The core mechanism: `_apply_profile_override()` in `hermes_cli/main.py` sets
`HERMES_HOME` before any module imports. All `get_hermes_home()` references
automatically scope to the active profile.

### Rules for profile-safe code

1. **Use `get_hermes_home()` for all HERMES_HOME paths.** Import from `hermes_constants`.
   NEVER hardcode `~/.hermes` or `Path.home() / ".hermes"` in code that reads/writes state.
   ```python
   # GOOD
   from hermes_constants import get_hermes_home
   config_path = get_hermes_home() / "config.yaml"

   # BAD — breaks profiles
   config_path = Path.home() / ".hermes" / "config.yaml"
   ```

2. **Use `display_hermes_home()` for user-facing messages.** Import from `hermes_constants`.
   This returns `~/.hermes` for default or `~/.hermes/profiles/<name>` for profiles.
   ```python
   # GOOD
   from hermes_constants import display_hermes_home
   print(f"Config saved to {display_hermes_home()}/config.yaml")

   # BAD — shows wrong path for profiles
   print("Config saved to ~/.hermes/config.yaml")
   ```

3. **Module-level constants are fine** — they cache `get_hermes_home()` at import time,
   which is AFTER `_apply_profile_override()` sets the env var. Just use `get_hermes_home()`,
   not `Path.home() / ".hermes"`.

4. **Tests that mock `Path.home()` must also set `HERMES_HOME`** — since code now uses
   `get_hermes_home()` (reads env var), not `Path.home() / ".hermes"`:
   ```python
   with patch.object(Path, "home", return_value=tmp_path), \
        patch.dict(os.environ, {"HERMES_HOME": str(tmp_path / ".hermes")}):
       ...
   ```

5. **Gateway platform adapters should use token locks** — if the adapter connects with
   a unique credential (bot token, API key), call `acquire_scoped_lock()` from
   `gateway.status` in the `connect()`/`start()` method and `release_scoped_lock()` in
   `disconnect()`/`stop()`. This prevents two profiles from using the same credential.
   See `plugins/platforms/irc/adapter.py` for the canonical pattern.

6. **Profile operations are HOME-anchored, not HERMES_HOME-anchored** — `_get_profiles_root()`
   returns `Path.home() / ".hermes" / "profiles"`, NOT `get_hermes_home() / "profiles"`.
   This is intentional — it lets `hermes -p coder profile list` see all profiles regardless
   of which one is active.

## Known Pitfalls

### DO NOT hardcode `~/.hermes` paths
Use `get_hermes_home()` from `hermes_constants` for code paths. Use `display_hermes_home()`
for user-facing print/log messages. Hardcoding `~/.hermes` breaks profiles — each profile
has its own `HERMES_HOME` directory. This was the source of 5 bugs fixed in PR #3575.

### DO NOT introduce new `simple_term_menu` usage
Existing call sites in `hermes_cli/main.py` remain for legacy fallback only;
the preferred UI is curses (stdlib) because `simple_term_menu` has
ghost-duplication rendering bugs in tmux/iTerm2 with arrow keys. New
interactive menus must use `hermes_cli/curses_ui.py` — see
`hermes_cli/tools_config.py` for the canonical pattern.

### DO NOT use `\033[K` (ANSI erase-to-EOL) in spinner/display code
Leaks as literal `?[K` text under `prompt_toolkit`'s `patch_stdout`. Use space-padding: `f"\r{line}{' ' * pad}"`.

### `_last_resolved_tool_names` is a process-global in `model_tools.py`
`_run_single_child()` in `delegate_tool.py` saves and restores this global around subagent execution. If you add new code that reads this global, be aware it may be temporarily stale during child agent runs.

### DO NOT hardcode cross-tool references in schema descriptions
Tool schema descriptions must not mention tools from other toolsets by name (e.g., `browser_navigate` saying "prefer web_search"). Those tools may be unavailable (missing API keys, disabled toolset), causing the model to hallucinate calls to non-existent tools. If a cross-reference is needed, add it dynamically in `get_tool_definitions()` in `model_tools.py` — see the `browser_navigate` / `execute_code` post-processing blocks for the pattern.

### The gateway has TWO message guards — both must bypass approval/control commands
When an agent is running, messages pass through two sequential guards:
(1) **base adapter** (`gateway/platforms/base.py`) queues messages in
`_pending_messages` when `session_key in self._active_sessions`, and
(2) **gateway runner** (`gateway/run.py`) intercepts `/stop`, `/new`,
`/queue`, `/status`, `/approve`, `/deny` before they reach
`running_agent.interrupt()`. Any new command that must reach the runner
while the agent is blocked (e.g. approval prompts) MUST bypass BOTH
guards and be dispatched inline, not via `_process_message_background()`
(which races session lifecycle).

### Squash merges from stale branches silently revert recent fixes
Before squash-merging a PR, ensure the branch is up to date with `main`
(`git fetch origin main && git reset --hard origin/main` in the worktree,
then re-apply the PR's commits). A stale branch's version of an unrelated
file will silently overwrite recent fixes on main when squashed. Verify
with `git diff HEAD~1..HEAD` after merging — unexpected deletions are a
red flag.

### Don't wire in dead code without E2E validation
Unused code that was never shipped was dead for a reason. Before wiring an
unused module into a live code path, E2E test the real resolution chain
with actual imports (not mocks) against a temp `HERMES_HOME`.

### Tests must not write to `~/.hermes/`
The `_isolate_hermes_home` autouse fixture in `tests/conftest.py` redirects `HERMES_HOME` to a temp dir. Never hardcode `~/.hermes/` paths in tests.

**Profile tests**: When testing profile features, also mock `Path.home()` so that
`_get_profiles_root()` and `_get_default_hermes_home()` resolve within the temp dir.
Use the pattern from `tests/hermes_cli/test_profiles.py`:
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

---

## Testing

### Python
**ALWAYS use `scripts/run_tests.sh`** — do not call `pytest` directly. The script enforces
hermetic environment parity with CI (unset credential vars, TZ=UTC, LANG=C.UTF-8,
`-n auto` xdist workers, in-tree subprocess-isolation plugin). Direct `pytest`
on a 16+ core developer machine with API keys set diverges from CI in ways
that have caused multiple "works locally, fails in CI" incidents (and the reverse).

```bash
scripts/run_tests.sh                                  # full suite, CI-parity
scripts/run_tests.sh tests/gateway/                   # one directory
scripts/run_tests.sh tests/agent/test_foo.py::test_x  # one test
scripts/run_tests.sh -v --tb=long                     # pass-through pytest flags
```

**Flake policy:** the runner auto-retries a failing test FILE once in a fresh
subprocess (`--file-retries`, default 1; `HERMES_TEST_FILE_RETRIES=0` to
disable). Pass-on-retry counts as green but is printed in a `⚠ FLAKY` summary
section with both attempts' output. A FLAKY report is a bug to fix, not noise
to ignore — timing-sensitive tests must not assume a quiet runner (loose
wall-clock bounds ≥ 2s, event-based sync, no `assert not _wait_until(...)`
negative-timing races).

#### Subprocess-per-test-file isolation

Every test file runs in a freshly-spawned Python subprocess via `run_tests_parallel.py`. This means module-level dicts/sets and
ContextVars from one test file cannot leak into the next.

#### Why the wrapper

Without it, tests see your real env: provider API keys (auto-detected pools),
your real `~/.hermes/` config+auth, local timezone and locale. The wrapper
unsets credentials, uses a temp `HERMES_HOME` per test, TZ=UTC, LANG=C.UTF-8.

### Where to place what tests

The CI change classifier (`scripts/ci/classify_changes.py`) picks jobs by
changed files — a Python test asserting about JS-side artifacts won't run on
a JS-only PR (green PR, red `main`, where the classifier fails open). Any
test about `package.json`/`tsconfig.json`/`.ts`/`.tsx`/`.js` content belongs
in the JS (vitest) suite, not `tests/*.py`.

### Don't write change-detector tests

A test is a **change-detector** if it fails whenever data that is **expected
to change** gets updated — model catalogs, config version numbers,
enumeration counts, hardcoded lists of provider models. These tests add no
behavioral coverage; they just guarantee that routine source updates break
CI and cost engineering time to "fix."

**Do not write:** catalog snapshots (`assert "gemini-2.5-pro" in
_PROVIDER_MODELS["gemini"]`), config version literals
(`assert DEFAULT_CONFIG["_config_version"] == 21`), enumeration counts
(`assert len(models) == 8`).

**Do write:** behavior and relationships —

```python
assert raw["_config_version"] == DEFAULT_CONFIG["_config_version"]  # migration reaches latest
assert not (set(moonshot_models) & coding_plan_only_models)         # no plan-only leak
for m in _PROVIDER_MODELS["huggingface"]:                           # every entry has a context length
    assert m.lower() in DEFAULT_CONTEXT_LENGTHS_LOWER
```

The rule: if the test reads like a snapshot of current data, delete it. If
it reads like a contract about how two pieces of data must relate, keep it.
When a PR adds a new provider/model and you want a test, make the test
assert the relationship (e.g. "catalog entries all have context lengths"),
not the specific names.

Reviewers should reject new change-detector tests; authors should convert
them into invariants before re-requesting review.

### Never read source code in tests

A test that reads a source file's text is testing *the shape of the
source code*, not its behavior. This is a hard antipattern, banned outright.
Any test that reads a .py, .ts, .tsx, etc., file is suspect.

**Why it's actively harmful, not just weak:** it passes when the
implementation is subtly broken yet fails when a correct refactor changes
formatting or names (both failure directions wrong); it never executes the
code path it claims to guard (false confidence); and it blocks refactors by
failing on pure structural cleanup.

**Do not write:** `fs.readFileSync('main.ts')` + `assert.match(source,
/spawn\(...\)/)`-style regex assertions on source text.

**Do write — extract the logic into a small pure/DI-testable function and
call it for real:**

```ts
// backend-spawn.ts
export function hiddenWindowsChildOptions(options: SpawnOptionsLike = {}, isWindows = process.platform === 'win32') {
  if (!isWindows || 'windowsHide' in options) return options
  return { ...options, windowsHide: true }
}

// backend-spawn.test.ts
test('windowsHide defaults to true on Windows, is left alone elsewhere', () => {
  assert.equal(hiddenWindowsChildOptions({}, true).windowsHide, true)
  assert.equal(hiddenWindowsChildOptions({}, false).windowsHide, undefined)
  assert.equal(hiddenWindowsChildOptions({ windowsHide: false }, true).windowsHide, false)
})
```

If the logic lives inline in a god-file (`main.ts`, `cli.py`,
`gateway/run.py`) and extracting it feels disruptive: that's the actual
signal to do the extraction, not to regex around it.
