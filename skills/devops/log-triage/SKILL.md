---
name: log-triage
description: Parse, classify, and summarize log files for incident triage — tail-and-cap scanning, severity classification, and error clustering for plain text, JSON-lines, syslog, and common app log formats. Local files only, no network. Includes scripts/logtriage.py.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [DevOps, Logs, Triage, Incident, Debugging, Observability]
    category: devops
    related_skills: [self-healing, systematic-debugging]
prerequisites:
  commands: [python3]
---

# Log Triage

A local, keyless incident-triage engine for log files: tail the tail end of
a log, classify each line by severity, cluster repeated errors into
templates, and emit a compact JSON summary. No network calls, no shell-out —
everything is stdlib Python reading files on disk.

## When to Use

- "Something's wrong, what does the log say" — start with `summary` for a
  fast top-level read before diving into the raw file.
- "How many errors in the last hour" / "what's the error breakdown" — `scan`
  with `--level`.
- "Is this the same error repeating, or many different ones" — `cluster`
  collapses near-duplicate errors (same template, different ID/timestamp)
  into one entry with a count, so 500 lines of the same failing request
  read as one incident, not 500.
- Not for: real-time tailing/streaming (this is a single-pass, point-in-time
  read, not a `tail -f` loop — re-run it on a schedule via the `cron`/
  `schedule` skill if you need polling), remote log aggregation (no
  network — pull the file locally first, e.g. with `scp`/`rsync`), or
  structured log *querying* across many files/hosts (this is single-file,
  single-pass; reach for a real log aggregator for fleet-wide search).

## Log formats supported

| Format | How it's classified |
|---|---|
| Plain text (`2024-01-01 12:00:00 ERROR message`) | Regex keyword match: `DEBUG`/`INFO`/`WARN(ING)`/`ERROR`/`FATAL` and common aliases (`CRIT`, `PANIC`, `NOTICE`, `TRACE`, `ERR`, `SEVERE`) |
| JSON-lines (`{"level": "error", "msg": "..."}`) | Parses the line as JSON, reads `level`/`severity`/`loglevel`/`log_level` |
| syslog (`Jan  1 12:00:00 host program[1234]: message`) | Falls back to regex keyword match on the message body (syslog itself carries no explicit level field); timestamp is still extracted for time-span reporting |
| App-specific formats (Python tracebacks, Java stack traces, etc.) | Each physical line is classified independently — a multiline stack trace's continuation lines (indented, `File "..."`, `at com.foo.Bar...`) typically classify as `UNKNOWN` since they carry no level keyword; the triggering `ERROR`/`FATAL` line above them is what gets counted and clustered |

Unrecognized lines are classified `UNKNOWN` rather than guessed — they still
count toward `lines_scanned` but don't inflate the ERROR/WARN totals.

## Workflow

1. **Tail/scan** — `scan <logfile> --since-lines N` reads only the last N
   lines (default 200), capped at 50 MB read from the end regardless of
   total file size, and classifies each line by severity.
2. **Classify severity** — every line gets one of `DEBUG`/`INFO`/`WARN`/
   `ERROR`/`FATAL`/`UNKNOWN`. `scan` reports counts by level and extracts
   the matching lines (`ERROR`+`FATAL` by default, or a single `--level`).
3. **Cluster similar errors** — `cluster <logfile>` normalizes numbers,
   UUIDs, hex addresses, and timestamps in each ERROR/FATAL line to
   placeholders (`<NUM>`, `<UUID>`, `<HEX>`, `<TS>`) and groups by the
   resulting template, reporting the top-N most frequent templates with a
   count and one real example line each. This is the dedup step — three
   "failed to connect to db-uuid `<different-uuid>`" lines collapse to one
   template with `count: 3`.
4. **Summarize** — `summary <logfile>` runs both and adds the log's overall
   time span (first/last timestamp seen in the scanned window), producing
   one compact JSON object suitable for a human or a model to read in one
   shot.

```bash
python3 scripts/logtriage.py scan /var/log/app.log --since-lines 500 --level ERROR
python3 scripts/logtriage.py cluster /var/log/app.log --top-n 5
python3 scripts/logtriage.py summary /var/log/app.log
```

## Model Wiring

Same two-endpoint split used by `watch-notify` and `deal-hunting`: a
deterministic local model for structured extraction, a reasoning model for
narrative synthesis.

| Task | Model | Endpoint | Why |
|---|---|---|---|
| Deterministic error-line extraction / field-parsing (e.g. "pull the request ID and endpoint out of each clustered example line as structured JSON") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable structured output |
| Incident-narrative synthesis (e.g. "given this summary JSON, what happened and what's the likely root cause") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

```python
import json
import urllib.request

# agent1: pull structured fields out of clustered error examples, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract fields from each log line as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Extract from these clustered errors:\n\n{clusters_json}"},
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
# ornith: synthesize "what happened + likely cause" from a summary JSON, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"What happened and what's the likely root cause?\n\n{summary_json}"}],
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

**Verify wiring before relying on it:**

```bash
# agent1 (Ollama, deterministic extraction)
curl -s http://localhost:11434/api/tags | grep -o 'Agents-A1[^"]*'
# ornith (llama-swap, reasoning synthesis)
curl -s http://localhost:1235/v1/models | grep -o 'ornith-uncensored'
```

## Pitfalls

- **Huge logs — always tail/cap.** Never point a generic file-read at a
  multi-gigabyte log; `logtriage.py` seeks from the end and caps total
  bytes read at 50 MB regardless of `--since-lines`, so it's safe by
  default, but a raw `cat`/`open().read()` on the same file is not.
- **Multiline stack traces don't cluster as one unit.** Classification and
  clustering both operate per physical line, so a traceback's continuation
  lines usually come back `UNKNOWN` and won't merge into the triggering
  error's template — read the raw file around a clustered example line if
  you need the full trace, don't expect `cluster` to reassemble it.
- **PII in logs.** Log lines are passed through verbatim in `matches` and
  cluster `example` fields — if the log contains emails, tokens, or other
  sensitive values, that's now in the JSON output too. Don't pipe raw
  `scan`/`summary` output somewhere world-readable without checking first.
- **`--since-lines` counts lines in the read window, not wall-clock time.**
  There's no `--since <duration>` — if you need "last hour", pick a line
  count that comfortably covers it or filter by the `time_span` field
  after the fact.
