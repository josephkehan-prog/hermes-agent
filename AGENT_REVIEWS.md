# Agent Reviews — Session Findings Log

Findings produced by review/scout sub-agents during the 2026-07-12 autonomous
feature-loop session (Claude Code). Each feature branch was TDD-built, then
audited by a `cavecrew-reviewer` sub-agent before merge; backlog items were
sourced by scout sub-agents. This log records what those agents found — the
real bugs caught pre-merge, the unreliable-backlog lesson, and the
test-isolation root causes — so the review value is preserved beyond the commit
messages.

Baseline at session end: `main == fork/main == 52fde0e1b`.

## Reviewer catches — real bugs fixed before merge

These would have shipped without the adversarial review step. All fixed on the
same branch, with a regression test, before merge.

| Iter | Severity | Bug | Fix |
|---|---|---|---|
| 8 | 🔴 | `uptime_check` schema: a `replace_all` edit updated only one of two look-alike `expect_status` blocks; `check_urls` still declared `"type":"integer"`, making the new `2xx`/`3xx`/set forms unreachable through that entry point. | Widened both schema blocks to `["integer","string"]`; added a schema-consistency test asserting both `check_url` and `check_urls` match. |
| 9 | 🔴 | `notify` click URL: a CR/LF in the URL passed scheme/netloc validation, then `http.client` raised an **uncaught `ValueError`** mid-send (classic header injection → tool crash). | `_validate_click` now rejects control chars; added `except ValueError` on the send path as defense-in-depth. |
| 9 | 🟡 | Same header-injection crash was latent on the existing `title` field (pre-existing, not introduced this session). | The `except ValueError` catch closes it too. |
| 7 | (self-found, reviewer-confirmed) | `session_search` tool handler never forwarded `after`/`before` to the function — the iteration-1 date filters worked when called directly but were silently dropped through the real agent tool. | Handler now threads `after`/`before`/`source`; added handler-level regression tests via `registry.get_entry(...).handler`. |

Clean passes (no findings): iter3 jieba fallback (behavioral equivalence when
jieba present verified), iter4 `json_diff` `ignore_paths` (7 edge cases incl.
segment-aware prefix, empty-string, backward-compat), iter5 `grep_tail`
`case_insensitive` (doubled-`(?i)` proven safe; worker re-validates as
defense-in-depth).

**Takeaway:** the review step earned its cost — two of the catches were
security/correctness bugs (header injection, unreachable schema) that unit tests
alone did not surface, because the tests exercised the function, not the schema
or the real send path.

## Scout findings — the backlog was unreliable

A scout sub-agent proposed 34 backlog features. On inspection, roughly **two of
every three checked were wrong or redundant**:

- `todo` recurrence field — the `todo` tool is an in-memory, per-session
  planner (re-injected after compaction) and a **core** model-tool; a recurrence
  field is both meaningless on an ephemeral store and schema-bloat on every API
  call.
- `kanban` filter-by — `assignee`/`status`/`tenant`/`limit` filters already
  existed.
- Cross-adapter parity items were real but sat in 8000-line adapter files —
  high navigation cost per iteration.

**Rule adopted mid-session:** verify every backlog pick against the code before
building; prefer new skills and bounded gated tools over large adapters and
core-schema tools.

## Test-isolation root causes — "why the runs keep failing"

21 tests failed deterministically on the macOS dev box while passing on Linux
CI, because they read real host state instead of mocking it. All fixed
(`fb57f174c`, `52fde0e1b`); no production code changed.

| Tests | Leak | Fix |
|---|---|---|
| `test_anthropic_adapter` (12) | Token resolution mocked env + `Path.home` but not the macOS **Keychain** (`security find-generic-password`), so a real Claude Code OAuth token leaked into assertions. | Module-level autouse fixture stubbing `_read_claude_code_credentials_from_keychain` → `None`. |
| `test_file_tools` (3) | Asserted the mock was called with `/tmp/...`, but the file tool canonicalizes the path and macOS `/tmp` is a symlink to `/private/tmp`. | Assert against `os.path.realpath(...)` — identity on Linux. |
| `test_list_picker_providers` (1) | Probed the real running Ollama on `localhost:11434`. | Mock `hermes_cli.models.fetch_api_models` → `[]` (config passthrough). |
| `test_model_switch_custom_providers` (3) | Same live-Ollama probe; sibling tests mocked `fetch_api_models`, these three didn't. | Same `fetch_api_models` → `[]` mock. |
| `test_runtime_provider_resolution` (2) | Mocked `resolve_qwen_runtime_credentials` but not `load_pool`; a real qwen credential pool on the machine won resolution first (`runtime_provider.py:1689` before `:1806`). | Mock `load_pool` → `SimpleNamespace(has_credentials=lambda: False)` (file idiom). |

### Not fixable on macOS (do not chase)
Linux/systemd tests (`gateway_service`, `service_manager`, `gateway_wsl`); the
approval-cluster + `live_system_guard` tests (collide with the **running**
gateway, pass on CI); timing flakes (`base_environment` concurrency, LSP e2e,
`mcp_tool_issue_948` malware-timeout, `wecom_callback`, `background_command`,
`shutdown_forensics`, `pip_install_detection`, `signal_handler_kanban_worker`).

## Process notes for future review cycles
- Full suite (~340 files, 36 workers) gets OOM-killed under load with zero
  output — gate code changes on a targeted subset (`scripts/run_tests.sh
  tests/tools/ tests/test_plugin_skills.py`), not the whole suite in background.
- Markdown-only skill changes are safe to gate on the skill suites alone (no
  runtime code imports them).
- Fork CI is the arbiter for the environmental failures above.

## Post-review validation and NousResearch update — 2026-07-12

This log was reviewed against the current tree before merging official
`NousResearch/hermes-agent` `main`.

### Credibility verdict

The recorded reviewer catches and test-isolation fixes are credible:

- Feature commits `f1305c40b`, `d518c6891`, `682ffcd0e`, and `5ad9ff273`
  exist, and the described schema, handler-forwarding, URL-validation, and
  regression-test changes remain in the tree.
- Test-isolation commits `fb57f174c` and `52fde0e1b` exist. Their modified
  tests match the host-state leaks described above.
- The listed failure count is internally consistent: 12 + 3 + 1 + 3 + 2 =
  21 tests.

Two statements above need current-context qualification:

- “Not fixable on macOS” means unsuitable for this live macOS validation run,
  not inherently impossible to fix. Several cases require Linux/systemd;
  others collide with a running gateway or are timing-sensitive.
- The “~340 files” full-suite note is stale. Current discovery finds 2,058
  `test_*.py` files. Continue using targeted suites locally and fork CI for the
  full environmental matrix.

### Additional isolation finding

The canonical test runner used `env -i` but retained real `HOME` and left
`HERMES_HOME` unset until per-test fixtures ran. Collection-time imports could
therefore load `~/.hermes/.env`, inherit Tor proxy settings, and write thousands
of SOCKS warnings to the real agent log before fixture isolation began.

Commit `dff880662` fixes the gap by creating a suite-level temporary
`HERMES_HOME` before Python starts, passing it through the clean environment,
and deleting it when the runner exits. The real SOCKS-warning count remained
unchanged during the focused metadata test run.

### Validation evidence

- Before upstream merge: 482 focused regression tests passed.
- After upstream merge: 486 focused regression tests passed, including the
  release manifest lockstep tests and the three live-model-probe regressions.
- `scripts/release.py` compiled successfully after conflict resolution.
- `git diff --check` passed; working tree was clean after merge.
- Both official `origin/main` and backup branch
  `backup/pre-nous-update-20260712` are ancestors of the merged result.

### Official update record

- Pre-update official tip: `8121dbb16`.
- Fetched official tip: `7b5ba2054`.
- Divergence before merge: 51 local commits and 72 official commits.
- Local preservation commit: `dff880662` (`scripts/run_tests.sh` isolation).
- Backup branch: `backup/pre-nous-update-20260712`.
- Merge commit: `4f5af6847`.
- Only merge conflict: `scripts/release.py`; resolved by preserving the local
  `josephkehan-prog` author mapping and all four new official contributor
  mappings.
- Live checkout `/Users/josephhan/.hermes/hermes-agent` was clean and a direct
  ancestor of the reviewed development branch, then fast-forwarded to the
  merged result. No dependency manifests changed across that fast-forward.
- Hermes gateway was restarted after the live checkout update.

No local commit was reset, rebased away, or discarded.
