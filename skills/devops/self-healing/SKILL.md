---
name: self-healing
description: Monitor, detect, and remediate local service health.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [DevOps, Self-Healing, Monitoring, Remediation, Health-Check, Automation]
    category: devops
    related_skills: [watch-notify, local-model-ops]
prerequisites:
  commands: [python3, pgrep]
---

# Self-Healing

A runbook-driven watchdog: define a set of health checks and, per check, an
optional remediation action. Run it once to see status, or run it with
`--confirm` to let it act on failures. Everything destructive is dry-run by
default.

## When to Use

- "Restart the worker if it dies" / "clear the temp dir if disk gets full"
  / "page me if ornith goes down" — anything that fits check → threshold →
  action.
- You already have discrete health signals (`uptime_check_tool`,
  `pgrep`, disk/load) and want one engine to poll them on a schedule and
  react, instead of hand-rolling a bash script per service.
- Not for: `watch-notify`'s job — content-hash/JSON-field *change*
  detection on arbitrary sources has no remediation step, it's alert-only.
  Reach for `watch-notify` when you just want "tell me when X changes."
  Not for `local-model-ops`'s job either — that skill is the *manual*
  troubleshooting runbook (commands to run yourself); this skill is the
  *automated* version of the same checks, wired into a scheduled
  check→remediate loop.

## Ethics / Safety

Remediation actions (`restart`, `clear-temp`) are **destructive** — they run
a subprocess or delete files. `selfheal.py run` is **dry-run by default**:
without `--confirm` it only prints what it would do. Passing `--confirm`
authorizes every gated action in the runbook for that run; there is no
per-action confirmation prompt, so review the runbook's `remediations`
block before you ever run it with `--confirm`, especially one you didn't
author yourself. `alert-only` is not gated (nothing destructive happens) —
it always fires on a failing check.

## Check catalog

| Type | What it checks | Backing |
|---|---|---|
| `http` | Any HTTP(S) endpoint's reachability/status/body substring | `tools.uptime_check_tool.check_url` — same SSRF guard as `watch-notify` (rejects loopback/private targets by design; **not** for checking your own localhost services, see `local_model` below) |
| `local_model` | agent1 (`:11434`) or ornith (`:1235`) reachability | A narrow, hardcoded-allowlist loopback fetch (fixed host/port/path per name, never runbook-supplied) — the one place this script calls `urlopen` directly, because `check_url`'s guard structurally can't reach loopback. See `scripts/selfheal.py`'s module docstring for the full rationale. |
| `process` | Is a process alive matching a pattern | `pgrep -f <pattern>` via `subprocess.run` (list-args, no shell) |
| `disk` | Free space % on a path | `shutil.disk_usage` |
| `load` | 1-minute load average | `os.getloadavg()` (POSIX only — no Windows support, hence `platforms: [linux, macos]` above) |

For a process spawned and tracked by Hermes itself (not an external
daemon), `tools/process_registry.py`'s `process_registry.poll(session_id)`
is a richer alternative to `pgrep` — it distinguishes "still running" from
"finished" from "crashed," and can tail output. `selfheal.py`'s `process`
check type is deliberately the simpler, universal `pgrep` case; wire
`process_registry` in yourself if the target is a Hermes-managed session.

## Remediation catalog

| Action | What it does | Gated? |
|---|---|---|
| `restart` | Runs `command` (a JSON list of argv strings) via `subprocess.run` | Yes — `--confirm` required, dry-run prints the argv otherwise |
| `clear-temp` | Deletes files under `path` matching a glob `pattern` | Yes — `--confirm` required; refuses `/` and `$HOME`, and `path` must resolve under an allowed temp root (`tempfile.gettempdir()`, `/tmp`, `/var/tmp`, or `$TMPDIR` if set) — still scope `path` narrowly yourself |
| `alert-only` | Sends a push notification via `tools.notify_tool.notify` (ntfy.sh) | No — always fires on a failing check, nothing destructive happens |

## Runbook format

A runbook is one JSON file: a list of `checks` (each with a unique `id` and
a `type` from the catalog above) and a list of `remediations` (each tied to
a `check_id` by exact match, with an `action` from the catalog above). A
check with no matching remediation just gets reported as failing — nothing
runs.

```json
{
  "name": "local-model-watchdog",
  "checks": [
    {"id": "agent1-up", "type": "local_model", "name": "agent1"},
    {"id": "worker-alive", "type": "process", "pattern": "hermes-worker"},
    {"id": "disk-free", "type": "disk", "path": "/", "min_free_pct": 10},
    {"id": "load-ok", "type": "load", "max_1min": 8.0}
  ],
  "remediations": [
    {"check_id": "worker-alive", "action": "restart", "command": ["systemctl", "restart", "hermes-worker"]},
    {"check_id": "disk-free", "action": "clear-temp", "path": "/tmp/hermes-scratch", "pattern": "*.tmp"},
    {"check_id": "agent1-up", "action": "alert-only", "topic": "hermes-selfheal-<random>", "message": "agent1 down"}
  ]
}
```

See `scripts/example.json` for a runnable copy (swap the placeholder ntfy
topic before using `alert-only` for real — see
[watch-notify's ntfy topic privacy note](../../research/watch-notify/SKILL.md#notification-backends)).

## Workflow

1. **Define** a runbook (above) — start from `scripts/example.json`.
2. **Check**: `python3 selfheal.py check runbook.json` — report-only, prints
   a status table, exit 0 if everything passed, 1 if anything failed. Never
   remediates, safe to run anytime (e.g. from a heartbeat or cron poll).
3. **Detect + dry-run**: `python3 selfheal.py run runbook.json` — same
   checks, and for each failure with a matching remediation, prints what it
   *would* run without executing it.
4. **Remediate**: `python3 selfheal.py run runbook.json --confirm` — same
   as above, but gated actions actually execute. `alert-only` fires either
   way.
5. **Notify**: wire `alert-only` remediations into the runbook for the
   checks you want a push for, or pipe `run`'s stdout into
   `watch-notify`'s `notify` command yourself for a summary alert.

This script does one pass per invocation and never loops — same convention
as `watch-notify`'s `watch.py`. Put `check`/`run` on a `cron`/`schedule`
skill entry to poll.

## Model Wiring

Same two-endpoint split as `watch-notify` and `deal-hunting`, for
workflows checking many runbooks or triaging a noisy failure batch instead
of reading `check`'s table by hand:

| Task | Model | Endpoint | Why |
|---|---|---|---|
| Deterministic status-table parsing/summarizing (e.g. "collapse this batch of `check` runs across N runbooks into one JSON list of failing checks") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable structured output |
| "Should I remediate / what's the root cause" triage (e.g. "disk-free failed and load-ok failed together — is clear-temp the right call, or is something else eating disk?") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

```python
import json
import urllib.request

# agent1: summarize a batch of check results, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "List which checks are failing as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Summarize:\n\n{results_json}"},
    ],
    "options": {"temperature": 0},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:11434/api/chat",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["message"]["content"]
```

```python
# ornith: triage root cause / whether to remediate, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Given these failing checks, is remediation safe or is this a symptom of something else?\n\n{results_json}"}],
    "chat_template_kwargs": {"enable_thinking": False},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:1235/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
```

Verify wiring before relying on it (or just run `python3 selfheal.py
status`, which checks both endpoints directly):

```bash
curl -s http://localhost:11434/api/tags | grep -o '"hf.co/InternScience/Agents-A1[^"]*"'
curl -s http://localhost:1235/v1/models | grep -o '"ornith-uncensored"'
```

## Pitfalls

- **Remediation loops / flapping**: a `restart` remediation that fixes the
  symptom but not the cause (e.g. a worker that OOMs and gets restarted
  every poll) will just loop. This engine has no backoff or loop-detection
  built in — if you need it, track a restart counter/timestamp in your own
  state file and skip the remediation once a threshold is crossed within a
  window, the same way you'd throttle any cron-driven action.
- **Destructive-action safety is real but scoped to temp roots**:
  `clear-temp` refuses `/`, `$HOME`, and any path that doesn't resolve
  under an allowed temp root (`tempfile.gettempdir()`, `/tmp`, `/var/tmp`,
  or `$TMPDIR` if set) — it will still happily delete matching files
  anywhere under those roots, including a path with important data if you
  point it there by mistake. Scope `path` to an actual scratch/temp
  directory, every time.
- **`--confirm` is all-or-nothing per run**: it authorizes every gated
  remediation that fires in that invocation, not just one. Don't attach a
  runbook you haven't read to `--confirm` on a schedule.
- **Alert fatigue**: `alert-only` fires on every failing check, every run,
  with no de-dup — a flapping check pages every poll interval. Pair with a
  state file (like `watch-notify`'s) if you need "alert once per outage"
  instead of "alert every poll," or space the runbook's polling interval
  out.
- **`http` checks can't see your own localhost services** — that's
  `check_url`'s SSRF guard doing its job (see `local_model` in the check
  catalog above for the intended path). Don't try to work around the guard
  for a generic `http` check; add a well-known local service to
  `LOCAL_MODEL_ENDPOINTS` in `scripts/selfheal.py` instead if you need to
  extend past agent1/ornith.
- **`load` checks don't work on Windows**: `os.getloadavg()` isn't
  available there (`platforms: [linux, macos]` above is not a formality).
- **ntfy topic privacy**: same as `watch-notify` — `alert-only`'s `topic`
  is public by default on ntfy.sh, use a long unguessable name, never put
  secrets in `message`.
